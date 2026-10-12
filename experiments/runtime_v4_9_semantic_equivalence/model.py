"""Immutable contracts for the isolated semantic-equivalence experiment."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class SemanticRefusalCode(StrEnum):
    UNSUPPORTED_LANGUAGE = "UNSUPPORTED_LANGUAGE"
    UNSUPPORTED_MEANING = "UNSUPPORTED_MEANING"
    UNKNOWN_ENTITY = "UNKNOWN_ENTITY"
    AMBIGUOUS_SEMANTICS = "AMBIGUOUS_SEMANTICS"
    TYPE_MISMATCH = "TYPE_MISMATCH"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"


@dataclass(frozen=True)
class SemanticRefusal(ValueError):
    code: SemanticRefusalCode
    message: str
    context: dict[str, Any]

    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"


@dataclass(frozen=True)
class SemanticEntity:
    key: str
    entity_id: str
    entity_type: str
    canonical_name: str
    surfaces: tuple[str, ...]
    description: str

    def canonical(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "canonical_name": self.canonical_name,
            "surfaces": list(self.surfaces),
            "description": self.description,
        }


@dataclass(frozen=True)
class SemanticPredicate:
    key: str
    predicate_id: str
    subject_type: str
    object_type: str

    def canonical(self) -> dict[str, str]:
        return {
            "key": self.key,
            "predicate_id": self.predicate_id,
            "subject_type": self.subject_type,
            "object_type": self.object_type,
        }


@dataclass(frozen=True)
class SemanticCoordinate:
    predicate: str
    subject: str
    object: str
    polarity: str
    modality: str
    time: str

    def canonical(self) -> dict[str, str]:
        return {
            "predicate": self.predicate,
            "subject": self.subject,
            "object": self.object,
            "polarity": self.polarity,
            "modality": self.modality,
            "time": self.time,
        }

    def key(self) -> tuple[str, ...]:
        value = self.canonical()
        return tuple(value[name] for name in (
            "predicate", "subject", "object", "polarity", "modality", "time"
        ))


@dataclass(frozen=True)
class SemanticMeaning:
    key: str
    meaning_id: str
    coordinate: SemanticCoordinate

    def canonical(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "meaning_id": self.meaning_id,
            "coordinate": self.coordinate.canonical(),
        }


@dataclass(frozen=True)
class LanguageFrame:
    key: str
    frame_id: str
    pattern: str
    predicate: str
    subject_group: str
    object_group: str
    polarity: str
    modality: str
    time: str

    def canonical(self) -> dict[str, str]:
        return {
            "key": self.key,
            "frame_id": self.frame_id,
            "pattern": self.pattern,
            "predicate": self.predicate,
            "subject_group": self.subject_group,
            "object_group": self.object_group,
            "polarity": self.polarity,
            "modality": self.modality,
            "time": self.time,
        }


@dataclass(frozen=True)
class InternalTransform:
    key: str
    transform_id: str
    source_relation: str
    predicate: str
    subject_argument: str
    object_argument: str
    polarity: str
    modality: str
    time: str

    def canonical(self) -> dict[str, str]:
        return {
            "key": self.key,
            "transform_id": self.transform_id,
            "source_relation": self.source_relation,
            "predicate": self.predicate,
            "subject_argument": self.subject_argument,
            "object_argument": self.object_argument,
            "polarity": self.polarity,
            "modality": self.modality,
            "time": self.time,
        }


@dataclass(frozen=True)
class SemanticWorld:
    schema: str
    source_hash: str
    world_hash: str
    entity_types: tuple[str, ...]
    entities: tuple[SemanticEntity, ...]
    predicates: tuple[SemanticPredicate, ...]
    meanings: tuple[SemanticMeaning, ...]
    frames: tuple[LanguageFrame, ...]
    transforms: tuple[InternalTransform, ...]
    thresholds: dict[str, float]

    def canonical(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "source_hash": self.source_hash,
            "entity_types": list(self.entity_types),
            "entities": [item.canonical() for item in self.entities],
            "predicates": [item.canonical() for item in self.predicates],
            "meanings": [item.canonical() for item in self.meanings],
            "frames": [item.canonical() for item in self.frames],
            "transforms": [item.canonical() for item in self.transforms],
            "thresholds": dict(sorted(self.thresholds.items())),
        }


@dataclass(frozen=True)
class SemanticSettlement:
    schema: str
    world_hash: str
    input_kind: str
    input_hash: str
    meaning_id: str
    coordinate: SemanticCoordinate
    total_energy_units: int
    trace: dict[str, Any]
    trace_hash: str

    def canonical(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "world_hash": self.world_hash,
            "input_kind": self.input_kind,
            "input_hash": self.input_hash,
            "meaning_id": self.meaning_id,
            "coordinate": self.coordinate.canonical(),
            "total_energy_units": self.total_energy_units,
            "trace": self.trace,
            "trace_hash": self.trace_hash,
        }
