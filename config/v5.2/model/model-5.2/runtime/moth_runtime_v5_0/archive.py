"""Content-addressed, encoder-free World archives."""

from __future__ import annotations

import math
import struct
from typing import Any

from .canonical import (
    canonical_bytes, digest, meaning_id, normalize_text, sha256_bytes,
)
from .model import (
    CompiledWorld, IntegrityError, Meaning, MeaningType, Provenance, SemanticEdge,
    Source, VectorRecord, WorldRole,
)

ARCHIVE_SCHEMA = "proof-energy-world-archive/5.0"
_ARCHIVE_KEYS = {
    "schema", "world_role", "capability_level", "world_hash", "compiler_hash",
    "encoder_hash", "generation_id", "parent_generation_id", "sources",
    "meanings", "names", "aliases", "edges", "vectors", "archive_hash",
}
_UNGROUNDED = {
    MeaningType.ALIAS, MeaningType.RELATION_FORM, MeaningType.PROGRAM_STEP,
    MeaningType.CODE_SPAN,
}


def _owner(value: dict[str, Any]) -> Provenance:
    if not isinstance(value, dict) or set(value) != {
        "source_id", "source_sha256", "statement_sha256", "char_start",
        "char_end", "byte_start", "byte_end", "line", "column",
        "compiler_version",
    }:
        raise IntegrityError("World archive provenance shape is invalid")
    return Provenance(**value)


def world_to_archive(
    field: CompiledWorld, *, parent_generation_id: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema": ARCHIVE_SCHEMA,
        "world_role": field.world_role.value,
        "capability_level": field.capability_level,
        "world_hash": field.world_hash,
        "compiler_hash": field.compiler_hash,
        "encoder_hash": field.encoder_hash,
        "generation_id": field.generation_id,
        "parent_generation_id": parent_generation_id,
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
    payload["archive_hash"] = digest("moth-world-archive/5.0", payload)
    return payload


def archive_bytes(
    field: CompiledWorld, *, parent_generation_id: str | None = None,
) -> bytes:
    return canonical_bytes(
        world_to_archive(field, parent_generation_id=parent_generation_id)
    )


def _verify_source(key: str, source: Source) -> None:
    if key != source.source_id or not source.source_id:
        raise IntegrityError("World archive source identity mismatch")
    if source.sha256 != sha256_bytes(source.text.encode("utf-8")):
        raise IntegrityError("World archive source hash mismatch")


def _verify_owner(owner: Provenance, sources: dict[str, Source]) -> None:
    source = sources.get(owner.source_id)
    if source is None or owner.source_sha256 != source.sha256:
        raise IntegrityError("World archive provenance source is unavailable")
    if owner.compiler_version not in {"5.0.0", "5.0.0"}:
        raise IntegrityError("World archive provenance compiler is unsupported")
    if any(not isinstance(item, int) or isinstance(item, bool) for item in (
        owner.char_start, owner.char_end, owner.byte_start, owner.byte_end,
        owner.line, owner.column,
    )):
        raise IntegrityError("World archive provenance offsets are invalid")
    raw = source.text.encode("utf-8")
    if not (
        0 <= owner.char_start <= owner.char_end <= len(source.text)
        and 0 <= owner.byte_start <= owner.byte_end <= len(raw)
        and owner.line >= 1 and owner.column >= 1
    ):
        raise IntegrityError("World archive provenance span is invalid")
    try:
        if (
            len(raw[:owner.byte_start].decode("utf-8")) != owner.char_start
            or len(raw[:owner.byte_end].decode("utf-8")) != owner.char_end
        ):
            raise IntegrityError("World archive provenance byte/character spans disagree")
    except UnicodeDecodeError as exc:
        raise IntegrityError("World archive provenance splits a UTF-8 character") from exc
    expected_line = source.text.count("\n", 0, owner.char_start) + 1
    if expected_line != owner.line:
        raise IntegrityError("World archive provenance line is invalid")
    if owner.compiler_version == "5.0.0":
        line_start = source.text.rfind("\n", 0, owner.char_start) + 1
        expected_column = owner.char_start - line_start + 1
        span_hash = sha256_bytes(
            normalize_text(source.text[owner.char_start:owner.char_end]).encode("utf-8")
        )
    else:
        line_start = raw.rfind(b"\n", 0, owner.byte_start) + 1
        expected_column = owner.byte_start - line_start + 1
        span_hash = sha256_bytes(raw[owner.byte_start:owner.byte_end])
    if owner.column != expected_column or owner.statement_sha256 != span_hash:
        raise IntegrityError("World archive provenance span receipt mismatch")


def _verify_owners(
    owners: tuple[Provenance, ...], sources: dict[str, Source], *, label: str,
) -> None:
    if not owners or owners != tuple(sorted(set(owners))):
        raise IntegrityError(f"World archive {label} provenance is not canonical")
    for owner in owners:
        _verify_owner(owner, sources)


def _expected_names(meanings: dict[str, Meaning]) -> dict[str, dict[str, tuple[str, ...]]]:
    rows: dict[str, dict[str, list[str]]] = {}
    for identifier, item in sorted(meanings.items()):
        if item.kind == MeaningType.ALIAS:
            continue
        rows.setdefault(item.kind.value, {}).setdefault(item.name.casefold(), []).append(identifier)
    return {
        kind: {
            surface: tuple(sorted(set(identifiers)))
            for surface, identifiers in surfaces.items()
        }
        for kind, surfaces in rows.items()
    }


def _expected_aliases(meanings: dict[str, Meaning]) -> dict[str, dict[str, tuple[str, ...]]]:
    rows: dict[str, dict[str, list[str]]] = {}
    for item in meanings.values():
        if item.kind != MeaningType.ALIAS:
            continue
        try:
            kind = MeaningType(str(item.payload["kind"]))
            surface = str(item.payload["surface"])
            target_id = str(item.payload["target_id"])
        except (KeyError, TypeError, ValueError) as exc:
            raise IntegrityError("World archive alias payload is invalid") from exc
        target = meanings.get(target_id)
        if kind == MeaningType.ALIAS or target is None or target.kind != kind:
            raise IntegrityError("World archive alias target is invalid")
        rows.setdefault(kind.value, {}).setdefault(surface.casefold(), []).append(target_id)
    return {
        kind: {
            surface: tuple(sorted(set(identifiers)))
            for surface, identifiers in surfaces.items()
        }
        for kind, surfaces in rows.items()
    }


def _vector_bytes(values: tuple[float, ...]) -> bytes:
    try:
        return b"".join(struct.pack("<f", value) for value in values)
    except (OverflowError, struct.error) as exc:
        raise IntegrityError("World archive vector is outside float32") from exc


def _verify_vectors(field: CompiledWorld) -> None:
    expected_ids = {
        identifier for identifier, item in field.meanings.items()
        if item.kind not in _UNGROUNDED
    }
    if field.encoder_hash == "NO_ENCODER":
        if field.vectors:
            raise IntegrityError("World archive has vectors without an encoder")
        return
    if set(field.vectors) != expected_ids:
        raise IntegrityError("World archive vector membership mismatch")
    if not expected_ids:
        return
    dimensions: set[int] = set()
    for key, record in field.vectors.items():
        if key != record.meaning_id:
            raise IntegrityError("World archive vector key mismatch")
        expected_text = str(field.meanings[key].payload.get(
            "text", field.meanings[key].payload.get("template", field.meanings[key].name),
        ))
        if record.text != expected_text or not record.vector:
            raise IntegrityError("World archive vector text or dimension mismatch")
        if any(not isinstance(item, float) or not math.isfinite(item) for item in record.vector):
            raise IntegrityError("World archive vector contains an invalid number")
        raw = _vector_bytes(record.vector)
        unpacked = struct.unpack(f"<{len(record.vector)}f", raw)
        if record.vector != tuple(float(item) for item in unpacked):
            raise IntegrityError("World archive vector is not canonical float32")
        dimensions.add(len(record.vector))
        expected_hash = (
            sha256_bytes(raw)
            if field.encoder_hash == "DETERMINISTIC-TEST-ENCODER-64"
            else sha256_bytes(
                b"moth-world-vector/5.0\0" + field.encoder_hash.encode("utf-8") + raw
            )
        )
        if record.vector_hash != expected_hash:
            raise IntegrityError("World archive vector hash mismatch")
    if len(dimensions) != 1 or (
        field.encoder_hash == "DETERMINISTIC-TEST-ENCODER-64" and dimensions != {64}
    ):
        raise IntegrityError("World archive vector dimensions are inconsistent")


def _verify_world(field: CompiledWorld, parent_generation_id: str | None) -> None:
    if field.capability_level not in {f"L{index}" for index in range(10)}:
        raise IntegrityError("World archive capability level is invalid")
    for key, source in field.sources.items():
        _verify_source(key, source)
    if not field.sources:
        raise IntegrityError("World archive contains no compiled source")
    for key, item in field.meanings.items():
        if key != item.meaning_id or not isinstance(item.payload, dict):
            raise IntegrityError("World archive meaning key mismatch")
        if item.payload.get("name") != item.name:
            raise IntegrityError("World archive meaning name differs from its payload")
        if item.meaning_id != meaning_id(item.kind.value, item.payload):
            raise IntegrityError("World archive meaning identifier mismatch")
        _verify_owners(item.owners, field.sources, label="meaning")
    expected_names = _expected_names(field.meanings)
    expected_aliases = _expected_aliases(field.meanings)
    if field.names != expected_names or field.aliases != expected_aliases:
        raise IntegrityError("World archive name or alias index mismatch")

    edge_keys: list[tuple[str, str, str]] = []
    for edge in field.edges:
        relation = field.meanings.get(edge.relation_id)
        if relation is None or relation.kind != MeaningType.RELATION:
            raise IntegrityError("World archive edge relation is invalid")
        if edge.source_id not in field.meanings or edge.destination_id not in field.meanings:
            raise IntegrityError("World archive semantic closure failed")
        edge_payload = {
            "relation_id": edge.relation_id, "source_id": edge.source_id,
            "destination_id": edge.destination_id,
        }
        if edge.edge_id != digest("moth-world-edge/5.0", edge_payload):
            raise IntegrityError("World archive edge identifier mismatch")
        _verify_owners(edge.owners, field.sources, label="edge")
        edge_keys.append((edge.relation_id, edge.source_id, edge.destination_id))
    if edge_keys != sorted(set(edge_keys)):
        raise IntegrityError("World archive edge order or uniqueness is invalid")

    semantic = {
        "capability_level": field.capability_level,
        "meanings": {
            key: value.canonical(include_owners=False)
            for key, value in sorted(field.meanings.items())
        },
        "aliases": {
            kind: {
                surface: sorted(set(identifiers))
                for surface, identifiers in sorted(values.items())
            }
            for kind, values in sorted(field.aliases.items())
        },
        "edges": [{
            "edge_id": edge.edge_id, "relation_id": edge.relation_id,
            "source_id": edge.source_id, "destination_id": edge.destination_id,
        } for edge in field.edges],
    }
    if field.compiler_hash != digest("moth-world-compiler/5.0", semantic):
        raise IntegrityError("World archive compiler hash mismatch")
    _verify_vectors(field)
    world_payload = {
        "world_role": field.world_role.value,
        "compiler_hash": field.compiler_hash,
        "encoder_hash": field.encoder_hash,
        "vector_hashes": {
            key: value.vector_hash for key, value in sorted(field.vectors.items())
        },
        "parent": parent_generation_id,
        "sources": {
            key: value.sha256 for key, value in sorted(field.sources.items())
        },
    }
    if field.world_hash != digest("moth-compiled-world/5.0", world_payload):
        raise IntegrityError("World archive World hash mismatch")
    if field.generation_id != digest("moth-world-generation/5.0", world_payload):
        raise IntegrityError("World archive generation identifier mismatch")


def world_from_archive(value: dict[str, Any]) -> CompiledWorld:
    try:
        if not isinstance(value, dict) or set(value) != _ARCHIVE_KEYS:
            raise IntegrityError("World archive shape is invalid")
        if value.get("schema") != ARCHIVE_SCHEMA:
            raise IntegrityError("cross-runtime or incompatible World archive")
        expected = value.get("archive_hash")
        unhashed = {key: child for key, child in value.items() if key != "archive_hash"}
        if expected != digest("moth-world-archive/5.0", unhashed):
            raise IntegrityError("World archive hash mismatch")
        if not isinstance(value["sources"], dict):
            raise IntegrityError("World archive source table is invalid")
        sources: dict[str, Source] = {}
        for key, child in value["sources"].items():
            if not isinstance(child, dict) or set(child) != {"source_id", "text", "sha256"}:
                raise IntegrityError("World archive source shape is invalid")
            sources[str(key)] = Source(**child)
        if not isinstance(value["meanings"], dict):
            raise IntegrityError("World archive meaning table is invalid")
        meanings: dict[str, Meaning] = {}
        for key, child in value["meanings"].items():
            if not isinstance(child, dict) or set(child) != {
                "meaning_id", "kind", "name", "payload", "owners",
            } or not isinstance(child["owners"], list):
                raise IntegrityError("World archive meaning shape is invalid")
            meanings[str(key)] = Meaning(
                child["meaning_id"], MeaningType(child["kind"]), child["name"],
                child["payload"], tuple(_owner(owner) for owner in child["owners"]),
            )
        if not isinstance(value["edges"], list):
            raise IntegrityError("World archive edge table is invalid")
        edges_list: list[SemanticEdge] = []
        for child in value["edges"]:
            if not isinstance(child, dict) or set(child) != {
                "edge_id", "relation_id", "source_id", "destination_id", "owners",
            } or not isinstance(child["owners"], list):
                raise IntegrityError("World archive edge shape is invalid")
            edges_list.append(SemanticEdge(
                child["edge_id"], child["relation_id"], child["source_id"],
                child["destination_id"], tuple(_owner(owner) for owner in child["owners"]),
            ))
        if not isinstance(value["vectors"], dict):
            raise IntegrityError("World archive vector table is invalid")
        vectors: dict[str, VectorRecord] = {}
        for key, child in value["vectors"].items():
            if not isinstance(child, dict) or set(child) != {
                "meaning_id", "text", "vector_hash", "vector",
            } or not isinstance(child["vector"], list):
                raise IntegrityError("World archive vector shape is invalid")
            # Preserve JSON numeric types until canonical float32 validation.
            vectors[str(key)] = VectorRecord(
                child["meaning_id"], child["text"], child["vector_hash"],
                tuple(child["vector"]),
            )
        if not isinstance(value["names"], dict) or not isinstance(value["aliases"], dict):
            raise IntegrityError("World archive grounding index is invalid")
        names = {
            str(kind): {
                str(surface): tuple(ids) for surface, ids in rows.items()
            }
            for kind, rows in value["names"].items()
        }
        aliases = {
            str(kind): {
                str(surface): tuple(ids) for surface, ids in rows.items()
            }
            for kind, rows in value["aliases"].items()
        }
        field = CompiledWorld(
            sources, meanings, names, aliases, tuple(edges_list), vectors,
            value["world_hash"], value["compiler_hash"], value["encoder_hash"],
            value["generation_id"], value["capability_level"],
            WorldRole(value["world_role"]),
        )
        _verify_world(field, value["parent_generation_id"])
        return field
    except IntegrityError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError, UnicodeError) as exc:
        raise IntegrityError("World archive is malformed") from exc
