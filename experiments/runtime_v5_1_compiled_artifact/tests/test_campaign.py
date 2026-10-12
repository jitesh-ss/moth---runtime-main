from experiments.runtime_v5_1_compiled_artifact.campaign import run_campaign


def test_complete_compiled_artifact_campaign() -> None:
    result = run_campaign()
    assert result["verdict"] == "WEIGHT_FREE_COMPILED_MODEL_ARTIFACT_5_1_CONFIRMED"
    assert result["surface_fidelity"]["outputs"] == 168
    assert result["inert_planning"]["cases"] == 36
    assert result["safety"] == {
        "weights": 0,
        "network_attempts": 0,
        "external_model_calls": 0,
        "tool_dispatches": 0,
        "generated_python_executions": 0,
        "task_workspace_writes": 0,
    }
