"""Run the Runtime 5.2 autonomous JSON parity qualification."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from moth_runtime_v5_0.canonical import canonical_bytes, digest, sha256_bytes

from .candidate_runtime import settle_json_prompt
from .compiler import HERE, ORACLE_FIXTURES, compile_candidate, deterministic_compilation


REPORTS = HERE / "reports"


def load_cases(name: str) -> list[dict[str, Any]]:
    return json.loads((ORACLE_FIXTURES / name).read_text(encoding="utf-8"))["cases"]


def source_hashes() -> dict[str, str]:
    paths = [
        ORACLE_FIXTURES / "json-formatting-field-en-1.0.json",
        ORACLE_FIXTURES / "json-formatting/SKILL.md",
        ORACLE_FIXTURES / "qualification-panel-1.0.json",
        ORACLE_FIXTURES / "negative-panel-1.0.json",
        ORACLE_FIXTURES / "metamorphic-panel-1.0.json",
    ]
    return {str(path.relative_to(HERE.parents[1])): sha256_bytes(path.read_bytes()) for path in paths}


def run(*, write_reports: bool = True) -> dict[str, Any]:
    with TemporaryDirectory(prefix="moth52-autonomous-json-") as temporary:
        candidate = compile_candidate(Path(temporary) / "candidate")
        positives = load_cases("qualification-panel-1.0.json")
        positive_rows = []
        families: Counter[str] = Counter()
        for case in positives:
            result = settle_json_prompt(candidate, case["prompt"])
            if not (
                result["status"] == "ANSWER"
                and result["response"] == case["expected_response"]
                and canonical_bytes(result["value"]) == canonical_bytes(case["expected_value"])
                and result["hcf"]["winning_energy"]
                == {
                    "base_violations": 0,
                    "system_violations": 0,
                    "context_violations": 0,
                    "grounding_cost_units": 0,
                }
                and not any(result["execution"].values())
            ):
                raise AssertionError(f"positive case failed: {case['id']} -> {result}")
            families[case["family"]] += 1
            positive_rows.append(
                {
                    "id": case["id"],
                    "family": case["family"],
                    "prompt": case["prompt"],
                    "response": result["response"],
                    "value": result["value"],
                    "route": result["route"],
                    "result_hash": result["result_hash"],
                }
            )

        negatives = load_cases("negative-panel-1.0.json")
        negative_categories: Counter[str] = Counter()
        for case in negatives:
            result = settle_json_prompt(candidate, case["prompt"])
            if result["status"] != "REFUSAL" or result["code"] != case["expected_code"]:
                raise AssertionError(f"negative case failed: {case['id']} -> {result['code']}")
            negative_categories[case["category"]] += 1

        metamorphic = load_cases("metamorphic-panel-1.0.json")
        relations: Counter[str] = Counter()
        for case in metamorphic:
            left = settle_json_prompt(candidate, case["left"])
            right = settle_json_prompt(candidate, case["right"])
            if left["status"] != "ANSWER" or right["status"] != "ANSWER":
                raise AssertionError(f"metamorphic case refused: {case['id']}")
            relation = case["relation"]
            same_value = canonical_bytes(left["value"]) == canonical_bytes(right["value"])
            if relation == "same_value":
                passed = same_value
            elif relation == "same_result":
                passed = same_value and left["response"] == right["response"] and left["route"]["family"] == right["route"]["family"]
            elif relation == "same_value_different_bytes":
                passed = same_value and left["response"] != right["response"]
            elif relation == "same_response":
                passed = left["response"] == right["response"]
            elif relation == "different_value":
                passed = not same_value
            else:
                raise AssertionError(f"unknown relation: {relation}")
            if not passed:
                raise AssertionError(f"metamorphic case failed: {case['id']}")
            relations[relation] += 1

        sample_prompt = positives[0]["prompt"]
        no_skill = settle_json_prompt(candidate, sample_prompt, skill_available=False)
        no_router = settle_json_prompt(candidate, sample_prompt, router_enabled=False)
        if no_skill["code"] != "SKILL_UNAVAILABLE" or no_router["code"] != "ROUTER_DISABLED":
            raise AssertionError("causal ablation did not remove the capability")

        result_body = {
            "schema": "moth-autonomous-json-qualification/5.2-experiment",
            "verdict": "PASS",
            "claim": "SAFETENSORS_AUTONOMOUS_JSON_PARITY_CONFIRMED",
            "compiled_objects": {
                "field": {
                    "schema": candidate.field.envelope.schema,
                    "logical_hash": candidate.field.envelope.logical_hash,
                    "file_hash": candidate.field.envelope.file_hash,
                },
                "skill": {
                    "schema": candidate.skill.envelope.schema,
                    "compilation_id": candidate.skill.compilation_id,
                    "policy_hash": candidate.skill.policy_hash,
                    "logical_hash": candidate.skill.envelope.logical_hash,
                    "file_hash": candidate.skill.envelope.file_hash,
                },
                "foundation": {
                    "schema": "moth-energy-foundation/5.2",
                    "logical_hash": candidate.foundation.logical_hash,
                    "file_hash": candidate.foundation.file_hash,
                    "candidate_count": candidate.foundation.candidate_count,
                },
            },
            "positive": {
                "cases": len(positive_rows),
                "exact": len(positive_rows),
                "prompt_only": len(positive_rows),
                "families": dict(sorted(families.items())),
            },
            "negative": {
                "cases": len(negatives),
                "correct_typed_refusals": len(negatives),
                "categories": dict(sorted(negative_categories.items())),
            },
            "metamorphic": {
                "cases": len(metamorphic),
                "passed": len(metamorphic),
                "relations": dict(sorted(relations.items())),
            },
            "causal": {"no_skill": True, "router_ablation": True},
            "determinism": deterministic_compilation(3),
            "source_hashes": source_hashes(),
            "side_effects": {"network": 0, "tool_dispatches": 0, "code_executions": 0, "workspace_writes_during_turns": 0},
            "promoted_runtime_modified": False,
        }
        result = {**result_body, "report_hash": digest("moth-autonomous-json-qualification/5.2-experiment", result_body)}
        if write_reports:
            REPORTS.mkdir(parents=True, exist_ok=True)
            (REPORTS / "RESULT-001.json").write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            variations = {
                "schema": "moth-autonomous-json-variations/5.2-experiment",
                "case_count": len(positive_rows),
                "cases": positive_rows,
            }
            (REPORTS / "VARIATIONS-001.json").write_text(json.dumps(variations, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return result


def main() -> int:
    print(json.dumps(run(), ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

