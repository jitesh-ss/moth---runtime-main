"""Policy-driven bounded prose realization and independent verification."""

from __future__ import annotations

import re
from typing import Any

from .compiler import validate_field, validate_policy
from .model import (
    COMPILATION_SCHEMA,
    RESPONSE_SCHEMA,
    SurfaceFidelityFailure,
    digest,
    normalize_text,
    policy_hash,
)


SEMANTIC_FIELDS = {
    "proposed-valid",
    "backup-valid",
    "selected-plan",
    "failure-reason",
}
REQUIRED_ACTIONS = {
    "VALIDATE_SEMANTIC_RESULT",
    "DETECT_SIZE_SIGNAL",
    "SELECT_MATERIAL_FACTS",
    "PLAN_OUTCOME_FIRST",
    "LEXICALIZE_DECISION",
    "LEXICALIZE_STATUS",
    "LEXICALIZE_REASON",
    "CONNECT_SENTENCES",
    "REMOVE_REDUNDANCY",
    "VERIFY_FACT_COVERAGE",
    "VERIFY_NO_INVENTION",
    "COUNT_WORDS",
    "BIND_SEMANTIC_HASH",
    "BIND_POLICY_HASH",
    "EMIT_RESPONSE",
}
REASON_WORDS = {"RESOURCE": "resource", "PERMISSION": "permission", "DEADLINE": "deadline"}


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text, flags=re.UNICODE))


def sentences(text: str) -> list[str]:
    if not text or text[-1] not in ".!?”":
        return []
    return [item.strip() for item in re.split(r"(?<=[.!?])\s+", text) if item.strip()]


def semantic_hash(runtime_output: dict[str, Any]) -> str:
    return digest("moth-runtime-v5-output/experimental-surface-1.0", runtime_output)


def _validate_semantic_result(runtime_output: dict[str, Any]) -> dict[str, str]:
    if not isinstance(runtime_output, dict) or set(runtime_output) != {"kind", "value"}:
        raise SurfaceFidelityFailure("MALFORMED_SEMANTIC_RESULT", "Runtime output envelope is invalid")
    if runtime_output.get("kind") != "FACTOR_RESULT" or not isinstance(runtime_output.get("value"), dict):
        raise SurfaceFidelityFailure("UNSUPPORTED_SEMANTIC_RESULT", "Surface skill supports one frozen result kind")
    value = runtime_output["value"]
    if set(value) != SEMANTIC_FIELDS or any(not isinstance(item, str) for item in value.values()):
        raise SurfaceFidelityFailure("MALFORMED_SEMANTIC_RESULT", "plan-decision fields are incomplete")
    proposed = value["proposed-valid"]
    backup = value["backup-valid"]
    selected = value["selected-plan"]
    reason = value["failure-reason"]
    if proposed not in {"true", "false"} or backup not in {"true", "false"}:
        raise SurfaceFidelityFailure("MALFORMED_SEMANTIC_RESULT", "validity value is outside the frozen domain")
    if selected not in {"PROPOSED", "BACKUP", "NONE"} or reason not in {"NONE", *REASON_WORDS}:
        raise SurfaceFidelityFailure("MALFORMED_SEMANTIC_RESULT", "decision value is outside the frozen domain")
    expected_selected = "PROPOSED" if proposed == "true" else "BACKUP" if backup == "true" else "NONE"
    if selected != expected_selected or (reason == "NONE") != (proposed == "true"):
        raise SurfaceFidelityFailure("INCONSISTENT_SEMANTIC_RESULT", "decision fields violate the frozen factor contract")
    return dict(value)


def select_size(request: str, field: dict[str, Any]) -> str:
    normalized = normalize_text(request).casefold().rstrip(".!?")
    if not normalized:
        return "STANDARD"
    matched = [
        mode
        for mode, values in field["size_signals"].items()
        if normalized in {normalize_text(value).casefold().rstrip(".!?") for value in values}
    ]
    if len(matched) != 1:
        raise SurfaceFidelityFailure(
            "UNSUPPORTED_PRESENTATION",
            "presentation request has no unique compiled meaning",
            {"request": request},
        )
    return matched[0]


def _concise(value: dict[str, str]) -> str:
    proposed = value["proposed-valid"] == "true"
    backup = value["backup-valid"] == "true"
    selected = value["selected-plan"]
    reason = REASON_WORDS.get(value["failure-reason"], "")
    if selected == "BACKUP":
        return f"Use the backup plan; the proposed plan is invalid after a {reason} failure, while the backup plan is valid."
    if selected == "PROPOSED" and backup:
        return "Use the proposed plan; both the proposed and backup plans are valid, and there is no recorded failure."
    if selected == "PROPOSED" and not backup:
        return "Use the proposed plan; the proposed plan is valid, the backup plan is invalid, and there is no recorded failure."
    if not proposed and not backup:
        return f"Use neither plan; both the proposed and backup plans are invalid, with a recorded {reason} failure."
    raise SurfaceFidelityFailure("INCONSISTENT_SEMANTIC_RESULT", "no concise realization exists")


def _standard(value: dict[str, str]) -> str:
    backup = value["backup-valid"] == "true"
    selected = value["selected-plan"]
    reason = REASON_WORDS.get(value["failure-reason"], "")
    if selected == "BACKUP":
        return (
            f"Use the backup plan. The proposed plan is not viable because it fails the {reason} requirement. "
            "The backup plan is valid and satisfies every required condition for this decision."
        )
    if selected == "PROPOSED" and backup:
        return (
            "Use the proposed plan. Both the proposed and backup plans are valid because each satisfies every "
            "required condition. No recorded failure prevents selection of the proposed option."
        )
    if selected == "PROPOSED" and not backup:
        return (
            "Use the proposed plan. The proposed plan is valid and satisfies every required condition, while the "
            "backup plan is invalid. No recorded failure prevents the proposed option from being selected."
        )
    return (
        f"Do not use either plan. Both the proposed and backup plans are invalid, and the proposed plan fails the "
        f"{reason} requirement. No valid replacement is available from the verified options."
    )


def _detailed(value: dict[str, str]) -> str:
    proposed = value["proposed-valid"] == "true"
    backup = value["backup-valid"] == "true"
    selected = value["selected-plan"]
    reason = REASON_WORDS.get(value["failure-reason"], "")
    opening = {
        "PROPOSED": "Use the proposed plan.",
        "BACKUP": "Use the backup plan.",
        "NONE": "Do not use either plan.",
    }[selected]
    proposed_sentence = (
        "The proposed plan satisfies every required condition and is therefore valid."
        if proposed
        else f"The proposed plan is not viable because it fails the {reason} requirement."
    )
    backup_sentence = (
        "The backup plan also satisfies every required condition and remains a valid option."
        if backup
        else "The backup plan does not satisfy every required condition and is not a valid option."
    )
    decision_sentence = {
        "PROPOSED": "Because the proposed option is valid, the verified decision keeps it selected rather than replacing it.",
        "BACKUP": "Because the proposed option fails while the backup remains valid, the verified decision selects the backup as the replacement.",
        "NONE": "Because neither option is valid, the verified decision selects no plan from the available alternatives.",
    }[selected]
    reason_sentence = (
        "The verified result records no failure reason for the proposed plan."
        if value["failure-reason"] == "NONE"
        else f"The only recorded failure reason for the proposed plan is {reason}; no additional cause is inferred."
    )
    return " ".join(
        [opening, proposed_sentence, backup_sentence, decision_sentence, reason_sentence]
    )


def _render_text(value: dict[str, str], mode: str) -> str:
    return {"CONCISE": _concise, "STANDARD": _standard, "DETAILED": _detailed}[mode](value)


def _verify_text(text: str, value: dict[str, str], mode: str, field: dict[str, Any]) -> dict[str, int]:
    lowered = text.casefold()
    selected_prefixes = {
        "PROPOSED": "use the proposed plan",
        "BACKUP": "use the backup plan",
        "NONE": ("use neither plan", "do not use either plan"),
    }
    prefix = selected_prefixes[value["selected-plan"]]
    if isinstance(prefix, tuple):
        outcome_first = any(lowered.startswith(item) for item in prefix)
    else:
        outcome_first = lowered.startswith(prefix)
    if not outcome_first:
        raise SurfaceFidelityFailure("INVALID_DISCOURSE", "response does not lead with the verified outcome")

    proposed_markers = {
        "true": ("proposed plan is valid", "proposed plan satisfies every required condition", "both the proposed and backup plans are valid", "proposed option is valid"),
        "false": ("proposed plan is invalid", "proposed plan is not viable", "proposed option fails", "both the proposed and backup plans are invalid"),
    }
    backup_markers = {
        "true": ("backup plan is valid", "backup plan also satisfies every required condition", "backup remains valid", "both the proposed and backup plans are valid"),
        "false": ("backup plan is invalid", "backup plan does not satisfy every required condition", "both the proposed and backup plans are invalid"),
    }
    if not any(marker in lowered for marker in proposed_markers[value["proposed-valid"]]):
        raise SurfaceFidelityFailure("SEMANTIC_OMISSION", "proposed validity is not recoverable from prose")
    if not any(marker in lowered for marker in backup_markers[value["backup-valid"]]):
        raise SurfaceFidelityFailure("SEMANTIC_OMISSION", "backup validity is not recoverable from prose")

    present_reasons = {name for name, word in REASON_WORDS.items() if re.search(rf"\b{word}\b", lowered)}
    expected_reason = value["failure-reason"]
    if expected_reason == "NONE":
        if present_reasons or not any(
            marker in lowered
            for marker in ("no recorded failure", "records no failure reason", "no failure prevents")
        ):
            raise SurfaceFidelityFailure("UNSUPPORTED_CLAIM", "failure reason changed or was omitted")
    elif present_reasons != {expected_reason}:
        raise SurfaceFidelityFailure(
            "UNSUPPORTED_CLAIM",
            "prose contains an omitted or unsupported failure reason",
            {"expected": expected_reason, "present": sorted(present_reasons)},
        )

    raw_identifiers = ("proposed-valid", "backup-valid", "selected-plan", "failure-reason")
    if any(identifier in lowered for identifier in raw_identifiers) or any(character in text for character in "{}[]="):
        raise SurfaceFidelityFailure("INVALID_PROSE", "structured representation leaked into prose")
    if "\n" in text or text.startswith("#") or not text[0].isupper():
        raise SurfaceFidelityFailure("INVALID_PROSE", "response shape is not plain sentence-form prose")
    sentence_rows = sentences(text)
    if not sentence_rows or any(not row[0].isupper() or row[-1] not in ".!?" for row in sentence_rows):
        raise SurfaceFidelityFailure("INVALID_PROSE", "response contains an incomplete sentence")
    if len({row.casefold() for row in sentence_rows}) != len(sentence_rows):
        raise SurfaceFidelityFailure("INVALID_PROSE", "response repeats a sentence")

    words = word_count(text)
    band = field["size_bands"][mode]
    if not band["minimum_words"] <= words <= band["maximum_words"]:
        raise SurfaceFidelityFailure("SIZE_VIOLATION", "word count is outside the compiled band", {"mode": mode, "words": words})
    if not band["minimum_sentences"] <= len(sentence_rows) <= band["maximum_sentences"]:
        raise SurfaceFidelityFailure("SIZE_VIOLATION", "sentence count is outside the compiled band", {"mode": mode, "sentences": len(sentence_rows)})
    return {"word_count": words, "sentence_count": len(sentence_rows)}


def _validate_compilation(compilation: dict[str, Any], field: dict[str, Any]) -> dict[str, Any]:
    validate_field(field)
    if compilation.get("schema") != COMPILATION_SCHEMA:
        raise SurfaceFidelityFailure("INVALID_SURFACE_POLICY", "compilation schema is invalid")
    if compilation.get("field_hash") != digest("moth-surface-instruction-field/1.0", field):
        raise SurfaceFidelityFailure("HASH_BINDING_INVALID", "compiled policy is detached from its field")
    policy = compilation.get("policy")
    if not isinstance(policy, dict):
        raise SurfaceFidelityFailure("INVALID_SURFACE_POLICY", "compiled policy is absent")
    validate_policy(policy, field)
    if compilation.get("policy_hash") != policy_hash(policy):
        raise SurfaceFidelityFailure("HASH_BINDING_INVALID", "compiled policy hash changed")
    missing = sorted(REQUIRED_ACTIONS - set(policy["workflow"]))
    if missing:
        raise SurfaceFidelityFailure("INCOMPLETE_SURFACE_POLICY", "required Surface action is absent", {"missing": missing})
    return policy


def realize(runtime_output: dict[str, Any], presentation_request: str, compilation: dict[str, Any], field: dict[str, Any]) -> dict[str, Any]:
    policy = _validate_compilation(compilation, field)
    value = _validate_semantic_result(runtime_output)
    mode = select_size(presentation_request, field)
    text = _render_text(value, mode)
    metrics = _verify_text(text, value, mode, field)
    response = {
        "schema": RESPONSE_SCHEMA,
        "status": "ANSWER",
        "text": text,
        "size_mode": mode,
        **metrics,
        "claims": value,
        "semantic_result_hash": semantic_hash(runtime_output),
        "policy_hash": policy_hash(policy),
    }
    response["response_hash"] = digest("moth-experimental-surface-response/1.0", response)
    return response


def verify_response(response: dict[str, Any], runtime_output: dict[str, Any], compilation: dict[str, Any], field: dict[str, Any]) -> None:
    policy = _validate_compilation(compilation, field)
    value = _validate_semantic_result(runtime_output)
    if response.get("schema") != RESPONSE_SCHEMA or response.get("status") != "ANSWER":
        raise SurfaceFidelityFailure("INVALID_RESPONSE", "Surface response envelope is invalid")
    without_hash = {key: item for key, item in response.items() if key != "response_hash"}
    if response.get("response_hash") != digest("moth-experimental-surface-response/1.0", without_hash):
        raise SurfaceFidelityFailure("RESPONSE_TAMPERED", "Surface response hash changed")
    if response.get("semantic_result_hash") != semantic_hash(runtime_output):
        raise SurfaceFidelityFailure("HASH_BINDING_INVALID", "response is detached from the Runtime result")
    if response.get("policy_hash") != policy_hash(policy):
        raise SurfaceFidelityFailure("HASH_BINDING_INVALID", "response is detached from the compiled policy")
    if response.get("claims") != value:
        raise SurfaceFidelityFailure("SEMANTIC_DRIFT", "response claims differ from the Runtime result")
    mode = response.get("size_mode")
    if mode not in field["size_bands"] or not isinstance(response.get("text"), str):
        raise SurfaceFidelityFailure("INVALID_RESPONSE", "response mode or text is invalid")
    metrics = _verify_text(response["text"], value, mode, field)
    if response.get("word_count") != metrics["word_count"] or response.get("sentence_count") != metrics["sentence_count"]:
        raise SurfaceFidelityFailure("RESPONSE_TAMPERED", "recorded response metrics changed")
