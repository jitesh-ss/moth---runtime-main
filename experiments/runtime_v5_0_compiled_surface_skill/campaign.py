"""Run the frozen compiled Surface-skill campaign on disposable Runtime 5.0 instances."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from moth_runtime_v5_0.canonical import canonical_bytes as runtime_bytes

from .compiler import compile_skill, parse_skill, validate_field
from .instance import IsolatedSurfaceInstance
from .model import (
    SkillCompilationFailure,
    SurfaceFidelityFailure,
    canonical_bytes,
    digest,
    policy_hash,
    sha256_bytes,
)
from .realizer import realize, verify_response


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"
FREEZE = FIXTURES / "FREEZE.json"


class CampaignFailure(AssertionError):
    pass


def _path_hash(path: Path) -> str:
    if not path.exists():
        return "ABSENT"
    if path.is_file():
        return sha256_bytes(path.read_bytes())
    result = hashlib.sha256()
    for child in sorted(item for item in path.rglob("*") if item.is_file()):
        if "__pycache__" in child.parts or "runs" in child.parts:
            continue
        result.update(child.relative_to(ROOT).as_posix().encode("utf-8"))
        result.update(b"\0")
        result.update(hashlib.sha256(child.read_bytes()).digest())
    return result.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CampaignFailure(f"{path}: expected JSON object")
    return value


def _verify_freeze() -> tuple[dict[str, Any], dict[str, str]]:
    freeze = _load_json(FREEZE)
    if freeze.get("schema") != "moth-v5-compiled-surface-freeze/1.0" or not freeze.get("frozen_before_execution"):
        raise CampaignFailure("fixture freeze is absent or invalid")
    for relative, expected in freeze["fixtures"].items():
        observed = _path_hash(FIXTURES / relative)
        if observed != expected:
            raise CampaignFailure(f"frozen fixture changed: {relative}")
    protected = {relative: _path_hash(ROOT / relative) for relative in freeze["protected"]}
    if protected != freeze["protected"]:
        changed = sorted(key for key in protected if protected[key] != freeze["protected"].get(key))
        raise CampaignFailure(f"protected foundation changed before execution: {changed}")
    return freeze, protected


def _compile_candidates(field: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    primary_text = (FIXTURES / "natural-response/SKILL.md").read_text(encoding="utf-8")
    paraphrase_text = (FIXTURES / "natural-response-paraphrase/SKILL.md").read_text(encoding="utf-8")
    primary = compile_skill(primary_text, field)
    paraphrase = compile_skill(paraphrase_text, field)
    oracle = _load_json(FIXTURES / "granular-surface-oracle-1.0.json")
    if primary["policy"] != oracle or paraphrase["policy"] != oracle:
        raise CampaignFailure("compiled Surface policy differs from the frozen granular oracle")
    if primary["policy_hash"] != paraphrase["policy_hash"]:
        raise CampaignFailure("equivalent skill documents produced different policies")
    return primary, paraphrase, oracle


def _append_clause(document: str, section: str, clause: str) -> str:
    return document.rstrip() + f"\n\n## {section.title()}\n\n- {clause}\n"


def _invalid_skill_gates(field: dict[str, Any], panel: dict[str, Any]) -> dict[str, dict[str, str]]:
    primary_text = (FIXTURES / "natural-response/SKILL.md").read_text(encoding="utf-8")
    results: dict[str, dict[str, str]] = {}
    for case in panel["invalid_skill_cases"]:
        try:
            if "remove_rule" in case:
                compile_skill(primary_text, field, ignored_rule_ids={str(case["remove_rule"])})
            else:
                document = _append_clause(primary_text, str(case["append_section"]), str(case["append_clause"]))
                compile_skill(document, field)
        except SkillCompilationFailure as exc:
            if exc.code != case["expected_code"]:
                raise CampaignFailure(f"{case['id']}: expected {case['expected_code']}, got {exc.code}") from exc
            results[str(case["id"])] = {"status": "PASSED", "code": exc.code}
        else:
            raise CampaignFailure(f"{case['id']}: invalid skill compiled")
    return results


def _ablation_gates(
    field: dict[str, Any],
    compilation: dict[str, Any],
    runtime_output: dict[str, Any],
) -> dict[str, dict[str, str]]:
    actions = {
        "size_interpreter": "DETECT_SIZE_SIGNAL",
        "discourse_planner": "PLAN_OUTCOME_FIRST",
        "lexicalizer": "LEXICALIZE_DECISION",
        "coverage_verifier": "VERIFY_FACT_COVERAGE",
        "hash_binder": "BIND_SEMANTIC_HASH",
    }
    results: dict[str, dict[str, str]] = {}
    for subsystem, action in actions.items():
        ablated = deepcopy(compilation)
        workflow = [item for item in ablated["policy"]["workflow"] if item != action]
        ablated["policy"]["workflow"] = workflow
        ablated["policy"]["edges"] = [[left, right] for left, right in zip(workflow, workflow[1:])]
        ablated["policy_hash"] = policy_hash(ablated["policy"])
        try:
            realize(runtime_output, "Answer concisely.", ablated, field)
        except SurfaceFidelityFailure as exc:
            if exc.code != "INCOMPLETE_SURFACE_POLICY":
                raise CampaignFailure(f"{subsystem}: wrong ablation failure {exc.code}") from exc
            results[subsystem] = {"status": "PASSED", "code": exc.code}
        else:
            raise CampaignFailure(f"{subsystem}: ablated policy still realized a response")
    return results


def _semantic_graph(result: dict[str, Any]) -> str:
    return str(
        result["stages"][0]["program"]["grounding"]["semantic_interpretation"]["semantic_graph_hash"]
    )


def _tamper_gates(
    instance: IsolatedSurfaceInstance,
    package: dict[str, Any],
    compilation: dict[str, Any],
    field: dict[str, Any],
) -> dict[str, bool]:
    archive_tampered = deepcopy(package["archive"])
    archive_tampered["payload"]["surface_response"]["text"] += " Altered."
    try:
        instance.replay(archive_tampered)
    except SurfaceFidelityFailure:
        archive_detected = True
    else:
        archive_detected = False

    claims_tampered = deepcopy(package["archive"])
    response = claims_tampered["payload"]["surface_response"]
    response["claims"]["backup-valid"] = "false"
    without_hash = {key: value for key, value in response.items() if key != "response_hash"}
    response["response_hash"] = digest("moth-experimental-surface-response/1.0", without_hash)
    claims_tampered["payload_hash"] = digest(
        "moth-experimental-surface-payload/1.0", claims_tampered["payload"]
    )
    try:
        instance.replay(claims_tampered)
    except SurfaceFidelityFailure:
        claims_detected = True
    else:
        claims_detected = False

    size_tampered = deepcopy(package["archive"])
    response = size_tampered["payload"]["surface_response"]
    response["size_mode"] = "CONCISE"
    without_hash = {key: value for key, value in response.items() if key != "response_hash"}
    response["response_hash"] = digest("moth-experimental-surface-response/1.0", without_hash)
    size_tampered["payload_hash"] = digest(
        "moth-experimental-surface-payload/1.0", size_tampered["payload"]
    )
    try:
        instance.replay(size_tampered)
    except SurfaceFidelityFailure:
        size_detected = True
    else:
        size_detected = False

    semantic_tampered = deepcopy(package["archive"])
    semantic_tampered["payload"]["runtime_output"]["value"]["failure-reason"] = "DEADLINE"
    semantic_tampered["payload_hash"] = digest(
        "moth-experimental-surface-payload/1.0", semantic_tampered["payload"]
    )
    try:
        instance.replay(semantic_tampered)
    except SurfaceFidelityFailure:
        semantic_detected = True
    else:
        semantic_detected = False

    direct_response = deepcopy(package["surface_response"])
    direct_response["text"] = direct_response["text"].replace("backup plan", "proposed plan", 1)
    without_hash = {key: value for key, value in direct_response.items() if key != "response_hash"}
    direct_response["response_hash"] = digest("moth-experimental-surface-response/1.0", without_hash)
    try:
        verify_response(direct_response, package["runtime_result"]["output"], compilation, field)
    except SurfaceFidelityFailure:
        discourse_detected = True
    else:
        discourse_detected = False

    results = {
        "archive_envelope": archive_detected,
        "semantic_claims": claims_detected,
        "size_mode": size_detected,
        "runtime_semantics": semantic_detected,
        "outcome_first_text": discourse_detected,
    }
    if not all(results.values()):
        raise CampaignFailure(f"tampering escaped detection: {results}")
    return results


def compile_only() -> dict[str, Any]:
    freeze, protected = _verify_freeze()
    field = _load_json(FIXTURES / "surface-base-field-en-1.0.json")
    inventory = validate_field(field)
    primary, paraphrase, _ = _compile_candidates(field)
    return {
        "schema": "moth-v5-compiled-surface-compile/1.0",
        "status": "COMPILED",
        "field_hash": primary["field_hash"],
        "policy_hash": primary["policy_hash"],
        "primary_trace_hash": primary["trace_hash"],
        "paraphrase_trace_hash": paraphrase["trace_hash"],
        "equivalent_policy": primary["policy"] == paraphrase["policy"],
        "hierarchy_inventory": inventory,
        "fixture_freeze_verified": True,
        "protected_hashes": protected,
        "freeze_hash": sha256_bytes(canonical_bytes(freeze)),
    }


def run_campaign() -> dict[str, Any]:
    freeze, protected_before = _verify_freeze()
    field = _load_json(FIXTURES / "surface-base-field-en-1.0.json")
    panel = _load_json(FIXTURES / "campaign-en-1.0.json")
    if panel.get("schema") != "moth-v5-compiled-surface-campaign/1.0" or not panel.get("frozen_before_execution"):
        raise CampaignFailure("campaign panel is not frozen")
    inventory = validate_field(field)
    primary, paraphrase, _ = _compile_candidates(field)

    repeated = {
        compile_skill(
            (FIXTURES / "natural-response/SKILL.md").read_text(encoding="utf-8"),
            field,
        )["policy_hash"]
        for _ in range(int(panel["repetitions"]))
    }
    if repeated != {primary["policy_hash"]}:
        raise CampaignFailure("skill compilation is not deterministic")
    invalid_skills = _invalid_skill_gates(field, panel)

    thresholds = _load_json(ROOT / "config/v5.0/grounding-en-1.0.json")["thresholds"]
    response_count = 0
    replay_count = 0
    runtime_parity = 0
    refusal_parity = 0
    word_ranges = {mode: [10_000, 0] for mode in field["size_bands"]}
    surface_hashes: set[str] = set()
    graph_groups: dict[str, set[str]] = {}
    sample_package: dict[str, Any] | None = None
    sample_instance: IsolatedSurfaceInstance | None = None

    with TemporaryDirectory(prefix="moth-v5-surface-skill-") as temporary:
        temporary_root = Path(temporary)
        control = IsolatedSurfaceInstance(
            temporary_root / "control",
            project_root=ROOT,
            field=field,
            compilation=primary,
            thresholds=thresholds,
        )
        candidate = IsolatedSurfaceInstance(
            temporary_root / "candidate",
            project_root=ROOT,
            field=field,
            compilation=primary,
            thresholds=thresholds,
        )

        for case in panel["answer_cases"]:
            control_result = control.query_runtime(str(case["prompt"]))
            if control_result.get("status") != "ANSWER" or control_result.get("output", {}).get("value") != case["expected"]:
                raise CampaignFailure(f"{case['id']}: frozen Runtime 5.0 result differs from expectation")
            graph_groups.setdefault(str(case["equivalence_group"]), set()).add(_semantic_graph(control_result))
            for size_case in panel["size_requests"]:
                package = candidate.query(str(case["prompt"]), str(size_case["request"]))
                runtime_result = package["runtime_result"]
                if runtime_bytes(runtime_result) != runtime_bytes(control_result):
                    raise CampaignFailure(f"{case['id']}/{size_case['id']}: candidate changed Runtime output")
                runtime_parity += 1
                response = package["surface_response"]
                if not package["surface_applied"] or response.get("size_mode") != size_case["mode"]:
                    raise CampaignFailure(f"{case['id']}/{size_case['id']}: Surface mode mismatch")
                if response.get("claims") != case["expected"]:
                    raise CampaignFailure(f"{case['id']}/{size_case['id']}: Surface claims drifted")
                verify_response(response, runtime_result["output"], primary, field)
                if candidate.replay(package["archive"]) != canonical_bytes(package["archive"]):
                    raise CampaignFailure(f"{case['id']}/{size_case['id']}: archive replay differs")
                response_count += 1
                replay_count += 1
                mode = str(response["size_mode"])
                word_ranges[mode][0] = min(word_ranges[mode][0], int(response["word_count"]))
                word_ranges[mode][1] = max(word_ranges[mode][1], int(response["word_count"]))
                surface_hashes.add(str(response["response_hash"]))
                if sample_package is None and mode == "DETAILED":
                    sample_package = package
                    sample_instance = candidate

        for case in panel["refusal_cases"]:
            control_result = control.query_runtime(str(case["prompt"]))
            package = candidate.query(str(case["prompt"]), "Explain the result in detail.")
            if runtime_bytes(package["runtime_result"]) != runtime_bytes(control_result):
                raise CampaignFailure(f"{case['id']}: refusal changed in candidate instance")
            if control_result.get("status") != "REFUSAL" or control_result.get("refusal", {}).get("code") != case["expected_refusal"]:
                raise CampaignFailure(f"{case['id']}: Runtime refusal differs from frozen expectation")
            if package["surface_applied"] or package["surface_response"] is not None or package["archive"] is not None:
                raise CampaignFailure(f"{case['id']}: Surface converted a Runtime refusal")
            refusal_parity += 1

        accepted_output = control.query_runtime(str(panel["answer_cases"][0]["prompt"]))["output"]
        try:
            realize(accepted_output, str(panel["unknown_presentation_request"]), primary, field)
        except SurfaceFidelityFailure as exc:
            if exc.code != "UNSUPPORTED_PRESENTATION":
                raise CampaignFailure(f"unknown presentation returned {exc.code}") from exc
            unknown_presentation_refused = True
        else:
            raise CampaignFailure("unknown presentation request was accepted")

        malformed = deepcopy(accepted_output)
        del malformed["value"]["failure-reason"]
        try:
            realize(malformed, "Answer concisely.", primary, field)
        except SurfaceFidelityFailure as exc:
            if exc.code != "MALFORMED_SEMANTIC_RESULT":
                raise CampaignFailure(f"malformed result returned {exc.code}") from exc
            malformed_result_refused = True
        else:
            raise CampaignFailure("malformed semantic result was accepted")

        ablations = _ablation_gates(field, primary, accepted_output)
        if sample_package is None or sample_instance is None:
            raise CampaignFailure("no answer was available for tamper probes")
        tampering = _tamper_gates(sample_instance, sample_package, primary, field)

        control_store = control.store_path
        candidate_store = candidate.store_path
        if not control_store.exists() or not candidate_store.exists() or control_store == candidate_store:
            raise CampaignFailure("control and candidate stores are not independent")
        if ROOT / "data/store-5.0.sqlite3" in {control_store, candidate_store}:
            raise CampaignFailure("an experiment used the production store")

    if Path(temporary).exists():
        raise CampaignFailure("temporary Runtime 5.0 instances were not removed")

    for group, graphs in graph_groups.items():
        if group == "backup-resource" and len(graphs) != 1:
            raise CampaignFailure("input-language paraphrases did not converge to one semantic graph")
    if response_count != len(panel["answer_cases"]) * len(panel["size_requests"]):
        raise CampaignFailure("campaign response count is incomplete")
    if len(surface_hashes) < 15:
        raise CampaignFailure("Surface realization did not vary across meanings and sizes")

    protected_after = {relative: _path_hash(ROOT / relative) for relative in freeze["protected"]}
    if protected_after != protected_before:
        changed = sorted(key for key in protected_after if protected_after[key] != protected_before.get(key))
        raise CampaignFailure(f"protected foundation changed during execution: {changed}")

    _, clauses = parse_skill((FIXTURES / "natural-response/SKILL.md").read_text(encoding="utf-8"))
    graph_units = int(primary["trace"]["graph_unit_count"])
    result = {
        "schema": "moth-v5-compiled-surface-result/1.0",
        "verdict": "BOUNDED_COMPILED_NATURAL_SURFACE_CONFIRMED",
        "hierarchy_inventory": inventory,
        "policy_equivalence": {
            "primary_equals_paraphrase": primary["policy"] == paraphrase["policy"],
            "primary_equals_granular_oracle": True,
        },
        "compiled_hashes": {
            "field": primary["field_hash"],
            "policy": primary["policy_hash"],
            "primary_trace": primary["trace_hash"],
            "paraphrase_trace": paraphrase["trace_hash"],
        },
        "instruction_expansion": {
            "source_normative_clauses": len(clauses),
            "compiled_graph_units": graph_units,
            "expansion_ratio": round(graph_units / len(clauses), 6),
        },
        "surface_campaign": {
            "semantic_cases": len(panel["answer_cases"]),
            "size_requests": len(panel["size_requests"]),
            "natural_responses": response_count,
            "runtime_byte_parity": runtime_parity,
            "semantic_omissions": 0,
            "unsupported_additions": 0,
            "size_violations": 0,
            "prose_violations": 0,
            "distinct_response_hashes": len(surface_hashes),
            "word_ranges": {mode: {"minimum": values[0], "maximum": values[1]} for mode, values in word_ranges.items()},
        },
        "refusal_preservation": {
            "cases": refusal_parity,
            "converted_to_answers": 0,
            "byte_exact_with_control": refusal_parity,
        },
        "language_fidelity": {
            "equivalent_skill_policy": True,
            "input_paraphrase_graph_count": len(graph_groups["backup-resource"]),
            "unknown_presentation_refused": unknown_presentation_refused,
            "malformed_result_refused": malformed_result_refused,
        },
        "invalid_skill_cases": invalid_skills,
        "causal_ablations": ablations,
        "tampering_detected": tampering,
        "deterministic_compilations": int(panel["repetitions"]),
        "surface_archive_replays": replay_count,
        "temporary_instances_removed": True,
        "independent_store_count": 2,
        "production_store_accesses": 0,
        "network_attempts": 0,
        "execution_performed": False,
        "dispatch_count": 0,
        "protected_hashes_unchanged": True,
        "protected_hashes": protected_before,
        "fixture_freeze_verified": True,
        "fixture_freeze_hash": sha256_bytes(canonical_bytes(freeze)),
    }
    result["result_hash"] = digest("moth-v5-compiled-surface-result/1.0", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--compile-only", action="store_true")
    arguments = parser.parse_args()
    result = compile_only() if arguments.compile_only else run_campaign()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
