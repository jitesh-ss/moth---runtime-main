from experiments.runtime_v5_1_autonomous_json_skill.compiler import compile_candidate
from experiments.runtime_v5_1_autonomous_json_skill.candidate_runtime import settle_json_request


def test_prompt_alone_routes_to_compiled_skill() -> None:
    field, skill = compile_candidate()
    result = settle_json_request(
        'Group the records by team as strict JSON. Source data: '
        '[{"id":1,"team":"a"},{"id":2,"team":"b"},{"id":3,"team":"a"}]',
        field,
        skill,
    )
    assert result["status"] == "ANSWER"
    assert result["route"]["family"] == "grouped_records"
    assert result["skill"]["policy_hash"] == skill["policy_hash"]
    assert result["hcf"]["winner_id"] == "skill.autonomous-json-formatting"
    assert result["hcf"]["winning_energy"]["context_violations"] == 0


def test_no_skill_and_router_ablation_remove_capability() -> None:
    field, skill = compile_candidate()
    prompt = 'Return compact strict JSON. Source data: {"a":1}'
    assert settle_json_request(prompt, field, None)["code"] == "SKILL_UNAVAILABLE"
    assert settle_json_request(prompt, field, skill, router_enabled=False)["code"] == "ROUTER_DISABLED"

