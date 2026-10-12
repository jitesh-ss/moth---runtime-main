from experiments.runtime_v5_1_hcf.campaign import run_campaign
from experiments.runtime_v5_1_hcf.build_assets import build_foundation
from moth_runtime_v5_1.runtime import Runtime51


def test_frozen_hcf_campaign():
    result = run_campaign()
    assert result["passed"] == result["case_count"] == 6
    assert result["failed"] == 0
    assert result["verdict"] == "THREE_LEVEL_HCF_SETTLEMENT_CONFIRMED"


def test_development_foundation_runs_in_console_runtime(tmp_path):
    attachment = build_foundation(tmp_path / "foundation")
    runtime = Runtime51.initialize(
        tmp_path / "runtime.sqlite3", attachment["foundation"],
    )
    conversation_id = runtime.create_conversation("Respond concisely.")
    result = runtime.turn(conversation_id, "Find Asterion.")
    assert result["status"] == "ANSWER"
    assert result["response"] == "Asterion"
    assert runtime.verify_conversation(conversation_id)["verified"] is True
