from experiments.runtime_v5_0_compiled_surface_skill.campaign import run_campaign


def test_frozen_compiled_surface_campaign():
    result = run_campaign()
    assert result["verdict"] == "BOUNDED_COMPILED_NATURAL_SURFACE_CONFIRMED"
    assert result["surface_campaign"]["natural_responses"] == 48
    assert result["surface_campaign"]["semantic_omissions"] == 0
    assert result["surface_campaign"]["size_violations"] == 0
    assert result["refusal_preservation"]["converted_to_answers"] == 0
    assert result["protected_hashes_unchanged"] is True
