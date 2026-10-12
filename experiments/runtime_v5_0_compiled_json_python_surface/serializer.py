"""Policy-driven JSON/Python serialization with independent parser checks."""

from __future__ import annotations

import ast
import json
from typing import Any

from experiments.runtime_v5_0_compiled_surface_skill.compiler import (
    validate_field,
    validate_policy,
)
from experiments.runtime_v5_0_compiled_surface_skill.model import (
    COMPILATION_SCHEMA,
    digest as compiler_digest,
    normalize_text,
    policy_hash,
)

from .model import ARTIFACT_SCHEMA, ArtifactFidelityFailure, digest


SEMANTIC_FIELDS = {
    "proposed-valid",
    "backup-valid",
    "selected-plan",
    "failure-reason",
}
REQUIRED_ACTIONS = {
    "VALIDATE_SEMANTIC_RESULT",
    "SELECT_MATERIAL_FIELDS",
    "DETECT_FORMAT_SIGNAL",
    "DETECT_LAYOUT_SIGNAL",
    "PLAN_EXACT_SCHEMA",
    "SERIALIZE_JSON",
    "SERIALIZE_PYTHON_LITERAL",
    "FORMAT_COMPACT",
    "FORMAT_READABLE",
    "PARSE_JSON_OUTPUT",
    "PARSE_PYTHON_AST",
    "VERIFY_EXACT_VALUE",
    "VERIFY_SAFE_AST",
    "VERIFY_LAYOUT",
    "BIND_SEMANTIC_HASH",
    "BIND_POLICY_HASH",
    "EMIT_ARTIFACT",
}


def semantic_hash(runtime_output: dict[str, Any]) -> str:
    return digest("moth-runtime-v5-output/structured-surface-1.0", runtime_output)


def _validate_semantic_result(runtime_output: dict[str, Any]) -> dict[str, str]:
    if not isinstance(runtime_output, dict) or set(runtime_output) != {"kind", "value"}:
        raise ArtifactFidelityFailure("MALFORMED_SEMANTIC_RESULT", "Runtime output envelope is invalid")
    if runtime_output.get("kind") != "FACTOR_RESULT" or not isinstance(runtime_output.get("value"), dict):
        raise ArtifactFidelityFailure("UNSUPPORTED_SEMANTIC_RESULT", "skill supports one frozen Runtime result kind")
    value = runtime_output["value"]
    if set(value) != SEMANTIC_FIELDS or any(not isinstance(item, str) for item in value.values()):
        raise ArtifactFidelityFailure("MALFORMED_SEMANTIC_RESULT", "plan-decision schema or type changed")
    proposed = value["proposed-valid"]
    backup = value["backup-valid"]
    selected = value["selected-plan"]
    reason = value["failure-reason"]
    if proposed not in {"true", "false"} or backup not in {"true", "false"}:
        raise ArtifactFidelityFailure("MALFORMED_SEMANTIC_RESULT", "validity is outside the frozen domain")
    if selected not in {"PROPOSED", "BACKUP", "NONE"} or reason not in {"NONE", "RESOURCE", "PERMISSION", "DEADLINE"}:
        raise ArtifactFidelityFailure("MALFORMED_SEMANTIC_RESULT", "decision is outside the frozen domain")
    expected = "PROPOSED" if proposed == "true" else "BACKUP" if backup == "true" else "NONE"
    if selected != expected or (reason == "NONE") != (proposed == "true"):
        raise ArtifactFidelityFailure("INCONSISTENT_SEMANTIC_RESULT", "decision violates the frozen factor contract")
    return dict(value)


def select_route(request: str, field: dict[str, Any]) -> tuple[str, str]:
    normalized = normalize_text(request).casefold().rstrip(".!?")
    matches = [
        route
        for route in field.get("presentation_routes", [])
        if normalized == normalize_text(str(route["request"])).casefold().rstrip(".!?")
    ]
    if len(matches) != 1:
        raise ArtifactFidelityFailure(
            "UNSUPPORTED_PRESENTATION",
            "format/layout request has no unique compiled route",
            {"request": request},
        )
    return str(matches[0]["format"]), str(matches[0]["layout"])


def _json_text(value: dict[str, str], layout: str) -> str:
    if layout == "COMPACT":
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)


def _python_text(value: dict[str, str], layout: str) -> str:
    ordered = {key: value[key] for key in sorted(value)}
    if layout == "COMPACT":
        return f"decision = {ordered!r}"
    rows = ["decision = {"]
    rows.extend(
        f"    {json.dumps(key, ensure_ascii=False)}: {json.dumps(item, ensure_ascii=False)},"
        for key, item in ordered.items()
    )
    rows.append("}")
    return "\n".join(rows)


def _parse_python_literal(text: str) -> dict[str, str]:
    try:
        tree = ast.parse(text, mode="exec")
    except SyntaxError as exc:
        raise ArtifactFidelityFailure("INVALID_PYTHON", "Python artifact does not parse") from exc
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.Assign):
        raise ArtifactFidelityFailure("UNSAFE_PYTHON", "Python artifact must contain one assignment")
    statement = tree.body[0]
    if (
        len(statement.targets) != 1
        or not isinstance(statement.targets[0], ast.Name)
        or statement.targets[0].id != "decision"
    ):
        raise ArtifactFidelityFailure("UNSAFE_PYTHON", "Python assignment target must be decision")
    allowed = (ast.Module, ast.Assign, ast.Name, ast.Store, ast.Dict, ast.Constant)
    if any(not isinstance(node, allowed) for node in ast.walk(tree)):
        raise ArtifactFidelityFailure("UNSAFE_PYTHON", "Python artifact contains an active AST node")
    try:
        value = ast.literal_eval(statement.value)
    except (ValueError, TypeError, SyntaxError) as exc:
        raise ArtifactFidelityFailure("UNSAFE_PYTHON", "Python value is not a safe literal") from exc
    if not isinstance(value, dict):
        raise ArtifactFidelityFailure("INVALID_PYTHON", "Python decision is not a dictionary")
    return value


def _expected_text(value: dict[str, str], output_format: str, layout: str) -> str:
    if output_format == "JSON":
        return _json_text(value, layout)
    if output_format == "PYTHON":
        return _python_text(value, layout)
    raise ArtifactFidelityFailure("UNSUPPORTED_FORMAT", "compiled route selected an unsupported format")


def _parse_and_verify(text: str, output_format: str, layout: str, expected: dict[str, str]) -> dict[str, Any]:
    if output_format == "JSON":
        try:
            recovered = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ArtifactFidelityFailure("INVALID_JSON", "JSON artifact does not parse") from exc
        if not isinstance(recovered, dict):
            raise ArtifactFidelityFailure("INVALID_JSON", "JSON artifact is not an object")
    elif output_format == "PYTHON":
        recovered = _parse_python_literal(text)
    else:
        raise ArtifactFidelityFailure("UNSUPPORTED_FORMAT", "artifact format is unsupported")
    if recovered != expected:
        raise ArtifactFidelityFailure(
            "SEMANTIC_DRIFT",
            "parsed artifact differs from the Runtime value",
            {"recovered": recovered, "expected": expected},
        )
    if text != _expected_text(expected, output_format, layout):
        raise ArtifactFidelityFailure("LAYOUT_INVALID", "artifact bytes differ from the compiled layout")
    line_count = text.count("\n") + 1
    if layout == "COMPACT" and line_count != 1:
        raise ArtifactFidelityFailure("LAYOUT_INVALID", "compact artifact is not one line")
    if layout == "READABLE" and line_count != 6:
        raise ArtifactFidelityFailure("LAYOUT_INVALID", "readable artifact does not have the frozen six-line form")
    return recovered


def _validate_compilation(compilation: dict[str, Any], field: dict[str, Any]) -> dict[str, Any]:
    validate_field(field)
    if compilation.get("schema") != COMPILATION_SCHEMA:
        raise ArtifactFidelityFailure("INVALID_SURFACE_POLICY", "compilation schema is invalid")
    expected_field_hash = compiler_digest("moth-surface-instruction-field/1.0", field)
    if compilation.get("field_hash") != expected_field_hash:
        raise ArtifactFidelityFailure("HASH_BINDING_INVALID", "policy is detached from its field")
    policy = compilation.get("policy")
    if not isinstance(policy, dict):
        raise ArtifactFidelityFailure("INVALID_SURFACE_POLICY", "compiled policy is absent")
    validate_policy(policy, field)
    if compilation.get("policy_hash") != policy_hash(policy):
        raise ArtifactFidelityFailure("HASH_BINDING_INVALID", "compiled policy hash changed")
    missing = sorted(REQUIRED_ACTIONS - set(policy["workflow"]))
    if missing:
        raise ArtifactFidelityFailure("INCOMPLETE_SURFACE_POLICY", "required serializer action is absent", {"missing": missing})
    return policy


def serialize_artifact(
    runtime_output: dict[str, Any],
    presentation_request: str,
    compilation: dict[str, Any],
    field: dict[str, Any],
) -> dict[str, Any]:
    policy = _validate_compilation(compilation, field)
    value = _validate_semantic_result(runtime_output)
    output_format, layout = select_route(presentation_request, field)
    text = _expected_text(value, output_format, layout)
    _parse_and_verify(text, output_format, layout, value)
    byte_count = len(text.encode("utf-8"))
    if byte_count > int(field["limits"]["maximum_artifact_bytes"]):
        raise ArtifactFidelityFailure("RESOURCE_LIMIT", "artifact exceeds the compiled byte limit")
    artifact = {
        "schema": ARTIFACT_SCHEMA,
        "status": "ANSWER",
        "format": output_format,
        "layout": layout,
        "text": text,
        "byte_count": byte_count,
        "line_count": text.count("\n") + 1,
        "value_hash": digest("moth-structured-surface-value/1.0", value),
        "semantic_result_hash": semantic_hash(runtime_output),
        "policy_hash": policy_hash(policy),
    }
    artifact["artifact_hash"] = digest("moth-experimental-structured-artifact/1.0", artifact)
    return artifact


def verify_artifact(
    artifact: dict[str, Any],
    runtime_output: dict[str, Any],
    compilation: dict[str, Any],
    field: dict[str, Any],
) -> None:
    policy = _validate_compilation(compilation, field)
    value = _validate_semantic_result(runtime_output)
    if artifact.get("schema") != ARTIFACT_SCHEMA or artifact.get("status") != "ANSWER":
        raise ArtifactFidelityFailure("INVALID_ARTIFACT", "artifact envelope is invalid")
    without_hash = {key: item for key, item in artifact.items() if key != "artifact_hash"}
    if artifact.get("artifact_hash") != digest("moth-experimental-structured-artifact/1.0", without_hash):
        raise ArtifactFidelityFailure("ARTIFACT_TAMPERED", "artifact hash changed")
    if artifact.get("semantic_result_hash") != semantic_hash(runtime_output):
        raise ArtifactFidelityFailure("HASH_BINDING_INVALID", "artifact is detached from the Runtime result")
    if artifact.get("policy_hash") != policy_hash(policy):
        raise ArtifactFidelityFailure("HASH_BINDING_INVALID", "artifact is detached from the compiled policy")
    if artifact.get("value_hash") != digest("moth-structured-surface-value/1.0", value):
        raise ArtifactFidelityFailure("SEMANTIC_DRIFT", "artifact value commitment changed")
    output_format = artifact.get("format")
    layout = artifact.get("layout")
    text = artifact.get("text")
    if output_format not in {"JSON", "PYTHON"} or layout not in {"COMPACT", "READABLE"} or not isinstance(text, str):
        raise ArtifactFidelityFailure("INVALID_ARTIFACT", "format, layout, or text is invalid")
    _parse_and_verify(text, output_format, layout, value)
    if artifact.get("byte_count") != len(text.encode("utf-8")) or artifact.get("line_count") != text.count("\n") + 1:
        raise ArtifactFidelityFailure("ARTIFACT_TAMPERED", "artifact metrics changed")
