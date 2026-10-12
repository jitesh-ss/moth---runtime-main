"""Deterministic compiler for the isolated semantic-equivalence field."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from moth_runtime_v4_9.canonical import canonical_bytes, digest, normalize_text, sha256_bytes

from .model import (
    InternalTransform,
    LanguageFrame,
    SemanticCoordinate,
    SemanticEntity,
    SemanticMeaning,
    SemanticPredicate,
    SemanticWorld,
)

SCHEMA = "moth-semantic-equivalence-experiment/1.0"
FIXTURE = Path(__file__).resolve().parent / "fixtures/semantic-world-en-1.0.json"


def _required(value: dict[str, Any], names: tuple[str, ...], context: str) -> None:
    missing = [name for name in names if name not in value]
    if missing:
        raise ValueError(f"{context} lacks required fields: {', '.join(missing)}")


def _unique(rows: list[dict[str, Any]], field: str, context: str) -> None:
    values = [str(row[field]) for row in rows]
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate {context} {field}")


def compile_semantic_world(source: dict[str, Any]) -> SemanticWorld:
    if source.get("schema") != SCHEMA:
        raise ValueError("unsupported semantic-world fixture schema")
    entity_types = tuple(sorted({str(value) for value in source.get("entity_types", [])}))
    if not entity_types:
        raise ValueError("semantic world requires entity types")

    raw_entities = list(source.get("entities", []))
    raw_predicates = list(source.get("predicates", []))
    raw_meanings = list(source.get("meanings", []))
    raw_frames = list(source.get("language_frames", []))
    raw_transforms = list(source.get("internal_transforms", []))
    for rows, field, context in (
        (raw_entities, "key", "entity"),
        (raw_predicates, "key", "predicate"),
        (raw_meanings, "key", "meaning"),
        (raw_frames, "key", "frame"),
        (raw_transforms, "key", "transform"),
    ):
        _unique(rows, field, context)

    entities: list[SemanticEntity] = []
    surface_owners: dict[tuple[str, str], str] = {}
    for row in raw_entities:
        _required(row, ("key", "type", "canonical_name", "surfaces", "description"), "entity")
        key = str(row["key"])
        entity_type = str(row["type"])
        if entity_type not in entity_types:
            raise ValueError(f"entity {key} has unknown type {entity_type}")
        surfaces = tuple(sorted({normalize_text(str(value)).casefold() for value in row["surfaces"]}))
        canonical_name = normalize_text(str(row["canonical_name"]))
        if not surfaces or canonical_name.casefold() not in surfaces:
            raise ValueError(f"entity {key} surfaces must contain its canonical name")
        for surface in surfaces:
            owner = surface_owners.setdefault((entity_type, surface), key)
            if owner != key:
                raise ValueError(f"surface {surface!r} is ambiguous within type {entity_type}")
        payload = {
            "key": key,
            "entity_type": entity_type,
            "canonical_name": canonical_name,
            "surfaces": list(surfaces),
            "description": normalize_text(str(row["description"])),
        }
        entities.append(SemanticEntity(
            key=key,
            entity_id=digest("moth-semantic-entity/1.0", payload),
            entity_type=entity_type,
            canonical_name=canonical_name,
            surfaces=surfaces,
            description=payload["description"],
        ))
    entity_by_key = {item.key: item for item in entities}

    predicates: list[SemanticPredicate] = []
    for row in raw_predicates:
        _required(row, ("key", "subject_type", "object_type"), "predicate")
        key = str(row["key"])
        subject_type = str(row["subject_type"])
        object_type = str(row["object_type"])
        if subject_type not in entity_types or object_type not in entity_types:
            raise ValueError(f"predicate {key} refers to an unknown entity type")
        payload = {"key": key, "subject_type": subject_type, "object_type": object_type}
        predicates.append(SemanticPredicate(
            key=key,
            predicate_id=digest("moth-semantic-predicate/1.0", payload),
            subject_type=subject_type,
            object_type=object_type,
        ))
    predicate_by_key = {item.key: item for item in predicates}

    allowed_polarity = {"POSITIVE", "NEGATIVE"}
    allowed_modality = {"ASSERTED", "POSSIBLE", "REQUIRED"}
    allowed_time = {"PAST", "CURRENT", "FUTURE"}

    def coordinate(row: dict[str, Any]) -> SemanticCoordinate:
        _required(row, ("predicate", "subject", "object", "polarity", "modality", "time"), "coordinate")
        predicate = predicate_by_key.get(str(row["predicate"]))
        subject = entity_by_key.get(str(row["subject"]))
        object_ = entity_by_key.get(str(row["object"]))
        if predicate is None or subject is None or object_ is None:
            raise ValueError("semantic coordinate has an unresolved identifier")
        if subject.entity_type != predicate.subject_type or object_.entity_type != predicate.object_type:
            raise ValueError("semantic coordinate violates predicate role types")
        polarity = str(row["polarity"])
        modality = str(row["modality"])
        time = str(row["time"])
        if polarity not in allowed_polarity or modality not in allowed_modality or time not in allowed_time:
            raise ValueError("semantic coordinate has an unsupported dimension value")
        return SemanticCoordinate(predicate.key, subject.key, object_.key, polarity, modality, time)

    meanings: list[SemanticMeaning] = []
    coordinate_owners: dict[tuple[str, ...], str] = {}
    for row in raw_meanings:
        _required(row, ("key", "coordinate"), "meaning")
        semantic_coordinate = coordinate(dict(row["coordinate"]))
        owner = coordinate_owners.setdefault(semantic_coordinate.key(), str(row["key"]))
        if owner != str(row["key"]):
            raise ValueError("two named meanings have the same semantic coordinate")
        meanings.append(SemanticMeaning(
            key=str(row["key"]),
            meaning_id=digest("moth-semantic-meaning/1.0", semantic_coordinate.canonical()),
            coordinate=semantic_coordinate,
        ))

    frames: list[LanguageFrame] = []
    for row in raw_frames:
        _required(row, (
            "key", "pattern", "predicate", "subject_group", "object_group",
            "polarity", "modality", "time",
        ), "language frame")
        pattern = str(row["pattern"])
        try:
            compiled = re.compile(pattern, re.IGNORECASE)
        except re.error as exc:
            raise ValueError(f"invalid language frame {row['key']}") from exc
        subject_group = str(row["subject_group"])
        object_group = str(row["object_group"])
        if subject_group not in compiled.groupindex or object_group not in compiled.groupindex:
            raise ValueError(f"language frame {row['key']} lacks its declared role groups")
        if str(row["predicate"]) not in predicate_by_key:
            raise ValueError(f"language frame {row['key']} has an unknown predicate")
        frame_payload = {name: row[name] for name in (
            "key", "pattern", "predicate", "subject_group", "object_group",
            "polarity", "modality", "time",
        )}
        coordinate({
            "predicate": row["predicate"],
            "subject": next(item.key for item in entities if item.entity_type == predicate_by_key[str(row["predicate"])].subject_type),
            "object": next(item.key for item in entities if item.entity_type == predicate_by_key[str(row["predicate"])].object_type),
            "polarity": row["polarity"], "modality": row["modality"], "time": row["time"],
        })
        frames.append(LanguageFrame(
            key=str(row["key"]),
            frame_id=digest("moth-semantic-language-frame/1.0", frame_payload),
            pattern=pattern,
            predicate=str(row["predicate"]),
            subject_group=subject_group,
            object_group=object_group,
            polarity=str(row["polarity"]),
            modality=str(row["modality"]),
            time=str(row["time"]),
        ))

    transforms: list[InternalTransform] = []
    source_relations: set[str] = set()
    for row in raw_transforms:
        _required(row, (
            "key", "source_relation", "predicate", "subject_argument", "object_argument",
            "polarity", "modality", "time",
        ), "internal transform")
        relation = str(row["source_relation"])
        if relation in source_relations:
            raise ValueError(f"duplicate source relation {relation}")
        source_relations.add(relation)
        if str(row["predicate"]) not in predicate_by_key:
            raise ValueError(f"internal transform {row['key']} has an unknown predicate")
        payload = {name: str(row[name]) for name in (
            "key", "source_relation", "predicate", "subject_argument", "object_argument",
            "polarity", "modality", "time",
        )}
        transforms.append(InternalTransform(
            key=payload["key"],
            transform_id=digest("moth-semantic-internal-transform/1.0", payload),
            source_relation=relation,
            predicate=payload["predicate"],
            subject_argument=payload["subject_argument"],
            object_argument=payload["object_argument"],
            polarity=payload["polarity"],
            modality=payload["modality"],
            time=payload["time"],
        ))

    thresholds = {str(key): float(value) for key, value in source.get("thresholds", {}).items()}
    required_thresholds = {"entity_score", "entity_window", "meaning_margin"}
    if set(thresholds) != required_thresholds or any(not 0.0 <= value <= 1.0 for value in thresholds.values()):
        raise ValueError("semantic thresholds are incomplete or invalid")

    source_hash = sha256_bytes(canonical_bytes(source))
    provisional = SemanticWorld(
        schema=SCHEMA,
        source_hash=source_hash,
        world_hash="",
        entity_types=entity_types,
        entities=tuple(sorted(entities, key=lambda item: item.entity_id)),
        predicates=tuple(sorted(predicates, key=lambda item: item.predicate_id)),
        meanings=tuple(sorted(meanings, key=lambda item: item.meaning_id)),
        frames=tuple(sorted(frames, key=lambda item: item.frame_id)),
        transforms=tuple(sorted(transforms, key=lambda item: item.transform_id)),
        thresholds=thresholds,
    )
    world_hash = digest("moth-semantic-world/1.0", provisional.canonical())
    return SemanticWorld(**{**provisional.__dict__, "world_hash": world_hash})


def load_semantic_world(path: str | Path = FIXTURE) -> SemanticWorld:
    source = json.loads(Path(path).read_text(encoding="utf-8"))
    return compile_semantic_world(source)
