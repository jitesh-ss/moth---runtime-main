from experiments.runtime_v5_0_typed_determiner_closure.campaign import run_campaign


def test_typed_determiner_corrective_closure_campaign():
    result = run_campaign()
    assert result["verdict"] == "TYPED_DETERMINER_COMPOSITIONAL_CLOSURE_CONFIRMED"
    assert result["field_sealed_before_prompts"] is True
    assert result["no_complete_test_language_in_field"] is True
    assert result["prior_regressions_passed"] == 4
    assert result["base_control_refusals"] == 12
    assert result["classifications"] == {
        "CORRECT_CONTRAST": 6,
        "CORRECT_EQUIVALENT": 12,
        "SAFE_REFUSAL": 10,
    }
    assert result["equivalent_unique_graphs"] == 1
    assert result["contrast_unique_graphs"] == 6
    assert result["unsafe_acceptances"] == 0
    assert result["determiner_trace_evidence_count"] > 0
    assert result["determiner_ablation_passed"] is True
    assert result["encoder_free_nested_replays"] == 32
    assert result["composition_tamper_detected"] is True
    assert result["semantic_tamper_detected"] is True
    assert result["network_attempts"] == 0
    assert result["protected_hashes_unchanged"] is True
