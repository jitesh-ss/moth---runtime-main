from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from experiments.runtime_v5_0_instruction_compression.compiler import (
    compile_skill,
    compose_skills,
    semantic_policy_bytes,
    validate_field,
)
from experiments.runtime_v5_0_instruction_compression.instance import IsolatedInstructionInstance
from experiments.runtime_v5_0_instruction_compression.model import CompilationFailure, canonical_bytes


HERE = Path(__file__).resolve().parents[1]
FIXTURES = HERE / "fixtures"


def load_json(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def load_skill(name: str) -> str:
    return (FIXTURES / name / "SKILL.md").read_text(encoding="utf-8")


def test_all_hierarchy_layers_validate():
    inventory = validate_field(load_json("base-field-en-1.0.json"))
    assert set(inventory) == {"L1", "L2", "L3", "L4", "L5", "L6"}
    assert inventory["L1"] == {"actions": 12, "states": 3}


def test_plain_skill_and_paraphrase_equal_granular_oracle():
    field = load_json("base-field-en-1.0.json")
    oracle = load_json("granular-oracle-1.0.json")
    primary = compile_skill(load_skill("safe-text-patch"), field)
    paraphrase = compile_skill(load_skill("safe-text-patch-paraphrase"), field)
    assert semantic_policy_bytes(primary) == canonical_bytes(oracle["single"])
    assert semantic_policy_bytes(paraphrase) == semantic_policy_bytes(primary)
    assert primary["trace"]["graph_unit_count"] / primary["trace"]["normative_clause_count"] >= 2.0


def test_composed_skill_equals_composite_oracle():
    field = load_json("base-field-en-1.0.json")
    oracle = load_json("granular-oracle-1.0.json")
    primary = compile_skill(load_skill("safe-text-patch"), field)
    evidence = compile_skill(load_skill("evidence-ledger"), field)
    composite = compose_skills(primary, evidence, field)
    assert semantic_policy_bytes(evidence) == canonical_bytes(oracle["evidence"])
    assert semantic_policy_bytes(composite) == canonical_bytes(oracle["composite"])


def test_missing_required_instruction_refuses_compilation():
    field = load_json("base-field-en-1.0.json")
    with pytest.raises(CompilationFailure) as failure:
        compile_skill(load_skill("safe-text-patch"), field, ignored_rule_ids={"POLICY_UNRELATED"})
    assert failure.value.code == "INCOMPLETE_SKILL"


def test_isolated_instance_performs_exact_intention():
    field = load_json("base-field-en-1.0.json")
    policy = compile_skill(load_skill("safe-text-patch"), field)["policy"]
    task = load_json("campaign-1.0.json")["tasks"][0]
    with TemporaryDirectory() as temporary:
        instance = IsolatedInstructionInstance(Path(temporary) / "instance", field)
        result = instance.execute(policy, task)
    assert result["status"] == "ANSWER"
    assert result["changed_paths"] == ["notes.txt"]
    text = result["final_workspace"]["notes.txt"]["base64"]
    assert text == "bW9kZT1uZXcKa2VlcD15ZXMK"
    assert result["final_workspace"]["other.txt"]["base64"] == "dW50b3VjaGVkCg=="

