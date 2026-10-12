"""Policy-driven realization for eight rich response modes."""

from __future__ import annotations

import json
import re
from typing import Any

from experiments.runtime_v5_0_compiled_surface_skill.compiler import validate_field, validate_policy
from experiments.runtime_v5_0_compiled_surface_skill.model import (
    COMPILATION_SCHEMA,
    digest as compiler_digest,
    normalize_text,
    policy_hash,
)

from .model import ARTIFACT_SCHEMA, OutputFidelityFailure, digest


SEMANTIC_FIELDS = {"proposed-valid", "backup-valid", "selected-plan", "failure-reason"}
REQUIRED_ACTIONS = {
    "VALIDATE_SEMANTIC_RESULT",
    "SELECT_PRESENTATION_ROUTE",
    "PLAN_DISCOURSE",
    "REALIZE_MATERIAL_FACTS",
    "FORMAT_OUTPUT",
    "VERIFY_INVERSE_RECOVERY",
    "VERIFY_LAYOUT",
    "VERIFY_SIZE",
    "BIND_HASHES",
    "EMIT_ARTIFACT",
}
MODES = {
    "COMPACT_PROSE",
    "DETAILED_PROSE",
    "FORMAL_TONE",
    "CONVERSATIONAL_TONE",
    "MARKDOWN_BULLETS",
    "MARKDOWN_TABLE",
    "EXPLANATION_JSON",
    "ACTION_PLAN",
}


def semantic_hash(runtime_output: dict[str, Any]) -> str:
    return digest("moth-runtime-v5-output/rich-surface-1.0", runtime_output)


def validate_semantic_result(runtime_output: dict[str, Any]) -> dict[str, str]:
    if not isinstance(runtime_output, dict) or set(runtime_output) != {"kind", "value"}:
        raise OutputFidelityFailure("MALFORMED_SEMANTIC_RESULT", "Runtime output envelope is invalid")
    if runtime_output.get("kind") != "FACTOR_RESULT" or not isinstance(runtime_output.get("value"), dict):
        raise OutputFidelityFailure("UNSUPPORTED_SEMANTIC_RESULT", "unsupported Runtime output kind")
    value = runtime_output["value"]
    if set(value) != SEMANTIC_FIELDS or any(not isinstance(item, str) for item in value.values()):
        raise OutputFidelityFailure("MALFORMED_SEMANTIC_RESULT", "decision schema or types changed")
    proposed = value["proposed-valid"]
    backup = value["backup-valid"]
    selected = value["selected-plan"]
    reason = value["failure-reason"]
    if proposed not in {"true", "false"} or backup not in {"true", "false"}:
        raise OutputFidelityFailure("MALFORMED_SEMANTIC_RESULT", "validity is outside the frozen domain")
    if selected not in {"PROPOSED", "BACKUP", "NONE"} or reason not in {"NONE", "RESOURCE", "PERMISSION", "DEADLINE"}:
        raise OutputFidelityFailure("MALFORMED_SEMANTIC_RESULT", "decision is outside the frozen domain")
    expected = "PROPOSED" if proposed == "true" else "BACKUP" if backup == "true" else "NONE"
    if selected != expected or (reason == "NONE") != (proposed == "true"):
        raise OutputFidelityFailure("INCONSISTENT_SEMANTIC_RESULT", "decision violates the factor contract")
    return dict(value)


def validate_compilation(compilation: dict[str, Any], field: dict[str, Any]) -> dict[str, Any]:
    validate_field(field)
    if compilation.get("schema") != COMPILATION_SCHEMA:
        raise OutputFidelityFailure("INVALID_SURFACE_POLICY", "compilation schema is invalid")
    if compilation.get("field_hash") != compiler_digest("moth-surface-instruction-field/1.0", field):
        raise OutputFidelityFailure("HASH_BINDING_INVALID", "policy is detached from its field")
    policy = compilation.get("policy")
    if not isinstance(policy, dict):
        raise OutputFidelityFailure("INVALID_SURFACE_POLICY", "compiled policy is absent")
    validate_policy(policy, field)
    if compilation.get("policy_hash") != policy_hash(policy):
        raise OutputFidelityFailure("HASH_BINDING_INVALID", "compiled policy hash changed")
    missing = sorted(REQUIRED_ACTIONS - set(policy["workflow"]))
    if missing:
        raise OutputFidelityFailure("INCOMPLETE_SURFACE_POLICY", "required realizer action is absent", {"missing": missing})
    return policy


def select_route(request: str, profile: str, field: dict[str, Any]) -> str:
    normalized = normalize_text(request).casefold().rstrip(".!?")
    matches = [
        route
        for route in field["presentation_routes"]
        if normalized == normalize_text(str(route["request"])).casefold().rstrip(".!?")
        and route["profile"] == profile
    ]
    if len(matches) != 1:
        raise OutputFidelityFailure("UNSUPPORTED_PRESENTATION", "request is unsupported by this compiled skill")
    return str(matches[0]["mode"])


def _validity(word: str) -> str:
    return "valid" if word == "true" else "invalid"


def _selection_words(selected: str) -> str:
    return {"PROPOSED": "the proposed plan", "BACKUP": "the backup plan", "NONE": "neither plan"}[selected]


def _reason_words(reason: str) -> str:
    return {"NONE": "none", "RESOURCE": "resource", "PERMISSION": "permission", "DEADLINE": "deadline"}[reason]


def build_text(value: dict[str, str], mode: str) -> str:
    proposed = _validity(value["proposed-valid"])
    backup = _validity(value["backup-valid"])
    selection = _selection_words(value["selected-plan"])
    reason = _reason_words(value["failure-reason"])
    if mode == "COMPACT_PROSE":
        return f"Use {selection}. The proposed plan is {proposed}, the backup plan is {backup}, and the failure reason is {reason}."
    if mode == "DETAILED_PROSE":
        action = f"Proceed with {selection} after confirming execution readiness." if value["selected-plan"] != "NONE" else "Do not proceed until a valid replacement is available."
        return (
            "Recommendation\n\n"
            f"Use {selection}.\n\n"
            "Assessment\n\n"
            f"The proposed plan is {proposed}. The backup plan is {backup}. The recorded failure reason is {reason}.\n\n"
            "Next step\n\n"
            f"{action}"
        )
    if mode == "FORMAL_TONE":
        return f"The assessment concludes that {selection} should be used: the proposed plan is {proposed}, the backup plan is {backup}, and the recorded failure reason is {reason}."
    if mode == "CONVERSATIONAL_TONE":
        return f"Go with {selection}. The proposed plan is {proposed}, the backup plan is {backup}, and the issue on record is {reason}."
    if mode == "MARKDOWN_BULLETS":
        return "\n".join(
            [
                f"- Proposed plan: {proposed}",
                f"- Backup plan: {backup}",
                f"- Selection: {value['selected-plan']}",
                f"- Failure reason: {value['failure-reason']}",
            ]
        )
    if mode == "MARKDOWN_TABLE":
        return "\n".join(
            [
                "| Field | Value |",
                "|---|---|",
                f"| Proposed plan | {proposed} |",
                f"| Backup plan | {backup} |",
                f"| Selection | {value['selected-plan']} |",
                f"| Failure reason | {value['failure-reason']} |",
            ]
        )
    if mode == "EXPLANATION_JSON":
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
        return f"Use {selection}; the complete verified decision follows.\n\n```json\n{encoded}\n```"
    if mode == "ACTION_PLAN":
        return "\n".join(
            [
                f"1. Record the proposed plan as {proposed}.",
                f"2. Record the backup plan as {backup}.",
                f"3. Record the failure reason as {value['failure-reason']}.",
                f"4. Select {value['selected-plan']} for execution.",
            ]
        )
    raise OutputFidelityFailure("UNSUPPORTED_PRESENTATION", "unknown rich-output mode")


def _domain_values() -> list[dict[str, str]]:
    values: list[dict[str, str]] = []
    for backup in ("true", "false"):
        values.append({"proposed-valid": "true", "backup-valid": backup, "selected-plan": "PROPOSED", "failure-reason": "NONE"})
    for backup in ("true", "false"):
        for reason in ("RESOURCE", "PERMISSION", "DEADLINE"):
            values.append(
                {
                    "proposed-valid": "false",
                    "backup-valid": backup,
                    "selected-plan": "BACKUP" if backup == "true" else "NONE",
                    "failure-reason": reason,
                }
            )
    return values


def recover_semantics(text: str, mode: str) -> dict[str, str]:
    if mode == "EXPLANATION_JSON":
        match = re.fullmatch(r"[^\n]+\n\n```json\n(\{.*\})\n```", text, flags=re.DOTALL)
        if match is None:
            raise OutputFidelityFailure("INVERSE_RECOVERY_FAILED", "mixed JSON region is malformed")
        try:
            recovered = json.loads(match.group(1))
        except json.JSONDecodeError as exc:
            raise OutputFidelityFailure("INVERSE_RECOVERY_FAILED", "mixed JSON region does not parse") from exc
        return validate_semantic_result({"kind": "FACTOR_RESULT", "value": recovered})
    matches = [value for value in _domain_values() if build_text(value, mode) == text]
    if len(matches) != 1:
        raise OutputFidelityFailure("INVERSE_RECOVERY_FAILED", "output does not uniquely recover one semantic value")
    return matches[0]


def _word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", text))


def verify_surface(text: str, mode: str, expected: dict[str, str], field: dict[str, Any]) -> dict[str, int]:
    if mode not in MODES:
        raise OutputFidelityFailure("UNSUPPORTED_PRESENTATION", "artifact mode is unsupported")
    recovered = recover_semantics(text, mode)
    if recovered != expected:
        raise OutputFidelityFailure("SEMANTIC_DRIFT", "inverse recovery differs from Runtime semantics")
    if text != build_text(expected, mode):
        raise OutputFidelityFailure("LAYOUT_INVALID", "artifact bytes differ from deterministic realization")
    line_count = text.count("\n") + 1
    word_count = _word_count(text)
    byte_count = len(text.encode("utf-8"))
    limits = field["mode_limits"][mode]
    if not int(limits["minimum_lines"]) <= line_count <= int(limits["maximum_lines"]):
        raise OutputFidelityFailure("LAYOUT_INVALID", "artifact line count is outside the mode band")
    if not int(limits["minimum_words"]) <= word_count <= int(limits["maximum_words"]):
        raise OutputFidelityFailure("SIZE_INVALID", "artifact word count is outside the mode band", {"words": word_count})
    if byte_count > int(limits["maximum_bytes"]):
        raise OutputFidelityFailure("SIZE_INVALID", "artifact byte count exceeds the mode band")
    return {"line_count": line_count, "word_count": word_count, "byte_count": byte_count}


def realize_artifact(
    runtime_output: dict[str, Any],
    presentation_request: str,
    compilation: dict[str, Any],
    field: dict[str, Any],
) -> dict[str, Any]:
    policy = validate_compilation(compilation, field)
    value = validate_semantic_result(runtime_output)
    mode = select_route(presentation_request, str(policy["policy_id"]), field)
    text = build_text(value, mode)
    metrics = verify_surface(text, mode, value, field)
    artifact = {
        "schema": ARTIFACT_SCHEMA,
        "status": "ANSWER",
        "mode": mode,
        "text": text,
        "metrics": metrics,
        "recovered_value_hash": digest("moth-v5-rich-output-recovered-value/1.0", value),
        "semantic_result_hash": semantic_hash(runtime_output),
        "policy_hash": policy_hash(policy),
    }
    artifact["artifact_hash"] = digest("moth-v5-rich-output-artifact/1.0", artifact)
    return artifact


def verify_artifact(
    artifact: dict[str, Any],
    runtime_output: dict[str, Any],
    compilation: dict[str, Any],
    field: dict[str, Any],
) -> None:
    policy = validate_compilation(compilation, field)
    value = validate_semantic_result(runtime_output)
    if artifact.get("schema") != ARTIFACT_SCHEMA or artifact.get("status") != "ANSWER":
        raise OutputFidelityFailure("INVALID_ARTIFACT", "artifact envelope is invalid")
    without_hash = {key: item for key, item in artifact.items() if key != "artifact_hash"}
    if artifact.get("artifact_hash") != digest("moth-v5-rich-output-artifact/1.0", without_hash):
        raise OutputFidelityFailure("ARTIFACT_TAMPERED", "artifact hash changed")
    if artifact.get("semantic_result_hash") != semantic_hash(runtime_output):
        raise OutputFidelityFailure("HASH_BINDING_INVALID", "artifact is detached from Runtime semantics")
    if artifact.get("policy_hash") != policy_hash(policy):
        raise OutputFidelityFailure("HASH_BINDING_INVALID", "artifact is detached from compiled policy")
    mode = artifact.get("mode")
    text = artifact.get("text")
    if not isinstance(mode, str) or not isinstance(text, str):
        raise OutputFidelityFailure("INVALID_ARTIFACT", "mode or text is invalid")
    if artifact.get("metrics") != verify_surface(text, mode, value, field):
        raise OutputFidelityFailure("ARTIFACT_TAMPERED", "artifact metrics changed")
    if artifact.get("recovered_value_hash") != digest("moth-v5-rich-output-recovered-value/1.0", value):
        raise OutputFidelityFailure("SEMANTIC_DRIFT", "recovered-value commitment changed")
