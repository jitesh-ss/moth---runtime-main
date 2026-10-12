from tempfile import TemporaryDirectory

from experiments.runtime_v5_2_autonomous_json_skill.campaign import run
from experiments.runtime_v5_2_autonomous_json_skill.candidate_runtime import settle_json_prompt
from experiments.runtime_v5_2_autonomous_json_skill.compiler import compile_candidate


def test_prompt_only_json_and_tensor_settlement() -> None:
    with TemporaryDirectory() as temporary:
        candidate = compile_candidate(temporary)
        result = settle_json_prompt(
            candidate,
            'Select fields name, active as strict JSON. Source data: {"id":1,"name":"Moth","active":true}',
        )
    assert result["response"] == '{"name":"Moth","active":true}'
    assert result["hcf"]["winning_energy"] == {
        "base_violations": 0,
        "system_violations": 0,
        "context_violations": 0,
        "grounding_cost_units": 0,
    }


def test_full_campaign() -> None:
    result = run(write_reports=False)
    assert result["verdict"] == "PASS"
    assert result["positive"]["exact"] == 240
    assert result["negative"]["correct_typed_refusals"] == 96
    assert result["metamorphic"]["passed"] == 64
