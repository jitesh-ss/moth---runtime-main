"""Run the sealed typed-determiner corrective qualification."""

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
from experiments.runtime_v5_0_blind_compositional_closure.field import compile_field
from experiments.runtime_v5_0_blind_compositional_closure.instance import (
    CompositionalInstance, CompositionIntegrityError,
)

from .grammar import compile_determiner_extension
from .instance import TypedDeterminerInstance


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BASE_FIELD = ROOT / "experiments/runtime_v5_0_blind_compositional_closure/fixtures/field-en-1.0.json"
PRIOR_CAMPAIGN = ROOT / "experiments/runtime_v5_0_blind_compositional_closure/fixtures/blind-campaign-en-1.0.json"
EXTENSION = HERE / "fixtures/determiner-extension-en-1.0.json"
CAMPAIGN = HERE / "fixtures/blind-campaign-en-1.0.json"
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


def _language_absent(field_text: str, extension_text: str, fixture: dict[str, Any]) -> bool:
    compiled_text = (field_text + extension_text).casefold()
    for group in ("equivalent", "contrasts", "refusals"):
        for row in fixture[group]:
            prompt = row["prompt"].casefold()
            if prompt in compiled_text:
                return False
            if any(sentence in compiled_text for sentence in (part.strip() for part in re.split(r"[.!?;]+", prompt) if part.strip())):
                return False
    return True


def run_campaign() -> dict[str, Any]:
    started = time.monotonic()
    base_bytes = BASE_FIELD.read_bytes()
    extension_bytes = EXTENSION.read_bytes()
    base_sha = sha256_bytes(base_bytes)
    extension_sha = sha256_bytes(extension_bytes)
    base_source = json.loads(base_bytes)
    extension_source = json.loads(extension_bytes)
    fixture = json.loads(CAMPAIGN.read_text())
    prior = json.loads(PRIOR_CAMPAIGN.read_text())
    if (
        fixture.get("schema") != "moth-v5-typed-determiner-blind-campaign/1.0"
        or fixture.get("frozen_after_extension_seal") is not True
        or fixture.get("base_field_sha256") != base_sha
        or fixture.get("extension_sha256") != extension_sha
    ):
        raise CampaignFailure("new campaign is not bound to both sealed field layers")
    if [len(fixture[key]) for key in ("equivalent", "contrasts", "refusals")] != [12, 6, 10]:
        raise CampaignFailure("typed-determiner campaign counts changed")
    language_absent = _language_absent(base_bytes.decode(), extension_bytes.decode(), fixture)
    if not language_absent:
        raise CampaignFailure("complete new test language leaked into the sealed field")
    prior_by_id = {row["id"]: row for row in prior["equivalent"]}
    regressions = [prior_by_id[value] for value in fixture["prior_regression_ids"]]
    base_field = compile_field(base_source)
    extended_field = compile_determiner_extension(base_field, extension_source, base_field_sha256=base_sha)
    before = _protected_hashes()
    network_attempts = 0
    original_connect = socket.socket.connect

    def blocked_connect(instance, address):
        nonlocal network_attempts
        network_attempts += 1
        raise RuntimeError(f"network disabled during typed-determiner campaign: {address}")

    socket.socket.connect = blocked_connect
    try:
        with TemporaryDirectory(prefix="moth-v5-determiner-") as temporary:
            encoder = LocalBGEEncoder()
            encoder_record = encoder.verify_assets()
            deterministic = DeterministicEncoder()
            store = WorldStore(Path(temporary) / "store-5.0.sqlite3")
            store.publish(WorldRole.INPUT, {"input.moth": semantic_source("delivery")}, encoder=encoder)
            store.publish(WorldRole.MAIN, {"main.moth": decision_source()}, encoder=deterministic)
            store.publish(WorldRole.SURFACE, {"surface.moth": SURFACE}, encoder=deterministic)
            bundle = store.activate()
            worlds = store.bundle_worlds(bundle)
            control = CompositionalInstance(store, encoder, THRESHOLDS, base_field)
            instructed = TypedDeterminerInstance(store, encoder, THRESHOLDS, extended_field)

            baseline = store.query(DELIVERY, encoder=encoder, thresholds=THRESHOLDS)
            if baseline["status"] != "ANSWER":
                raise CampaignFailure("rigid baseline refused")
            baseline_graph = str(baseline["stages"][0]["program"]["grounding"]["semantic_interpretation"]["semantic_graph_hash"])
            baseline_output = baseline["output"]["value"]

            regression_rows = []
            replay_count = 0
            for case in regressions:
                record = instructed.query(case["prompt"])
                correct = record["status"] == "ANSWER" and _graph(record) == baseline_graph and record["output"]["value"] == baseline_output
                if instructed.replay(record["episode_id"], encoder_free=True) != canonical_bytes(record):
                    raise CampaignFailure(f"{case['id']}: repaired regression replay changed")
                replay_count += 1
                regression_rows.append({"id": case["id"], "correct": correct, "status": record["status"]})

            control_rows = []
            for case in fixture["equivalent"]:
                record = control.query(case["prompt"])
                control_rows.append({"id": case["id"], "status": record["status"], "refusal": (record.get("refusal") or {}).get("code")})

            classifications: Counter[str] = Counter()
            rows = []
            equivalent_graphs = set()
            contrast_graphs = set()
            determiner_evidence = 0
            for group in ("equivalent", "contrasts", "refusals"):
                for case in fixture[group]:
                    record = instructed.query(case["prompt"])
                    if instructed.replay(record["episode_id"], encoder_free=True) != canonical_bytes(record):
                        raise CampaignFailure(f"{case['id']}: nested replay changed")
                    replay_count += 1
                    if record["composition"] is not None:
                        determiner_evidence += sum(row.get("noun_phrase_rule") is not None for row in record["composition"]["trace"])
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

            ablation_record = control.query(fixture["equivalent"][0]["prompt"])
            determiner_ablation_passed = ablation_record["status"] == "REFUSAL"
            representative = instructed.query(fixture["equivalent"][0]["prompt"])
            outer_tampered = deepcopy(representative)
            outer_tampered["composition"]["trace"][0]["determiner"] = "tampered"
            try:
                instructed.verify(outer_tampered)
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
    regressions_passed = sum(row["correct"] for row in regression_rows)
    control_refusals = sum(row["status"] == "REFUSAL" for row in control_rows)
    unsafe = classifications["UNSAFE_ACCEPT"]
    passed = (
        regressions_passed == 4 and control_refusals == 12
        and classifications["CORRECT_EQUIVALENT"] == 12 and len(equivalent_graphs) == 1
        and classifications["CORRECT_CONTRAST"] == 6 and len(contrast_graphs) == 6
        and classifications["SAFE_REFUSAL"] == 10 and unsafe == 0
        and determiner_evidence > 0 and determiner_ablation_passed
        and replay_count == 32 and composition_tamper_detected and semantic_tamper_detected
        and network_attempts == 0 and before == after
    )
    result = {
        "schema": "moth-v5-typed-determiner-closure-result/1.0",
        "verdict": "TYPED_DETERMINER_COMPOSITIONAL_CLOSURE_CONFIRMED" if passed else "GATE_FAILED",
        "field_sealed_before_prompts": True,
        "no_complete_test_language_in_field": language_absent,
        "base_field_sha256": base_sha,
        "extension_sha256": extension_sha,
        "base_compiled_field_hash": base_field.field_hash,
        "extended_compiled_field_hash": extended_field.field_hash,
        "prior_regressions_passed": regressions_passed,
        "regression_rows": regression_rows,
        "base_control_refusals": control_refusals,
        "control_rows": control_rows,
        "classifications": dict(sorted(classifications.items())),
        "equivalent_unique_graphs": len(equivalent_graphs),
        "contrast_unique_graphs": len(contrast_graphs),
        "unsafe_acceptances": unsafe,
        "determiner_trace_evidence_count": determiner_evidence,
        "determiner_ablation_passed": determiner_ablation_passed,
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
        "campaign_fixture_sha256": sha256_bytes(CAMPAIGN.read_bytes()),
        "result_manifest_sha256": sha256_bytes(canonical_bytes(rows)),
        "duration_seconds": round(time.monotonic() - started, 3),
    }
    if not passed:
        raise CampaignFailure(json.dumps(result, indent=2, sort_keys=True))
    return result


def main() -> None:
    print(json.dumps(run_campaign(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

