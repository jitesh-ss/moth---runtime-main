from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from experiments.runtime_v5_0_compiled_surface_skill.compiler import compile_skill
from experiments.runtime_v5_0_compiled_json_python_surface.model import ArtifactFidelityFailure, digest
from experiments.runtime_v5_0_compiled_json_python_surface.serializer import serialize_artifact, verify_artifact


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _assets():
    field = json.loads((FIXTURES / "structured-surface-field-en-1.0.json").read_text())
    compilation = compile_skill((FIXTURES / "structured-output/SKILL.md").read_text(), field)
    panel = json.loads((FIXTURES / "campaign-en-1.0.json").read_text())
    return field, compilation, panel


def test_all_json_and_python_artifacts_parse_to_exact_runtime_values():
    field, compilation, panel = _assets()
    for case in panel["answer_cases"]:
        output = {"kind": "FACTOR_RESULT", "value": case["expected"]}
        for request in panel["presentation_requests"]:
            artifact = serialize_artifact(output, request["request"], compilation, field)
            verify_artifact(artifact, output, compilation, field)
            if artifact["format"] == "JSON":
                assert json.loads(artifact["text"]) == case["expected"]
            else:
                import ast

                tree = ast.parse(artifact["text"], mode="exec")
                assert ast.literal_eval(tree.body[0].value) == case["expected"]
            assert artifact["line_count"] == (1 if artifact["layout"] == "COMPACT" else 6)


def test_python_call_is_rejected_even_with_recomputed_artifact_hash():
    field, compilation, panel = _assets()
    output = {"kind": "FACTOR_RESULT", "value": panel["answer_cases"][0]["expected"]}
    artifact = serialize_artifact(output, "Return compact Python.", compilation, field)
    altered = deepcopy(artifact)
    altered["text"] = "decision = dict()"
    altered["byte_count"] = len(altered["text"].encode())
    without_hash = {key: value for key, value in altered.items() if key != "artifact_hash"}
    altered["artifact_hash"] = digest("moth-experimental-structured-artifact/1.0", without_hash)
    with pytest.raises(ArtifactFidelityFailure) as unsafe:
        verify_artifact(altered, output, compilation, field)
    assert unsafe.value.code == "UNSAFE_PYTHON"


def test_unknown_request_and_malformed_result_fail_closed():
    field, compilation, panel = _assets()
    output = {"kind": "FACTOR_RESULT", "value": panel["answer_cases"][0]["expected"]}
    with pytest.raises(ArtifactFidelityFailure) as request:
        serialize_artifact(output, "Return executable JavaScript.", compilation, field)
    assert request.value.code == "UNSUPPORTED_PRESENTATION"
    malformed = deepcopy(output)
    del malformed["value"]["failure-reason"]
    with pytest.raises(ArtifactFidelityFailure) as result:
        serialize_artifact(malformed, "Return compact JSON.", compilation, field)
    assert result.value.code == "MALFORMED_SEMANTIC_RESULT"

