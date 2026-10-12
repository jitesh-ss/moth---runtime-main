import json
from pathlib import Path

from experiments.runtime_v5_0_compiled_surface_skill.compiler import compile_skill


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
FAMILIES = ["prose-range", "tone-adaptation", "markdown-structure", "mixed-response"]


def test_all_skill_pairs_compile_to_frozen_oracle_hashes() -> None:
    field = json.loads((FIXTURES / "rich-surface-field-en-1.0.json").read_text())
    oracle = json.loads((FIXTURES / "granular-policy-oracle-en-1.0.json").read_text())
    for family in FAMILIES:
        primary = compile_skill((FIXTURES / family / "SKILL.md").read_text(), field)
        paraphrase = compile_skill((FIXTURES / f"{family}-paraphrase" / "SKILL.md").read_text(), field)
        profile = primary["policy"]["policy_id"]
        assert primary["policy"] == paraphrase["policy"]
        assert primary["policy_hash"] == oracle["policy_hashes"][profile]
        assert primary["policy"]["workflow"] == oracle["workflow"]

