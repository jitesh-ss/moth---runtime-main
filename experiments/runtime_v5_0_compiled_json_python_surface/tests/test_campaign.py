from experiments.runtime_v5_0_compiled_json_python_surface.campaign import run_campaign


def test_frozen_json_python_surface_campaign():
    result = run_campaign()
    assert result["verdict"] == "BOUNDED_COMPILED_JSON_PYTHON_SURFACE_CONFIRMED"
    assert result["artifact_campaign"]["artifacts"] == 40
    assert result["artifact_campaign"]["json_artifacts"] == 24
    assert result["artifact_campaign"]["python_artifacts"] == 16
    assert result["artifact_campaign"]["semantic_drift"] == 0
    assert result["python_execution_count"] == 0
    assert result["protected_hashes_unchanged"] is True
