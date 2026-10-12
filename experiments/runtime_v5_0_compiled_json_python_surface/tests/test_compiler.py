from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.runtime_v5_0_compiled_surface_skill.compiler import compile_skill
from experiments.runtime_v5_0_compiled_surface_skill.model import SkillCompilationFailure


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _json(name: str):
    return json.loads((FIXTURES / name).read_text())


def test_equivalent_skills_compile_to_the_frozen_oracle():
    field = _json("structured-surface-field-en-1.0.json")
    primary = compile_skill((FIXTURES / "structured-output/SKILL.md").read_text(), field)
    paraphrase = compile_skill((FIXTURES / "structured-output-paraphrase/SKILL.md").read_text(), field)
    oracle = _json("granular-structured-oracle-1.0.json")
    assert primary["policy"] == paraphrase["policy"] == oracle
    assert primary["policy_hash"] == paraphrase["policy_hash"]
    assert primary["trace"]["normative_clause_count"] == 14
    assert primary["trace"]["graph_unit_count"] == 49


def test_python_safety_clause_is_required_and_execution_is_unsupported():
    field = _json("structured-surface-field-en-1.0.json")
    source = (FIXTURES / "structured-output/SKILL.md").read_text()
    with pytest.raises(SkillCompilationFailure) as missing:
        compile_skill(source, field, ignored_rule_ids={"POLICY_SAFE_PYTHON"})
    assert missing.value.code == "INCOMPLETE_SKILL"
    altered = source + "\n## Workflow\n\n- Execute the generated Python program.\n"
    with pytest.raises(SkillCompilationFailure) as unsupported:
        compile_skill(altered, field)
    assert unsupported.value.code == "UNSUPPORTED_INSTRUCTION"

