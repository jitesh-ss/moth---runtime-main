"""Immutable foundation loading for Runtime 5.1.

A foundation attaches one or more BASE HCF fields and exactly one compiled
Input, Main, and Surface World to a Runtime 5.1 store. It deliberately has no
weight-file concept: learned weights belong to a later model-artifact layer.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from moth_runtime_v5_0.archive import world_from_archive
from moth_runtime_v5_0.canonical import canonical_bytes, digest, sha256_bytes
from moth_runtime_v5_0.encoder import DeterministicEncoder, LocalBGEEncoder
from moth_runtime_v5_0.handoff import build_bundle, verify_bundle
from moth_runtime_v5_0.model import CompiledWorld, IntegrityError, WorldBundle, WorldRole

from .hcf import HcfEntry, compile_base_field, validate_entries


FOUNDATION_SCHEMA = "moth-runtime-foundation/5.1"
FOUNDATION_FILENAME = "runtime-foundation.json"


@dataclass(frozen=True)
class BaseFieldAttachment:
    field_id: str
    path: str
    file_hash: str
    entries: tuple[HcfEntry, ...]

    def receipt(self) -> dict[str, Any]:
        return {
            "field_id": self.field_id,
            "path": self.path,
            "sha256": self.file_hash,
            "entry_hashes": [entry.entry_hash for entry in self.entries],
        }


@dataclass(frozen=True)
class RuntimeFoundation:
    root: Path
    manifest: dict[str, Any]
    manifest_hash: str
    foundation_id: str
    foundation_hash: str
    base_fields: tuple[BaseFieldAttachment, ...]
    base_entries: tuple[HcfEntry, ...]
    worlds: dict[WorldRole, CompiledWorld]
    bundle: WorldBundle
    encoder: Any
    thresholds: dict[str, dict[str, float]]
    max_message_tokens: int
    active_context_tokens: int
    surface_modes: tuple[str, ...]

    @property
    def base_field_hashes(self) -> tuple[str, ...]:
        return tuple(field.file_hash for field in self.base_fields)

    def receipt(self) -> dict[str, Any]:
        return {
            "schema": FOUNDATION_SCHEMA,
            "foundation_id": self.foundation_id,
            "foundation_hash": self.foundation_hash,
            "manifest_hash": self.manifest_hash,
            "root": str(self.root),
            "base_fields": [field.receipt() for field in self.base_fields],
            "compiled_worlds": {
                role.value: {
                    "generation_id": world.generation_id,
                    "world_hash": world.world_hash,
                }
                for role, world in sorted(self.worlds.items(), key=lambda item: item[0].value)
            },
            "bundle_id": self.bundle.bundle_id,
            "bundle_hash": self.bundle.bundle_hash,
            "encoder_fingerprint": self.encoder.fingerprint,
        }


# Compatibility name for callers written against the first 5.1 draft.
RuntimeAssets = RuntimeFoundation


def _load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IntegrityError(f"invalid Runtime 5.1 foundation JSON: {path.name}") from exc
    if not isinstance(value, dict):
        raise IntegrityError(f"Runtime 5.1 foundation member must be an object: {path.name}")
    return value, raw


def _child(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise IntegrityError("Runtime 5.1 foundation path escapes its root") from exc
    if not candidate.is_file():
        raise IntegrityError(f"Runtime 5.1 foundation member is missing: {relative}")
    return candidate


def _verified_file(root: Path, descriptor: dict[str, Any]) -> tuple[Path, bytes]:
    if not isinstance(descriptor, dict) or not {"path", "sha256"} <= set(descriptor):
        raise IntegrityError("Runtime 5.1 foundation descriptor is incomplete")
    path = _child(root, str(descriptor["path"]))
    raw = path.read_bytes()
    if sha256_bytes(raw) != descriptor["sha256"]:
        raise IntegrityError(f"Runtime 5.1 foundation hash mismatch: {descriptor['path']}")
    return path, raw


def _foundation_identity(
    base_fields: tuple[BaseFieldAttachment, ...],
    worlds: dict[WorldRole, CompiledWorld],
    bundle: WorldBundle,
    encoder_fingerprint: str,
) -> tuple[str, str]:
    body = {
        "base_fields": [{
            "field_id": field.field_id,
            "sha256": field.file_hash,
            "entry_hashes": [entry.entry_hash for entry in field.entries],
        } for field in sorted(base_fields, key=lambda item: item.field_id)],
        "compiled_worlds": {
            role.value: {
                "generation_id": worlds[role].generation_id,
                "world_hash": worlds[role].world_hash,
            }
            for role in WorldRole
        },
        "bundle_id": bundle.bundle_id,
        "bundle_hash": bundle.bundle_hash,
        "encoder_fingerprint": encoder_fingerprint,
    }
    foundation_hash = digest("moth-runtime-foundation-content/5.1", body)
    foundation_id = f"foundation-{foundation_hash[:24]}"
    return foundation_id, foundation_hash


def load_foundation(path: str | Path) -> RuntimeFoundation:
    root = Path(path).resolve()
    manifest_path = _child(root, FOUNDATION_FILENAME)
    manifest, _ = _load_json(manifest_path)
    required = {
        "schema", "runtime", "hcf_schema", "base_fields", "compiled_worlds",
        "encoder", "context", "surface",
    }
    if set(manifest) != required or manifest.get("schema") != FOUNDATION_SCHEMA:
        raise IntegrityError("Runtime 5.1 foundation manifest schema is invalid")
    if manifest.get("runtime") != "5.1" or manifest.get("hcf_schema") != "moth-hcf-field/5.1":
        raise IntegrityError("Runtime 5.1 foundation compatibility mismatch")

    field_descriptors = manifest["base_fields"]
    if not isinstance(field_descriptors, list) or not field_descriptors:
        raise IntegrityError("Runtime 5.1 foundation requires at least one base field")
    fields: list[BaseFieldAttachment] = []
    seen_field_ids: set[str] = set()
    for descriptor in field_descriptors:
        if not isinstance(descriptor, dict) or set(descriptor) != {"field_id", "path", "sha256"}:
            raise IntegrityError("Runtime 5.1 base-field descriptor is invalid")
        field_id = str(descriptor["field_id"])
        if not field_id or field_id in seen_field_ids:
            raise IntegrityError("Runtime 5.1 base-field identity is empty or duplicated")
        base_path, base_raw = _verified_file(root, descriptor)
        base_value, _ = _load_json(base_path)
        if base_value.get("field_id") != field_id:
            raise IntegrityError("Runtime 5.1 base-field identity mismatch")
        base_hash = sha256_bytes(base_raw)
        entries = compile_base_field(base_value, source_hash=base_hash)
        fields.append(BaseFieldAttachment(field_id, str(descriptor["path"]), base_hash, entries))
        seen_field_ids.add(field_id)
    base_fields = tuple(fields)
    base_entries = validate_entries(entry for field in base_fields for entry in field.entries)

    world_descriptors = manifest.get("compiled_worlds")
    if not isinstance(world_descriptors, dict) or set(world_descriptors) != {
        role.value for role in WorldRole
    }:
        raise IntegrityError("Runtime 5.1 foundation requires fixed INPUT, MAIN, and SURFACE Worlds")
    worlds: dict[WorldRole, CompiledWorld] = {}
    for role in WorldRole:
        descriptor = world_descriptors[role.value]
        if not isinstance(descriptor, dict) or set(descriptor) != {
            "path", "sha256", "generation_id", "world_hash",
        }:
            raise IntegrityError("Runtime 5.1 compiled World descriptor is invalid")
        archive_path, _ = _verified_file(root, descriptor)
        archive, _ = _load_json(archive_path)
        world = world_from_archive(archive)
        if world.world_role != role:
            raise IntegrityError("Runtime 5.1 compiled World role mismatch")
        if descriptor.get("generation_id") != world.generation_id:
            raise IntegrityError("Runtime 5.1 compiled World generation identity mismatch")
        if descriptor.get("world_hash") != world.world_hash:
            raise IntegrityError("Runtime 5.1 compiled World hash mismatch")
        worlds[role] = world
    bundle = build_bundle(worlds)
    verify_bundle(bundle, worlds)

    encoder_descriptor = manifest["encoder"]
    if not isinstance(encoder_descriptor, dict) or set(encoder_descriptor) != {
        "kind", "fingerprint", "thresholds",
    }:
        raise IntegrityError("Runtime 5.1 encoder descriptor is invalid")
    kind = encoder_descriptor.get("kind")
    if kind == "DETERMINISTIC":
        encoder = DeterministicEncoder()
    elif kind == "LOCAL_BGE":
        encoder = LocalBGEEncoder()
    else:
        raise IntegrityError("Runtime 5.1 encoder kind is unsupported")
    expected_fingerprint = encoder_descriptor.get("fingerprint")
    if expected_fingerprint != getattr(encoder, "fingerprint", None):
        raise IntegrityError("Runtime 5.1 encoder fingerprint mismatch")
    if any(world.encoder_hash != expected_fingerprint for world in worlds.values()):
        raise IntegrityError("Runtime 5.1 compiled World encoder identity mismatch")
    thresholds = encoder_descriptor.get("thresholds", {})
    if not isinstance(thresholds, dict):
        raise IntegrityError("Runtime 5.1 grounding thresholds are invalid")

    context = manifest["context"]
    if not isinstance(context, dict) or set(context) != {
        "max_message_tokens", "active_context_tokens",
    }:
        raise IntegrityError("Runtime 5.1 context limits are invalid")
    max_message_tokens = context["max_message_tokens"]
    active_context_tokens = context["active_context_tokens"]
    if (
        not isinstance(max_message_tokens, int) or not isinstance(active_context_tokens, int)
        or max_message_tokens < 1 or active_context_tokens < max_message_tokens
    ):
        raise IntegrityError("Runtime 5.1 context limits are outside the valid range")

    surface = manifest["surface"]
    if not isinstance(surface, dict) or set(surface) != {"modes"}:
        raise IntegrityError("Runtime 5.1 Surface configuration is invalid")
    modes = tuple(surface["modes"])
    if not modes or len(set(modes)) != len(modes) or set(modes) - {
        "concise", "detailed", "structured",
    }:
        raise IntegrityError("Runtime 5.1 Surface modes are invalid")

    foundation_id, foundation_hash = _foundation_identity(
        base_fields, worlds, bundle, expected_fingerprint,
    )
    return RuntimeFoundation(
        root=root, manifest=manifest,
        manifest_hash=sha256_bytes(canonical_bytes(manifest)),
        foundation_id=foundation_id, foundation_hash=foundation_hash,
        base_fields=base_fields, base_entries=base_entries,
        worlds=worlds, bundle=bundle, encoder=encoder, thresholds=thresholds,
        max_message_tokens=max_message_tokens,
        active_context_tokens=active_context_tokens, surface_modes=modes,
    )


# Compatibility function for the first 5.1 draft. It now loads foundations.
load_assets = load_foundation
