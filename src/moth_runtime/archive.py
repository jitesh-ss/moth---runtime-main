"""Content-addressed, encoder-free field archives."""

from __future__ import annotations

from typing import Any

from .canonical import canonical_bytes, digest
from .model import (
    CompiledField, IntegrityError, Meaning, MeaningType, Provenance, SemanticEdge,
    Source, VectorRecord,
)

ARCHIVE_SCHEMA = "proof-energy-capability-archive/4.7"


def _owner(value: dict[str, Any]) -> Provenance:
    return Provenance(**value)


def field_to_archive(field: CompiledField) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema": ARCHIVE_SCHEMA,
        "capability_level": field.capability_level,
        "field_hash": field.field_hash,
        "compiler_hash": field.compiler_hash,
        "encoder_hash": field.encoder_hash,
        "generation_id": field.generation_id,
        "sources": {
            key: {"source_id": value.source_id, "text": value.text, "sha256": value.sha256}
            for key, value in sorted(field.sources.items())
        },
        "meanings": {
            key: value.canonical() for key, value in sorted(field.meanings.items())
        },
        "names": field.names,
        "aliases": field.aliases,
        "edges": [edge.canonical() for edge in field.edges],
        "vectors": {
            key: {
                "meaning_id": value.meaning_id, "text": value.text,
                "vector_hash": value.vector_hash, "vector": list(value.vector),
            } for key, value in sorted(field.vectors.items())
        },
    }
    payload["archive_hash"] = digest("moth-capability-archive/4.7", payload)
    return payload


def archive_bytes(field: CompiledField) -> bytes:
    return canonical_bytes(field_to_archive(field))


def field_from_archive(value: dict[str, Any]) -> CompiledField:
    if value.get("schema") != ARCHIVE_SCHEMA:
        raise IntegrityError("cross-runtime or incompatible field archive")
    expected = value.get("archive_hash")
    unhashed = {key: child for key, child in value.items() if key != "archive_hash"}
    if expected != digest("moth-capability-archive/4.7", unhashed):
        raise IntegrityError("field archive hash mismatch")
    sources = {key: Source(**child) for key, child in value["sources"].items()}
    meanings = {
        key: Meaning(
            child["meaning_id"], MeaningType(child["kind"]), child["name"], child["payload"],
            tuple(_owner(owner) for owner in child["owners"]),
        ) for key, child in value["meanings"].items()
    }
    edges = tuple(SemanticEdge(
        child["edge_id"], child["relation_id"], child["source_id"], child["destination_id"],
        tuple(_owner(owner) for owner in child["owners"]),
    ) for child in value["edges"])
    vectors = {key: VectorRecord(
        child["meaning_id"], child["text"], child["vector_hash"],
        tuple(float(number) for number in child["vector"]),
    ) for key, child in value["vectors"].items()}
    field = CompiledField(
        sources, meanings,
        {kind: {surface: tuple(ids) for surface, ids in rows.items()}
         for kind, rows in value["names"].items()},
        {kind: {surface: tuple(ids) for surface, ids in rows.items()}
         for kind, rows in value["aliases"].items()},
        edges, vectors, value["field_hash"], value["compiler_hash"], value["encoder_hash"],
        value["generation_id"], value["capability_level"],
    )
    # Identifier closure is checked before any replay or query can use the archive.
    if any(edge.relation_id not in meanings or edge.source_id not in meanings or
           edge.destination_id not in meanings or not edge.owners for edge in edges):
        raise IntegrityError("field archive semantic closure failed")
    if any(key != item.meaning_id for key, item in meanings.items()):
        raise IntegrityError("field archive meaning key mismatch")
    return field

