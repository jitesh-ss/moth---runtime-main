from experiments.runtime_v5_0_instruction_compression.campaign import run_campaign


def test_frozen_instruction_compression_campaign():
    result = run_campaign()
    assert result["verdict"] == "BOUNDED_HIERARCHICAL_INSTRUCTION_FIDELITY_CONFIRMED"
    assert set(result["hierarchy_gates"].values()) == {"PASSED"}
    assert result["behavior"]["total_oracle_comparisons"] == 36
    assert result["behavior"]["unsafe_acceptances"] == 0
    assert result["archive_tampering_detected"] is True
    assert result["protected_hashes_unchanged"] is True
