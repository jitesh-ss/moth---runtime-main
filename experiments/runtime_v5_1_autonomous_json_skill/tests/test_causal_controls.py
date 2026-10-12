from copy import deepcopy

from experiments.runtime_v5_1_autonomous_json_skill.compiler import compile_candidate
from experiments.runtime_v5_1_autonomous_json_skill.candidate_runtime import settle_json_request


PROMPT = 'Return compact strict JSON. Source data: {"a":1,"b":true}'


def test_skill_is_causally_required() -> None:
    field, skill = compile_candidate()
    assert settle_json_request(PROMPT, field, skill)["status"] == "ANSWER"
    assert settle_json_request(PROMPT, field, None)["status"] == "REFUSAL"
    assert settle_json_request(PROMPT, field, skill, unrelated_skill=True)["code"] == "SKILL_NOT_APPLICABLE"


def test_trigger_and_workflow_corruption_are_detected() -> None:
    field, skill = compile_candidate()
    trigger = deepcopy(skill)
    trigger["policy"]["trigger"] = "CORRUPTED"
    assert settle_json_request(PROMPT, field, trigger)["code"] == "INTEGRITY_FAILURE"
    workflow = deepcopy(skill)
    workflow["policy"]["workflow"].remove("VERIFY_EXACT_DATA")
    assert settle_json_request(PROMPT, field, workflow)["code"] == "INTEGRITY_FAILURE"

