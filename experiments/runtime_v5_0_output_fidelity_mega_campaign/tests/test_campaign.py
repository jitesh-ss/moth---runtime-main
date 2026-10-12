from experiments.runtime_v5_0_output_fidelity_mega_campaign.campaign import compile_only, run_campaign, run_rich_phase


def test_compile_only_verifies_frozen_skills() -> None:
    result = compile_only()
    assert result["status"] == "COMPILED"
    assert result["family_count"] == 4


def test_rich_phase_passes() -> None:
    result = run_rich_phase()
    assert result["verdict"] == "BOUNDED_COMPILED_RICH_OUTPUT_SURFACE_CONFIRMED"
    assert result["output_campaign"]["artifacts"] == 64


def test_mega_campaign_passes() -> None:
    result = run_campaign()
    assert result["verdict"] == "BOUNDED_MULTI_PHASE_LLM_LIKE_OUTPUT_FIDELITY_CONFIRMED"
    assert result["total_realized_outputs"] == 168
    assert result["runtime_byte_parity"] == 168
