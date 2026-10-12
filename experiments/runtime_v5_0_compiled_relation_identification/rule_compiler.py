"""Compile bounded relation-identification instructions into Runtime 5.0 frames."""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any

from moth_runtime_v5_0.canonical import digest, normalize_text
from moth_runtime_v5_0.model import CompilationError


RULE_SCHEMA = "moth-v5-relation-identification-rules/1.0"
MANIFEST_SCHEMA = "moth-v5-compiled-relation-identification/1.0"
_COORDINATES = {
    "polarity": "NEGATIVE",
    "modality": "ASSERTED",
    "time": "PRESENT",
    "quantity": "SINGULAR",
}


def _construction(value: Any) -> str:
    text = normalize_text(str(value)).casefold()
    slots = re.findall(r"\{([A-Z_]+)\}", text.upper())
    if slots != ["SUBJECT", "OBJECT"]:
        raise CompilationError("relation identification requires ordered SUBJECT and OBJECT placeholders")
    residue = re.sub(r"\{[A-Za-z_]+\}", "", text)
    if not residue.strip() or "{" in residue or "}" in residue:
        raise CompilationError("relation identification construction is unsafe")
    return text


def compile_relation_identification(
    contract: dict[str, Any], rules: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate instructions atomically and emit an ordinary 5.0 contract."""
    required = {
        "schema", "frozen_before_execution", "predicate", "subject_roles",
        "object_roles", "coordinates", "rules",
    }
    if not isinstance(rules, dict) or set(rules) != required or rules.get("schema") != RULE_SCHEMA:
        raise CompilationError("unsupported relation-identification rule schema")
    if rules.get("frozen_before_execution") is not True:
        raise CompilationError("relation-identification rules are not frozen")
    if rules.get("coordinates") != _COORDINATES:
        raise CompilationError("relation-identification coordinates exceed the frozen boundary")
    subject_roles = sorted({normalize_text(str(value)).upper() for value in rules["subject_roles"]})
    object_roles = sorted({normalize_text(str(value)).upper() for value in rules["object_roles"]})
    predicates = [row for row in contract.get("predicates", []) if row.get("id") == rules["predicate"]]
    if len(predicates) != 1:
        raise CompilationError("relation-identification predicate is not uniquely compiled")
    predicate = predicates[0]
    if subject_roles != sorted(predicate["subject_roles"]) or object_roles != sorted(predicate["object_roles"]):
        raise CompilationError("relation-identification roles differ from the compiled predicate")
    raw_rows = rules.get("rules")
    if not isinstance(raw_rows, list) or not 1 <= len(raw_rows) <= 64:
        raise CompilationError("relation-identification rule count is outside 1..64")
    compiled_rows: list[dict[str, str]] = []
    identifiers: set[str] = set()
    constructions: set[str] = set()
    for row in raw_rows:
        if not isinstance(row, dict) or set(row) != {"id", "construction"}:
            raise CompilationError("relation-identification rule shape is invalid")
        identifier = normalize_text(str(row["id"]))
        construction = _construction(row["construction"])
        if not identifier or identifier in identifiers or construction in constructions:
            raise CompilationError("relation-identification rule is empty or duplicated")
        identifiers.add(identifier)
        constructions.add(construction)
        compiled_rows.append({"id": identifier, "construction": construction})

    result = deepcopy(contract)
    target = next(row for row in result["predicates"] if row["id"] == rules["predicate"])
    existing = {normalize_text(str(row["template"])).casefold() for row in target["frames"]}
    if constructions & existing:
        raise CompilationError("relation-identification construction duplicates a compiled frame")
    for row in sorted(compiled_rows, key=lambda item: item["id"]):
        target["frames"].append({
            "template": row["construction"],
            "polarity": _COORDINATES["polarity"],
            "modality": _COORDINATES["modality"],
            "time": _COORDINATES["time"],
            "quantity": _COORDINATES["quantity"],
        })
    manifest_payload = {
        "schema": MANIFEST_SCHEMA,
        "predicate": rules["predicate"],
        "subject_roles": subject_roles,
        "object_roles": object_roles,
        "coordinates": _COORDINATES,
        "rules": sorted(compiled_rows, key=lambda item: item["id"]),
    }
    manifest = {**manifest_payload, "manifest_hash": digest(MANIFEST_SCHEMA, manifest_payload)}
    return result, manifest

