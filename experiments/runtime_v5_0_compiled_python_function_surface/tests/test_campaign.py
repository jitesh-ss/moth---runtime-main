from experiments.runtime_v5_0_compiled_python_function_surface.campaign import compile_only, run_campaign


def test_compile_only_verifies_frozen_policy() -> None:
    result = compile_only()
    assert result["status"] == "COMPILED"
    assert result["equivalent_policy"] is True


def test_frozen_campaign_passes() -> None:
    result = run_campaign()
    assert result["verdict"] == "BOUNDED_COMPILED_PYTHON_FUNCTION_SURFACE_CONFIRMED"
    assert result["program_campaign"]["programs"] == 16
    assert result["program_campaign"]["executed_exact_value"] == 16
    assert result["protected_hashes_unchanged"] is True
