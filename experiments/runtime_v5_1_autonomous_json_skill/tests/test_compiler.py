from copy import deepcopy

from experiments.runtime_v5_1_autonomous_json_skill.compiler import (
    compile_candidate,
    verify_deterministic_compilation,
)
from experiments.runtime_v5_1_autonomous_json_skill.candidate_runtime import settle_json_request


def test_one_detailed_skill_compiles_deterministically() -> None:
    receipt = verify_deterministic_compilation(10)
    assert receipt["profile_id"] == "AUTONOMOUS_JSON_FORMATTING"
    assert receipt["normative_clause_count"] == 14
    assert receipt["graph_unit_count"] >= 40


def test_policy_tampering_fails_closed() -> None:
    field, skill = compile_candidate()
    skill = deepcopy(skill)
    skill["policy_hash"] = "0" * 64
    result = settle_json_request(
        'Return compact strict JSON. Source data: {"a":1}', field, skill,
    )
    assert result["status"] == "REFUSAL"
    assert result["code"] == "INTEGRITY_FAILURE"

