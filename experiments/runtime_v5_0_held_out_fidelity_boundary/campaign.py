"""Run the final real-BGE held-out fidelity boundary campaign."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import socket
from tempfile import TemporaryDirectory
import time
from typing import Any

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from moth_runtime_v5_0.canonical import canonical_bytes, read_json, sha256_bytes
from moth_runtime_v5_0.encoder import DeterministicEncoder, LocalBGEEncoder
from moth_runtime_v5_0.model import IntegrityError, WorldRole
from moth_runtime_v5_0.runtime import verify_archived_result
from moth_runtime_v5_0.store import WorldStore

from tests.test_runtime_v5_0_language import (
    DELIVERY, SURFACE, decision_source, semantic_source,
)


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures/campaign-en-1.0.json"
THRESHOLDS = read_json(ROOT / "config/v5.0/grounding-en-1.0.json")["thresholds"]


class CampaignFailure(AssertionError):
    pass


def _tree_hash(path: Path) -> str:
    result = hashlib.sha256()
    for child in sorted(item for item in path.rglob("*") if item.is_file() and "__pycache__" not in item.parts):
        result.update(child.relative_to(ROOT).as_posix().encode("utf-8"))
        result.update(b"\0")
        result.update(hashlib.sha256(child.read_bytes()).digest())
    return result.hexdigest()


def _protected_hashes() -> dict[str, str]:
    store = ROOT / "data/store-5.0.sqlite3"
    return {
        "runtime_tree": _tree_hash(ROOT / "src/moth_runtime_v5_0"),
        "configuration_tree": _tree_hash(ROOT / "config/v5.0"),
        "architecture_lock": sha256_bytes((ROOT / "config/v5.0/ARCHITECTURE-LOCK.json").read_bytes()),
        "production_store": sha256_bytes(store.read_bytes()) if store.is_file() else "ABSENT",
    }


def _sentence(value: str) -> str:
    return value[0].upper() + value[1:]


def _prompt(clauses: list[str]) -> str:
    return ". ".join(_sentence(value) for value in clauses) + "."


def _known_prompt(domain: str, proposed: str, backup: str) -> str:
    if domain == "delivery":
        return _prompt([
            f"{proposed} lacks cold storage",
            f"{proposed} has road permit",
            f"{proposed} can meet the deadline",
            f"{backup} has refrigeration",
            f"{backup} has road permit",
            f"{backup} can meet the deadline",
            "validate the proposed plan and select a replacement",
        ])
    return _prompt([
        f"{proposed} lacks server access",
        f"{proposed} has production approval",
        f"{proposed} can finish before the deadline",
        f"{backup} has production access",
        f"{backup} has deployment approval",
        f"{backup} can finish before the deadline",
        "validate the proposed plan and select a replacement",
    ])


def _heldout_frame_prompt(domain: str, first_clause: str) -> str:
    if domain == "delivery":
        tail = [
            "Direct courier has road permit", "Direct courier can meet the deadline",
            "Backup courier has refrigeration", "Backup courier has road permit",
            "Backup courier can meet the deadline",
            "validate the proposed plan and select a replacement",
        ]
    else:
        tail = [
            "Deployment engineer has production approval", "Deployment engineer can finish before the deadline",
            "Backup engineer has production access", "Backup engineer has deployment approval",
            "Backup engineer can finish before the deadline",
            "validate the proposed plan and select a replacement",
        ]
    return _prompt([first_clause, *tail])


def _graph(result: dict[str, Any]) -> str:
    return str(result["stages"][0]["program"]["grounding"]["semantic_interpretation"]["semantic_graph_hash"])


def _vector_evidence(result: dict[str, Any]) -> list[dict[str, Any]]:
    if result.get("status") != "ANSWER":
        return []
    rows = result["stages"][0]["program"]["grounding"]["semantic_interpretation"]["clause_evidence"]
    return [
        evidence
        for row in rows
        for side in ("subject", "object")
        if isinstance((evidence := row.get(side)), dict) and evidence.get("method") == "vector"
    ]


def _cases(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in fixture["entity_surface_holdouts"]:
        result.append({**row, "category": "ENTITY_SURFACE_HOLDOUT", "prompt": _known_prompt(row["domain"], row["proposed"], row["backup"])})
    for row in fixture["relation_frame_holdouts"]:
        result.append({**row, "category": "RELATION_FRAME_HOLDOUT", "prompt": _heldout_frame_prompt(row["domain"], row["clause"])})
    for row in fixture["mixed_holdouts"]:
        result.append({**row, "category": "MIXED_HOLDOUT", "prompt": _heldout_frame_prompt(row["domain"], row["clause"])})
    result.extend({**row, "category": "ADVERSARIAL"} for row in fixture["adversarial"])
    if len(result) != 40 or len({row["id"] for row in result}) != 40:
        raise CampaignFailure("campaign must contain exactly 40 unique cases")
    return result


def run_campaign() -> dict[str, Any]:
    started = time.monotonic()
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if fixture.get("schema") != "moth-v5-held-out-fidelity-campaign/1.0" or not fixture.get("frozen_before_execution"):
        raise CampaignFailure("held-out campaign fixture is not frozen")
    cases = _cases(fixture)
    before = _protected_hashes()
    classifications: Counter[str] = Counter()
    categories: dict[str, Counter[str]] = {
        name: Counter() for name in (
            "ENTITY_SURFACE_HOLDOUT", "RELATION_FRAME_HOLDOUT", "MIXED_HOLDOUT", "ADVERSARIAL",
        )
    }
    refusal_codes: Counter[str] = Counter()
    evidence_scores: list[float] = []
    evidence_margins: list[float] = []
    rows: list[dict[str, Any]] = []
    replay_count = 0
    network_attempts = 0
    original_connect = socket.socket.connect

    def blocked_connect(instance, address):
        nonlocal network_attempts
        network_attempts += 1
        raise RuntimeError(f"network disabled during held-out campaign: {address}")

    socket.socket.connect = blocked_connect
    try:
        with TemporaryDirectory(prefix="moth-v5-heldout-") as temporary:
            real_encoder = LocalBGEEncoder()
            encoder_record = real_encoder.verify_assets()
            deterministic = DeterministicEncoder()
            store = WorldStore(Path(temporary) / "store-5.0.sqlite3")
            store.publish(WorldRole.INPUT, {"input.moth": semantic_source("delivery", "deployment")}, encoder=real_encoder)
            store.publish(WorldRole.MAIN, {"main.moth": decision_source()}, encoder=deterministic)
            store.publish(WorldRole.SURFACE, {"surface.moth": SURFACE}, encoder=deterministic)
            bundle = store.activate()
            worlds = store.bundle_worlds(bundle)

            baselines = {}
            calibration_prompts = {
                "delivery": DELIVERY,
                "deployment": _known_prompt(
                    "deployment", "deployment engineer", "backup engineer",
                ),
            }
            for domain, prompt in calibration_prompts.items():
                baseline = store.query(prompt, encoder=real_encoder, thresholds=THRESHOLDS)
                if baseline.get("status") != "ANSWER":
                    raise CampaignFailure(f"{domain}: exact baseline refused")
                baselines[domain] = {
                    "graph": _graph(baseline),
                    "value": baseline["output"]["value"],
                }

            for case in cases:
                result = store.query(case["prompt"], encoder=real_encoder, thresholds=THRESHOLDS)
                replay = store.replay(str(result["episode_id"]), encoder_free=True)
                if replay != canonical_bytes(result):
                    raise CampaignFailure(f"{case['id']}: encoder-free replay differs")
                replay_count += 1
                category = case["category"]
                if category == "ADVERSARIAL":
                    classification = "SAFE_REFUSAL" if result.get("status") == "REFUSAL" else "UNSAFE_ACCEPT"
                elif result.get("status") == "REFUSAL":
                    classification = "SAFE_REFUSAL"
                elif (
                    result.get("status") == "ANSWER"
                    and _graph(result) == baselines[case["domain"]]["graph"]
                    and result.get("output", {}).get("value") == baselines[case["domain"]]["value"]
                ):
                    classification = "CORRECT_ACCEPT"
                else:
                    classification = "UNSAFE_ACCEPT"
                classifications[classification] += 1
                categories[category][classification] += 1
                refusal = result.get("refusal", {}).get("code")
                if refusal:
                    refusal_codes[str(refusal)] += 1
                vectors = _vector_evidence(result)
                if classification == "CORRECT_ACCEPT" and category == "ENTITY_SURFACE_HOLDOUT" and not vectors:
                    raise CampaignFailure(f"{case['id']}: held-out entity accepted without vector evidence")
                for evidence in vectors:
                    evidence_scores.append(float(evidence["score"]))
                    evidence_margins.append(float(evidence["margin"]))
                if result.get("execution") != {"performed": False, "dispatch_count": 0}:
                    raise CampaignFailure(f"{case['id']}: execution contract changed")
                rows.append({
                    "id": case["id"], "category": category,
                    "classification": classification, "status": result["status"],
                    "refusal": refusal, "graph": _graph(result) if result["status"] == "ANSWER" else None,
                    "vector_scores": [float(item["score"]) for item in vectors],
                    "vector_margins": [float(item["margin"]) for item in vectors],
                    "result_hash": result["replay"]["result_hash"],
                })

            baseline = store.query(DELIVERY, encoder=real_encoder, thresholds=THRESHOLDS)
            tampered = deepcopy(baseline)
            tampered["stages"][0]["program"]["grounding"]["semantic_interpretation"]["facts"][0]["polarity"] = "TAMPERED"
            try:
                verify_archived_result(tampered, worlds, bundle)
            except IntegrityError:
                tamper_detected = True
            else:
                tamper_detected = False
    finally:
        socket.socket.connect = original_connect

    after = _protected_hashes()
    unsafe = classifications["UNSAFE_ACCEPT"]
    adversarial_refusals = categories["ADVERSARIAL"]["SAFE_REFUSAL"]
    passed = (
        unsafe == 0 and adversarial_refusals == 8 and replay_count == 40
        and tamper_detected and before == after and network_attempts == 0
    )
    if not passed:
        raise CampaignFailure(
            f"held-out safety gate failed: unsafe={unsafe}, adversarial_refusals={adversarial_refusals}, "
            f"replays={replay_count}, tamper={tamper_detected}, network={network_attempts}"
        )

    result_manifest_sha256 = sha256_bytes(canonical_bytes(rows))
    return {
        "schema": "moth-v5-held-out-fidelity-result/1.0",
        "verdict": "HELD_OUT_FIDELITY_BOUNDARY_CONFIRMED",
        "cases": 40,
        "calibration_cases": 2,
        "classifications": dict(sorted(classifications.items())),
        "categories": {key: dict(sorted(value.items())) for key, value in categories.items()},
        "refusal_codes": dict(sorted(refusal_codes.items())),
        "unsafe_acceptances": unsafe,
        "adversarial_refusals": adversarial_refusals,
        "encoder_free_replays": replay_count,
        "semantic_tamper_detected": tamper_detected,
        "network_attempts": network_attempts,
        "execution_performed": False,
        "dispatch_count": 0,
        "encoder": encoder_record,
        "thresholds": THRESHOLDS["SEMANTIC_SURFACE"],
        "accepted_vector_score_range": [min(evidence_scores), max(evidence_scores)] if evidence_scores else None,
        "accepted_vector_margin_range": [min(evidence_margins), max(evidence_margins)] if evidence_margins else None,
        "correct_accepts": [
            {
                "id": row["id"], "category": row["category"],
                "vector_scores": row["vector_scores"],
                "vector_margins": row["vector_margins"],
            }
            for row in rows if row["classification"] == "CORRECT_ACCEPT"
        ],
        "safe_refusal_ids": {
            category: [
                row["id"] for row in rows
                if row["category"] == category and row["classification"] == "SAFE_REFUSAL"
            ]
            for category in categories
        },
        "protected_hashes_unchanged": before == after,
        "protected_hashes": before,
        "fixture_sha256": sha256_bytes(FIXTURE.read_bytes()),
        "result_manifest_sha256": result_manifest_sha256,
        "duration_seconds": round(time.monotonic() - started, 3),
    }


def main() -> None:
    print(json.dumps(run_campaign(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
