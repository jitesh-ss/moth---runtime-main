from __future__ import annotations

import json
from pathlib import Path

from moth_runtime_v5_0.canonical import canonical_bytes as runtime_bytes

from experiments.runtime_v5_0_compiled_surface_skill.compiler import compile_skill
from experiments.runtime_v5_0_compiled_surface_skill.instance import IsolatedSurfaceInstance
from experiments.runtime_v5_0_compiled_surface_skill.model import canonical_bytes


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
FIXTURES = HERE / "fixtures"


def _assets():
    field = json.loads((FIXTURES / "surface-base-field-en-1.0.json").read_text())
    compilation = compile_skill((FIXTURES / "natural-response/SKILL.md").read_text(), field)
    panel = json.loads((FIXTURES / "campaign-en-1.0.json").read_text())
    thresholds = json.loads((ROOT / "config/v5.0/grounding-en-1.0.json").read_text())["thresholds"]
    return field, compilation, panel, thresholds


def test_disposable_instance_preserves_runtime_bytes_and_replays_surface(tmp_path):
    field, compilation, panel, thresholds = _assets()
    control = IsolatedSurfaceInstance(tmp_path / "control", project_root=ROOT, field=field, compilation=compilation, thresholds=thresholds)
    candidate = IsolatedSurfaceInstance(tmp_path / "candidate", project_root=ROOT, field=field, compilation=compilation, thresholds=thresholds)
    case = panel["answer_cases"][0]
    control_result = control.query_runtime(case["prompt"])
    package = candidate.query(case["prompt"], "Explain the result in detail.")
    assert runtime_bytes(package["runtime_result"]) == runtime_bytes(control_result)
    assert package["surface_response"]["claims"] == case["expected"]
    assert candidate.replay(package["archive"]) == canonical_bytes(package["archive"])
    assert control.store_path != candidate.store_path
    assert control.store_path != ROOT / "data/store-5.0.sqlite3"


def test_runtime_refusal_is_not_realized(tmp_path):
    field, compilation, panel, thresholds = _assets()
    instance = IsolatedSurfaceInstance(tmp_path / "candidate", project_root=ROOT, field=field, compilation=compilation, thresholds=thresholds)
    case = panel["refusal_cases"][0]
    package = instance.query(case["prompt"], "Explain the result in detail.")
    assert package["runtime_result"]["status"] == "REFUSAL"
    assert package["runtime_result"]["refusal"]["code"] == case["expected_refusal"]
    assert package["surface_applied"] is False
    assert package["surface_response"] is None

