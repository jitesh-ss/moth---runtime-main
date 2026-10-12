from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from experiments.runtime_v5_0_compiled_surface_skill.compiler import compile_skill
from experiments.runtime_v5_0_compiled_surface_skill.model import SurfaceFidelityFailure
from experiments.runtime_v5_0_compiled_surface_skill.realizer import realize, verify_response


HERE = Path(__file__).resolve().parents[1]
FIXTURES = HERE / "fixtures"


def _assets():
    field = json.loads((FIXTURES / "surface-base-field-en-1.0.json").read_text())
    compilation = compile_skill((FIXTURES / "natural-response/SKILL.md").read_text(), field)
    panel = json.loads((FIXTURES / "campaign-en-1.0.json").read_text())
    return field, compilation, panel


def test_every_frozen_semantic_result_meets_every_size_contract():
    field, compilation, panel = _assets()
    for case in panel["answer_cases"]:
        runtime_output = {"kind": "FACTOR_RESULT", "value": case["expected"]}
        for size in panel["size_requests"]:
            response = realize(runtime_output, size["request"], compilation, field)
            verify_response(response, runtime_output, compilation, field)
            band = field["size_bands"][size["mode"]]
            assert response["size_mode"] == size["mode"]
            assert band["minimum_words"] <= response["word_count"] <= band["maximum_words"]
            assert band["minimum_sentences"] <= response["sentence_count"] <= band["maximum_sentences"]
            assert response["claims"] == case["expected"]


def test_unknown_presentation_and_malformed_semantics_refuse():
    field, compilation, panel = _assets()
    runtime_output = {"kind": "FACTOR_RESULT", "value": panel["answer_cases"][0]["expected"]}
    with pytest.raises(SurfaceFidelityFailure) as unsupported:
        realize(runtime_output, "Write it as a sonnet.", compilation, field)
    assert unsupported.value.code == "UNSUPPORTED_PRESENTATION"
    malformed = deepcopy(runtime_output)
    del malformed["value"]["selected-plan"]
    with pytest.raises(SurfaceFidelityFailure) as invalid:
        realize(malformed, "Answer concisely.", compilation, field)
    assert invalid.value.code == "MALFORMED_SEMANTIC_RESULT"


def test_text_tampering_is_not_excused_by_unchanged_claim_metadata():
    field, compilation, panel = _assets()
    runtime_output = {"kind": "FACTOR_RESULT", "value": panel["answer_cases"][0]["expected"]}
    response = realize(runtime_output, "Answer concisely.", compilation, field)
    altered = deepcopy(response)
    altered["text"] = altered["text"].replace("backup plan", "proposed plan", 1)
    with pytest.raises(SurfaceFidelityFailure):
        verify_response(altered, runtime_output, compilation, field)

