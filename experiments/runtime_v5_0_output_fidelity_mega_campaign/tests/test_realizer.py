import json
from pathlib import Path

import pytest

from experiments.runtime_v5_0_compiled_surface_skill.compiler import compile_skill
from experiments.runtime_v5_0_output_fidelity_mega_campaign.model import OutputFidelityFailure
from experiments.runtime_v5_0_output_fidelity_mega_campaign.realizer import (
    MODES,
    _domain_values,
    build_text,
    realize_artifact,
    recover_semantics,
    verify_surface,
)


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _field() -> dict:
    return json.loads((FIXTURES / "rich-surface-field-en-1.0.json").read_text())


def test_all_modes_are_invertible_across_the_semantic_domain() -> None:
    field = _field()
    for value in _domain_values():
        texts = set()
        for mode in MODES:
            text = build_text(value, mode)
            assert recover_semantics(text, mode) == value
            verify_surface(text, mode, value, field)
            texts.add(text)
        assert len(texts) == len(MODES)


def test_tampered_text_does_not_recover() -> None:
    value = _domain_values()[2]
    text = build_text(value, "COMPACT_PROSE").replace("backup", "proposed", 1)
    with pytest.raises(OutputFidelityFailure):
        recover_semantics(text, "COMPACT_PROSE")


def test_compiled_family_rejects_another_family_route() -> None:
    field = _field()
    compilation = compile_skill((FIXTURES / "prose-range" / "SKILL.md").read_text(), field)
    runtime_output = {"kind": "FACTOR_RESULT", "value": _domain_values()[0]}
    with pytest.raises(OutputFidelityFailure, match="UNSUPPORTED_PRESENTATION"):
        realize_artifact(runtime_output, "Return a Markdown table.", compilation, field)

