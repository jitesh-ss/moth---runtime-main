from pathlib import Path

from moth_runtime_v5_0.canonical import canonical_bytes

from experiments.runtime_v5_1_autonomous_json_skill.campaign import (
    _metamorphic,
    _negative,
    _positive,
    worker_digest,
)
from experiments.runtime_v5_1_autonomous_json_skill.compiler import compile_candidate
from experiments.runtime_v5_1_autonomous_json_skill.candidate_runtime import AutonomousJsonRuntime


def test_campaign_panels_and_fresh_store_replay(tmp_path: Path) -> None:
    field, skill = compile_candidate()
    positive, _ = _positive(field, skill, tmp_path / "panel.sqlite3")
    negative, _ = _negative(field, skill)
    metamorphic, _ = _metamorphic(field, skill)
    assert positive["cases"] == positive["semantic_exact"] == 240
    assert negative["cases"] == negative["correct_typed_refusals"] == 96
    assert metamorphic["cases"] == metamorphic["passed"] == 64

    prompt = 'Return compact strict JSON. Source data: {"a":1}'
    left = AutonomousJsonRuntime(tmp_path / "left.sqlite3", field, skill)
    right = AutonomousJsonRuntime(tmp_path / "right.sqlite3", field, skill)
    a = left.turn(left.create_conversation(), prompt)
    b = right.turn(right.create_conversation(), prompt)
    assert canonical_bytes(a) == canonical_bytes(b)


def test_worker_digest_is_deterministic() -> None:
    assert worker_digest() == worker_digest()

