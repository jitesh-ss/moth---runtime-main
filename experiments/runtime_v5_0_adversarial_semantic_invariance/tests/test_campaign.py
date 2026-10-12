from experiments.runtime_v5_0_adversarial_semantic_invariance.campaign import run_campaign


def test_frozen_adversarial_semantic_invariance_campaign():
    result = run_campaign()
    assert result["verdict"] == "ADVERSARIAL_SEMANTIC_INVARIANCE_CONFIRMED"
    assert result["cases"] == 50
    assert result["equivalent_accepted"] == 40
    assert result["valid_contrasts"] == 3
    assert result["expected_refusals"] == 7
    assert result["unsafe_acceptances"] == 0
    assert result["equivalence_graph_counts"] == {"delivery": 1, "deployment": 1}
    assert result["shared_main_program_count"] == 1
    assert result["encoder_free_replays"] == 50
    assert result["semantic_tamper_detected"] is True
    assert result["protected_hashes_unchanged"] is True
