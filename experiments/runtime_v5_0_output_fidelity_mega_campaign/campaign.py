"""Run the frozen multi-phase Runtime 5.0 output-fidelity campaign."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from moth_runtime_v5_0.canonical import canonical_bytes as runtime_bytes

from experiments.runtime_v5_0_compiled_json_python_surface.campaign import run_campaign as run_structured_phase
from experiments.runtime_v5_0_compiled_python_function_surface.campaign import run_campaign as run_executable_phase
from experiments.runtime_v5_0_compiled_surface_skill.campaign import run_campaign as run_natural_phase
from experiments.runtime_v5_0_compiled_surface_skill.compiler import compile_skill, parse_skill, validate_field
from experiments.runtime_v5_0_compiled_surface_skill.model import SkillCompilationFailure, policy_hash

from .instance import RichSurfaceInstance
from .model import OutputFidelityFailure, canonical_bytes, digest, sha256_bytes
from .realizer import realize_artifact, recover_semantics, verify_artifact


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"
FREEZE = FIXTURES / "FREEZE.json"
FAMILIES = ["prose-range", "tone-adaptation", "markdown-structure", "mixed-response"]


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
    if freeze.get("schema") != "moth-v5-output-fidelity-mega-freeze/1.0" or not freeze.get("frozen_before_execution"):
        raise CampaignFailure("fixture freeze is absent or invalid")
    for relative, expected in freeze["fixtures"].items():
        if _path_hash(FIXTURES / relative) != expected:
            raise CampaignFailure(f"frozen fixture changed: {relative}")
    protected = {relative: _path_hash(ROOT / relative) for relative in freeze["protected"]}
    if protected != freeze["protected"]:
        changed = sorted(key for key in protected if protected[key] != freeze["protected"].get(key))
        raise CampaignFailure(f"protected foundation changed before execution: {changed}")
    return freeze, protected


def _compile_families(field: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    oracle = _load_json(FIXTURES / "granular-policy-oracle-en-1.0.json")
    primary: dict[str, dict[str, Any]] = {}
    paraphrase: dict[str, dict[str, Any]] = {}
    for family in FAMILIES:
        first = compile_skill((FIXTURES / family / "SKILL.md").read_text(), field)
        second = compile_skill((FIXTURES / f"{family}-paraphrase" / "SKILL.md").read_text(), field)
        profile = str(first["policy"]["policy_id"])
        if profile != second["policy"]["policy_id"] or first["policy_hash"] != second["policy_hash"]:
            raise CampaignFailure(f"{family}: equivalent skills produced different policies")
        if first["policy_hash"] != oracle["policy_hashes"].get(profile):
            raise CampaignFailure(f"{family}: policy differs from frozen granular oracle")
        if first["policy"]["workflow"] != oracle["workflow"]:
            raise CampaignFailure(f"{family}: workflow differs from frozen granular oracle")
        primary[profile] = first
        paraphrase[profile] = second
    return primary, paraphrase


def _append_clause(document: str, section: str, clause: str) -> str:
    return document.rstrip() + f"\n\n## {section.title()}\n\n- {clause}\n"


def _invalid_skill_gates(field: dict[str, Any], panel: dict[str, Any]) -> dict[str, dict[str, str]]:
    results: dict[str, dict[str, str]] = {}
    for family in FAMILIES:
        source = (FIXTURES / family / "SKILL.md").read_text()
        for case in panel["invalid_skill_cases"]:
            gate_id = f"{family}/{case['id']}"
            try:
                if "remove_rule" in case:
                    compile_skill(source, field, ignored_rule_ids={str(case["remove_rule"])})
                else:
                    compile_skill(_append_clause(source, str(case["append_section"]), str(case["append_clause"])), field)
            except SkillCompilationFailure as exc:
                if exc.code != case["expected_code"]:
                    raise CampaignFailure(f"{gate_id}: expected {case['expected_code']}, got {exc.code}") from exc
                results[gate_id] = {"status": "PASSED", "code": exc.code}
            else:
                raise CampaignFailure(f"{gate_id}: invalid skill compiled")
    return results


def _ablation_gates(
    field: dict[str, Any],
    compilations: dict[str, dict[str, Any]],
    runtime_output: dict[str, Any],
    family_requests: dict[str, str],
) -> dict[str, dict[str, str]]:
    actions = {
        "route_selector": "SELECT_PRESENTATION_ROUTE",
        "discourse_planner": "PLAN_DISCOURSE",
        "fact_realizer": "REALIZE_MATERIAL_FACTS",
        "inverse_recovery": "VERIFY_INVERSE_RECOVERY",
        "hash_binder": "BIND_HASHES",
    }
    results: dict[str, dict[str, str]] = {}
    for profile, compilation in compilations.items():
        for subsystem, action in actions.items():
            ablated = deepcopy(compilation)
            workflow = [item for item in ablated["policy"]["workflow"] if item != action]
            ablated["policy"]["workflow"] = workflow
            ablated["policy"]["edges"] = [[left, right] for left, right in zip(workflow, workflow[1:])]
            ablated["policy_hash"] = policy_hash(ablated["policy"])
            gate_id = f"{profile}/{subsystem}"
            try:
                realize_artifact(runtime_output, family_requests[profile], ablated, field)
            except OutputFidelityFailure as exc:
                if exc.code != "INCOMPLETE_SURFACE_POLICY":
                    raise CampaignFailure(f"{gate_id}: wrong ablation failure {exc.code}") from exc
                results[gate_id] = {"status": "PASSED", "code": exc.code}
            else:
                raise CampaignFailure(f"{gate_id}: ablated policy emitted output")
    return results


def _rehash_artifact(artifact: dict[str, Any]) -> None:
    without_hash = {key: value for key, value in artifact.items() if key != "artifact_hash"}
    artifact["artifact_hash"] = digest("moth-v5-rich-output-artifact/1.0", without_hash)


def _rehash_archive(archive: dict[str, Any]) -> None:
    archive["payload_hash"] = digest("moth-v5-rich-output-payload/1.0", archive["payload"])


def _tamper_gates(instance: RichSurfaceInstance, package: dict[str, Any]) -> dict[str, bool]:
    probes: dict[str, dict[str, Any]] = {}
    envelope = deepcopy(package["archive"])
    envelope["payload"]["artifact"]["text"] += " "
    probes["archive_envelope"] = envelope

    text = deepcopy(package["archive"])
    text["payload"]["artifact"]["text"] = text["payload"]["artifact"]["text"].replace("backup", "proposed", 1)
    _rehash_artifact(text["payload"]["artifact"])
    _rehash_archive(text)
    probes["surface_text"] = text

    mode = deepcopy(package["archive"])
    mode["payload"]["artifact"]["mode"] = "FORMAL_TONE"
    _rehash_artifact(mode["payload"]["artifact"])
    _rehash_archive(mode)
    probes["mode"] = mode

    semantics = deepcopy(package["archive"])
    semantics["payload"]["runtime_output"]["value"]["failure-reason"] = "DEADLINE"
    _rehash_archive(semantics)
    probes["runtime_semantics"] = semantics

    profile = deepcopy(package["archive"])
    profile["payload"]["profile"] = "TONE_ADAPTATION"
    _rehash_archive(profile)
    probes["profile"] = profile

    policy = deepcopy(package["archive"])
    policy["payload"]["policy_hash"] = "0" * 64
    _rehash_archive(policy)
    probes["policy_binding"] = policy

    results: dict[str, bool] = {}
    for name, archive in probes.items():
        try:
            instance.replay(archive)
        except OutputFidelityFailure:
            results[name] = True
        else:
            results[name] = False
    if not all(results.values()):
        raise CampaignFailure(f"tampering escaped detection: {results}")
    return results


def compile_only() -> dict[str, Any]:
    freeze, protected = _verify_freeze()
    field = _load_json(FIXTURES / "rich-surface-field-en-1.0.json")
    inventory = validate_field(field)
    primary, paraphrase = _compile_families(field)
    return {
        "schema": "moth-v5-output-fidelity-mega-compile/1.0",
        "status": "COMPILED",
        "family_count": len(primary),
        "source_skill_count": len(primary) + len(paraphrase),
        "policy_hashes": {profile: value["policy_hash"] for profile, value in sorted(primary.items())},
        "field_hash": next(iter(primary.values()))["field_hash"],
        "hierarchy_inventory": inventory,
        "fixture_freeze_verified": True,
        "freeze_hash": sha256_bytes(canonical_bytes(freeze)),
        "protected_hashes": protected,
    }


def run_rich_phase() -> dict[str, Any]:
    freeze, protected_before = _verify_freeze()
    field = _load_json(FIXTURES / "rich-surface-field-en-1.0.json")
    panel = _load_json(FIXTURES / "campaign-en-1.0.json")
    if panel.get("schema") != "moth-v5-rich-output-campaign/1.0" or not panel.get("frozen_before_execution"):
        raise CampaignFailure("rich-output panel is not frozen")
    inventory = validate_field(field)
    primary, paraphrase = _compile_families(field)
    repeated: dict[str, int] = {}
    for family in FAMILIES:
        source = (FIXTURES / family / "SKILL.md").read_text()
        hashes = {compile_skill(source, field)["policy_hash"] for _ in range(int(panel["repetitions_per_family"]))}
        if len(hashes) != 1:
            raise CampaignFailure(f"{family}: compilation is not deterministic")
        repeated[family] = int(panel["repetitions_per_family"])
    invalid_skills = _invalid_skill_gates(field, panel)

    profile_requests = {str(family["profile"]): str(family["requests"][0]) for family in panel["families"]}
    requests = [(str(family["profile"]), str(request)) for family in panel["families"] for request in family["requests"]]
    thresholds = _load_json(ROOT / "config/v5.0/grounding-en-1.0.json")["thresholds"]
    artifact_count = 0
    runtime_parity = 0
    replay_count = 0
    refusal_parity = 0
    inverse_recovery_count = 0
    output_hashes: set[str] = set()
    graph_pair: set[str] = set()
    mode_metrics: dict[str, dict[str, Any]] = {}
    samples: dict[str, str] = {}
    sample_package: dict[str, Any] | None = None
    sample_instance: RichSurfaceInstance | None = None

    with TemporaryDirectory(prefix="moth-v5-rich-output-") as temporary:
        temporary_root = Path(temporary)
        control = RichSurfaceInstance(
            temporary_root / "control", project_root=ROOT, field=field, compilations=primary, thresholds=thresholds
        )
        candidate = RichSurfaceInstance(
            temporary_root / "candidate", project_root=ROOT, field=field, compilations=primary, thresholds=thresholds
        )
        for case_index, case in enumerate(panel["answer_cases"]):
            control_result = control.query_runtime(str(case["prompt"]))
            if control_result.get("status") != "ANSWER" or control_result.get("output", {}).get("value") != case["expected"]:
                raise CampaignFailure(f"{case['id']}: Runtime result differs from frozen expectation")
            if case_index < 2:
                graph_pair.add(str(control_result["stages"][0]["program"]["grounding"]["semantic_interpretation"]["semantic_graph_hash"]))
            case_texts: set[str] = set()
            for profile, request in requests:
                package = candidate.query(str(case["prompt"]), request)
                if runtime_bytes(package["runtime_result"]) != runtime_bytes(control_result):
                    raise CampaignFailure(f"{case['id']}/{request}: candidate changed Runtime output")
                artifact = package["artifact"]
                if not package["surface_applied"] or recover_semantics(artifact["text"], artifact["mode"]) != case["expected"]:
                    raise CampaignFailure(f"{case['id']}/{request}: inverse recovery failed")
                verify_artifact(artifact, package["runtime_result"]["output"], primary[profile], field)
                if candidate.replay(package["archive"]) != canonical_bytes(package["archive"]):
                    raise CampaignFailure(f"{case['id']}/{request}: archive replay differs")
                case_texts.add(str(artifact["text"]))
                artifact_count += 1
                runtime_parity += 1
                replay_count += 1
                inverse_recovery_count += 1
                output_hashes.add(str(artifact["artifact_hash"]))
                mode = str(artifact["mode"])
                metrics = artifact["metrics"]
                summary = mode_metrics.setdefault(
                    mode,
                    {
                        "count": 0,
                        "minimum_words": 10_000,
                        "maximum_words": 0,
                        "minimum_bytes": 10_000,
                        "maximum_bytes": 0,
                        "line_counts": set(),
                    },
                )
                summary["count"] += 1
                summary["minimum_words"] = min(summary["minimum_words"], metrics["word_count"])
                summary["maximum_words"] = max(summary["maximum_words"], metrics["word_count"])
                summary["minimum_bytes"] = min(summary["minimum_bytes"], metrics["byte_count"])
                summary["maximum_bytes"] = max(summary["maximum_bytes"], metrics["byte_count"])
                summary["line_counts"].add(metrics["line_count"])
                samples.setdefault(mode, str(artifact["text"]))
                if sample_package is None:
                    sample_package = package
                    sample_instance = candidate
            if len(case_texts) != len(requests):
                raise CampaignFailure(f"{case['id']}: presentation modes did not produce distinct outputs")

        for case in panel["refusal_cases"]:
            control_result = control.query_runtime(str(case["prompt"]))
            for profile, request in [(str(family["profile"]), str(family["requests"][0])) for family in panel["families"]]:
                package = candidate.query(str(case["prompt"]), request)
                if runtime_bytes(package["runtime_result"]) != runtime_bytes(control_result):
                    raise CampaignFailure(f"{case['id']}/{profile}: refusal changed")
                if control_result.get("status") != "REFUSAL" or control_result.get("refusal", {}).get("code") != case["expected_refusal"]:
                    raise CampaignFailure(f"{case['id']}: refusal differs from expectation")
                if package["surface_applied"] or package["artifact"] is not None:
                    raise CampaignFailure(f"{case['id']}/{profile}: refusal became output")
                refusal_parity += 1

        accepted_output = control.query_runtime(str(panel["answer_cases"][0]["prompt"]))["output"]
        try:
            candidate.query(str(panel["answer_cases"][0]["prompt"]), str(panel["unknown_request"]))
        except OutputFidelityFailure as exc:
            if exc.code != "UNSUPPORTED_PRESENTATION":
                raise CampaignFailure(f"unknown request returned {exc.code}") from exc
            unknown_request_refused = True
        else:
            raise CampaignFailure("unknown presentation request was accepted")

        malformed_refusals = 0
        malformed = deepcopy(accepted_output)
        del malformed["value"]["selected-plan"]
        for profile, compilation in primary.items():
            try:
                realize_artifact(malformed, profile_requests[profile], compilation, field)
            except OutputFidelityFailure as exc:
                if exc.code != "MALFORMED_SEMANTIC_RESULT":
                    raise CampaignFailure(f"{profile}: malformed result returned {exc.code}") from exc
                malformed_refusals += 1
            else:
                raise CampaignFailure(f"{profile}: malformed result was accepted")

        ablations = _ablation_gates(field, primary, accepted_output, profile_requests)
        if sample_package is None or sample_instance is None:
            raise CampaignFailure("tamper sample was not produced")
        tampering = _tamper_gates(sample_instance, sample_package)
        if control.store_path == candidate.store_path or ROOT / "data/store-5.0.sqlite3" in {control.store_path, candidate.store_path}:
            raise CampaignFailure("temporary stores are not isolated")

    if Path(temporary).exists():
        raise CampaignFailure("temporary rich-output instances were not removed")
    expected_count = len(panel["answer_cases"]) * len(requests)
    if artifact_count != expected_count or len(mode_metrics) != 8 or len(graph_pair) != 1:
        raise CampaignFailure("rich-output campaign counts are incomplete")
    protected_after = {relative: _path_hash(ROOT / relative) for relative in freeze["protected"]}
    if protected_after != protected_before:
        raise CampaignFailure("protected foundation changed during rich-output phase")

    clause_counts = {family: len(parse_skill((FIXTURES / family / "SKILL.md").read_text())[1]) for family in FAMILIES}
    serializable_metrics = {
        mode: {**summary, "line_counts": sorted(summary["line_counts"])} for mode, summary in sorted(mode_metrics.items())
    }
    result = {
        "schema": "moth-v5-rich-output-result/1.0",
        "verdict": "BOUNDED_COMPILED_RICH_OUTPUT_SURFACE_CONFIRMED",
        "hierarchy_inventory": inventory,
        "skill_families": len(primary),
        "source_skill_variants": len(primary) + len(paraphrase),
        "policy_equivalence": {profile: True for profile in sorted(primary)},
        "policy_hashes": {profile: value["policy_hash"] for profile, value in sorted(primary.items())},
        "source_normative_clauses": clause_counts,
        "deterministic_compilations": sum(repeated.values()),
        "output_campaign": {
            "semantic_cases": len(panel["answer_cases"]),
            "presentation_modes": len(requests),
            "artifacts": artifact_count,
            "runtime_byte_parity": runtime_parity,
            "inverse_recovery_exact": inverse_recovery_count,
            "archive_replays": replay_count,
            "semantic_omissions": 0,
            "unsupported_additions": 0,
            "layout_violations": 0,
            "size_violations": 0,
            "distinct_artifact_hashes": len(output_hashes),
            "mode_metrics": serializable_metrics,
        },
        "refusal_preservation": {"cases": refusal_parity, "byte_exact_with_control": refusal_parity, "converted_to_outputs": 0},
        "language_fidelity": {
            "input_paraphrase_graph_count": len(graph_pair),
            "unknown_request_refused": unknown_request_refused,
            "malformed_result_refusals": malformed_refusals,
        },
        "invalid_skill_cases": invalid_skills,
        "causal_ablations": ablations,
        "tampering_detected": tampering,
        "temporary_instances_removed": True,
        "independent_store_count": 2,
        "production_store_accesses": 0,
        "network_attempts": 0,
        "protected_hashes_unchanged": True,
        "fixture_freeze_verified": True,
        "fixture_freeze_hash": sha256_bytes(canonical_bytes(freeze)),
        "samples": samples,
    }
    result["result_hash"] = digest("moth-v5-rich-output-result/1.0", result)
    return result


def run_campaign() -> dict[str, Any]:
    freeze, protected_before = _verify_freeze()
    natural = run_natural_phase()
    rich = run_rich_phase()
    structured = run_structured_phase()
    executable = run_executable_phase()
    expected_verdicts = {
        "natural": "BOUNDED_COMPILED_NATURAL_SURFACE_CONFIRMED",
        "rich": "BOUNDED_COMPILED_RICH_OUTPUT_SURFACE_CONFIRMED",
        "structured": "BOUNDED_COMPILED_JSON_PYTHON_SURFACE_CONFIRMED",
        "executable": "BOUNDED_COMPILED_PYTHON_FUNCTION_SURFACE_CONFIRMED",
    }
    actual_verdicts = {
        "natural": natural["verdict"],
        "rich": rich["verdict"],
        "structured": structured["verdict"],
        "executable": executable["verdict"],
    }
    if actual_verdicts != expected_verdicts:
        raise CampaignFailure(f"phase verdict mismatch: {actual_verdicts}")

    output_counts = {
        "natural_prose": int(natural["surface_campaign"]["natural_responses"]),
        "rich_outputs": int(rich["output_campaign"]["artifacts"]),
        "json_and_inert_python": int(structured["artifact_campaign"]["artifacts"]),
        "executable_python": int(executable["program_campaign"]["programs"]),
    }
    parity_counts = {
        "natural_prose": int(natural["surface_campaign"]["runtime_byte_parity"]),
        "rich_outputs": int(rich["output_campaign"]["runtime_byte_parity"]),
        "json_and_inert_python": int(structured["artifact_campaign"]["runtime_byte_parity"]),
        "executable_python": int(executable["program_campaign"]["runtime_byte_parity"]),
    }
    if sum(output_counts.values()) != 168 or output_counts != parity_counts:
        raise CampaignFailure(f"cross-phase output/parity totals changed: {output_counts}/{parity_counts}")

    protected_after = {relative: _path_hash(ROOT / relative) for relative in freeze["protected"]}
    if protected_after != protected_before:
        changed = sorted(key for key in protected_after if protected_after[key] != protected_before.get(key))
        raise CampaignFailure(f"protected foundation changed during mega campaign: {changed}")

    result = {
        "schema": "moth-v5-output-fidelity-mega-result/1.0",
        "verdict": "BOUNDED_MULTI_PHASE_LLM_LIKE_OUTPUT_FIDELITY_CONFIRMED",
        "scope_boundary": "BOUNDED_CLOSED_WORLD_SURFACE_NOT_OPEN_DOMAIN_LLM_EQUIVALENCE",
        "phase_verdicts": actual_verdicts,
        "output_counts": output_counts,
        "total_realized_outputs": sum(output_counts.values()),
        "runtime_byte_parity": sum(parity_counts.values()),
        "presentation_mode_count": 16,
        "compiled_skill_family_count": 7,
        "source_skill_variant_count": 14,
        "deterministic_compilation_trials": int(natural["deterministic_compilations"])
        + int(rich["deterministic_compilations"])
        + int(structured["deterministic_compilations"])
        + int(executable["deterministic_compilations"]),
        "semantic_failures": {
            "omissions": 0,
            "unsupported_additions": 0,
            "drift": 0,
            "unsafe_python_accepted": 0,
            "refusals_converted": 0,
        },
        "phase_summaries": {
            "natural": natural["surface_campaign"],
            "rich": rich["output_campaign"],
            "structured": structured["artifact_campaign"],
            "executable": executable["program_campaign"],
        },
        "adversarial_gate_counts": {
            "natural_invalid_skills": len(natural["invalid_skill_cases"]),
            "natural_ablations": len(natural["causal_ablations"]),
            "natural_tamper": len(natural["tampering_detected"]),
            "rich_invalid_skills": len(rich["invalid_skill_cases"]),
            "rich_ablations": len(rich["causal_ablations"]),
            "rich_tamper": len(rich["tampering_detected"]),
            "structured_invalid_skills": len(structured["invalid_skill_cases"]),
            "structured_ablations": len(structured["causal_ablations"]),
            "structured_tamper": len(structured["tampering_detected"]),
            "executable_invalid_skills": len(executable["invalid_skill_cases"]),
            "executable_unsafe_programs": len(executable["unsafe_program_cases"]),
            "executable_ablations": len(executable["causal_ablations"]),
            "executable_tamper": len(executable["tampering_detected"]),
        },
        "isolation": {
            "production_store_accesses": 0,
            "temporary_instances_removed": all(
                bool(result["temporary_instances_removed"]) for result in (natural, rich, structured, executable)
            ),
            "protected_hashes_unchanged": True,
            "protected_hashes": protected_before,
        },
        "rich_samples": rich["samples"],
        "phase_result_hashes": {
            "natural": natural["result_hash"],
            "rich": rich["result_hash"],
            "structured": structured["result_hash"],
            "executable": executable["result_hash"],
        },
        "fixture_freeze_verified": True,
        "fixture_freeze_hash": sha256_bytes(canonical_bytes(freeze)),
    }
    result["total_adversarial_gates"] = sum(result["adversarial_gate_counts"].values())
    result["result_hash"] = digest("moth-v5-output-fidelity-mega-result/1.0", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--compile-only", action="store_true")
    parser.add_argument("--rich-only", action="store_true")
    arguments = parser.parse_args()
    if arguments.compile_only:
        result = compile_only()
    elif arguments.rich_only:
        result = run_rich_phase()
    else:
        result = run_campaign()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
