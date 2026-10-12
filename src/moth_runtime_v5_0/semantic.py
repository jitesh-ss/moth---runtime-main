"""Compiled, closed-world language settlement for Runtime 5.0 Input Worlds."""

from __future__ import annotations

from collections.abc import Callable
import math
import re
from typing import Any

import numpy as np

from .canonical import canonical_bytes, digest, normalize_text, sha256_bytes
from .model import (
    CompiledWorld, CompilationError, GroundedProgram, Meaning, MeaningType,
    Provenance, RefusalCode,
)

CONTRACT_SCHEMA = "moth-semantic-contract/5.0"
TRACE_SCHEMA = "moth-semantic-settlement/5.0"
Q = 1_000_000
MAX_TRACE_BYTES = 64 * 1024 * 1024

_SLOT_TYPES = {
    "ENTITY": MeaningType.ENTITY,
    "RELATION": MeaningType.RELATION,
    "NUMERAL": MeaningType.NUMERAL,
    "SCHEMA": MeaningType.OUTPUT_SCHEMA,
    "OUTPUT_SCHEMA": MeaningType.OUTPUT_SCHEMA,
    "STRUCTURE": MeaningType.STRUCTURED_SCHEMA,
    "RELATION_SEQUENCE": MeaningType.RELATION_SEQUENCE,
    "SEQUENCE": MeaningType.RELATION_SEQUENCE,
    "PROGRAM": MeaningType.PROGRAM,
    "TOOL": MeaningType.TOOL,
    "CODE_SYMBOL": MeaningType.CODE_SYMBOL,
    "SYMBOL": MeaningType.CODE_SYMBOL,
    "CODE_FILE": MeaningType.CODE_FILE,
    "CODE_SPAN": MeaningType.CODE_SPAN,
    "SPAN": MeaningType.CODE_SPAN,
    "PATCH_TEMPLATE": MeaningType.PATCH_TEMPLATE,
    "PATCH": MeaningType.PATCH_TEMPLATE,
    "TEXT_FRAGMENT": MeaningType.TEXT_FRAGMENT,
    "FRAGMENT": MeaningType.TEXT_FRAGMENT,
}
_VALUE_KINDS = (MeaningType.VALUE, MeaningType.ENUM_MEMBER, MeaningType.LIST_VALUE, MeaningType.ENTITY)
_COORDINATES = {"polarity", "modality", "time", "quantity"}


class SemanticFailure(ValueError):
    def __init__(self, code: RefusalCode, message: str, context: dict[str, Any]):
        super().__init__(f"{code.value}: {message}")
        self.code = code
        self.message = message
        self.context = context


def _surface(value: Any) -> str:
    result = normalize_text(str(value)).casefold()
    if not result:
        raise CompilationError("semantic surface is empty")
    return result


def _surfaces(values: Any, *, maximum: int = 32) -> list[str]:
    if not isinstance(values, list):
        raise CompilationError("semantic surfaces must be an array")
    result = sorted({_surface(value) for value in values})
    if not result or len(result) > maximum:
        raise CompilationError("semantic surface count outside its frozen limit")
    return result


def _safe_template(template: Any) -> tuple[str, tuple[str, ...]]:
    value = _surface(template)
    slots = tuple(re.findall(r"\{([A-Z_]+)\}", value.upper()))
    if not slots or slots.count("SUBJECT") != 1 or len(set(slots)) != len(slots):
        raise CompilationError("semantic frame requires one unique SUBJECT placeholder")
    if set(slots) - {"SUBJECT", "OBJECT"}:
        raise CompilationError("semantic frame contains an unsupported placeholder")
    residue = re.sub(r"\{[A-Za-z_]+\}", "", value)
    if "{" in residue or "}" in residue:
        raise CompilationError("semantic frame contains raw pattern syntax")
    return value, slots


def _resolve_value(
    name: str,
    target: Callable[[MeaningType, str], str],
) -> str:
    found: list[str] = []
    for kind in _VALUE_KINDS:
        try:
            found.append(target(kind, name))
        except CompilationError:
            pass
    if len(set(found)) != 1:
        raise CompilationError(f"undeclared or ambiguous semantic value: {name}")
    return found[0]


def compile_semantic_contract(
    *,
    name: str,
    source: Any,
    owner: Provenance,
    meanings: dict[str, Meaning],
    target: Callable[[MeaningType, str], str],
    declare: Callable[[MeaningType, str, dict[str, Any], Provenance], str],
) -> str:
    """Validate, resolve, and atomically declare one semantic contract."""
    if not isinstance(source, dict) or source.get("schema") != CONTRACT_SCHEMA:
        raise CompilationError("unsupported semantic contract schema")
    allowed = {"schema", "language", "domain", "entities", "predicates", "pronouns", "intents", "transformations"}
    if set(source) != allowed:
        raise CompilationError("semantic contract shape is invalid")
    if source["language"] != "en":
        raise CompilationError("only compiled English semantic contracts are supported")

    raw_domain = source["domain"]
    if not isinstance(raw_domain, dict) or set(raw_domain) != {"id", "surfaces"}:
        raise CompilationError("semantic domain shape is invalid")
    domain_id = normalize_text(str(raw_domain["id"]))
    if not domain_id:
        raise CompilationError("semantic domain identifier is empty")
    domain_surfaces = _surfaces(raw_domain["surfaces"])

    raw_entities = source["entities"]
    if not isinstance(raw_entities, list) or not 1 <= len(raw_entities) <= 4096:
        raise CompilationError("semantic entity count outside 1..4096")
    entities: list[dict[str, Any]] = []
    entity_keys: set[str] = set()
    entity_surfaces: dict[str, str] = {}
    roles: set[str] = set()
    for row in raw_entities:
        if not isinstance(row, dict) or set(row) != {"key", "entity", "role", "surfaces"}:
            raise CompilationError("semantic entity shape is invalid")
        key = normalize_text(str(row["key"]))
        role = normalize_text(str(row["role"])).upper()
        if not key or key in entity_keys or not role:
            raise CompilationError("semantic entity key or role is invalid")
        resolved_surfaces = _surfaces(row["surfaces"])
        for candidate in resolved_surfaces:
            if candidate in entity_surfaces:
                raise CompilationError("semantic entity surfaces are ambiguous within a contract")
            entity_surfaces[candidate] = key
        entity_keys.add(key)
        roles.add(role)
        entities.append({
            "key": key,
            "entity_id": target(MeaningType.ENTITY, normalize_text(str(row["entity"]))),
            "role": role,
            "surfaces": resolved_surfaces,
        })

    raw_predicates = source["predicates"]
    if not isinstance(raw_predicates, list) or not raw_predicates:
        raise CompilationError("semantic predicates are missing")
    predicates: list[dict[str, Any]] = []
    predicate_ids: set[str] = set()
    frame_count = 0
    for row in raw_predicates:
        if not isinstance(row, dict) or set(row) != {"id", "relation", "subject_roles", "object_roles", "frames"}:
            raise CompilationError("semantic predicate shape is invalid")
        predicate_id = normalize_text(str(row["id"]))
        subject_roles = sorted({normalize_text(str(value)).upper() for value in row["subject_roles"]})
        object_roles = sorted({normalize_text(str(value)).upper() for value in row["object_roles"]})
        if not predicate_id or predicate_id in predicate_ids or not subject_roles or set(subject_roles) - roles:
            raise CompilationError("semantic predicate identifier or subject role is invalid")
        if set(object_roles) - roles:
            raise CompilationError("semantic predicate object role is invalid")
        frames: list[dict[str, Any]] = []
        if not isinstance(row["frames"], list) or not row["frames"]:
            raise CompilationError("semantic predicate frames are missing")
        for raw_frame in row["frames"]:
            required = {"template", "polarity"}
            optional = {"object", "modality", "time", "quantity"}
            if not isinstance(raw_frame, dict) or not required <= set(raw_frame) or set(raw_frame) - required - optional:
                raise CompilationError("semantic frame shape is invalid")
            template, slots = _safe_template(raw_frame["template"])
            polarity = normalize_text(str(raw_frame["polarity"])).upper()
            if polarity not in {"POSITIVE", "NEGATIVE"}:
                raise CompilationError("semantic frame polarity is invalid")
            static_object = raw_frame.get("object")
            if ("OBJECT" in slots) == (static_object is not None):
                raise CompilationError("semantic frame must use OBJECT or a static object, not both/neither")
            object_key = None if static_object is None else normalize_text(str(static_object))
            if object_key is not None and object_key not in entity_keys:
                raise CompilationError("semantic frame static object is undeclared")
            coordinates = {
                key: normalize_text(str(raw_frame.get(key, default))).upper()
                for key, default in (("modality", "ASSERTED"), ("time", "PRESENT"), ("quantity", "SINGULAR"))
            }
            frames.append({
                "frame_id": digest("moth-semantic-frame/5.0", {"contract": name, "predicate": predicate_id, "template": template, "polarity": polarity, "object": object_key, **coordinates}),
                "template": template,
                "slots": list(slots),
                "polarity": polarity,
                "object_key": object_key,
                **coordinates,
            })
            frame_count += 1
        if frame_count > 256:
            raise CompilationError("RESOURCE_LIMIT: semantic frames per contract")
        predicate_ids.add(predicate_id)
        predicates.append({
            "id": predicate_id,
            "relation_id": target(MeaningType.RELATION, normalize_text(str(row["relation"]))),
            "subject_roles": subject_roles,
            "object_roles": object_roles,
            "frames": sorted(frames, key=lambda item: item["frame_id"]),
        })

    raw_pronouns = source["pronouns"]
    if not isinstance(raw_pronouns, dict) or set(raw_pronouns) != {"surfaces", "policy"}:
        raise CompilationError("semantic pronoun contract is invalid")
    if raw_pronouns["policy"] != "MOST_RECENT_UNAMBIGUOUS":
        raise CompilationError("unsupported semantic pronoun policy")
    pronouns = {"surfaces": _surfaces(raw_pronouns["surfaces"]), "policy": raw_pronouns["policy"]}

    raw_intents = source["intents"]
    if not isinstance(raw_intents, list) or not raw_intents:
        raise CompilationError("semantic intents are missing")
    intents: list[dict[str, Any]] = []
    intent_ids: set[str] = set()
    for row in raw_intents:
        if not isinstance(row, dict) or set(row) != {"id", "surfaces", "instruction", "slots", "projections"}:
            raise CompilationError("semantic intent shape is invalid")
        intent_id = normalize_text(str(row["id"]))
        if not intent_id or intent_id in intent_ids:
            raise CompilationError("semantic intent identifier is invalid")
        instruction_id = target(MeaningType.INSTRUCTION, normalize_text(str(row["instruction"])))
        instruction = meanings[instruction_id]
        expected_slots = set(re.findall(r"\{([A-Z_]+)\}", str(instruction.payload["template"])))
        raw_slots = row["slots"]
        if not isinstance(raw_slots, dict):
            raise CompilationError("semantic intent slots are invalid")
        slots: dict[str, str] = {}
        for slot, referenced_name in raw_slots.items():
            canonical_slot = normalize_text(str(slot)).upper()
            kind = _SLOT_TYPES.get(canonical_slot)
            if kind is None:
                raise CompilationError("semantic intent contains unsupported slot")
            slots[canonical_slot] = target(kind, normalize_text(str(referenced_name)))
        raw_projections = row["projections"]
        if not isinstance(raw_projections, list) or not raw_projections:
            raise CompilationError("semantic intent projections are missing")
        projections: list[dict[str, Any]] = []
        projected_fields: set[str] = set()
        for projection in raw_projections:
            required = {"subject_role", "predicate", "object_role", "field", "positive_value", "negative_value"}
            if not isinstance(projection, dict) or set(projection) != required:
                raise CompilationError("semantic projection shape is invalid")
            subject_role = normalize_text(str(projection["subject_role"])).upper()
            object_role = normalize_text(str(projection["object_role"])).upper()
            predicate = normalize_text(str(projection["predicate"]))
            if subject_role not in roles or object_role not in roles or predicate not in predicate_ids:
                raise CompilationError("semantic projection references an undeclared coordinate")
            field_id = target(MeaningType.SCHEMA_FIELD, normalize_text(str(projection["field"])))
            if field_id in projected_fields:
                raise CompilationError("semantic projection field is duplicated")
            projected_fields.add(field_id)
            projections.append({
                "subject_role": subject_role,
                "predicate": predicate,
                "object_role": object_role,
                "field_id": field_id,
                "positive_value_id": _resolve_value(normalize_text(str(projection["positive_value"])), target),
                "negative_value_id": _resolve_value(normalize_text(str(projection["negative_value"])), target),
            })
            if any(
                meanings[value_id].payload.get("type_id") != meanings[field_id].payload.get("type_id")
                for value_id in (
                    projections[-1]["positive_value_id"], projections[-1]["negative_value_id"],
                )
            ):
                raise CompilationError("semantic projection value type differs from schema field")
        if expected_slots != set(slots) | {"BINDINGS"}:
            raise CompilationError("semantic intent does not satisfy its instruction envelope")
        intent_ids.add(intent_id)
        intents.append({
            "id": intent_id,
            "surfaces": _surfaces(row["surfaces"]),
            "instruction_id": instruction_id,
            "operation_id": str(instruction.payload["operation_id"]),
            "slots": {key: value for key, value in sorted(slots.items())},
            "projections": sorted(projections, key=lambda item: item["field_id"]),
        })

    transformations = source["transformations"]
    if not isinstance(transformations, list) or any(not isinstance(value, str) for value in transformations):
        raise CompilationError("semantic transformations must be an array of identifiers")
    payload = {
        "schema": CONTRACT_SCHEMA,
        "language": "en",
        "domain": {"id": domain_id, "surfaces": domain_surfaces},
        "entities": sorted(entities, key=lambda item: item["key"]),
        "predicates": sorted(predicates, key=lambda item: item["id"]),
        "pronouns": pronouns,
        "intents": sorted(intents, key=lambda item: item["id"]),
        "transformations": sorted(set(transformations)),
    }
    contract_id = declare(MeaningType.SEMANTIC_CONTRACT, name, payload, owner)

    surface_rows: list[tuple[str, str, dict[str, Any]]] = []
    surface_rows.extend(("DOMAIN", text, {"domain_id": domain_id}) for text in domain_surfaces)
    for entity in entities:
        surface_rows.extend(("ENTITY", text, {"entity_id": entity["entity_id"], "entity_key": entity["key"], "role": entity["role"]}) for text in entity["surfaces"])
    for intent in intents:
        surface_rows.extend(("INTENT", text, {"intent_id": intent["id"]}) for text in intent["surfaces"])
    for index, (kind, text, extra) in enumerate(surface_rows):
        declare(MeaningType.SEMANTIC_SURFACE, f"{name}:{kind}:{index}", {
            "contract_id": contract_id, "surface_kind": kind, "text": text, **extra,
        }, owner)
    return contract_id


def _contains(surface: str, text: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(surface)}(?!\w)", text) is not None


def _template_regex(template: str) -> re.Pattern[str]:
    expression = re.escape(template)
    expression = expression.replace(re.escape("{subject}"), r"(?P<subject>.+?)")
    expression = expression.replace(re.escape("{object}"), r"(?P<object>.+?)")
    return re.compile("^" + expression + "$", re.IGNORECASE)


def _cost(score: float) -> int:
    return round(Q * (1.0 - max(-1.0, min(1.0, score))) / 2.0)


def _vector_hash(vector: np.ndarray) -> str:
    return sha256_bytes(np.asarray(vector, dtype="<f4").tobytes(order="C"))


def _resolve_entity(
    world: CompiledWorld,
    contract: Meaning,
    span: str,
    allowed_roles: set[str],
    *,
    encoder: Any,
    thresholds: dict[str, dict[str, float]],
) -> tuple[dict[str, Any], dict[str, Any], int]:
    cleaned = _surface(span).strip(" .,!?:;\"'")
    candidates = [item for item in contract.payload["entities"] if item["role"] in allowed_roles]
    exact = [item for item in candidates if cleaned in item["surfaces"]]
    if len(exact) == 1:
        return exact[0], {"method": "exact", "surface": cleaned, "score": 1.0, "margin": 1.0}, 0
    if len(exact) > 1:
        raise SemanticFailure(RefusalCode.AMBIGUOUS_REFERENCE, "entity surface is ambiguous", {"surface": cleaned})
    if encoder is None:
        raise SemanticFailure(RefusalCode.UNKNOWN_ENTITY, "entity is not compiled", {"surface": cleaned})
    query = np.asarray(encoder.encode_query(cleaned, token_limit=128), dtype=np.float32)
    norm = float(np.linalg.norm(query))
    if not math.isfinite(norm) or norm == 0.0:
        raise SemanticFailure(RefusalCode.INTEGRITY_FAILURE, "semantic query vector is invalid", {})
    query = query / norm
    surface_records = [item for item in world.by_kind(MeaningType.SEMANTIC_SURFACE) if item.payload.get("contract_id") == contract.meaning_id and item.payload.get("surface_kind") == "ENTITY" and item.payload.get("role") in allowed_roles and item.meaning_id in world.vectors]
    ranked_surfaces: list[tuple[float, Meaning]] = []
    for item in surface_records[:64]:
        vector = np.asarray(world.vectors[item.meaning_id].vector, dtype=np.float32)
        ranked_surfaces.append((round(float(np.dot(query, vector)), 6), item))
    ranked_surfaces.sort(key=lambda value: (-value[0], value[1].meaning_id))
    best_by_entity: dict[str, tuple[float, Meaning]] = {}
    for score, item in ranked_surfaces:
        entity_id = str(item.payload["entity_id"])
        if entity_id not in best_by_entity:
            best_by_entity[entity_id] = (score, item)
    ranked = sorted(best_by_entity.values(), key=lambda value: (-value[0], value[1].meaning_id))
    if not ranked:
        raise SemanticFailure(RefusalCode.UNKNOWN_ENTITY, "no typed semantic candidates exist", {"surface": cleaned})
    top_score, top_surface = ranked[0]
    second_score = ranked[1][0] if len(ranked) > 1 else -1.0
    margin = round(top_score - second_score, 6)
    gate = thresholds.get("SEMANTIC_SURFACE", {"score": 0.82, "margin": 0.05})
    if top_score <= float(gate["score"]):
        raise SemanticFailure(RefusalCode.UNKNOWN_ENTITY, "semantic entity score is below the compiled boundary", {"score": top_score, "margin": margin})
    if margin <= float(gate["margin"]):
        raise SemanticFailure(RefusalCode.AMBIGUOUS_REFERENCE, "semantic entity retrieval is not unique", {"score": top_score, "margin": margin})
    entity = next(item for item in candidates if item["entity_id"] == top_surface.payload["entity_id"])
    evidence = {
        "method": "vector", "surface": cleaned, "score": top_score, "margin": margin,
        "threshold": gate, "query_vector": [float(value) for value in query],
        "query_vector_hash": _vector_hash(query),
        "ranked_candidates": [{"entity_id": str(item.payload["entity_id"]), "surface_id": item.meaning_id, "score": score} for score, item in ranked[:64]],
    }
    return entity, evidence, _cost(top_score)


def settle_semantic(
    world: CompiledWorld,
    prompt: str,
    *,
    encoder: Any = None,
    thresholds: dict[str, dict[str, float]] | None = None,
) -> GroundedProgram:
    thresholds = thresholds or {}
    text = normalize_text(prompt)
    folded = text.casefold()
    clauses = [value.strip(" ,") for part in re.split(r"[.!?;]+", folded) if (value := part.strip())]
    if not clauses or len(clauses) > 32:
        raise SemanticFailure(RefusalCode.UNSUPPORTED_LANGUAGE, "prompt clause count is outside 1..32", {})
    contracts = list(world.by_kind(MeaningType.SEMANTIC_CONTRACT))
    ranked_contracts: list[tuple[int, Meaning, list[str]]] = []
    for contract in contracts:
        surfaces = list(contract.payload["domain"]["surfaces"])
        surfaces.extend(surface for entity in contract.payload["entities"] for surface in entity["surfaces"])
        matched = sorted({surface for surface in surfaces if _contains(surface, folded)})
        ranked_contracts.append((len(matched), contract, matched))
    ranked_contracts.sort(key=lambda item: (-item[0], item[1].meaning_id))
    if not ranked_contracts or ranked_contracts[0][0] == 0:
        raise SemanticFailure(RefusalCode.UNKNOWN_DOMAIN, "prompt does not select a compiled domain", {})
    if len(ranked_contracts) > 1 and ranked_contracts[0][0] == ranked_contracts[1][0]:
        raise SemanticFailure(RefusalCode.UNKNOWN_DOMAIN, "prompt does not uniquely select a compiled domain", {"scores": {item[1].name: item[0] for item in ranked_contracts}})
    _, contract, domain_matches = ranked_contracts[0]

    intent_matches: list[tuple[dict[str, Any], int, str]] = []
    for intent in contract.payload["intents"]:
        for index, clause in enumerate(clauses):
            if clause in intent["surfaces"]:
                intent_matches.append((intent, index, clause))
    unique_intents = {(item[0]["id"], item[1]) for item in intent_matches}
    if len(unique_intents) != 1:
        raise SemanticFailure(RefusalCode.UNSUPPORTED_INTENT, "prompt does not select exactly one compiled intent", {})
    intent, intent_index, intent_surface = intent_matches[0]

    entity_by_key = {item["key"]: item for item in contract.payload["entities"]}
    predicate_by_id = {item["id"]: item for item in contract.payload["predicates"]}
    pronouns = set(contract.payload["pronouns"]["surfaces"])
    facts_by_coordinate: dict[tuple[str, str, str, str, str, str], dict[str, Any]] = {}
    evidence_rows: list[dict[str, Any]] = []
    last_entity: dict[str, Any] | None = None
    reference_ambiguous = False
    total_cost = 0
    for clause_index, clause in enumerate(clauses):
        if clause_index == intent_index:
            continue
        matches: list[tuple[dict[str, Any], dict[str, Any], re.Match[str]]] = []
        for predicate in contract.payload["predicates"]:
            for frame in predicate["frames"]:
                if match := _template_regex(frame["template"]).fullmatch(clause):
                    matches.append((predicate, frame, match))
        if len(matches) > 1:
            literal_lengths = [
                len(re.sub(r"\{(?:subject|object)\}", "", item[1]["template"]))
                for item in matches
            ]
            longest = max(literal_lengths)
            matches = [item for item, length in zip(matches, literal_lengths) if length == longest]
        if len(matches) != 1:
            mentioned = [item for item in contract.payload["entities"] if any(_contains(surface, clause) for surface in item["surfaces"])]
            if not matches and len(mentioned) > 1:
                last_entity = None
                reference_ambiguous = True
                evidence_rows.append({"clause_index": clause_index, "clause": clause, "discourse_only": True, "mentioned_entity_ids": sorted(item["entity_id"] for item in mentioned)})
                continue
            code = RefusalCode.UNKNOWN_CAPABILITY if not matches else RefusalCode.UNSUPPORTED_LANGUAGE
            raise SemanticFailure(code, "clause does not select exactly one compiled frame", {"clause_index": clause_index, "match_count": len(matches)})
        predicate, frame, match = matches[0]
        raw_subject = _surface(match.group("subject")).strip(" ,")
        if raw_subject in pronouns:
            if last_entity is None or reference_ambiguous or last_entity["role"] not in predicate["subject_roles"]:
                raise SemanticFailure(RefusalCode.AMBIGUOUS_REFERENCE, "singular reference has no unique compatible antecedent", {"clause_index": clause_index})
            subject = last_entity
            subject_evidence = {"method": "pronoun", "surface": raw_subject, "antecedent_id": subject["entity_id"]}
            subject_cost = 0
        else:
            subject, subject_evidence, subject_cost = _resolve_entity(world, contract, raw_subject, set(predicate["subject_roles"]), encoder=encoder, thresholds=thresholds)
            last_entity = subject
            reference_ambiguous = False
        if "object" in match.groupdict() and match.group("object") is not None:
            obj, object_evidence, object_cost = _resolve_entity(world, contract, match.group("object"), set(predicate["object_roles"]), encoder=encoder, thresholds=thresholds)
        else:
            obj = entity_by_key[str(frame["object_key"])]
            if obj["role"] not in predicate["object_roles"]:
                raise SemanticFailure(RefusalCode.UNKNOWN_CAPABILITY, "static object violates predicate role type", {"clause_index": clause_index})
            object_evidence = {"method": "compiled_static", "entity_id": obj["entity_id"]}
            object_cost = 0
        total_cost += subject_cost + object_cost
        coordinate = (subject["entity_id"], predicate["id"], obj["entity_id"], frame["modality"], frame["time"], frame["quantity"])
        prior = facts_by_coordinate.get(coordinate)
        if prior is not None and prior["polarity"] != frame["polarity"]:
            raise SemanticFailure(RefusalCode.CONFLICTING_FACTS, "prompt asserts conflicting semantic coordinates", {"clause_index": clause_index})
        fact = {
            "subject_id": subject["entity_id"], "subject_role": subject["role"],
            "predicate_id": predicate["id"], "relation_id": predicate["relation_id"],
            "object_id": obj["entity_id"], "object_role": obj["role"],
            "polarity": frame["polarity"], "modality": frame["modality"],
            "time": frame["time"], "quantity": frame["quantity"],
        }
        facts_by_coordinate[coordinate] = fact
        evidence_rows.append({"clause_index": clause_index, "clause": clause, "frame_id": frame["frame_id"], "subject": subject_evidence, "object": object_evidence, "fact": fact})
        if len(facts_by_coordinate) > 128:
            raise SemanticFailure(RefusalCode.RESOURCE_LIMIT, "canonical fact count exceeds 128", {})

    bindings: dict[str, str] = {}
    projection_evidence: list[dict[str, Any]] = []
    facts = sorted(facts_by_coordinate.values(), key=lambda item: (item["subject_id"], item["predicate_id"], item["object_id"], item["modality"], item["time"], item["quantity"]))
    for projection in intent["projections"]:
        candidates = [fact for fact in facts if fact["subject_role"] == projection["subject_role"] and fact["predicate_id"] == projection["predicate"] and fact["object_role"] == projection["object_role"]]
        if len(candidates) != 1:
            raise SemanticFailure(RefusalCode.INCOMPLETE_FACT_GRAPH, "projection lacks one unique canonical fact", {"field_id": projection["field_id"], "match_count": len(candidates)})
        fact = candidates[0]
        value_id = projection["positive_value_id"] if fact["polarity"] == "POSITIVE" else projection["negative_value_id"]
        bindings[projection["field_id"]] = value_id
        projection_evidence.append({"field_id": projection["field_id"], "value_id": value_id, "fact_coordinate": [fact[key] for key in ("subject_id", "predicate_id", "object_id", "modality", "time", "quantity")]})

    slots = dict(intent["slots"])
    operation = world.meanings[intent["operation_id"]]
    steps: tuple[dict[str, Any], ...] = ()
    if "PROGRAM" in slots:
        steps = tuple(world.meanings[slots["PROGRAM"]].payload["steps"])
    graph = {"contract_id": contract.meaning_id, "domain_id": contract.payload["domain"]["id"], "intent_id": intent["id"], "facts": facts, "bindings": {key: value for key, value in sorted(bindings.items())}}
    semantic_graph_hash = digest("moth-semantic-graph/5.0", graph)
    interpretation = {
        "schema": TRACE_SCHEMA,
        "mode": "SEMANTIC_CONTRACT",
        "contract_id": contract.meaning_id,
        "domain_id": contract.payload["domain"]["id"],
        "intent_id": intent["id"],
        "facts": facts,
        "projected_bindings": graph["bindings"],
        "domain_evidence": {"matched_surfaces": domain_matches, "scores": {item[1].name: item[0] for item in ranked_contracts}},
        "intent_evidence": {"clause_index": intent_index, "surface": intent_surface},
        "clause_evidence": evidence_rows,
        "projection_evidence": projection_evidence,
        "grounding_cost_units": total_cost,
        "semantic_energy_units": total_cost,
        "semantic_graph_hash": semantic_graph_hash,
    }
    interpretation["trace_hash"] = digest(TRACE_SCHEMA, interpretation)
    if len(canonical_bytes(interpretation)) > MAX_TRACE_BYTES:
        raise SemanticFailure(RefusalCode.RESOURCE_LIMIT, "semantic trace exceeds 64 MiB", {})
    grounding = {"mode": "SEMANTIC_CONTRACT", "semantic_interpretation": interpretation}
    return GroundedProgram(
        intent["instruction_id"], intent["operation_id"], str(operation.payload["primitive"]),
        slots, bindings, steps, total_cost, grounding,
    )


def semantic_graph_hash(program: GroundedProgram) -> str:
    interpretation = program.grounding.get("semantic_interpretation") if isinstance(program.grounding, dict) else None
    if isinstance(interpretation, dict):
        return str(interpretation.get("semantic_graph_hash", ""))
    return digest("moth-semantic-graph/5.0", {
        "mode": "LEGACY_ENVELOPE", "instruction_id": program.instruction_id,
        "operation_id": program.operation_id, "slots": program.slots,
        "bindings": program.bindings,
    })


def verify_semantic_program(world: CompiledWorld, program: GroundedProgram) -> None:
    """Encoder-free verification of the archived semantic proof and projections."""
    interpretation = program.grounding.get("semantic_interpretation") if isinstance(program.grounding, dict) else None
    if not isinstance(interpretation, dict):
        return
    trace_hash = interpretation.get("trace_hash")
    unhashed = {key: value for key, value in interpretation.items() if key != "trace_hash"}
    if trace_hash != digest(TRACE_SCHEMA, unhashed):
        raise SemanticFailure(RefusalCode.INTEGRITY_FAILURE, "semantic trace hash changed", {})
    contract = world.meanings.get(str(interpretation.get("contract_id")))
    if contract is None or contract.kind != MeaningType.SEMANTIC_CONTRACT:
        raise SemanticFailure(RefusalCode.INTEGRITY_FAILURE, "semantic contract is absent", {})
    graph = {
        "contract_id": contract.meaning_id,
        "domain_id": interpretation.get("domain_id"),
        "intent_id": interpretation.get("intent_id"),
        "facts": interpretation.get("facts"),
        "bindings": interpretation.get("projected_bindings"),
    }
    if interpretation.get("semantic_graph_hash") != digest("moth-semantic-graph/5.0", graph):
        raise SemanticFailure(RefusalCode.INTEGRITY_FAILURE, "semantic graph hash changed", {})
    if program.bindings != interpretation.get("projected_bindings"):
        raise SemanticFailure(RefusalCode.INTEGRITY_FAILURE, "semantic projection changed", {})
    for row in interpretation.get("clause_evidence", []):
        for side in ("subject", "object"):
            evidence = row.get(side)
            if not isinstance(evidence, dict) or evidence.get("method") != "vector":
                continue
            query = np.asarray(evidence.get("query_vector"), dtype=np.float32)
            if query.ndim != 1 or _vector_hash(query) != evidence.get("query_vector_hash"):
                raise SemanticFailure(RefusalCode.INTEGRITY_FAILURE, "semantic query vector changed", {})
            recomputed = []
            for candidate in evidence.get("ranked_candidates", []):
                record = world.vectors.get(str(candidate.get("surface_id")))
                if record is None:
                    raise SemanticFailure(RefusalCode.INTEGRITY_FAILURE, "semantic candidate vector is absent", {})
                score = round(float(np.dot(query, np.asarray(record.vector, dtype=np.float32))), 6)
                if score != candidate.get("score"):
                    raise SemanticFailure(RefusalCode.INTEGRITY_FAILURE, "semantic candidate score changed", {})
                recomputed.append((score, str(candidate.get("surface_id"))))
            if recomputed != sorted(recomputed, key=lambda value: (-value[0], value[1])):
                raise SemanticFailure(RefusalCode.INTEGRITY_FAILURE, "semantic candidate ranking changed", {})
