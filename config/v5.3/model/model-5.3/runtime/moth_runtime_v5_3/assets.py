"""Frozen Runtime 5.0 kernel foundation loading for Runtime 5.3."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from moth_runtime_v5_3.legacy.archive import world_from_archive
from moth_runtime_v5_3.legacy.canonical import canonical_bytes, digest, sha256_bytes
from moth_runtime_v5_3.legacy.encoder import DeterministicEncoder, LocalBGEEncoder
from moth_runtime_v5_3.legacy.handoff import build_bundle, verify_bundle
from moth_runtime_v5_3.legacy.model import (
    CompiledWorld,
    IntegrityError,
    WorldBundle,
    WorldRole,
)


FOUNDATION_SCHEMA = "moth-kernel-foundation/5.3"
FOUNDATION_FILENAME = "kernel-foundation.json"


@dataclass(frozen=True)
class RuntimeFoundation:
    root: Path
    manifest: dict[str, Any]
    manifest_hash: str
    foundation_id: str
    foundation_hash: str
    worlds: dict[WorldRole, CompiledWorld]
    bundle: WorldBundle
    encoder: Any
    thresholds: dict[str, dict[str, float]]
    max_message_tokens: int
    active_context_tokens: int
    surface_modes: tuple[str, ...]

    def receipt(self) -> dict[str, Any]:
        return {
            "schema": FOUNDATION_SCHEMA,
            "foundation_id": self.foundation_id,
            "foundation_hash": self.foundation_hash,
            "manifest_hash": self.manifest_hash,
            "compiled_worlds": {
                role.value: {
                    "generation_id": world.generation_id,
                    "world_hash": world.world_hash,
                }
                for role, world in sorted(
                    self.worlds.items(), key=lambda item: item[0].value
                )
            },
            "bundle_id": self.bundle.bundle_id,
            "bundle_hash": self.bundle.bundle_hash,
            "encoder_fingerprint": self.encoder.fingerprint,
        }


RuntimeAssets = RuntimeFoundation


def _load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IntegrityError(
            f"invalid Runtime 5.3 kernel foundation JSON: {path.name}"
        ) from exc
    if not isinstance(value, dict):
        raise IntegrityError(
            f"Runtime 5.3 foundation member must be an object: {path.name}"
        )
    return value, raw


def _child(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise IntegrityError(
            "Runtime 5.3 foundation path escapes its root"
        ) from exc
    if not candidate.is_file():
        raise IntegrityError(
            f"Runtime 5.3 foundation member is missing: {relative}"
        )
    return candidate


def _verified_file(
    root: Path, descriptor: dict[str, Any]
) -> tuple[Path, bytes]:
    if not isinstance(descriptor, dict) or not {
        "path",
        "sha256",
    } <= set(descriptor):
        raise IntegrityError(
            "Runtime 5.3 foundation descriptor is incomplete"
        )
    path = _child(root, str(descriptor["path"]))
    raw = path.read_bytes()
    if sha256_bytes(raw) != descriptor["sha256"]:
        raise IntegrityError(
            f"Runtime 5.3 foundation hash mismatch: {descriptor['path']}"
        )
    return path, raw


def load_foundation(path: str | Path) -> RuntimeFoundation:
    root = Path(path).resolve()
    manifest, raw_manifest = _load_json(
        _child(root, FOUNDATION_FILENAME)
    )
    required = {
        "schema",
        "runtime",
        "kernel_runtime",
        "compiled_worlds",
        "encoder",
        "context",
        "surface",
    }
    if set(manifest) != required or manifest.get("schema") != FOUNDATION_SCHEMA:
        raise IntegrityError(
            "Runtime 5.3 kernel foundation schema is invalid"
        )
    if (
        manifest.get("runtime") != "5.3"
        or manifest.get("kernel_runtime") != "5.0"
    ):
        raise IntegrityError(
            "Runtime 5.3 kernel foundation compatibility mismatch"
        )

    descriptors = manifest["compiled_worlds"]
    if not isinstance(descriptors, dict) or set(descriptors) != {
        role.value for role in WorldRole
    }:
        raise IntegrityError(
            "Runtime 5.3 requires fixed INPUT, MAIN, and SURFACE Worlds"
        )
    worlds: dict[WorldRole, CompiledWorld] = {}
    for role in WorldRole:
        descriptor = descriptors[role.value]
        if not isinstance(descriptor, dict) or set(descriptor) != {
            "path",
            "sha256",
            "generation_id",
            "world_hash",
        }:
            raise IntegrityError(
                "Runtime 5.3 compiled World descriptor is invalid"
            )
        archive_path, archive_raw = _verified_file(root, descriptor)
        try:
            archive = json.loads(archive_raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise IntegrityError(
                f"invalid Runtime 5.3 kernel foundation JSON: {archive_path.name}"
            ) from exc
        if not isinstance(archive, dict):
            raise IntegrityError(
                f"Runtime 5.3 foundation member must be an object: {archive_path.name}"
            )
        del archive_raw
        world = world_from_archive(archive)
        if (
            world.world_role != role
            or world.generation_id != descriptor["generation_id"]
            or world.world_hash != descriptor["world_hash"]
        ):
            raise IntegrityError(
                "Runtime 5.3 compiled World binding changed"
            )
        worlds[role] = world
    bundle = build_bundle(worlds)
    verify_bundle(bundle, worlds)

    encoder_descriptor = manifest["encoder"]
    if not isinstance(encoder_descriptor, dict) or set(
        encoder_descriptor
    ) != {"kind", "fingerprint", "thresholds"}:
        raise IntegrityError(
            "Runtime 5.3 encoder descriptor is invalid"
        )
    kind = encoder_descriptor["kind"]
    if kind == "DETERMINISTIC":
        encoder = DeterministicEncoder()
    elif kind == "LOCAL_BGE":
        encoder = LocalBGEEncoder()
    else:
        raise IntegrityError(
            "Runtime 5.3 encoder kind is unsupported"
        )
    if encoder_descriptor["fingerprint"] != encoder.fingerprint or any(
        world.encoder_hash != encoder.fingerprint for world in worlds.values()
    ):
        raise IntegrityError(
            "Runtime 5.3 encoder identity changed"
        )
    thresholds = encoder_descriptor["thresholds"]
    if not isinstance(thresholds, dict):
        raise IntegrityError(
            "Runtime 5.3 grounding thresholds are invalid"
        )

    context = manifest["context"]
    if not isinstance(context, dict) or set(context) != {
        "max_message_tokens",
        "active_context_tokens",
    }:
        raise IntegrityError(
            "Runtime 5.3 context limits are invalid"
        )
    maximum = context["max_message_tokens"]
    active = context["active_context_tokens"]
    if (
        not isinstance(maximum, int)
        or not isinstance(active, int)
        or maximum < 1
        or active < maximum
    ):
        raise IntegrityError(
            "Runtime 5.3 context limits are outside the valid range"
        )
    surface = manifest["surface"]
    if not isinstance(surface, dict) or set(surface) != {"modes"}:
        raise IntegrityError(
            "Runtime 5.3 Surface configuration is invalid"
        )
    modes = tuple(str(value) for value in surface["modes"])
    if not modes or len(set(modes)) != len(modes):
        raise IntegrityError(
            "Runtime 5.3 Surface modes are invalid"
        )

    foundation_body = {
        "compiled_worlds": {
            role.value: {
                "generation_id": worlds[role].generation_id,
                "world_hash": worlds[role].world_hash,
            }
            for role in WorldRole
        },
        "bundle_id": bundle.bundle_id,
        "bundle_hash": bundle.bundle_hash,
        "encoder_fingerprint": encoder.fingerprint,
    }
    foundation_hash = digest(
        "moth-kernel-foundation-content/5.3", foundation_body
    )
    return RuntimeFoundation(
        root=root,
        manifest=manifest,
        manifest_hash=sha256_bytes(raw_manifest),
        foundation_id=f"kernel-foundation-{foundation_hash[:24]}",
        foundation_hash=foundation_hash,
        worlds=worlds,
        bundle=bundle,
        encoder=encoder,
        thresholds=thresholds,
        max_message_tokens=maximum,
        active_context_tokens=active,
        surface_modes=modes,
    )


load_assets = load_foundation
