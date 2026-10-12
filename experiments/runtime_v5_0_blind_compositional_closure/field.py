"""Compile the sealed reusable language field for the closure experiment."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import re
from typing import Any

from moth_runtime_v5_0.canonical import digest, normalize_text
from moth_runtime_v5_0.model import CompilationError


FIELD_SCHEMA = "moth-v5-compositional-language-field/1.0"
COMPILED_SCHEMA = "moth-v5-compiled-compositional-language-field/1.0"


@dataclass(frozen=True)
class CompiledField:
    payload: dict[str, Any]
    field_hash: str


def _surface(value: Any) -> str:
    result = normalize_text(str(value)).casefold()
    if not result:
        raise CompilationError("compositional field surface is empty")
    return result


def ablate_field(source: dict[str, Any], subsystem: str) -> dict[str, Any]:
    result = deepcopy(source)
    kind, _, identifier = subsystem.partition(":")
    if kind == "entity":
        result["entities"] = [row for row in result["entities"] if row["id"] != identifier]
    elif kind == "capability":
        for row in result["capabilities"]:
            if row["id"] == identifier:
                row["surfaces"] = [f"unreachable ablated {identifier}"]
    elif kind == "relation":
        result["relation_rules"] = [row for row in result["relation_rules"] if row["id"] != identifier]
    elif subsystem == "coordination":
        result["coordination"]["operators"] = []
    elif subsystem == "intent:validation":
        result["intent"]["validation_markers"] = []
    elif subsystem == "pronouns":
        result["pronouns"]["surfaces"] = []
    else:
        raise CompilationError("unknown compositional field ablation")
    return result


def compile_field(source: dict[str, Any]) -> CompiledField:
    required = {
        "schema", "frozen_before_prompts", "language", "domain", "entities",
        "capabilities", "relation_rules", "coordination", "intent", "pronouns",
        "forbidden_markers", "limits",
    }
    if not isinstance(source, dict) or set(source) != required or source.get("schema") != FIELD_SCHEMA:
        raise CompilationError("unsupported compositional language field schema")
    if source.get("frozen_before_prompts") is not True or source.get("language") != "en":
        raise CompilationError("compositional language field is not frozen English")

    entities = []
    entity_surfaces: set[str] = set()
    for row in source["entities"]:
        if not isinstance(row, dict) or set(row) != {"id", "canonical", "role", "surfaces"}:
            raise CompilationError("compositional entity shape is invalid")
        surfaces = sorted({_surface(value) for value in row["surfaces"]})
        if not surfaces or entity_surfaces.intersection(surfaces):
            raise CompilationError("compositional entity surfaces are empty or ambiguous")
        entity_surfaces.update(surfaces)
        entities.append({
            "id": _surface(row["id"]), "canonical": _surface(row["canonical"]),
            "role": _surface(row["role"]).upper(), "surfaces": surfaces,
        })

    capabilities = []
    capability_surfaces: set[str] = set()
    capability_by_role: dict[str, dict[str, Any]] = {}
    for row in source["capabilities"]:
        if not isinstance(row, dict) or set(row) != {"id", "canonical", "role", "surfaces"}:
            raise CompilationError("compositional capability shape is invalid")
        surfaces = sorted({_surface(value) for value in row["surfaces"]})
        role = _surface(row["role"]).upper()
        if not surfaces or role in capability_by_role or capability_surfaces.intersection(surfaces):
            raise CompilationError("compositional capability surfaces are empty or ambiguous")
        compiled = {
            "id": _surface(row["id"]), "canonical": _surface(row["canonical"]),
            "role": role, "surfaces": surfaces,
        }
        capability_surfaces.update(surfaces)
        capabilities.append(compiled)
        capability_by_role[role] = compiled

    relation_rules = []
    rule_ids: set[str] = set()
    for row in source["relation_rules"]:
        if not isinstance(row, dict) or set(row) != {"id", "fragment", "emit"}:
            raise CompilationError("compositional relation rule shape is invalid")
        identifier = _surface(row["id"])
        fragment = _surface(row["fragment"])
        emit = _surface(row["emit"])
        fragment_slots = re.findall(r"\{([A-Z_]+)\}", fragment.upper())
        emit_slots = re.findall(r"\{([A-Z_]+)\}", emit.upper())
        if identifier in rule_ids or len(fragment_slots) > 1 or set(fragment_slots) - set(capability_by_role):
            raise CompilationError("compositional relation rule identifier or typed slot is invalid")
        if set(emit_slots) - ({"SUBJECT"} | set(capability_by_role)) or "SUBJECT" not in emit_slots:
            raise CompilationError("compositional relation output is not typed")
        if "{" in re.sub(r"\{[A-Za-z_]+\}", "", fragment) or "}" in re.sub(r"\{[A-Za-z_]+\}", "", fragment):
            raise CompilationError("compositional relation fragment contains unsafe syntax")
        rule_ids.add(identifier)
        relation_rules.append({
            "id": identifier, "fragment": fragment, "emit": emit,
            "object_role": fragment_slots[0] if fragment_slots else None,
        })

    coordination = source["coordination"]
    if set(coordination) != {"operators", "policy", "maximum_facts_per_sentence"} or coordination["policy"] != "INHERIT_UNIQUE_SENTENCE_SUBJECT":
        raise CompilationError("unsupported compositional coordination policy")
    operators = sorted({_surface(value) for value in coordination["operators"]})
    if any(not re.fullmatch(r"[a-z]+", value) for value in operators):
        raise CompilationError("compositional coordination operator is unsafe")

    intent = source["intent"]
    if set(intent) != {"id", "validation_markers", "selection_markers"}:
        raise CompilationError("compositional intent shape is invalid")
    compiled_intent = {
        "id": _surface(intent["id"]),
        "validation_markers": sorted({_surface(value) for value in intent["validation_markers"]}),
        "selection_markers": sorted({_surface(value) for value in intent["selection_markers"]}),
    }
    pronouns = source["pronouns"]
    if set(pronouns) != {"surfaces", "policy"} or pronouns["policy"] != "MOST_RECENT_UNAMBIGUOUS":
        raise CompilationError("unsupported compositional pronoun policy")
    forbidden = source["forbidden_markers"]
    if set(forbidden) != {"modality", "time"}:
        raise CompilationError("compositional forbidden-marker shape is invalid")
    limits = source["limits"]
    if limits != {"sentences": 8, "facts": 8, "tokens": 128}:
        raise CompilationError("compositional limits differ from the frozen boundary")

    payload = {
        "schema": COMPILED_SCHEMA, "language": "en", "domain": _surface(source["domain"]),
        "entities": sorted(entities, key=lambda row: row["id"]),
        "capabilities": sorted(capabilities, key=lambda row: row["id"]),
        "relation_rules": sorted(relation_rules, key=lambda row: row["id"]),
        "coordination": {**coordination, "operators": operators},
        "intent": compiled_intent,
        "pronouns": {"surfaces": sorted({_surface(value) for value in pronouns["surfaces"]}), "policy": pronouns["policy"]},
        "forbidden_markers": {key: sorted({_surface(value) for value in values}) for key, values in forbidden.items()},
        "limits": limits,
    }
    return CompiledField(payload, digest(COMPILED_SCHEMA, payload))
