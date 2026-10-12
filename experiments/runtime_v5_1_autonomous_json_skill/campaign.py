"""Run the sealed autonomous JSON skill qualification attempt."""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

from moth_runtime_v5_0.canonical import canonical_bytes, digest, sha256_bytes
from moth_runtime_v5_1.artifact import ModelArtifact51

from .candidate_runtime import AutonomousJsonRuntime, settle_json_request
from .compiler import HERE, compile_candidate, verify_deterministic_compilation


ROOT = HERE.parents[1]
FIXTURES = HERE / "fixtures"
RUNS = HERE / "runs"
REPORTS = HERE / "reports"
BASE_ARTIFACT = ROOT / "experiments/runtime_v5_1_compiled_artifact/runs/moth-model-5.1-qualified-final"
SOURCE_FILES = (
    "README.md",
    "SPEC.md",
    "PLAN.md",
    "TASKS.md",
    "compiler.py",
    "candidate_runtime.py",
    "generate_fixtures.py",
    "campaign.py",
    "fixtures/json-formatting-field-en-1.0.json",
    "fixtures/json-formatting/SKILL.md",
    "fixtures/qualification-panel-1.0.json",
    "fixtures/negative-panel-1.0.json",
    "fixtures/metamorphic-panel-1.0.json",
)


class CampaignFailure(AssertionError):
    pass


def _load(name: str) -> list[dict[str, Any]]:
    return json.loads((FIXTURES / name).read_text())["cases"]


def expected_manifest() -> dict[str, Any]:
    base = ModelArtifact51.open(BASE_ARTIFACT)
    return {
        "schema": "moth-autonomous-json-source-freeze/5.1-experiment",
        "base_artifact_hash": base.artifact_hash,
        "sources": {
            path: sha256_bytes((HERE / path).read_bytes())
            for path in sorted(SOURCE_FILES)
        },
    }


def freeze_manifest() -> dict[str, Any]:
    path = FIXTURES / "SOURCE-MANIFEST.json"
    if path.exists():
        raise RuntimeError("refusing to overwrite frozen source manifest")
    manifest = expected_manifest()
    path.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    return manifest


def verify_manifest() -> dict[str, Any]:
    path = FIXTURES / "SOURCE-MANIFEST.json"
    if not path.exists():
        raise CampaignFailure("source manifest has not been frozen")
    observed = json.loads(path.read_text())
    expected = expected_manifest()
    if canonical_bytes(observed) != canonical_bytes(expected):
        raise CampaignFailure("frozen source manifest changed")
    return observed


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def _positive(field: Any, skill: dict[str, Any], store: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    runtime = AutonomousJsonRuntime(store, field, skill)
    conversation = runtime.create_conversation()
    rows = []
    families: dict[str, int] = {}
    layout_cases = 0
    for case in _load("qualification-panel-1.0.json"):
        result = runtime.turn(conversation, case["prompt"])
        semantic = result["status"] == "ANSWER" and canonical_bytes(result["value"]) == canonical_bytes(case["expected_value"])
        exact_bytes = result.get("response") == case["expected_response"]
        attributed = result.get("skill", {}).get("policy_hash") == skill["policy_hash"]
        autonomous = result.get("skill", {}).get("candidate_id") == "skill.autonomous-json-formatting"
        if not all((semantic, exact_bytes, attributed, autonomous)):
            raise CampaignFailure(f"positive case failed: {case['id']}")
        if result["hcf"]["winning_energy"] != {
            "base_violations": 0,
            "system_violations": 0,
            "context_violations": 0,
            "grounding_cost_units": 0,
        }:
            raise CampaignFailure(f"nonzero winning energy: {case['id']}")
        if any(result["execution"].values()):
            raise CampaignFailure(f"side effect recorded: {case['id']}")
        families[case["family"]] = families.get(case["family"], 0) + 1
        if case["family"] in {"canonical_order", "source_order", "compact_json", "pretty_json"}:
            layout_cases += 1
        rows.append({
            "id": case["id"],
            "family": case["family"],
            "prompt": case["prompt"],
            "response": result["response"],
            "value": result["value"],
            "route": result["route"],
            "result_hash": result["result_hash"],
        })
    return {
        "cases": len(rows),
        "semantic_exact": len(rows),
        "shape_exact": len(rows),
        "byte_exact": len(rows),
        "layout_cases": layout_cases,
        "layout_exact": layout_cases,
        "policy_attributed": len(rows),
        "autonomously_routed": len(rows),
        "families": families,
    }, rows


def _negative(field: Any, skill: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows = []
    categories: dict[str, int] = {}
    for case in _load("negative-panel-1.0.json"):
        result = settle_json_request(case["prompt"], field, skill)
        if result["status"] != "REFUSAL" or result["code"] != case["expected_code"]:
            raise CampaignFailure(f"negative case failed: {case['id']}")
        categories[case["category"]] = categories.get(case["category"], 0) + 1
        rows.append({"id": case["id"], "category": case["category"], "code": result["code"], "result_hash": result["result_hash"]})
    return {"cases": len(rows), "correct_typed_refusals": len(rows), "categories": categories}, rows


def _metamorphic(field: Any, skill: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows = []
    relations: dict[str, int] = {}
    for case in _load("metamorphic-panel-1.0.json"):
        left = settle_json_request(case["left"], field, skill)
        right = settle_json_request(case["right"], field, skill)
        if left["status"] != "ANSWER" or right["status"] != "ANSWER":
            raise CampaignFailure(f"metamorphic case refused: {case['id']}")
        relation = case["relation"]
        if relation == "same_value":
            passed = canonical_bytes(left["value"]) == canonical_bytes(right["value"])
        elif relation == "same_result":
            passed = (
                canonical_bytes(left["value"]) == canonical_bytes(right["value"])
                and left["response"] == right["response"]
                and left["route"]["family"] == right["route"]["family"]
            )
        elif relation == "same_value_different_bytes":
            passed = canonical_bytes(left["value"]) == canonical_bytes(right["value"]) and left["response"] != right["response"]
        elif relation == "same_response":
            passed = left["response"] == right["response"]
        elif relation == "different_value":
            passed = canonical_bytes(left["value"]) != canonical_bytes(right["value"])
        else:
            raise CampaignFailure(f"unknown metamorphic relation: {relation}")
        if not passed:
            raise CampaignFailure(f"metamorphic invariant failed: {case['id']}")
        relations[relation] = relations.get(relation, 0) + 1
        rows.append({"id": case["id"], "relation": relation, "left_hash": left["result_hash"], "right_hash": right["result_hash"]})
    return {"cases": len(rows), "passed": len(rows), "relations": relations}, rows


def _causal(field: Any, skill: dict[str, Any], attempt: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    prompts = [case["prompt"] for case in _load("qualification-panel-1.0.json")]
    controls: dict[str, bool] = {}
    controls["no_skill"] = all(settle_json_request(prompt, field, None)["code"] == "SKILL_UNAVAILABLE" for prompt in prompts)
    controls["unrelated_skill"] = all(settle_json_request(prompt, field, skill, unrelated_skill=True)["code"] == "SKILL_NOT_APPLICABLE" for prompt in prompts)

    trigger = deepcopy(skill)
    trigger["policy"]["trigger"] = "OTHER_TRIGGER"
    controls["trigger_corruption"] = settle_json_request(prompts[0], field, trigger)["code"] == "INTEGRITY_FAILURE"

    workflow = deepcopy(skill)
    workflow["policy"]["workflow"].remove("VERIFY_EXACT_DATA")
    controls["workflow_corruption"] = settle_json_request(prompts[0], field, workflow)["code"] == "INTEGRITY_FAILURE"

    policy_hash = deepcopy(skill)
    policy_hash["policy_hash"] = "0" * 64
    controls["policy_hash_corruption"] = settle_json_request(prompts[0], field, policy_hash)["code"] == "INTEGRITY_FAILURE"
    controls["router_ablation"] = all(settle_json_request(prompt, field, skill, router_enabled=False)["code"] == "ROUTER_DISABLED" for prompt in prompts)

    scanned = [HERE / "candidate_runtime.py", HERE / "compiler.py", FIXTURES / "json-formatting-field-en-1.0.json", FIXTURES / "json-formatting/SKILL.md"]
    code = "\n".join(path.read_text() for path in scanned)
    case_ids_absent = all(row["id"] not in code for row in rows)
    complete_outputs_absent = all(len(row["response"]) < 24 or row["response"] not in code for row in rows)
    controls["oracle_leak_scan"] = case_ids_absent and complete_outputs_absent

    replay_a = attempt / "fresh-a.sqlite3"
    replay_b = attempt / "fresh-b.sqlite3"
    first_runtime = AutonomousJsonRuntime(replay_a, field, skill)
    second_runtime = AutonomousJsonRuntime(replay_b, field, skill)
    first_conversation = first_runtime.create_conversation()
    second_conversation = second_runtime.create_conversation()
    first = first_runtime.turn(first_conversation, prompts[0])
    second = second_runtime.turn(second_conversation, prompts[0])
    controls["fresh_store_replay"] = canonical_bytes(first) == canonical_bytes(second)

    if not all(controls.values()):
        raise CampaignFailure(f"causal controls failed: {[key for key, value in controls.items() if not value]}")
    return {"passed": sum(controls.values()), "required": len(controls), "controls": controls}


def worker_digest() -> str:
    field, skill = compile_candidate()
    bodies = []
    for case in _load("qualification-panel-1.0.json"):
        result = settle_json_request(case["prompt"], field, skill)
        bodies.append({"id": case["id"], "status": result["status"], "response": result["response"], "route": result["route"], "skill": result["skill"]})
    return digest("moth-json-repeat-panel/5.1-experiment", bodies)


def _repeatability() -> dict[str, Any]:
    digests: dict[str, list[str]] = {}
    for seed in ("1", "777"):
        values = []
        for _ in range(5):
            environment = dict(os.environ)
            environment["PYTHONHASHSEED"] = seed
            completed = subprocess.run(
                [sys.executable, "-m", "experiments.runtime_v5_1_autonomous_json_skill.campaign", "--worker-digest"],
                cwd=ROOT,
                env=environment,
                check=True,
                capture_output=True,
                text=True,
            )
            values.append(completed.stdout.strip())
        digests[seed] = values
    if len({value for values in digests.values() for value in values}) != 1:
        raise CampaignFailure("repeatability differs across runs or hash seeds")
    return {"runs_per_seed": 5, "hash_seeds": [1, 777], "digests": digests, "identical": True}


def _preservation() -> dict[str, Any]:
    before = ModelArtifact51.open(BASE_ARTIFACT).artifact_hash
    command = [
        str(ROOT / ".venv/bin/python"), "-m", "pytest",
        "tests/test_runtime_v5_1.py",
        "tests/test_launcher_v5_1.py",
        "experiments/runtime_v5_1_hcf/tests",
        "experiments/runtime_v5_1_compiled_artifact/tests",
        "-q",
    ]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    after = ModelArtifact51.open(BASE_ARTIFACT).artifact_hash
    if completed.returncode != 0 or before != after:
        raise CampaignFailure("existing Runtime 5.1 preservation gate failed")
    summary = completed.stdout.strip().splitlines()[-1] if completed.stdout.strip() else ""
    return {"tests_passed": True, "summary": summary, "artifact_hash_before": before, "artifact_hash_after": after, "unchanged": before == after}


def run_attempt(number: int) -> dict[str, Any]:
    verify_manifest()
    attempt = RUNS / f"attempt-{number:03d}"
    if attempt.exists():
        raise RuntimeError(f"refusing to overwrite sealed attempt: {attempt}")
    attempt.mkdir(parents=True)
    field, skill = compile_candidate()
    compilation = verify_deterministic_compilation(10)
    _write_json(attempt / "artifact/compiled-field.json", field.archive)
    _write_json(attempt / "artifact/compiled-skill.json", skill)
    positive, positive_rows = _positive(field, skill, attempt / "campaign.sqlite3")
    negative, negative_rows = _negative(field, skill)
    metamorphic, metamorphic_rows = _metamorphic(field, skill)
    causal = _causal(field, skill, attempt, positive_rows)
    repeatability = _repeatability()
    preservation = _preservation()
    all_rows = {"positive": positive_rows, "negative": negative_rows, "metamorphic": metamorphic_rows}
    _write_json(attempt / "rows.json", all_rows)

    result_body = {
        "schema": "moth-autonomous-json-qualification/5.1-experiment",
        "attempt": number,
        "verdict": "PASS",
        "claim": "ONE_COMPILED_JSON_SKILL_AUTONOMOUS_VARIETY_CONFIRMED",
        "compilation": compilation,
        "positive": positive,
        "negative": negative,
        "metamorphic": metamorphic,
        "causal": causal,
        "repeatability": repeatability,
        "preservation": preservation,
        "base_artifact_hash": ModelArtifact51.open(BASE_ARTIFACT).artifact_hash,
        "candidate_artifact_hash": AutonomousJsonRuntime(attempt / "receipt.sqlite3", field, skill).artifact_hash,
        "source_manifest_hash": sha256_bytes((FIXTURES / "SOURCE-MANIFEST.json").read_bytes()),
        "side_effects": {"network": 0, "tool_dispatches": 0, "code_executions": 0, "workspace_writes": 0},
    }
    result = {**result_body, "report_hash": digest("moth-autonomous-json-qualification/5.1-experiment", result_body)}
    _write_json(attempt / "result.json", result)
    _write_json(REPORTS / f"RESULT-{number:03d}.json", result)
    _write_json(REPORTS / f"VARIATIONS-{number:03d}.json", {"schema": "moth-json-variation-gallery/1.0", "cases": positive_rows})
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=int)
    parser.add_argument("--freeze-manifest", action="store_true")
    parser.add_argument("--worker-digest", action="store_true")
    args = parser.parse_args(argv)
    if args.worker_digest:
        print(worker_digest())
        return 0
    if args.freeze_manifest:
        print(json.dumps(freeze_manifest(), sort_keys=True))
        return 0
    if args.attempt is None:
        parser.error("--attempt is required")
    print(json.dumps(run_attempt(args.attempt), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

