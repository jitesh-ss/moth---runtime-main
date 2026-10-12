from experiments.runtime_v5_0_blind_compositional_closure.campaign import run_campaign


def test_blind_compositional_language_fidelity_campaign():
    result = run_campaign()
    assert result["verdict"] == "BLIND_COMPOSITIONAL_LANGUAGE_FIDELITY_NOT_CONFIRMED"
    assert result["capability_target_met"] is False
    assert result["safety_integrity_passed"] is True
    assert result["field_sealed_before_prompts"] is True
    assert result["no_complete_test_language_in_field"] is True
    assert result["control_equivalent_answers"] == 0
    assert result["classifications"] == {
        "CORRECT_CONTRAST": 6,
        "CORRECT_EQUIVALENT": 8,
        "SAFE_REFUSAL": 14,
    }
    assert result["equivalent_refusal_ids"] == ["e03", "e04", "e08", "e10"]
    assert result["refusal_controls_passed"] == 10
    assert result["equivalent_unique_graphs"] == 1
    assert result["contrast_unique_graphs"] == 6
    assert result["unsafe_acceptances"] == 0
    assert result["ablations_passed"] == 6
    assert result["encoder_free_nested_replays"] == 28
    assert result["composition_tamper_detected"] is True
    assert result["semantic_tamper_detected"] is True
    assert result["network_attempts"] == 0
    assert result["protected_hashes_unchanged"] is True
