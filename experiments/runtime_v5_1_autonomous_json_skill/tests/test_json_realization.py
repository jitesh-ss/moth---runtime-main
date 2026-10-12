import json
from pathlib import Path

from experiments.runtime_v5_1_autonomous_json_skill.compiler import compile_candidate
from experiments.runtime_v5_1_autonomous_json_skill.candidate_runtime import settle_json_request


HERE = Path(__file__).resolve().parents[1]


def test_all_frozen_positive_variations_are_exact() -> None:
    field, skill = compile_candidate()
    cases = json.loads((HERE / "fixtures/qualification-panel-1.0.json").read_text())["cases"]
    assert len(cases) == 240
    assert len({case["family"] for case in cases}) == 16
    for case in cases:
        result = settle_json_request(case["prompt"], field, skill)
        assert result["status"] == "ANSWER", case["id"]
        assert result["value"] == case["expected_value"], case["id"]
        assert result["response"] == case["expected_response"], case["id"]


def test_all_negative_variations_refuse_with_exact_code() -> None:
    field, skill = compile_candidate()
    cases = json.loads((HERE / "fixtures/negative-panel-1.0.json").read_text())["cases"]
    assert len(cases) == 96
    for case in cases:
        result = settle_json_request(case["prompt"], field, skill)
        assert result["status"] == "REFUSAL", case["id"]
        assert result["code"] == case["expected_code"], case["id"]

