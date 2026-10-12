from experiments.runtime_v5_0_compiled_relation_identification.campaign import run_campaign


def test_compiled_relation_identification_causal_campaign():
    result = run_campaign()
    assert result["verdict"] == "COMPILED_RELATION_IDENTIFICATION_PARTIALLY_CONFIRMED"
    assert result["capability_target_met"] is False
    assert result["safety_integrity_passed"] is True
    assert result["control_relation_refusals"] == 12
    assert result["categories"]["RELATION_HOLDOUT"] == {
        "CORRECT_ACCEPT": 11, "SAFE_REFUSAL": 1,
    }
    assert result["categories"]["MIXED_HOLDOUT"] == {
        "CORRECT_ACCEPT": 5, "SAFE_REFUSAL": 3,
    }
    assert result["unsafe_acceptances"] == 0
    assert result["adversarial_refusals"] == 8
    assert result["encoder_free_replays"] == 28
    assert result["semantic_tamper_detected"] is True
    assert result["main_world_identical"] is True
    assert result["surface_world_identical"] is True
    assert result["network_attempts"] == 0
    assert result["protected_hashes_unchanged"] is True
