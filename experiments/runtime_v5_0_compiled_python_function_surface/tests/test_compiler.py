import json
from pathlib import Path

from experiments.runtime_v5_0_compiled_surface_skill.compiler import compile_skill


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_equivalent_skills_compile_to_frozen_oracle() -> None:
    field = json.loads((FIXTURES / "python-function-surface-field-en-1.0.json").read_text())
    primary = compile_skill((FIXTURES / "python-function-output/SKILL.md").read_text(), field)
    paraphrase = compile_skill((FIXTURES / "python-function-output-paraphrase/SKILL.md").read_text(), field)
    oracle = json.loads((FIXTURES / "granular-python-function-oracle-1.0.json").read_text())
    assert primary["policy"] == paraphrase["policy"] == oracle
    assert primary["policy_hash"] == paraphrase["policy_hash"]

