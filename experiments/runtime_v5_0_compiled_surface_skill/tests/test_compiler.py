from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.runtime_v5_0_compiled_surface_skill.compiler import (
    compile_skill,
    validate_field,
)
from experiments.runtime_v5_0_compiled_surface_skill.model import SkillCompilationFailure


HERE = Path(__file__).resolve().parents[1]
FIXTURES = HERE / "fixtures"


def _json(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_primary_and_paraphrase_compile_to_frozen_oracle():
    field = _json("surface-base-field-en-1.0.json")
    inventory = validate_field(field)
    primary = compile_skill((FIXTURES / "natural-response/SKILL.md").read_text(), field)
    paraphrase = compile_skill((FIXTURES / "natural-response-paraphrase/SKILL.md").read_text(), field)
    oracle = _json("granular-surface-oracle-1.0.json")
    assert primary["policy"] == paraphrase["policy"] == oracle
    assert primary["policy_hash"] == paraphrase["policy_hash"]
    assert inventory == {
        "L1": {"actions": 15, "states": 2},
        "L2": {"operators": 6, "conditions": 8},
        "L3": {"workflow_macros": 6},
        "L4": {"interpretation_rules": 12},
        "L5": {"skill_profiles": 1},
        "SIZE": {"modes": 3, "signals": 8},
    }


def test_missing_rule_and_unknown_instruction_fail_closed():
    field = _json("surface-base-field-en-1.0.json")
    source = (FIXTURES / "natural-response/SKILL.md").read_text()
    with pytest.raises(SkillCompilationFailure) as missing:
        compile_skill(source, field, ignored_rule_ids={"POLICY_PRESERVE"})
    assert missing.value.code == "INCOMPLETE_SKILL"
    altered = source + "\n## Workflow\n\n- Publish the answer to a remote service.\n"
    with pytest.raises(SkillCompilationFailure) as unknown:
        compile_skill(altered, field)
    assert unknown.value.code == "UNSUPPORTED_INSTRUCTION"


def test_compilation_is_byte_stable():
    field = _json("surface-base-field-en-1.0.json")
    source = (FIXTURES / "natural-response/SKILL.md").read_text()
    hashes = {compile_skill(source, field)["policy_hash"] for _ in range(10)}
    assert len(hashes) == 1

