"""Proof-carrying semantic settlement for text and internal observations."""

from __future__ import annotations

from dataclasses import replace
import itertools
import math
import re
from typing import Any, Protocol

import numpy as np

from moth_runtime_v4_9.canonical import canonical_bytes, digest, normalize_text

from .model import (
    SemanticCoordinate,
    SemanticEntity,
    SemanticRefusal,
    SemanticRefusalCode,
    SemanticSettlement,
    SemanticWorld,
)

Q = 1_000_000
SETTLEMENT_SCHEMA = "moth-semantic-settlement/1.0"


class SemanticEncoder(Protocol):
    def encode_passages(self, texts: list[str]): ...
    def encode_query(self, text: str, *, token_limit: int = 128): ...


def _span(value: str) -> str:
    value = normalize_text(value).casefold().strip(" .,!?:;\"'")
    return re.sub(r"^(?:the|a|an)\s+", "", value)


def _entity_indexes(world: SemanticWorld) -> tuple[dict[tuple[str, str], SemanticEntity], dict[str, list[SemanticEntity]]]:
    exact: dict[tuple[str, str], SemanticEntity] = {}
    by_type: dict[str, list[SemanticEntity]] = {kind: [] for kind in world.entity_types}
    for entity in world.entities:
        by_type[entity.entity_type].append(entity)
        for surface in entity.surfaces:
            exact[(entity.entity_type, surface)] = entity
    for values in by_type.values():
        values.sort(key=lambda item: item.entity_id)
    return exact, by_type


def _resolve_entities(
    world: SemanticWorld,
    raw: str,
    required_type: str,
    encoder: SemanticEncoder | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    surface = _span(raw)
    exact, by_type = _entity_indexes(world)
    if item := exact.get((required_type, surface)):
        row = {
            "entity_key": item.key,
            "entity_id": item.entity_id,
            "score": 1.0,
            "cost": 0,
            "method": "exact",
        }
        return [row], {"surface": surface, "required_type": required_type, "candidates": [row]}

    wrong_types = sorted({kind for (kind, candidate_surface) in exact if candidate_surface == surface})
    if wrong_types:
        raise SemanticRefusal(
            SemanticRefusalCode.TYPE_MISMATCH,
            "language role resolves to an entity of the wrong compiled type",
            {"surface": surface, "required_type": required_type, "actual_types": wrong_types},
        )
    candidates = by_type.get(required_type, [])
    if encoder is None or not candidates:
        raise SemanticRefusal(
            SemanticRefusalCode.UNKNOWN_ENTITY,
            "language role does not resolve to a compiled entity",
            {"surface": surface, "required_type": required_type},
        )
    query = np.asarray(encoder.encode_query(surface, token_limit=128), dtype=np.float32)
    passages = np.asarray(encoder.encode_passages([item.description for item in candidates]), dtype=np.float32)
    if passages.shape[0] != len(candidates) or passages.shape[1:] != query.shape:
        raise SemanticRefusal(SemanticRefusalCode.INTEGRITY_FAILURE, "semantic encoder shape changed", {})
    ranked: list[tuple[float, SemanticEntity]] = []
    for item, vector in zip(candidates, passages, strict=True):
        score = round(float(np.dot(query, vector)), 6)
        if not math.isfinite(score):
            raise SemanticRefusal(SemanticRefusalCode.INTEGRITY_FAILURE, "semantic encoder returned a non-finite score", {})
        ranked.append((score, item))
    ranked.sort(key=lambda pair: (-pair[0], pair[1].entity_id))
    top_score = ranked[0][0]
    score_gate = world.thresholds["entity_score"]
    window = world.thresholds["entity_window"]
    accepted = [
        {
            "entity_key": item.key,
            "entity_id": item.entity_id,
            "score": score,
            "cost": round(Q * (1.0 - max(-1.0, min(1.0, score)))),
            "method": "vector",
        }
        for score, item in ranked
        if score >= score_gate and top_score - score <= window
    ]
    evidence = {
        "surface": surface,
        "required_type": required_type,
        "score_gate": score_gate,
        "candidate_window": window,
        "ranked": [
            {"entity_key": item.key, "entity_id": item.entity_id, "score": score}
            for score, item in ranked
        ],
        "candidates": accepted,
    }
    if not accepted:
        raise SemanticRefusal(
            SemanticRefusalCode.UNKNOWN_ENTITY,
            "no compiled entity passes the frozen semantic candidate gate",
            evidence,
        )
    return accepted, evidence


def _meaning_index(world: SemanticWorld) -> dict[tuple[str, ...], Any]:
    return {item.coordinate.key(): item for item in world.meanings}


def _select(
    world: SemanticWorld,
    *,
    input_kind: str,
    input_payload: dict[str, Any],
    observations: list[dict[str, Any]],
    compatible_rows: list[dict[str, Any]],
) -> SemanticSettlement:
    if not compatible_rows:
        raise SemanticRefusal(
            SemanticRefusalCode.UNSUPPORTED_MEANING,
            "the observation does not denote a compiled canonical meaning",
            {"observations": observations},
        )
    deduplicated: dict[str, dict[str, Any]] = {}
    for row in compatible_rows:
        previous = deduplicated.get(row["meaning_id"])
        if previous is None or (row["energy_units"], row["evidence_hash"]) < (
            previous["energy_units"], previous["evidence_hash"]
        ):
            deduplicated[row["meaning_id"]] = row
    ranked = sorted(deduplicated.values(), key=lambda row: (
        row["energy_units"], row["meaning_id"], row["evidence_hash"]
    ))
    top = ranked[0]
    second = ranked[1] if len(ranked) > 1 else None
    margin_units = None if second is None else second["energy_units"] - top["energy_units"]
    required_margin = round(Q * world.thresholds["meaning_margin"])
    if second is not None and margin_units < required_margin:
        raise SemanticRefusal(
            SemanticRefusalCode.AMBIGUOUS_SEMANTICS,
            "multiple compiled meanings remain inside the frozen semantic margin",
            {
                "candidate_meaning_ids": [row["meaning_id"] for row in ranked],
                "energies": [row["energy_units"] for row in ranked],
                "margin_units": margin_units,
                "required_margin_units": required_margin,
            },
        )
    meaning = next(item for item in world.meanings if item.meaning_id == top["meaning_id"])
    input_hash = digest(f"moth-semantic-{input_kind.lower()}-input/1.0", input_payload)
    trace = {
        "schema": "moth-semantic-trace/1.0",
        "world_hash": world.world_hash,
        "input_kind": input_kind,
        "input_hash": input_hash,
        "observations": observations,
        "compatible_rows": ranked,
        "selection": {
            "meaning_id": meaning.meaning_id,
            "coordinate": meaning.coordinate.canonical(),
            "total_energy_units": top["energy_units"],
            "next_energy_units": None if second is None else second["energy_units"],
            "margin_units": margin_units,
            "required_margin_units": required_margin,
        },
    }
    trace_hash = digest("moth-semantic-trace/1.0", trace)
    return SemanticSettlement(
        schema=SETTLEMENT_SCHEMA,
        world_hash=world.world_hash,
        input_kind=input_kind,
        input_hash=input_hash,
        meaning_id=meaning.meaning_id,
        coordinate=meaning.coordinate,
        total_energy_units=top["energy_units"],
        trace=trace,
        trace_hash=trace_hash,
    )


def settle_text(
    world: SemanticWorld,
    text: str,
    *,
    encoder: SemanticEncoder | None = None,
) -> SemanticSettlement:
    normalized = normalize_text(text)
    predicate_by_key = {item.key: item for item in world.predicates}
    meaning_by_coordinate = _meaning_index(world)
    observations: list[dict[str, Any]] = []
    compatible_rows: list[dict[str, Any]] = []
    matched = False
    for frame in world.frames:
        match = re.fullmatch(frame.pattern, normalized, flags=re.IGNORECASE)
        if match is None:
            continue
        matched = True
        predicate = predicate_by_key[frame.predicate]
        subject_raw = match.group(frame.subject_group)
        object_raw = match.group(frame.object_group)
        subject_candidates, subject_evidence = _resolve_entities(
            world, subject_raw, predicate.subject_type, encoder,
        )
        object_candidates, object_evidence = _resolve_entities(
            world, object_raw, predicate.object_type, encoder,
        )
        observation = {
            "frame_id": frame.frame_id,
            "frame_key": frame.key,
            "predicate": frame.predicate,
            "polarity": frame.polarity,
            "modality": frame.modality,
            "time": frame.time,
            "subject": subject_evidence,
            "object": object_evidence,
        }
        observations.append(observation)
        for subject, object_ in itertools.product(subject_candidates, object_candidates):
            coordinate = SemanticCoordinate(
                frame.predicate,
                subject["entity_key"],
                object_["entity_key"],
                frame.polarity,
                frame.modality,
                frame.time,
            )
            meaning = meaning_by_coordinate.get(coordinate.key())
            if meaning is None:
                continue
            evidence = {
                "frame_id": frame.frame_id,
                "subject_entity_id": subject["entity_id"],
                "object_entity_id": object_["entity_id"],
                "subject_cost": subject["cost"],
                "object_cost": object_["cost"],
            }
            compatible_rows.append({
                "meaning_id": meaning.meaning_id,
                "coordinate": coordinate.canonical(),
                "energy_units": subject["cost"] + object_["cost"],
                "evidence": evidence,
                "evidence_hash": digest("moth-semantic-candidate-evidence/1.0", evidence),
            })
    if not matched:
        raise SemanticRefusal(
            SemanticRefusalCode.UNSUPPORTED_LANGUAGE,
            "no compiled reusable language frame matches the observation",
            {"text": normalized},
        )
    return _select(
        world,
        input_kind="TEXT",
        input_payload={"text": normalized},
        observations=observations,
        compatible_rows=compatible_rows,
    )


def settle_internal(world: SemanticWorld, observation: dict[str, Any]) -> SemanticSettlement:
    relation = str(observation.get("relation", ""))
    transform = next((item for item in world.transforms if item.source_relation == relation), None)
    if transform is None:
        raise SemanticRefusal(
            SemanticRefusalCode.UNSUPPORTED_MEANING,
            "internal relation has no compiled semantic transformation",
            {"relation": relation},
        )
    arguments = observation.get("arguments")
    if not isinstance(arguments, dict):
        raise SemanticRefusal(SemanticRefusalCode.UNSUPPORTED_MEANING, "internal observation lacks arguments", {})
    subject_key = str(arguments.get(transform.subject_argument, ""))
    object_key = str(arguments.get(transform.object_argument, ""))
    entity_by_key = {item.key: item for item in world.entities}
    predicate = next(item for item in world.predicates if item.key == transform.predicate)
    subject = entity_by_key.get(subject_key)
    object_ = entity_by_key.get(object_key)
    if subject is None or object_ is None:
        raise SemanticRefusal(
            SemanticRefusalCode.UNKNOWN_ENTITY,
            "internal observation refers to an uncompiled entity",
            {"subject": subject_key, "object": object_key},
        )
    if subject.entity_type != predicate.subject_type or object_.entity_type != predicate.object_type:
        raise SemanticRefusal(
            SemanticRefusalCode.TYPE_MISMATCH,
            "internal relation arguments violate compiled role types",
            {
                "subject_type": subject.entity_type,
                "required_subject_type": predicate.subject_type,
                "object_type": object_.entity_type,
                "required_object_type": predicate.object_type,
            },
        )
    coordinate = SemanticCoordinate(
        transform.predicate,
        subject.key,
        object_.key,
        transform.polarity,
        transform.modality,
        transform.time,
    )
    meaning = _meaning_index(world).get(coordinate.key())
    compatible_rows: list[dict[str, Any]] = []
    evidence = {
        "transform_id": transform.transform_id,
        "source_relation": transform.source_relation,
        "subject_entity_id": subject.entity_id,
        "object_entity_id": object_.entity_id,
    }
    if meaning is not None:
        compatible_rows.append({
            "meaning_id": meaning.meaning_id,
            "coordinate": coordinate.canonical(),
            "energy_units": 0,
            "evidence": evidence,
            "evidence_hash": digest("moth-semantic-candidate-evidence/1.0", evidence),
        })
    canonical_input = {
        "relation": relation,
        "arguments": {str(key): str(value) for key, value in sorted(arguments.items())},
    }
    return _select(
        world,
        input_kind="INTERNAL",
        input_payload=canonical_input,
        observations=[{
            "transform_id": transform.transform_id,
            "source_relation": relation,
            "coordinate": coordinate.canonical(),
        }],
        compatible_rows=compatible_rows,
    )


def verify_settlement(
    world: SemanticWorld,
    settlement: SemanticSettlement,
    *,
    text: str | None = None,
    observation: dict[str, Any] | None = None,
    encoder: SemanticEncoder | None = None,
) -> None:
    if settlement.schema != SETTLEMENT_SCHEMA or settlement.world_hash != world.world_hash:
        raise SemanticRefusal(SemanticRefusalCode.INTEGRITY_FAILURE, "settlement identity changed", {})
    if settlement.trace_hash != digest("moth-semantic-trace/1.0", settlement.trace):
        raise SemanticRefusal(SemanticRefusalCode.INTEGRITY_FAILURE, "semantic trace hash changed", {})
    if (text is None) == (observation is None):
        raise ValueError("verify exactly one text or internal observation")
    expected = (
        settle_text(world, text, encoder=encoder)
        if text is not None
        else settle_internal(world, observation or {})
    )
    if canonical_bytes(expected.canonical()) != canonical_bytes(settlement.canonical()):
        raise SemanticRefusal(
            SemanticRefusalCode.INTEGRITY_FAILURE,
            "semantic settlement differs from independent reconstruction",
            {},
        )


def forged_trace(settlement: SemanticSettlement, trace: dict[str, Any]) -> SemanticSettlement:
    """Test helper that preserves the original hash around altered evidence."""
    return replace(settlement, trace=trace)
