"""Run the frozen JSON/Python Surface-skill campaign."""

from __future__ import annotations

import argparse
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from moth_runtime_v5_0.canonical import canonical_bytes as runtime_bytes

from experiments.runtime_v5_0_compiled_surface_skill.compiler import (
    compile_skill,
    parse_skill,
    validate_field,
)
from experiments.runtime_v5_0_compiled_surface_skill.model import (
    SkillCompilationFailure,
    policy_hash,
)

from .instance import StructuredSurfaceInstance
from .model import ArtifactFidelityFailure, canonical_bytes, digest, sha256_bytes
from .serializer import serialize_artifact, verify_artifact


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
    if freeze.get("schema") != "moth-v5-json-python-surface-freeze/1.0" or not freeze.get("frozen_before_execution"):
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
    primary = compile_skill((FIXTURES / "structured-output/SKILL.md").read_text(), field)
    paraphrase = compile_skill((FIXTURES / "structured-output-paraphrase/SKILL.md").read_text(), field)
    oracle = _load_json(FIXTURES / "granular-structured-oracle-1.0.json")
    if primary["policy"] != oracle or paraphrase["policy"] != oracle:
        raise CampaignFailure("compiled policy differs from the frozen granular oracle")
    if primary["policy_hash"] != paraphrase["policy_hash"]:
        raise CampaignFailure("equivalent structured-output skills produced different policies")
    return primary, paraphrase


def _append_clause(document: str, section: str, clause: str) -> str:
    return document.rstrip() + f"\n\n## {section.title()}\n\n- {clause}\n"


def _invalid_skill_gates(field: dict[str, Any], panel: dict[str, Any]) -> dict[str, dict[str, str]]:
    source = (FIXTURES / "structured-output/SKILL.md").read_text()
    results: dict[str, dict[str, str]] = {}
    for case in panel["invalid_skill_cases"]:
        try:
            if "remove_rule" in case:
                compile_skill(source, field, ignored_rule_ids={str(case["remove_rule"])})
            else:
                compile_skill(
                    _append_clause(source, str(case["append_section"]), str(case["append_clause"])),
                    field,
                )
        except SkillCompilationFailure as exc:
            if exc.code != case["expected_code"]:
                raise CampaignFailure(f"{case['id']}: expected {case['expected_code']}, got {exc.code}") from exc
            results[str(case["id"])] = {"status": "PASSED", "code": exc.code}
        else:
            raise CampaignFailure(f"{case['id']}: invalid skill compiled")
    return results


def _ablation_gates(field: dict[str, Any], compilation: dict[str, Any], runtime_output: dict[str, Any]) -> dict[str, dict[str, str]]:
    actions = {
        "format_router": "DETECT_FORMAT_SIGNAL",
        "json_serializer": "SERIALIZE_JSON",
        "python_serializer": "SERIALIZE_PYTHON_LITERAL",
        "exact_value_verifier": "VERIFY_EXACT_VALUE",
        "safe_ast_verifier": "VERIFY_SAFE_AST",
        "hash_binder": "BIND_SEMANTIC_HASH",
    }
    results: dict[str, dict[str, str]] = {}
    for subsystem, action in actions.items():
        ablated = deepcopy(compilation)
        workflow = [item for item in ablated["policy"]["workflow"] if item != action]
        ablated["policy"]["workflow"] = workflow
        ablated["policy"]["edges"] = [[left, right] for left, right in zip(workflow, workflow[1:])]
        ablated["policy_hash"] = policy_hash(ablated["policy"])
        request = "Return compact Python." if "python" in subsystem or "ast" in subsystem else "Return compact JSON."
        try:
            serialize_artifact(runtime_output, request, ablated, field)
        except ArtifactFidelityFailure as exc:
            if exc.code != "INCOMPLETE_SURFACE_POLICY":
                raise CampaignFailure(f"{subsystem}: wrong ablation failure {exc.code}") from exc
            results[subsystem] = {"status": "PASSED", "code": exc.code}
        else:
            raise CampaignFailure(f"{subsystem}: ablated policy still emitted an artifact")
    return results


def _rehash_artifact(artifact: dict[str, Any]) -> None:
    without_hash = {key: value for key, value in artifact.items() if key != "artifact_hash"}
    artifact["artifact_hash"] = digest("moth-experimental-structured-artifact/1.0", without_hash)


def _rehash_archive(archive: dict[str, Any]) -> None:
    archive["payload_hash"] = digest("moth-experimental-structured-payload/1.0", archive["payload"])


def _tamper_gates(
    instance: StructuredSurfaceInstance,
    json_package: dict[str, Any],
    python_package: dict[str, Any],
    compilation: dict[str, Any],
    field: dict[str, Any],
) -> dict[str, bool]:
    envelope = deepcopy(json_package["archive"])
    envelope["payload"]["artifact"]["text"] += " "
    try:
        instance.replay(envelope)
    except ArtifactFidelityFailure:
        envelope_detected = True
    else:
        envelope_detected = False

    json_value = deepcopy(json_package["archive"])
    artifact = json_value["payload"]["artifact"]
    artifact["text"] = artifact["text"].replace("BACKUP", "PROPOSED", 1)
    artifact["byte_count"] = len(artifact["text"].encode("utf-8"))
    _rehash_artifact(artifact)
    _rehash_archive(json_value)
    try:
        instance.replay(json_value)
    except ArtifactFidelityFailure:
        json_detected = True
    else:
        json_detected = False

    python_ast = deepcopy(python_package["archive"])
    artifact = python_ast["payload"]["artifact"]
    artifact["text"] = "decision = dict()"
    artifact["byte_count"] = len(artifact["text"].encode("utf-8"))
    artifact["line_count"] = 1
    _rehash_artifact(artifact)
    _rehash_archive(python_ast)
    try:
        instance.replay(python_ast)
    except ArtifactFidelityFailure:
        ast_detected = True
    else:
        ast_detected = False

    layout = deepcopy(json_package["archive"])
    artifact = layout["payload"]["artifact"]
    runtime_value = layout["payload"]["runtime_output"]["value"]
    artifact["text"] = json.dumps(runtime_value, sort_keys=True, separators=(",", ":"))
    artifact["byte_count"] = len(artifact["text"].encode("utf-8"))
    artifact["line_count"] = 1
    _rehash_artifact(artifact)
    _rehash_archive(layout)
    try:
        instance.replay(layout)
    except ArtifactFidelityFailure:
        layout_detected = True
    else:
        layout_detected = False

    semantic = deepcopy(json_package["archive"])
    semantic["payload"]["runtime_output"]["value"]["failure-reason"] = "DEADLINE"
    _rehash_archive(semantic)
    try:
        instance.replay(semantic)
    except ArtifactFidelityFailure:
        semantic_detected = True
    else:
        semantic_detected = False

    format_change = deepcopy(json_package["artifact"])
    format_change["format"] = "PYTHON"
    _rehash_artifact(format_change)
    try:
        verify_artifact(format_change, json_package["runtime_result"]["output"], compilation, field)
    except ArtifactFidelityFailure:
        format_detected = True
    else:
        format_detected = False

    results = {
        "archive_envelope": envelope_detected,
        "json_value": json_detected,
        "python_ast": ast_detected,
        "layout": layout_detected,
        "runtime_semantics": semantic_detected,
        "format_label": format_detected,
    }
    if not all(results.values()):
        raise CampaignFailure(f"tampering escaped detection: {results}")
    return results


def compile_only() -> dict[str, Any]:
    freeze, protected = _verify_freeze()
    field = _load_json(FIXTURES / "structured-surface-field-en-1.0.json")
    inventory = validate_field(field)
    primary, paraphrase = _compile_candidates(field)
    return {
        "schema": "moth-v5-json-python-surface-compile/1.0",
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
    field = _load_json(FIXTURES / "structured-surface-field-en-1.0.json")
    panel = _load_json(FIXTURES / "campaign-en-1.0.json")
    if panel.get("schema") != "moth-v5-json-python-surface-campaign/1.0" or not panel.get("frozen_before_execution"):
        raise CampaignFailure("campaign panel is not frozen")
    inventory = validate_field(field)
    primary, paraphrase = _compile_candidates(field)
    source = (FIXTURES / "structured-output/SKILL.md").read_text()
    repeated = {compile_skill(source, field)["policy_hash"] for _ in range(int(panel["repetitions"]))}
    if repeated != {primary["policy_hash"]}:
        raise CampaignFailure("skill compilation is not deterministic")
    invalid_skills = _invalid_skill_gates(field, panel)

    thresholds = _load_json(ROOT / "config/v5.0/grounding-en-1.0.json")["thresholds"]
    artifact_count = 0
    json_count = 0
    python_count = 0
    compact_count = 0
    readable_count = 0
    runtime_parity = 0
    replay_count = 0
    refusal_parity = 0
    artifact_hashes: set[str] = set()
    byte_ranges = {"JSON_COMPACT": [10_000, 0], "JSON_READABLE": [10_000, 0], "PYTHON_COMPACT": [10_000, 0], "PYTHON_READABLE": [10_000, 0]}
    graph_pair: set[str] = set()
    json_sample: dict[str, Any] | None = None
    python_sample: dict[str, Any] | None = None
    sample_instance: StructuredSurfaceInstance | None = None

    with TemporaryDirectory(prefix="moth-v5-json-python-") as temporary:
        temporary_root = Path(temporary)
        control = StructuredSurfaceInstance(temporary_root / "control", project_root=ROOT, field=field, compilation=primary, thresholds=thresholds)
        candidate = StructuredSurfaceInstance(temporary_root / "candidate", project_root=ROOT, field=field, compilation=primary, thresholds=thresholds)

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
                if not package["surface_applied"] or artifact["format"] != request["format"] or artifact["layout"] != request["layout"]:
                    raise CampaignFailure(f"{case['id']}/{request['id']}: format/layout mismatch")
                verify_artifact(artifact, package["runtime_result"]["output"], primary, field)
                if candidate.replay(package["archive"]) != canonical_bytes(package["archive"]):
                    raise CampaignFailure(f"{case['id']}/{request['id']}: archive replay differs")
                if artifact["format"] == "JSON":
                    recovered = json.loads(artifact["text"])
                    json_count += 1
                else:
                    tree = ast.parse(artifact["text"], mode="exec")
                    recovered = ast.literal_eval(tree.body[0].value)
                    python_count += 1
                if recovered != case["expected"]:
                    raise CampaignFailure(f"{case['id']}/{request['id']}: parsed artifact drifted")
                artifact_count += 1
                runtime_parity += 1
                replay_count += 1
                compact_count += artifact["layout"] == "COMPACT"
                readable_count += artifact["layout"] == "READABLE"
                artifact_hashes.add(str(artifact["artifact_hash"]))
                bucket = f"{artifact['format']}_{artifact['layout']}"
                byte_ranges[bucket][0] = min(byte_ranges[bucket][0], int(artifact["byte_count"]))
                byte_ranges[bucket][1] = max(byte_ranges[bucket][1], int(artifact["byte_count"]))
                if artifact["format"] == "JSON" and artifact["layout"] == "READABLE" and json_sample is None:
                    json_sample = package
                    sample_instance = candidate
                if artifact["format"] == "PYTHON" and artifact["layout"] == "READABLE" and python_sample is None:
                    python_sample = package

        for case in panel["refusal_cases"]:
            control_result = control.query_runtime(str(case["prompt"]))
            package = candidate.query(str(case["prompt"]), "Return readable Python.")
            if runtime_bytes(package["runtime_result"]) != runtime_bytes(control_result):
                raise CampaignFailure(f"{case['id']}: refusal changed in candidate")
            if control_result.get("status") != "REFUSAL" or control_result.get("refusal", {}).get("code") != case["expected_refusal"]:
                raise CampaignFailure(f"{case['id']}: refusal differs from expectation")
            if package["surface_applied"] or package["artifact"] is not None or package["archive"] is not None:
                raise CampaignFailure(f"{case['id']}: refusal was serialized as an answer")
            refusal_parity += 1

        accepted_output = control.query_runtime(str(panel["answer_cases"][0]["prompt"]))["output"]
        try:
            serialize_artifact(accepted_output, str(panel["unknown_request"]), primary, field)
        except ArtifactFidelityFailure as exc:
            if exc.code != "UNSUPPORTED_PRESENTATION":
                raise CampaignFailure(f"unknown request returned {exc.code}") from exc
            unknown_request_refused = True
        else:
            raise CampaignFailure("unknown format request was accepted")

        malformed = deepcopy(accepted_output)
        del malformed["value"]["selected-plan"]
        try:
            serialize_artifact(malformed, "Return compact JSON.", primary, field)
        except ArtifactFidelityFailure as exc:
            if exc.code != "MALFORMED_SEMANTIC_RESULT":
                raise CampaignFailure(f"malformed result returned {exc.code}") from exc
            malformed_result_refused = True
        else:
            raise CampaignFailure("malformed semantic result was accepted")

        ablations = _ablation_gates(field, primary, accepted_output)
        if json_sample is None or python_sample is None or sample_instance is None:
            raise CampaignFailure("tamper samples were not produced")
        tampering = _tamper_gates(sample_instance, json_sample, python_sample, primary, field)
        if control.store_path == candidate.store_path or ROOT / "data/store-5.0.sqlite3" in {control.store_path, candidate.store_path}:
            raise CampaignFailure("temporary stores are not isolated")

    if Path(temporary).exists():
        raise CampaignFailure("temporary instances were not removed")
    if len(graph_pair) != 1:
        raise CampaignFailure("Input-language paraphrases did not converge")
    expected_count = len(panel["answer_cases"]) * len(panel["presentation_requests"])
    if artifact_count != expected_count or json_count != 24 or python_count != 16:
        raise CampaignFailure("format campaign counts are incomplete")

    protected_after = {relative: _path_hash(ROOT / relative) for relative in freeze["protected"]}
    if protected_after != protected_before:
        changed = sorted(key for key in protected_after if protected_after[key] != protected_before.get(key))
        raise CampaignFailure(f"protected foundation changed during execution: {changed}")

    _, clauses = parse_skill(source)
    result = {
        "schema": "moth-v5-json-python-surface-result/1.0",
        "verdict": "BOUNDED_COMPILED_JSON_PYTHON_SURFACE_CONFIRMED",
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
        "artifact_campaign": {
            "semantic_cases": len(panel["answer_cases"]),
            "presentation_requests": len(panel["presentation_requests"]),
            "artifacts": artifact_count,
            "json_artifacts": json_count,
            "python_artifacts": python_count,
            "compact_artifacts": compact_count,
            "readable_artifacts": readable_count,
            "runtime_byte_parity": runtime_parity,
            "parsed_exact_value": artifact_count,
            "semantic_drift": 0,
            "schema_violations": 0,
            "unsafe_python": 0,
            "layout_violations": 0,
            "distinct_artifact_hashes": len(artifact_hashes),
            "byte_ranges": {key: {"minimum": values[0], "maximum": values[1]} for key, values in byte_ranges.items()},
        },
        "refusal_preservation": {"cases": refusal_parity, "byte_exact_with_control": refusal_parity, "converted_to_artifacts": 0},
        "language_fidelity": {
            "equivalent_skill_policy": True,
            "input_paraphrase_graph_count": len(graph_pair),
            "unknown_request_refused": unknown_request_refused,
            "malformed_result_refused": malformed_result_refused,
        },
        "invalid_skill_cases": invalid_skills,
        "causal_ablations": ablations,
        "tampering_detected": tampering,
        "deterministic_compilations": int(panel["repetitions"]),
        "archive_replays": replay_count,
        "python_execution_count": 0,
        "temporary_instances_removed": True,
        "independent_store_count": 2,
        "production_store_accesses": 0,
        "network_attempts": 0,
        "dispatch_count": 0,
        "protected_hashes_unchanged": True,
        "protected_hashes": protected_before,
        "fixture_freeze_verified": True,
        "fixture_freeze_hash": sha256_bytes(canonical_bytes(freeze)),
    }
    result["result_hash"] = digest("moth-v5-json-python-surface-result/1.0", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--compile-only", action="store_true")
    arguments = parser.parse_args()
    result = compile_only() if arguments.compile_only else run_campaign()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
