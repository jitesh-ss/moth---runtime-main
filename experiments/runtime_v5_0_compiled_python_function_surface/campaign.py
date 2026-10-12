"""Run the frozen Runtime 5.0 Python-function Surface campaign."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from moth_runtime_v5_0.canonical import canonical_bytes as runtime_bytes

from experiments.runtime_v5_0_compiled_surface_skill.compiler import compile_skill, parse_skill, validate_field
from experiments.runtime_v5_0_compiled_surface_skill.model import SkillCompilationFailure, policy_hash

from .instance import PythonFunctionSurfaceInstance
from .model import ProgramFidelityFailure, canonical_bytes, digest, sha256_bytes
from .realizer import build_program, realize_artifact, verify_program_ast


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
    if freeze.get("schema") != "moth-v5-python-function-surface-freeze/1.0" or not freeze.get("frozen_before_execution"):
        raise CampaignFailure("fixture freeze is absent or invalid")
    for relative, expected in freeze["fixtures"].items():
        if _path_hash(FIXTURES / relative) != expected:
            raise CampaignFailure(f"frozen fixture changed: {relative}")
    protected = {relative: _path_hash(ROOT / relative) for relative in freeze["protected"]}
    if protected != freeze["protected"]:
        changed = sorted(key for key in protected if protected[key] != freeze["protected"].get(key))
        raise CampaignFailure(f"protected foundation changed before execution: {changed}")
    return freeze, protected


def _compile_candidates(field: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    primary = compile_skill((FIXTURES / "python-function-output/SKILL.md").read_text(), field)
    paraphrase = compile_skill((FIXTURES / "python-function-output-paraphrase/SKILL.md").read_text(), field)
    oracle = _load_json(FIXTURES / "granular-python-function-oracle-1.0.json")
    if primary["policy"] != oracle or paraphrase["policy"] != oracle:
        raise CampaignFailure("compiled policy differs from the frozen granular oracle")
    if primary["policy_hash"] != paraphrase["policy_hash"]:
        raise CampaignFailure("equivalent skills produced different policies")
    return primary, paraphrase


def _append_clause(document: str, section: str, clause: str) -> str:
    return document.rstrip() + f"\n\n## {section.title()}\n\n- {clause}\n"


def _invalid_skill_gates(field: dict[str, Any], panel: dict[str, Any]) -> dict[str, dict[str, str]]:
    source = (FIXTURES / "python-function-output/SKILL.md").read_text()
    results: dict[str, dict[str, str]] = {}
    for case in panel["invalid_skill_cases"]:
        try:
            if "remove_rule" in case:
                compile_skill(source, field, ignored_rule_ids={str(case["remove_rule"])})
            else:
                compile_skill(_append_clause(source, str(case["append_section"]), str(case["append_clause"])), field)
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
    execution_parent: Path,
) -> dict[str, dict[str, str]]:
    actions = {
        "variable_binder": "BIND_INPUT_VARIABLES",
        "function_planner": "DEFINE_SELECT_PLAN",
        "ast_verifier": "VERIFY_AST_ALLOWLIST",
        "shape_verifier": "VERIFY_PROGRAM_SHAPE",
        "execution_harness": "EXECUTE_CONSTRAINED",
        "value_verifier": "VERIFY_EXACT_VALUE",
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
            realize_artifact(
                runtime_output,
                "Return Python with functions and variables.",
                ablated,
                field,
                execution_parent,
            )
        except ProgramFidelityFailure as exc:
            if exc.code != "INCOMPLETE_SURFACE_POLICY":
                raise CampaignFailure(f"{subsystem}: wrong failure {exc.code}") from exc
            results[subsystem] = {"status": "PASSED", "code": exc.code}
        else:
            raise CampaignFailure(f"{subsystem}: ablated policy still emitted a program")
    return results


def _unsafe_program_gates(sample_text: str, field: dict[str, Any]) -> dict[str, str]:
    variants = {
        "import": "import os\n" + sample_text,
        "filesystem_call": sample_text + "\nopen('result.txt', 'w')",
        "attribute_call": sample_text + "\nfailure_reason.lower()",
        "loop": sample_text + "\nfor item in decision:\n    print(item)",
        "dynamic_call": sample_text + "\neval('1 + 1')",
    }
    results: dict[str, str] = {}
    for name, text in variants.items():
        try:
            verify_program_ast(text, field)
        except ProgramFidelityFailure as exc:
            if exc.code not in {"UNSAFE_PYTHON", "INVALID_PROGRAM_SHAPE"}:
                raise CampaignFailure(f"{name}: wrong unsafe-program failure {exc.code}") from exc
            results[name] = exc.code
        else:
            raise CampaignFailure(f"{name}: unsafe program was accepted")
    return results


def _rehash_artifact(artifact: dict[str, Any]) -> None:
    without_hash = {key: value for key, value in artifact.items() if key != "artifact_hash"}
    artifact["artifact_hash"] = digest("moth-experimental-python-function-artifact/1.0", without_hash)


def _rehash_archive(archive: dict[str, Any]) -> None:
    archive["payload_hash"] = digest("moth-experimental-python-function-payload/1.0", archive["payload"])


def _tamper_gates(instance: PythonFunctionSurfaceInstance, package: dict[str, Any]) -> dict[str, bool]:
    probes: dict[str, dict[str, Any]] = {}

    envelope = deepcopy(package["archive"])
    envelope["payload"]["artifact"]["text"] += "\n"
    probes["archive_envelope"] = envelope

    source = deepcopy(package["archive"])
    source["payload"]["artifact"]["text"] = source["payload"]["artifact"]["text"].replace(
        'return "BACKUP"', 'return "PROPOSED"', 1
    )
    _rehash_artifact(source["payload"]["artifact"])
    _rehash_archive(source)
    probes["function_return"] = source

    variable = deepcopy(package["archive"])
    artifact = variable["payload"]["artifact"]
    artifact["text"] = artifact["text"].replace("backup_valid = True", "backup_valid = False", 1)
    _rehash_artifact(artifact)
    _rehash_archive(variable)
    probes["input_variable"] = variable

    execution_hash = deepcopy(package["archive"])
    execution_hash["payload"]["artifact"]["execution_value_hash"] = "0" * 64
    _rehash_artifact(execution_hash["payload"]["artifact"])
    _rehash_archive(execution_hash)
    probes["execution_value_hash"] = execution_hash

    semantics = deepcopy(package["archive"])
    semantics["payload"]["runtime_output"]["value"]["failure-reason"] = "DEADLINE"
    _rehash_archive(semantics)
    probes["runtime_semantics"] = semantics

    policy = deepcopy(package["archive"])
    policy["payload"]["policy_hash"] = "0" * 64
    _rehash_archive(policy)
    probes["policy_binding"] = policy

    results: dict[str, bool] = {}
    for name, archive in probes.items():
        try:
            instance.replay(archive)
        except ProgramFidelityFailure:
            results[name] = True
        else:
            results[name] = False
    if not all(results.values()):
        raise CampaignFailure(f"tampering escaped detection: {results}")
    return results


def compile_only() -> dict[str, Any]:
    freeze, protected = _verify_freeze()
    field = _load_json(FIXTURES / "python-function-surface-field-en-1.0.json")
    inventory = validate_field(field)
    primary, paraphrase = _compile_candidates(field)
    return {
        "schema": "moth-v5-python-function-surface-compile/1.0",
        "status": "COMPILED",
        "field_hash": primary["field_hash"],
        "policy_hash": primary["policy_hash"],
        "primary_trace_hash": primary["trace_hash"],
        "paraphrase_trace_hash": paraphrase["trace_hash"],
        "equivalent_policy": True,
        "hierarchy_inventory": inventory,
        "fixture_freeze_verified": True,
        "protected_hashes": protected,
        "freeze_hash": sha256_bytes(canonical_bytes(freeze)),
    }


def run_campaign() -> dict[str, Any]:
    freeze, protected_before = _verify_freeze()
    field = _load_json(FIXTURES / "python-function-surface-field-en-1.0.json")
    panel = _load_json(FIXTURES / "campaign-en-1.0.json")
    if panel.get("schema") != "moth-v5-python-function-surface-campaign/1.0" or not panel.get("frozen_before_execution"):
        raise CampaignFailure("campaign panel is not frozen")
    inventory = validate_field(field)
    primary, paraphrase = _compile_candidates(field)
    source = (FIXTURES / "python-function-output/SKILL.md").read_text()
    repeated = {compile_skill(source, field)["policy_hash"] for _ in range(int(panel["repetitions"]))}
    if repeated != {primary["policy_hash"]}:
        raise CampaignFailure("skill compilation is not deterministic")
    invalid_skills = _invalid_skill_gates(field, panel)

    thresholds = _load_json(ROOT / "config/v5.0/grounding-en-1.0.json")["thresholds"]
    artifact_count = 0
    runtime_parity = 0
    replay_count = 0
    refusal_parity = 0
    artifact_hashes: set[str] = set()
    byte_minimum = 10_000
    byte_maximum = 0
    line_counts: set[int] = set()
    ast_node_counts: set[int] = set()
    graph_pair: set[str] = set()
    sample_package: dict[str, Any] | None = None
    sample_instance: PythonFunctionSurfaceInstance | None = None
    sample_program = ""

    with TemporaryDirectory(prefix="moth-v5-python-function-") as temporary:
        temporary_root = Path(temporary)
        control = PythonFunctionSurfaceInstance(
            temporary_root / "control", project_root=ROOT, field=field, compilation=primary, thresholds=thresholds
        )
        candidate = PythonFunctionSurfaceInstance(
            temporary_root / "candidate", project_root=ROOT, field=field, compilation=primary, thresholds=thresholds
        )

        for case_index, case in enumerate(panel["answer_cases"]):
            control_result = control.query_runtime(str(case["prompt"]))
            if control_result.get("status") != "ANSWER" or control_result.get("output", {}).get("value") != case["expected"]:
                raise CampaignFailure(f"{case['id']}: Runtime result differs from frozen expectation")
            if case_index < 2:
                graph_pair.add(str(control_result["stages"][0]["program"]["grounding"]["semantic_interpretation"]["semantic_graph_hash"]))
            for request in panel["presentation_requests"]:
                package = candidate.query(str(case["prompt"]), str(request["request"]))
                if runtime_bytes(package["runtime_result"]) != runtime_bytes(control_result):
                    raise CampaignFailure(f"{case['id']}/{request['id']}: candidate changed Runtime output")
                artifact = package["artifact"]
                if not package["surface_applied"] or artifact.get("format") != "PYTHON":
                    raise CampaignFailure(f"{case['id']}/{request['id']}: Python program was not emitted")
                if artifact["ast"]["functions"] != ["boolean_text", "select_plan", "build_decision"]:
                    raise CampaignFailure(f"{case['id']}/{request['id']}: function shape changed")
                if artifact["ast"]["module_variables"] != ["proposed_valid", "backup_valid", "failure_reason", "decision"]:
                    raise CampaignFailure(f"{case['id']}/{request['id']}: variable shape changed")
                if candidate.replay(package["archive"]) != canonical_bytes(package["archive"]):
                    raise CampaignFailure(f"{case['id']}/{request['id']}: archive replay differs")
                artifact_count += 1
                runtime_parity += 1
                replay_count += 1
                artifact_hashes.add(str(artifact["artifact_hash"]))
                byte_minimum = min(byte_minimum, int(artifact["ast"]["byte_count"]))
                byte_maximum = max(byte_maximum, int(artifact["ast"]["byte_count"]))
                line_counts.add(int(artifact["ast"]["line_count"]))
                ast_node_counts.add(int(artifact["ast"]["node_count"]))
                if sample_package is None:
                    sample_package = package
                    sample_instance = candidate
                    sample_program = str(artifact["text"])

        for case in panel["refusal_cases"]:
            control_result = control.query_runtime(str(case["prompt"]))
            package = candidate.query(str(case["prompt"]), "Return Python with functions and variables.")
            if runtime_bytes(package["runtime_result"]) != runtime_bytes(control_result):
                raise CampaignFailure(f"{case['id']}: refusal changed in candidate")
            if control_result.get("status") != "REFUSAL" or control_result.get("refusal", {}).get("code") != case["expected_refusal"]:
                raise CampaignFailure(f"{case['id']}: refusal differs from expectation")
            if package["surface_applied"] or package["artifact"] is not None or package["archive"] is not None:
                raise CampaignFailure(f"{case['id']}: refusal became a program")
            refusal_parity += 1

        accepted_output = control.query_runtime(str(panel["answer_cases"][0]["prompt"]))["output"]
        try:
            realize_artifact(accepted_output, str(panel["unknown_request"]), primary, field, candidate.execution_parent)
        except ProgramFidelityFailure as exc:
            if exc.code != "UNSUPPORTED_PRESENTATION":
                raise CampaignFailure(f"unknown request returned {exc.code}") from exc
            unknown_request_refused = True
        else:
            raise CampaignFailure("unknown presentation request was accepted")

        malformed = deepcopy(accepted_output)
        del malformed["value"]["selected-plan"]
        try:
            realize_artifact(
                malformed,
                "Return Python with functions and variables.",
                primary,
                field,
                candidate.execution_parent,
            )
        except ProgramFidelityFailure as exc:
            if exc.code != "MALFORMED_SEMANTIC_RESULT":
                raise CampaignFailure(f"malformed result returned {exc.code}") from exc
            malformed_result_refused = True
        else:
            raise CampaignFailure("malformed semantic result was accepted")

        ablations = _ablation_gates(field, primary, accepted_output, candidate.execution_parent)
        if sample_package is None or sample_instance is None:
            raise CampaignFailure("tamper sample was not produced")
        unsafe_programs = _unsafe_program_gates(sample_program, field)
        tampering = _tamper_gates(sample_instance, sample_package)
        if control.store_path == candidate.store_path or ROOT / "data/store-5.0.sqlite3" in {control.store_path, candidate.store_path}:
            raise CampaignFailure("temporary stores are not isolated")
        if any(candidate.execution_parent.iterdir()):
            raise CampaignFailure("disposable execution directories remain")

    if Path(temporary).exists():
        raise CampaignFailure("temporary Runtime instances were not removed")
    if len(graph_pair) != 1:
        raise CampaignFailure("input-language paraphrases did not converge")
    expected_count = len(panel["answer_cases"]) * len(panel["presentation_requests"])
    if artifact_count != expected_count:
        raise CampaignFailure("program campaign count is incomplete")

    protected_after = {relative: _path_hash(ROOT / relative) for relative in freeze["protected"]}
    if protected_after != protected_before:
        changed = sorted(key for key in protected_after if protected_after[key] != protected_before.get(key))
        raise CampaignFailure(f"protected foundation changed during execution: {changed}")

    _, clauses = parse_skill(source)
    positive_execution_count = artifact_count * 3
    result = {
        "schema": "moth-v5-python-function-surface-result/1.0",
        "verdict": "BOUNDED_COMPILED_PYTHON_FUNCTION_SURFACE_CONFIRMED",
        "execution_boundary": "CONSTRAINED_LOCAL_SUBPROCESS_NOT_HARDENED_CONTAINER",
        "hierarchy_inventory": inventory,
        "policy_equivalence": {"primary_equals_paraphrase": True, "primary_equals_granular_oracle": True},
        "compiled_hashes": {
            "field": primary["field_hash"],
            "policy": primary["policy_hash"],
            "primary_trace": primary["trace_hash"],
            "paraphrase_trace": paraphrase["trace_hash"],
        },
        "instruction_expansion": {
            "source_normative_clauses": len(clauses),
            "compiled_graph_units": primary["trace"]["graph_unit_count"],
            "expansion_ratio": round(primary["trace"]["graph_unit_count"] / len(clauses), 6),
        },
        "program_campaign": {
            "semantic_cases": len(panel["answer_cases"]),
            "presentation_requests": len(panel["presentation_requests"]),
            "programs": artifact_count,
            "runtime_byte_parity": runtime_parity,
            "ast_valid": artifact_count,
            "executed_exact_value": artifact_count,
            "archive_replays": replay_count,
            "positive_execution_count_including_replay_verification": positive_execution_count,
            "semantic_drift": 0,
            "unsafe_python_accepted": 0,
            "functions_per_program": 3,
            "module_variables_per_program": 4,
            "distinct_program_artifact_hashes": len(artifact_hashes),
            "byte_range": {"minimum": byte_minimum, "maximum": byte_maximum},
            "line_counts": sorted(line_counts),
            "ast_node_counts": sorted(ast_node_counts),
        },
        "refusal_preservation": {"cases": refusal_parity, "byte_exact_with_control": refusal_parity, "converted_to_programs": 0},
        "language_fidelity": {
            "equivalent_skill_policy": True,
            "input_paraphrase_graph_count": len(graph_pair),
            "unknown_request_refused": unknown_request_refused,
            "malformed_result_refused": malformed_result_refused,
        },
        "invalid_skill_cases": invalid_skills,
        "unsafe_program_cases": unsafe_programs,
        "causal_ablations": ablations,
        "tampering_detected": tampering,
        "deterministic_compilations": int(panel["repetitions"]),
        "temporary_instances_removed": True,
        "temporary_execution_directories_removed": True,
        "independent_store_count": 2,
        "production_store_accesses": 0,
        "network_capable_ast_nodes": 0,
        "dispatch_count": 0,
        "protected_hashes_unchanged": True,
        "protected_hashes": protected_before,
        "fixture_freeze_verified": True,
        "fixture_freeze_hash": sha256_bytes(canonical_bytes(freeze)),
        "sample_program": sample_program,
    }
    result["result_hash"] = digest("moth-v5-python-function-surface-result/1.0", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--compile-only", action="store_true")
    arguments = parser.parse_args()
    result = compile_only() if arguments.compile_only else run_campaign()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
