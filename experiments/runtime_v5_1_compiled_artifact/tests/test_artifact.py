from copy import deepcopy
import json
from pathlib import Path

import pytest

from moth_runtime_v5_0.canonical import canonical_bytes
from moth_runtime_v5_0.model import IntegrityError
from moth_runtime_v5_1.artifact import ModelArtifact51
from moth_runtime_v5_1.cli import main as cli_main
from moth_runtime_v5_1.compiled_fields import FieldFailure
from moth_runtime_v5_1.runtime import Runtime51

from experiments.runtime_v5_1_compiled_artifact.build_artifact import ROOT, build_artifact


def test_artifact_build_load_and_runtime(tmp_path: Path) -> None:
    target = tmp_path / "model"
    receipt = build_artifact(target)
    assert receipt["verified"] is True
    assert receipt["weights_present"] is False
    assert receipt["field_count"] == 5
    assert receipt["skill_count"] == 10
    assert receipt["surface_mode_count"] == 16
    runtime = Runtime51.initialize_from_artifact(tmp_path / "store.sqlite3", target)
    panel = json.loads((ROOT / "experiments/runtime_v5_0_compiled_surface_skill/fixtures/campaign-en-1.0.json").read_text())
    result = runtime.turn(runtime.create_conversation(""), panel["answer_cases"][0]["prompt"], presentation="Return a Markdown table.")
    assert result["status"] == "ANSWER"
    assert result["response_mode"] == "markdown_table"
    assert result["surface"]["execution"]["performed"] is False


def test_artifact_rejects_extra_weight_member(tmp_path: Path) -> None:
    target = tmp_path / "model"
    build_artifact(target)
    (target / "weights.bin").write_bytes(b"not allowed")
    with pytest.raises(IntegrityError):
        ModelArtifact51.open(target)


def test_skills_are_fixed_and_plans_are_inert(tmp_path: Path) -> None:
    target = tmp_path / "model"
    build_artifact(target)
    runtime = Runtime51.initialize_from_artifact(tmp_path / "store.sqlite3", target)
    with pytest.raises(FieldFailure) as duplicate:
        runtime.create_conversation("", skill_ids=("SAFE_TEXT_PATCH", "SAFE_TEXT_PATCH"))
    assert duplicate.value.code == "DUPLICATE_SKILL"
    compilation = next(item for item in runtime.artifact.skills.values() if item["profile_id"] == "SAFE_TEXT_PATCH")
    task = {"target": "notes.txt", "files": {"notes.txt": "mode=old\n"}, "old": "mode=old", "new": "mode=new"}
    frozen = canonical_bytes(task)
    plan = runtime.plan_skill(compilation["compilation_id"], task)
    assert plan["status"] == "ACTION_PLAN"
    assert plan["execution"] == {"performed": False, "dispatch_count": 0, "writes": 0}
    assert canonical_bytes(task) == frozen


def test_surface_replay_after_presentation_change(tmp_path: Path) -> None:
    target = tmp_path / "model"
    build_artifact(target)
    runtime = Runtime51.initialize_from_artifact(tmp_path / "store.sqlite3", target)
    case = json.loads((ROOT / "experiments/runtime_v5_0_compiled_surface_skill/fixtures/campaign-en-1.0.json").read_text())["answer_cases"][0]
    conversation = runtime.create_conversation("")
    first = runtime.turn(conversation, case["prompt"], presentation="Give me the short version.")
    second = runtime.turn(conversation, "repeat that", presentation="Return a Markdown table.")
    assert first["kernel"]["output"] == second["kernel"]["output"]
    assert runtime.verify_conversation(conversation)["verified_result_chain"] is True


def test_artifact_console_workflow(tmp_path: Path, capsys) -> None:
    target, store = tmp_path / "model", tmp_path / "store.sqlite3"
    build_artifact(target)
    assert cli_main(["--json", "artifact", "verify", str(target)]) == 0
    assert json.loads(capsys.readouterr().out)["verified"] is True
    assert cli_main(["--store", str(store), "init", "--artifact", str(target)]) == 0
    capsys.readouterr()
    assert cli_main(["--store", str(store), "field", "list"]) == 0
    assert len(json.loads(capsys.readouterr().out)) == 5

    skill_path = ROOT / "experiments/runtime_v5_0_instruction_compression/fixtures/safe-text-patch-paraphrase/SKILL.md"
    assert cli_main([
        "--store", str(store), "--json", "skill", "compile", "--field",
        "bounded-agent-skill-en-1.0", "--file", str(skill_path),
    ]) == 0
    compilation_id = json.loads(capsys.readouterr().out)["compilation_id"]
    assert cli_main(["--store", str(store), "skill", "inspect", compilation_id]) == 0
    capsys.readouterr()
    task_path = tmp_path / "task.json"
    task_path.write_text(json.dumps({
        "target": "notes.txt", "files": {"notes.txt": "mode=old\n"},
        "old": "mode=old", "new": "mode=new",
    }))
    assert cli_main([
        "--store", str(store), "--json", "skill", "plan", compilation_id,
        "--task", str(task_path),
    ]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "ACTION_PLAN"

    system = tmp_path / "system.txt"
    system.write_text("")
    assert cli_main([
        "--store", str(store), "session", "create", "--system", str(system),
        "--skill", "NATURAL_RESPONSE",
    ]) == 0
    conversation = json.loads(capsys.readouterr().out)["conversation_id"]
    panel = json.loads((ROOT / "experiments/runtime_v5_0_compiled_surface_skill/fixtures/campaign-en-1.0.json").read_text())
    assert cli_main([
        "--store", str(store), "--json", "turn", conversation,
        panel["answer_cases"][0]["prompt"], "--presentation", "Return a Markdown table.",
    ]) == 0
    turn = json.loads(capsys.readouterr().out)
    assert turn["response_mode"] == "markdown_table"
    assert cli_main(["--store", str(store), "--json", "inspect", "artifact"]) == 0
    assert json.loads(capsys.readouterr().out)["weights_present"] is False
    assert cli_main([
        "--store", str(store), "--json", "inspect", "metrics", conversation,
        "--turn", turn["turn_id"],
    ]) == 0
    assert "timings_ns" in json.loads(capsys.readouterr().out)
