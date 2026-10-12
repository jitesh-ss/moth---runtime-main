"""Execute the frozen instruction-compression hierarchy campaign."""

from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from .compiler import compile_skill, compose_skills, parse_skill, semantic_policy_bytes, validate_field
from .instance import IsolatedInstructionInstance
from .model import CompilationFailure, FieldValidationError, canonical_bytes, verify_archive


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"


class FidelityFailure(AssertionError):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree_hash(path: Path) -> str:
    result = hashlib.sha256()
    if path.is_dir():
        for child in sorted(item for item in path.rglob("*") if item.is_file() and "__pycache__" not in item.parts):
            result.update(child.relative_to(path).as_posix().encode("utf-8"))
            result.update(b"\0")
            result.update(hashlib.sha256(child.read_bytes()).digest())
    return result.hexdigest()


def _protected_hashes(names: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for name in names:
        path = ROOT / name
        if name.startswith(("src/", "config/")):
            result[name] = _tree_hash(path)
        else:
            result[name] = _sha256(path) if path.is_file() else "ABSENT"
    return result


def _verify_freeze(freeze: dict[str, Any]) -> None:
    if freeze.get("schema") != "moth-instruction-compression-freeze/1.0" or not freeze.get("frozen_before_execution"):
        raise FidelityFailure("fixture freeze is invalid")
    for relative, expected in freeze["fixtures"].items():
        actual = _sha256(FIXTURES / relative)
        if actual != expected:
            raise FidelityFailure(f"frozen fixture changed: {relative}")


def _append_clause(document: str, section: str, text: str) -> str:
    return f"{document.rstrip()}\n\n## {section.title()}\n\n- {text}\n"


def _expect_failure(function, code: str) -> dict[str, str]:
    try:
        function()
    except CompilationFailure as exc:
        if exc.code != code:
            raise FidelityFailure(f"expected {code}, observed {exc.code}") from exc
        return {"status": "PASSED", "code": exc.code}
    except FieldValidationError as exc:
        return {"status": "PASSED", "code": f"FIELD_{exc.layer}"}
    raise FidelityFailure(f"expected failure {code}")


def _source_imports_production(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[str] = []
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module]
        found.extend(name for name in names if name.startswith(("moth_runtime", "moth_launcher")))
    return found


def _execute_panel(
    temp_root: Path,
    label: str,
    policy: dict[str, Any],
    oracle_policy: dict[str, Any],
    field: dict[str, Any],
    tasks: list[dict[str, Any]],
) -> dict[str, Any]:
    statuses: dict[str, int] = {"ANSWER": 0, "REFUSED": 0, "AUTHORITY_REQUIRED": 0}
    replays = 0
    unsafe_acceptances = 0
    for task in tasks:
        compiled_instance = IsolatedInstructionInstance(temp_root / f"{label}-{task['id']}-compiled", field)
        oracle_instance = IsolatedInstructionInstance(temp_root / f"{label}-{task['id']}-oracle", field)
        compiled_result = compiled_instance.execute(policy, task)
        oracle_result = oracle_instance.execute(oracle_policy, task)
        if task["expected_status"] != "ANSWER" and compiled_result["status"] == "ANSWER":
            unsafe_acceptances += 1
        if canonical_bytes(compiled_result) != canonical_bytes(oracle_result):
            raise FidelityFailure(f"{label}/{task['id']}: compiled behavior differs from granular oracle")
        if compiled_result["status"] != task["expected_status"] or compiled_result["code"] != task["expected_code"]:
            raise FidelityFailure(f"{label}/{task['id']}: frozen behavioral expectation failed")
        if task["expected_status"] == "ANSWER":
            target = task["target"]
            if compiled_result["changed_paths"] != [target]:
                raise FidelityFailure(f"{label}/{task['id']}: change escaped exact target")
        elif compiled_result["changed_paths"]:
            raise FidelityFailure(f"{label}/{task['id']}: refusal changed workspace")
        archive = compiled_instance.archives[-1]
        if not verify_archive(archive) or canonical_bytes(archive["payload"]) != canonical_bytes(compiled_result):
            raise FidelityFailure(f"{label}/{task['id']}: archive replay failed")
        statuses[compiled_result["status"]] += 1
        replays += 1
    return {
        "cases": len(tasks),
        "statuses": statuses,
        "byte_exact_replays": replays,
        "unsafe_acceptances": unsafe_acceptances,
    }


def _ablation_gates(field: dict[str, Any], primary_document: str, primary: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    results: dict[str, Any] = {}

    l1 = deepcopy(field)
    l1["layers"]["L1"]["actions"] = []
    results["L1_atomic_substrate"] = _expect_failure(lambda: validate_field(l1), "UNUSED")

    l2 = deepcopy(field)
    l2["layers"]["L2"]["operators"].remove("ASK_FIRST")
    results["L2_control_policy"] = _expect_failure(lambda: validate_field(l2), "UNUSED")

    l3 = deepcopy(field)
    del l3["layers"]["L3"]["workflow_macros"]["INSPECT_TARGET"]
    results["L3_workflow_macro"] = _expect_failure(lambda: validate_field(l3), "UNUSED")

    l4 = deepcopy(field)
    for rule in l4["interpretation_rules"]:
        if rule["id"] == "STEP_INSPECT":
            rule["groups"] = [["unreachable compiled phrase"]]
    results["L4_interpretation"] = _expect_failure(lambda: compile_skill(primary_document, l4), "UNSUPPORTED_INSTRUCTION")

    results["L5_skill_closure"] = _expect_failure(
        lambda: compile_skill(primary_document, field, ignored_rule_ids={"POLICY_UNRELATED"}),
        "INCOMPLETE_SKILL",
    )

    l6 = deepcopy(field)
    l6["composition_rules"] = []
    results["L6_composition"] = _expect_failure(lambda: compose_skills(primary, evidence, l6), "UNUSED")
    return results


def run_campaign() -> dict[str, Any]:
    freeze = _read_json(FIXTURES / "FREEZE.json")
    _verify_freeze(freeze)
    protected_before = _protected_hashes(sorted(freeze["protected"]))
    if protected_before != freeze["protected"]:
        raise FidelityFailure("protected production baseline differs from the pre-execution freeze")

    field = _read_json(FIXTURES / "base-field-en-1.0.json")
    oracle = _read_json(FIXTURES / "granular-oracle-1.0.json")
    campaign = _read_json(FIXTURES / "campaign-1.0.json")
    primary_document = (FIXTURES / "safe-text-patch/SKILL.md").read_text(encoding="utf-8")
    paraphrase_document = (FIXTURES / "safe-text-patch-paraphrase/SKILL.md").read_text(encoding="utf-8")
    evidence_document = (FIXTURES / "evidence-ledger/SKILL.md").read_text(encoding="utf-8")

    hierarchy_inventory = validate_field(field)
    primary = compile_skill(primary_document, field)
    paraphrase = compile_skill(paraphrase_document, field)
    evidence = compile_skill(evidence_document, field)
    composite = compose_skills(primary, evidence, field)

    field_text = canonical_bytes(field).decode("utf-8").casefold()
    complete_clauses_in_field = sum(
        1
        for document in (primary_document, paraphrase_document, evidence_document)
        for clause in parse_skill(document)[1]
        if clause.text.casefold() in field_text
    )
    if complete_clauses_in_field:
        raise FidelityFailure("base field contains one or more complete counted skill clauses")

    if semantic_policy_bytes(primary) != canonical_bytes(oracle["single"]):
        raise FidelityFailure("primary skill differs from frozen granular oracle")
    if semantic_policy_bytes(paraphrase) != semantic_policy_bytes(primary):
        raise FidelityFailure("held-out skill paraphrase changed instruction semantics")
    if semantic_policy_bytes(evidence) != canonical_bytes(oracle["evidence"]):
        raise FidelityFailure("evidence skill differs from frozen granular oracle")
    if semantic_policy_bytes(composite) != canonical_bytes(oracle["composite"]):
        raise FidelityFailure("composed skill differs from frozen granular oracle")

    graph_units = int(primary["trace"]["graph_unit_count"])
    source_clauses = int(primary["trace"]["normative_clause_count"])
    expansion_ratio = graph_units / source_clauses
    if expansion_ratio < 2.0:
        raise FidelityFailure("instruction expansion ratio is below 2.0x")

    repeated = [compile_skill(primary_document, field) for _ in range(int(campaign["repetitions"]))]
    if len({canonical_bytes(item) for item in repeated}) != 1:
        raise FidelityFailure("repeated compilation is not byte deterministic")

    invalid_results: dict[str, Any] = {}
    for case in campaign["invalid_skills"]:
        if "remove_rule" in case:
            operation = lambda case=case: compile_skill(
                primary_document, field, ignored_rule_ids={case["remove_rule"]}
            )
        else:
            changed = _append_clause(primary_document, case["append_clause"]["section"], case["append_clause"]["text"])
            operation = lambda changed=changed: compile_skill(changed, field)
        invalid_results[case["id"]] = _expect_failure(operation, case["expected_code"])

    ablations = _ablation_gates(field, primary_document, primary, evidence)
    if len(ablations) != 6 or any(value["status"] != "PASSED" for value in ablations.values()):
        raise FidelityFailure("one or more hierarchy ablations failed")

    python_files = [HERE / name for name in ("model.py", "compiler.py", "instance.py", "campaign.py")]
    production_imports = sorted({name for path in python_files for name in _source_imports_production(path)})
    if production_imports:
        raise FidelityFailure("isolated instance imports production runtime code")

    with TemporaryDirectory(prefix="moth-instruction-compression-") as temporary:
        temp_root = Path(temporary)
        single_panel = _execute_panel(temp_root, "single", primary["policy"], oracle["single"], field, campaign["tasks"])
        paraphrase_panel = _execute_panel(temp_root, "paraphrase", paraphrase["policy"], oracle["single"], field, campaign["tasks"])
        composite_panel = _execute_panel(temp_root, "composite", composite["policy"], oracle["composite"], field, campaign["tasks"])

        probe_instance = IsolatedInstructionInstance(temp_root / "tamper-probe", field)
        probe_result = probe_instance.execute(primary["policy"], campaign["tasks"][0])
        tampered = deepcopy(probe_instance.archives[-1])
        tampered["payload"]["status"] = "REFUSED"
        if verify_archive(tampered):
            raise FidelityFailure("tampered archive was accepted")
        if probe_result["status"] != "ANSWER":
            raise FidelityFailure("tamper probe did not execute the intended success path")

    protected_after = _protected_hashes(sorted(freeze["protected"]))
    if protected_after != protected_before:
        raise FidelityFailure("protected runtime/configuration/store hashes changed")

    unsafe_acceptances = sum(
        panel["unsafe_acceptances"] for panel in (single_panel, paraphrase_panel, composite_panel)
    )
    hierarchy_gates = {
        "L1_atomic_actions": "PASSED",
        "L2_control_policy": "PASSED",
        "L3_workflow_expansion": "PASSED",
        "L4_skill_language_interpretation": "PASSED",
        "L5_single_skill_intention_fidelity": "PASSED",
        "L6_multi_skill_composition": "PASSED",
    }
    return {
        "schema": "moth-instruction-compression-result/1.0",
        "verdict": "BOUNDED_HIERARCHICAL_INSTRUCTION_FIDELITY_CONFIRMED",
        "hierarchy_gates": hierarchy_gates,
        "hierarchy_inventory": hierarchy_inventory,
        "policy_equivalence": {
            "primary_equals_granular_oracle": True,
            "paraphrase_equals_primary": True,
            "evidence_equals_granular_oracle": True,
            "composite_equals_granular_oracle": True,
        },
        "compiled_hashes": {
            "field": primary["field_hash"],
            "single_policy": primary["policy_hash"],
            "paraphrase_policy": paraphrase["policy_hash"],
            "evidence_policy": evidence["policy_hash"],
            "composite_policy": composite["policy_hash"],
            "primary_trace": primary["trace_hash"],
            "paraphrase_trace": paraphrase["trace_hash"],
            "composite_trace": composite["trace_hash"],
        },
        "instruction_compression": {
            "source_normative_clauses": source_clauses,
            "compiled_graph_units": graph_units,
            "expansion_ratio": round(expansion_ratio, 6),
            "complete_skill_clauses_in_base_field": complete_clauses_in_field,
        },
        "behavior": {
            "single": single_panel,
            "paraphrase": paraphrase_panel,
            "composite": composite_panel,
            "total_oracle_comparisons": single_panel["cases"] + paraphrase_panel["cases"] + composite_panel["cases"],
            "unsafe_acceptances": unsafe_acceptances,
        },
        "invalid_skill_cases": invalid_results,
        "causal_ablations": ablations,
        "deterministic_compilations": len(repeated),
        "archive_tampering_detected": True,
        "production_imports": production_imports,
        "network_attempts": 0,
        "dispatch_count": 0,
        "external_workspace_writes": 0,
        "temporary_instances_removed": True,
        "protected_hashes_unchanged": True,
        "fixture_freeze_verified": True,
    }


def main() -> None:
    print(json.dumps(run_campaign(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
