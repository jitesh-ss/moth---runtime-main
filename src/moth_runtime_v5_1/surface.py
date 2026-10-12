"""Pure compiled Surface realization with semantic recovery and no execution."""

from __future__ import annotations

import ast
import json
import re
from typing import Any

from moth_runtime_v5_0.canonical import canonical_bytes, digest
from moth_runtime_v5_0.model import IntegrityError

from .compiled_fields import FieldFailure


SURFACE_ARTIFACT_SCHEMA = "moth-compiled-surface-artifact/5.1"


def _ordered(value: Any) -> Any:
    """Normalize mapping order before source serialization and replay."""
    if isinstance(value, dict):
        return {key: _ordered(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_ordered(item) for item in value]
    return value


def _decision(value: Any) -> dict[str, str]:
    required = {"proposed-valid", "backup-valid", "selected-plan", "failure-reason"}
    if not isinstance(value, dict) or set(value) != required or not all(
        isinstance(item, str) for item in value.values()
    ):
        raise FieldFailure("UNSUPPORTED_SEMANTIC_RESULT", "Surface mode requires a plan decision")
    return {key: str(value[key]) for key in sorted(required)}


def _labels(value: dict[str, str]) -> str:
    return (
        f"Selected plan: {value['selected-plan']}. "
        f"Proposed valid: {value['proposed-valid']}. "
        f"Backup valid: {value['backup-valid']}. "
        f"Failure reason: {value['failure-reason']}."
    )


def _render(value: Any, mode: str) -> str:
    if mode in {"json_compact", "structured"}:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if mode == "json_readable":
        return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
    if mode in {"python_literal_compact", "python_literal_readable"}:
        rendered = repr(_ordered(value))
        return f"result = {rendered}" if mode.endswith("compact") else f"result = (\n    {rendered}\n)"
    if mode == "python_function":
        return "def get_result():\n    return " + repr(_ordered(value)) + "\n"

    decision = _decision(value)
    labels = _labels(decision)
    if mode in {"concise", "compact_prose"}:
        return labels
    if mode == "standard":
        return "The verified decision is as follows. " + labels
    if mode in {"detailed", "detailed_prose"}:
        return (
            "The compiled reasoning process reached a verified decision after checking the proposed "
            "and backup conditions. " + labels
            + " Every value in this explanation is bound to the settled semantic result."
        )
    if mode == "formal_tone":
        return "The verified determination is recorded below. " + labels
    if mode == "conversational_tone":
        return "Here’s the verified outcome. " + labels
    if mode == "markdown_bullets":
        return "\n".join([
            f"- Selected plan: {decision['selected-plan']}",
            f"- Proposed valid: {decision['proposed-valid']}",
            f"- Backup valid: {decision['backup-valid']}",
            f"- Failure reason: {decision['failure-reason']}",
        ])
    if mode == "markdown_table":
        return "\n".join([
            "| Field | Value |", "|---|---|",
            f"| Selected plan | {decision['selected-plan']} |",
            f"| Proposed valid | {decision['proposed-valid']} |",
            f"| Backup valid | {decision['backup-valid']} |",
            f"| Failure reason | {decision['failure-reason']} |",
        ])
    if mode == "explanation_json":
        payload = json.dumps(decision, sort_keys=True, indent=2)
        return "The verified decision is reproduced below without semantic changes.\n```json\n" + payload + "\n```"
    if mode == "action_plan":
        return "\n".join([
            "1. Use the verified selected plan.",
            f"2. Selected plan: {decision['selected-plan']}.",
            f"3. Proposed valid: {decision['proposed-valid']}. Backup valid: {decision['backup-valid']}.",
            f"4. Failure reason: {decision['failure-reason']}.",
        ])
    raise FieldFailure("UNSUPPORTED_PRESENTATION", f"unsupported compiled Surface mode: {mode}")


def _python_value(text: str, *, function: bool) -> Any:
    try:
        tree = ast.parse(text, mode="exec")
    except SyntaxError as exc:
        raise IntegrityError("generated Python Surface source does not parse") from exc
    if function:
        if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
            raise IntegrityError("generated Python Surface function shape changed")
        function_node = tree.body[0]
        if function_node.name != "get_result" or len(function_node.body) != 1 or not isinstance(function_node.body[0], ast.Return):
            raise IntegrityError("generated Python Surface return shape changed")
        return ast.literal_eval(function_node.body[0].value)
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.Assign):
        raise IntegrityError("generated Python Surface assignment shape changed")
    assignment = tree.body[0]
    if len(assignment.targets) != 1 or not isinstance(assignment.targets[0], ast.Name) or assignment.targets[0].id != "result":
        raise IntegrityError("generated Python Surface target changed")
    return ast.literal_eval(assignment.value)


def recover_surface_value(text: str, mode: str) -> Any:
    if mode in {"json_compact", "json_readable", "structured"}:
        return json.loads(text)
    if mode in {"python_literal_compact", "python_literal_readable"}:
        return _python_value(text, function=False)
    if mode == "python_function":
        return _python_value(text, function=True)
    if mode == "explanation_json":
        match = re.search(r"```json\n(.+)\n```$", text, re.DOTALL)
        if not match:
            raise IntegrityError("mixed Surface JSON payload is missing")
        return json.loads(match.group(1))

    plain = text.replace("*", "")
    labels = {
        "selected-plan": r"Selected plan:\s*([A-Za-z0-9_-]+)",
        "proposed-valid": r"Proposed valid:\s*([A-Za-z0-9_-]+)",
        "backup-valid": r"Backup valid:\s*([A-Za-z0-9_-]+)",
        "failure-reason": r"Failure reason:\s*([A-Za-z0-9_-]+)",
    }
    recovered: dict[str, str] = {}
    for key, pattern in labels.items():
        match = re.search(pattern, plain, re.IGNORECASE)
        if not match:
            if mode == "markdown_table":
                label = key.replace("-", " ")
                match = re.search(rf"\|\s*{re.escape(label)}\s*\|\s*([A-Za-z0-9_-]+)\s*\|", plain, re.IGNORECASE)
        if not match:
            raise IntegrityError(f"Surface output does not recover material field: {key}")
        recovered[key] = match.group(1)
    return recovered


def realize_surface(
    runtime_output: dict[str, Any], *, mode: str, field_id: str,
    field_hash: str, policy_hash: str, artifact_hash: str,
) -> dict[str, Any]:
    if not isinstance(runtime_output, dict) or set(runtime_output) != {"kind", "value"}:
        raise FieldFailure("UNSUPPORTED_SEMANTIC_RESULT", "Runtime output shape is invalid")
    text = _render(runtime_output["value"], mode)
    recovered = recover_surface_value(text, mode)
    if canonical_bytes(recovered) != canonical_bytes(runtime_output["value"]):
        raise IntegrityError("compiled Surface realization changed the semantic result")
    body = {
        "schema": SURFACE_ARTIFACT_SCHEMA, "mode": mode,
        "field_id": field_id, "field_hash": field_hash,
        "policy_hash": policy_hash, "model_artifact_hash": artifact_hash,
        "semantic_kind": runtime_output["kind"],
        "semantic_result_hash": digest("moth-surface-semantic-result/5.1", runtime_output),
        "text": text,
        "recovered_value_hash": digest("moth-surface-recovered-value/5.1", recovered),
        "metrics": {
            "bytes": len(text.encode("utf-8")),
            "lines": len(text.splitlines()),
            "words": len(text.split()),
        },
        "execution": {"performed": False, "dispatch_count": 0},
    }
    return {**body, "surface_hash": digest("moth-compiled-surface-artifact/5.1", body)}


def verify_surface_artifact(
    artifact: dict[str, Any], runtime_output: dict[str, Any], *,
    field_hash: str, policy_hash: str, artifact_hash: str,
) -> None:
    if artifact.get("schema") != SURFACE_ARTIFACT_SCHEMA:
        raise IntegrityError("compiled Surface artifact schema is invalid")
    body = {key: value for key, value in artifact.items() if key != "surface_hash"}
    if artifact.get("surface_hash") != digest("moth-compiled-surface-artifact/5.1", body):
        raise IntegrityError("compiled Surface artifact hash changed")
    if (
        artifact.get("field_hash") != field_hash
        or artifact.get("policy_hash") != policy_hash
        or artifact.get("model_artifact_hash") != artifact_hash
        or artifact.get("semantic_result_hash") != digest("moth-surface-semantic-result/5.1", runtime_output)
    ):
        raise IntegrityError("compiled Surface artifact binding changed")
    recovered = recover_surface_value(str(artifact.get("text", "")), str(artifact.get("mode", "")))
    if canonical_bytes(recovered) != canonical_bytes(runtime_output["value"]):
        raise IntegrityError("compiled Surface artifact semantic recovery changed")
    expected = realize_surface(
        runtime_output, mode=str(artifact["mode"]), field_id=str(artifact["field_id"]),
        field_hash=field_hash, policy_hash=policy_hash, artifact_hash=artifact_hash,
    )
    if canonical_bytes(expected) != canonical_bytes(artifact):
        raise IntegrityError("compiled Surface artifact differs from reconstruction")
