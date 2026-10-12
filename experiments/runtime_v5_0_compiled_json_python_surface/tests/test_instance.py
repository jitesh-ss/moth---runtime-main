from __future__ import annotations

import json
from pathlib import Path

from moth_runtime_v5_0.canonical import canonical_bytes as runtime_bytes

from experiments.runtime_v5_0_compiled_surface_skill.compiler import compile_skill
from experiments.runtime_v5_0_compiled_json_python_surface.instance import StructuredSurfaceInstance
from experiments.runtime_v5_0_compiled_json_python_surface.model import canonical_bytes


ROOT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _assets():
    field = json.loads((FIXTURES / "structured-surface-field-en-1.0.json").read_text())
    compilation = compile_skill((FIXTURES / "structured-output/SKILL.md").read_text(), field)
    panel = json.loads((FIXTURES / "campaign-en-1.0.json").read_text())
    thresholds = json.loads((ROOT / "config/v5.0/grounding-en-1.0.json").read_text())["thresholds"]
    return field, compilation, panel, thresholds


def test_disposable_instance_preserves_runtime_and_replays_python(tmp_path):
    field, compilation, panel, thresholds = _assets()
    control = StructuredSurfaceInstance(tmp_path / "control", project_root=ROOT, field=field, compilation=compilation, thresholds=thresholds)
    candidate = StructuredSurfaceInstance(tmp_path / "candidate", project_root=ROOT, field=field, compilation=compilation, thresholds=thresholds)
    case = panel["answer_cases"][0]
    control_result = control.query_runtime(case["prompt"])
    package = candidate.query(case["prompt"], "Return readable Python.")
    assert runtime_bytes(package["runtime_result"]) == runtime_bytes(control_result)
    assert candidate.replay(package["archive"]) == canonical_bytes(package["archive"])
    assert package["artifact"]["format"] == "PYTHON"
    assert control.store_path != candidate.store_path


def test_runtime_refusal_is_never_serialized(tmp_path):
    field, compilation, panel, thresholds = _assets()
    instance = StructuredSurfaceInstance(tmp_path / "candidate", project_root=ROOT, field=field, compilation=compilation, thresholds=thresholds)
    case = panel["refusal_cases"][0]
    package = instance.query(case["prompt"], "Return readable JSON.")
    assert package["runtime_result"]["status"] == "REFUSAL"
    assert package["runtime_result"]["refusal"]["code"] == case["expected_refusal"]
    assert package["surface_applied"] is False
    assert package["artifact"] is None

