from experiments.runtime_v5_0_held_out_fidelity_boundary.campaign import run_campaign


def test_frozen_real_bge_held_out_fidelity_boundary():
    result = run_campaign()
    assert result["verdict"] == "HELD_OUT_FIDELITY_BOUNDARY_CONFIRMED"
    assert result["cases"] == 40
    assert result["unsafe_acceptances"] == 0
    assert result["adversarial_refusals"] == 8
    assert result["encoder_free_replays"] == 40
    assert result["semantic_tamper_detected"] is True
    assert result["network_attempts"] == 0
    assert result["protected_hashes_unchanged"] is True
    assert result["categories"] == {
        "ADVERSARIAL": {"SAFE_REFUSAL": 8},
        "ENTITY_SURFACE_HOLDOUT": {"CORRECT_ACCEPT": 8, "SAFE_REFUSAL": 4},
        "MIXED_HOLDOUT": {"SAFE_REFUSAL": 8},
        "RELATION_FRAME_HOLDOUT": {"SAFE_REFUSAL": 12},
    }
    assert [row["id"] for row in result["correct_accepts"]] == [
        "e01", "e02", "e03", "e04", "e07", "e08", "e09", "e10",
    ]
