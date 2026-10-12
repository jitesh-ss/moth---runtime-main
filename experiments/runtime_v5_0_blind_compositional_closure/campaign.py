"""Run the final sealed blind compositional-closure campaign."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
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
from tests.test_runtime_v5_0_language import DELIVERY, SURFACE, decision_source, semantic_source

from .field import ablate_field, compile_field
from .instance import CompositionalInstance, CompositionIntegrityError


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FIELD_FIXTURE = HERE / "fixtures/field-en-1.0.json"
CAMPAIGN_FIXTURE = HERE / "fixtures/blind-campaign-en-1.0.json"
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


def _graph(record: dict[str, Any]) -> str:
    return str(record["base_result"]["stages"][0]["program"]["grounding"]["semantic_interpretation"]["semantic_graph_hash"])


def _no_complete_test_language_in_field(field_text: str, fixture: dict[str, Any]) -> bool:
    folded_field = field_text.casefold()
    for group in ("equivalent", "contrasts", "refusals"):
        for row in fixture[group]:
            prompt = row["prompt"].casefold()
            if prompt in folded_field:
                return False
            for sentence in (part.strip() for part in re.split(r"[.!?;]+", prompt) if part.strip()):
                if sentence in folded_field:
                    return False
    return True


def run_campaign() -> dict[str, Any]:
    started = time.monotonic()
    field_bytes = FIELD_FIXTURE.read_bytes()
    field_source = json.loads(field_bytes)
    fixture = json.loads(CAMPAIGN_FIXTURE.read_text())
    field_sha = sha256_bytes(field_bytes)
    if (
        fixture.get("schema") != "moth-v5-blind-compositional-closure-campaign/1.0"
        or fixture.get("frozen_after_field_seal") is not True
        or fixture.get("sealed_field_sha256") != field_sha
    ):
        raise CampaignFailure("blind campaign is not bound to the sealed field")
    if [len(fixture[key]) for key in ("equivalent", "contrasts", "refusals", "ablations")] != [12, 6, 10, 6]:
        raise CampaignFailure("blind campaign case counts changed")
    no_complete_frames = _no_complete_test_language_in_field(field_bytes.decode(), fixture)
    if not no_complete_frames:
        raise CampaignFailure("complete blind test language leaked into the field")
    compiled_field = compile_field(field_source)
    before = _protected_hashes()
    network_attempts = 0
    original_connect = socket.socket.connect

    def blocked_connect(instance, address):
        nonlocal network_attempts
        network_attempts += 1
        raise RuntimeError(f"network disabled during compositional closure campaign: {address}")

    socket.socket.connect = blocked_connect
    try:
        with TemporaryDirectory(prefix="moth-v5-compositional-") as temporary:
            encoder = LocalBGEEncoder()
            encoder_record = encoder.verify_assets()
            deterministic = DeterministicEncoder()
            store = WorldStore(Path(temporary) / "store-5.0.sqlite3")
            store.publish(WorldRole.INPUT, {"input.moth": semantic_source("delivery")}, encoder=encoder)
            store.publish(WorldRole.MAIN, {"main.moth": decision_source()}, encoder=deterministic)
            store.publish(WorldRole.SURFACE, {"surface.moth": SURFACE}, encoder=deterministic)
            bundle = store.activate()
            worlds = store.bundle_worlds(bundle)
            instance = CompositionalInstance(store, encoder, THRESHOLDS, compiled_field)

            baseline = store.query(DELIVERY, encoder=encoder, thresholds=THRESHOLDS)
            if baseline["status"] != "ANSWER":
                raise CampaignFailure("rigid Runtime 5.0 baseline refused")
            baseline_graph = str(baseline["stages"][0]["program"]["grounding"]["semantic_interpretation"]["semantic_graph_hash"])
            baseline_output = baseline["output"]["value"]

            control_answers = 0
            control_rows = []
            for row in fixture["equivalent"]:
                result = store.query(row["prompt"], encoder=encoder, thresholds=THRESHOLDS)
                if result["status"] == "ANSWER":
                    control_answers += 1
                control_rows.append({"id": row["id"], "status": result["status"], "refusal": result.get("refusal", {}).get("code")})

            classifications: Counter[str] = Counter()
            rows = []
            replay_count = 0
            equivalent_graphs = set()
            contrast_graphs = set()
            for group in ("equivalent", "contrasts", "refusals"):
                for case in fixture[group]:
                    record = instance.query(case["prompt"])
                    if instance.replay(record["episode_id"], encoder_free=True) != canonical_bytes(record):
                        raise CampaignFailure(f"{case['id']}: compositional replay changed")
                    replay_count += 1
                    if group == "equivalent":
                        correct = record["status"] == "ANSWER" and _graph(record) == baseline_graph and record["output"]["value"] == baseline_output
                        classification = "CORRECT_EQUIVALENT" if correct else "SAFE_REFUSAL" if record["status"] == "REFUSAL" else "UNSAFE_ACCEPT"
                        if record["status"] == "ANSWER":
                            equivalent_graphs.add(_graph(record))
                    elif group == "contrasts":
                        correct = record["status"] == "ANSWER" and record["output"]["value"] == case["expected"] and _graph(record) != baseline_graph
                        classification = "CORRECT_CONTRAST" if correct else "SAFE_REFUSAL" if record["status"] == "REFUSAL" else "UNSAFE_ACCEPT"
                        if record["status"] == "ANSWER":
                            contrast_graphs.add(_graph(record))
                    else:
                        classification = "SAFE_REFUSAL" if record["status"] == "REFUSAL" else "UNSAFE_ACCEPT"
                    classifications[classification] += 1
                    rows.append({
                        "id": case["id"], "group": group, "classification": classification,
                        "status": record["status"], "refusal": (record.get("refusal") or {}).get("code"),
                        "graph": _graph(record) if record["status"] == "ANSWER" else None,
                        "outer_hash": record["outer_hash"],
                    })

            equivalent_by_id = {row["id"]: row for row in fixture["equivalent"]}
            ablation_rows = []
            for ablation in fixture["ablations"]:
                ablated = compile_field(ablate_field(field_source, ablation["subsystem"]))
                ablated_instance = CompositionalInstance(store, encoder, THRESHOLDS, ablated)
                record = ablated_instance.query(equivalent_by_id[ablation["case_id"]]["prompt"])
                ablation_rows.append({
                    "id": ablation["id"], "subsystem": ablation["subsystem"],
                    "status": record["status"], "refusal": (record.get("refusal") or {}).get("code"),
                    "field_hash_changed": ablated.field_hash != compiled_field.field_hash,
                })

            representative = instance.query(fixture["equivalent"][0]["prompt"])
            outer_tampered = deepcopy(representative)
            outer_tampered["composition"]["trace"][0]["rule_id"] = "tampered"
            try:
                instance.verify(outer_tampered)
            except CompositionIntegrityError:
                composition_tamper_detected = True
            else:
                composition_tamper_detected = False
            semantic_tampered = deepcopy(representative["base_result"])
            semantic_tampered["stages"][0]["program"]["grounding"]["semantic_interpretation"]["facts"][0]["polarity"] = "TAMPERED"
            try:
                verify_archived_result(semantic_tampered, worlds, bundle)
            except IntegrityError:
                semantic_tamper_detected = True
            else:
                semantic_tamper_detected = False
    finally:
        socket.socket.connect = original_connect

    after = _protected_hashes()
    unsafe = classifications["UNSAFE_ACCEPT"]
    ablations_passed = sum(row["status"] == "REFUSAL" and row["field_hash_changed"] for row in ablation_rows)
    capability_target_met = classifications["CORRECT_EQUIVALENT"] == 12 and len(equivalent_graphs) == 1
    refusal_controls_passed = sum(
        row["group"] == "refusals" and row["classification"] == "SAFE_REFUSAL" for row in rows
    )
    safety_integrity_passed = (
        control_answers == 0
        and classifications["CORRECT_CONTRAST"] == 6
        and len(contrast_graphs) == 6
        and refusal_controls_passed == 10
        and unsafe == 0 and ablations_passed == 6 and replay_count == 28
        and composition_tamper_detected and semantic_tamper_detected
        and network_attempts == 0 and before == after
    )
    result = {
        "schema": "moth-v5-blind-compositional-closure-result/1.0",
        "verdict": (
            "BLIND_COMPOSITIONAL_LANGUAGE_FIDELITY_CONFIRMED"
            if capability_target_met and safety_integrity_passed
            else "BLIND_COMPOSITIONAL_LANGUAGE_FIDELITY_NOT_CONFIRMED"
        ),
        "capability_target_met": capability_target_met,
        "safety_integrity_passed": safety_integrity_passed,
        "field_sealed_before_prompts": True,
        "no_complete_test_language_in_field": no_complete_frames,
        "sealed_field_sha256": field_sha,
        "compiled_field_hash": compiled_field.field_hash,
        "control_equivalent_answers": control_answers,
        "control_rows": control_rows,
        "classifications": dict(sorted(classifications.items())),
        "equivalent_correct_ids": [row["id"] for row in rows if row["group"] == "equivalent" and row["classification"] == "CORRECT_EQUIVALENT"],
        "equivalent_refusal_ids": [row["id"] for row in rows if row["group"] == "equivalent" and row["classification"] == "SAFE_REFUSAL"],
        "refusal_controls_passed": refusal_controls_passed,
        "equivalent_unique_graphs": len(equivalent_graphs),
        "contrast_unique_graphs": len(contrast_graphs),
        "unsafe_acceptances": unsafe,
        "ablations_passed": ablations_passed,
        "ablation_rows": ablation_rows,
        "encoder_free_nested_replays": replay_count,
        "composition_tamper_detected": composition_tamper_detected,
        "semantic_tamper_detected": semantic_tamper_detected,
        "network_attempts": network_attempts,
        "execution_performed": False,
        "dispatch_count": 0,
        "encoder": encoder_record,
        "thresholds": THRESHOLDS["SEMANTIC_SURFACE"],
        "protected_hashes_unchanged": before == after,
        "protected_hashes": before,
        "campaign_fixture_sha256": sha256_bytes(CAMPAIGN_FIXTURE.read_bytes()),
        "result_manifest_sha256": sha256_bytes(canonical_bytes(rows)),
        "duration_seconds": round(time.monotonic() - started, 3),
    }
    if not safety_integrity_passed:
        raise CampaignFailure(json.dumps(result, indent=2, sort_keys=True))
    return result


def main() -> None:
    print(json.dumps(run_campaign(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
