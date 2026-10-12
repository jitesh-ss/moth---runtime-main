"""Run the isolated control/instructed Runtime 5.0 relation campaign."""

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
    DELIVERY, SURFACE, decision_source, semantic_contract, semantic_source,
)

from .rule_compiler import compile_relation_identification


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
RULE_FIXTURE = HERE / "fixtures/relation-identification-en-1.0.json"
CAMPAIGN_FIXTURE = HERE / "fixtures/campaign-en-1.0.json"
THRESHOLDS = read_json(ROOT / "config/v5.0/grounding-en-1.0.json")["thresholds"]


class CampaignFailure(AssertionError):
    pass


def _tree_hash(path: Path) -> str:
    result = hashlib.sha256()
    for child in sorted(item for item in path.rglob("*") if item.is_file() and "__pycache__" not in item.parts):
        result.update(child.relative_to(ROOT).as_posix().encode())
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


def _quoted(value: Any) -> str:
    return json.dumps(json.dumps(value, separators=(",", ":")))


def _instructed_source(rules: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    rows = [decision_source()]
    manifests = []
    for domain in ("delivery", "deployment"):
        contract, manifest = compile_relation_identification(semantic_contract(domain), rules)
        manifests.append({"domain": domain, **manifest})
        rows.append(f'Semantic contract "{domain}-en" is canonical semantic JSON {_quoted(contract)}.')
    return "\n".join(rows) + "\n", manifests


def _sentence(value: str) -> str:
    return value[0].upper() + value[1:]


def _prompt(clauses: list[str]) -> str:
    return ". ".join(_sentence(value) for value in clauses) + "."


def _known_prompt(domain: str) -> str:
    if domain == "delivery":
        return DELIVERY
    return _prompt([
        "deployment engineer lacks server access",
        "deployment engineer has production approval",
        "deployment engineer can finish before the deadline",
        "backup engineer has production access",
        "backup engineer has deployment approval",
        "backup engineer can finish before the deadline",
        "validate the proposed plan and select a replacement",
    ])


def _case_prompt(domain: str, first_clause: str) -> str:
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


def _make_store(path: Path, input_source: str, real_encoder: Any) -> tuple[WorldStore, Any, dict[Any, Any]]:
    deterministic = DeterministicEncoder()
    store = WorldStore(path)
    store.publish(WorldRole.INPUT, {"input.moth": input_source}, encoder=real_encoder)
    store.publish(WorldRole.MAIN, {"main.moth": decision_source()}, encoder=deterministic)
    store.publish(WorldRole.SURFACE, {"surface.moth": SURFACE}, encoder=deterministic)
    bundle = store.activate()
    return store, bundle, store.bundle_worlds(bundle)


def _cases(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        {**row, "category": "RELATION_HOLDOUT", "prompt": _case_prompt(row["domain"], row["clause"])}
        for row in fixture["relation_holdouts"]
    ]
    rows.extend(
        {**row, "category": "MIXED_HOLDOUT", "prompt": _case_prompt(row["domain"], row["clause"])}
        for row in fixture["mixed_holdouts"]
    )
    rows.extend({**row, "category": "ADVERSARIAL"} for row in fixture["adversarial"])
    if len(rows) != 28 or len({row["id"] for row in rows}) != 28:
        raise CampaignFailure("campaign must contain exactly 28 unique cases")
    return rows


def run_campaign() -> dict[str, Any]:
    started = time.monotonic()
    rules = json.loads(RULE_FIXTURE.read_text())
    fixture = json.loads(CAMPAIGN_FIXTURE.read_text())
    if fixture.get("schema") != "moth-v5-compiled-relation-identification-campaign/1.0" or fixture.get("frozen_before_execution") is not True:
        raise CampaignFailure("campaign fixture is not frozen")
    cases = _cases(fixture)
    instructed_source, compiled_manifests = _instructed_source(rules)
    before = _protected_hashes()
    original_connect = socket.socket.connect
    network_attempts = 0

    def blocked_connect(instance, address):
        nonlocal network_attempts
        network_attempts += 1
        raise RuntimeError(f"network disabled during compiled relation experiment: {address}")

    socket.socket.connect = blocked_connect
    try:
        with TemporaryDirectory(prefix="moth-v5-relation-id-") as temporary:
            encoder = LocalBGEEncoder()
            encoder_record = encoder.verify_assets()
            control, control_bundle, _ = _make_store(
                Path(temporary) / "control-store-5.0.sqlite3",
                semantic_source("delivery", "deployment"), encoder,
            )
            instructed, instructed_bundle, instructed_worlds = _make_store(
                Path(temporary) / "instructed-store-5.0.sqlite3",
                instructed_source, encoder,
            )
            control_main = control.bundle_worlds(control_bundle)[WorldRole.MAIN].world_hash
            instructed_main = instructed_worlds[WorldRole.MAIN].world_hash
            control_surface = control.bundle_worlds(control_bundle)[WorldRole.SURFACE].world_hash
            instructed_surface = instructed_worlds[WorldRole.SURFACE].world_hash

            control_rows = []
            for case in cases[:12]:
                result = control.query(case["prompt"], encoder=encoder, thresholds=THRESHOLDS)
                control_rows.append({"id": case["id"], "status": result["status"], "refusal": result.get("refusal", {}).get("code")})

            baselines = {}
            for domain in ("delivery", "deployment"):
                result = instructed.query(_known_prompt(domain), encoder=encoder, thresholds=THRESHOLDS)
                if result.get("status") != "ANSWER":
                    raise CampaignFailure(f"{domain}: instructed exact baseline refused")
                baselines[domain] = {"graph": _graph(result), "value": result["output"]["value"]}

            categories = {name: Counter() for name in ("RELATION_HOLDOUT", "MIXED_HOLDOUT", "ADVERSARIAL")}
            classifications: Counter[str] = Counter()
            refusal_codes: Counter[str] = Counter()
            rows = []
            replay_count = 0
            for case in cases:
                result = instructed.query(case["prompt"], encoder=encoder, thresholds=THRESHOLDS)
                replay = instructed.replay(str(result["episode_id"]), encoder_free=True)
                if replay != canonical_bytes(result):
                    raise CampaignFailure(f"{case['id']}: encoder-free replay differs")
                replay_count += 1
                if case["category"] == "ADVERSARIAL":
                    classification = "SAFE_REFUSAL" if result["status"] == "REFUSAL" else "UNSAFE_ACCEPT"
                elif result["status"] == "REFUSAL":
                    classification = "SAFE_REFUSAL"
                elif _graph(result) == baselines[case["domain"]]["graph"] and result["output"]["value"] == baselines[case["domain"]]["value"]:
                    classification = "CORRECT_ACCEPT"
                else:
                    classification = "UNSAFE_ACCEPT"
                classifications[classification] += 1
                categories[case["category"]][classification] += 1
                refusal = result.get("refusal", {}).get("code")
                if refusal:
                    refusal_codes[str(refusal)] += 1
                if result.get("execution") != {"performed": False, "dispatch_count": 0}:
                    raise CampaignFailure(f"{case['id']}: execution contract changed")
                rows.append({
                    "id": case["id"], "category": case["category"],
                    "classification": classification, "status": result["status"],
                    "refusal": refusal,
                    "graph": _graph(result) if result["status"] == "ANSWER" else None,
                    "result_hash": result["replay"]["result_hash"],
                })

            baseline = instructed.query(_known_prompt("delivery"), encoder=encoder, thresholds=THRESHOLDS)
            tampered = deepcopy(baseline)
            tampered["stages"][0]["program"]["grounding"]["semantic_interpretation"]["facts"][0]["polarity"] = "TAMPERED"
            try:
                verify_archived_result(tampered, instructed_worlds, instructed_bundle)
            except IntegrityError:
                tamper_detected = True
            else:
                tamper_detected = False
    finally:
        socket.socket.connect = original_connect

    after = _protected_hashes()
    control_refusals = sum(row["status"] == "REFUSAL" for row in control_rows)
    relation_accepts = categories["RELATION_HOLDOUT"]["CORRECT_ACCEPT"]
    adversarial_refusals = categories["ADVERSARIAL"]["SAFE_REFUSAL"]
    unsafe = classifications["UNSAFE_ACCEPT"]
    safety_integrity_passed = (
        control_refusals == 12 and unsafe == 0
        and adversarial_refusals == 8 and replay_count == 28 and tamper_detected
        and control_main == instructed_main and control_surface == instructed_surface
        and network_attempts == 0 and before == after
    )
    capability_target_met = relation_accepts == 12
    result_manifest_hash = sha256_bytes(canonical_bytes(rows))
    result = {
        "schema": "moth-v5-compiled-relation-identification-result/1.0",
        "verdict": (
            "COMPILED_RELATION_IDENTIFICATION_CONFIRMED"
            if capability_target_met and safety_integrity_passed
            else "COMPILED_RELATION_IDENTIFICATION_PARTIALLY_CONFIRMED"
        ),
        "capability_target_met": capability_target_met,
        "safety_integrity_passed": safety_integrity_passed,
        "cases": 28,
        "control_relation_refusals": control_refusals,
        "control_rows": control_rows,
        "classifications": dict(sorted(classifications.items())),
        "categories": {key: dict(sorted(value.items())) for key, value in categories.items()},
        "correct_accept_ids": [row["id"] for row in rows if row["classification"] == "CORRECT_ACCEPT"],
        "safe_refusal_ids": [row["id"] for row in rows if row["classification"] == "SAFE_REFUSAL"],
        "refusal_codes": dict(sorted(refusal_codes.items())),
        "unsafe_acceptances": unsafe,
        "adversarial_refusals": adversarial_refusals,
        "encoder_free_replays": replay_count,
        "semantic_tamper_detected": tamper_detected,
        "main_world_identical": control_main == instructed_main,
        "surface_world_identical": control_surface == instructed_surface,
        "network_attempts": network_attempts,
        "execution_performed": False,
        "dispatch_count": 0,
        "encoder": encoder_record,
        "thresholds": THRESHOLDS["SEMANTIC_SURFACE"],
        "compiled_rule_manifests": compiled_manifests,
        "rule_fixture_sha256": sha256_bytes(RULE_FIXTURE.read_bytes()),
        "campaign_fixture_sha256": sha256_bytes(CAMPAIGN_FIXTURE.read_bytes()),
        "result_manifest_sha256": result_manifest_hash,
        "protected_hashes_unchanged": before == after,
        "protected_hashes": before,
        "duration_seconds": round(time.monotonic() - started, 3),
    }
    if not safety_integrity_passed:
        raise CampaignFailure(json.dumps(result, indent=2, sort_keys=True))
    return result


def main() -> None:
    print(json.dumps(run_campaign(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
