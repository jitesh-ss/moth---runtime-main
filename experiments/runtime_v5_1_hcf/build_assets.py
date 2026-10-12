"""Build a tiny deterministic, weight-free Runtime 5.1 foundation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from moth_runtime_v5_0.archive import world_to_archive
from moth_runtime_v5_0.canonical import canonical_bytes, sha256_bytes
from moth_runtime_v5_0.compiler import compile_sources
from moth_runtime_v5_0.encoder import DeterministicEncoder
from moth_runtime_v5_0.handoff import build_bundle
from moth_runtime_v5_0.model import WorldRole
from moth_runtime_v5_1.assets import load_foundation


ROOT = Path(__file__).resolve().parents[2]
LOOKUP = """\
Entity "Asterion" is declared.
Operation "lookup" selects kernel primitive "LOOKUP".
Instruction "lookup" selects operation "lookup" accepts "Find {ENTITY}.".
"""
SURFACE = """\
Operation "realize-semantic-result" selects kernel primitive "REALIZE_SEMANTIC_RESULT".
Instruction "realize-semantic-result" selects operation "realize-semantic-result" accepts "Realize the verified semantic result.".
"""


def _write(path: Path, value) -> bytes:
    raw = canonical_bytes(value)
    path.write_bytes(raw)
    return raw


def build_foundation(destination: str | Path) -> dict:
    target = Path(destination).resolve()
    target.mkdir(parents=True, exist_ok=True)
    encoder = DeterministicEncoder()
    worlds = {
        WorldRole.INPUT: compile_sources(
            {"lookup.moth": LOOKUP}, encoder=encoder, world_role=WorldRole.INPUT,
        ),
        WorldRole.MAIN: compile_sources(
            {"lookup.moth": LOOKUP}, encoder=encoder, world_role=WorldRole.MAIN,
        ),
        WorldRole.SURFACE: compile_sources(
            {"surface.moth": SURFACE}, encoder=encoder, world_role=WorldRole.SURFACE,
        ),
    }
    bundle = build_bundle(worlds)
    descriptors = {}
    for role, world in worlds.items():
        filename = f"{role.value.casefold()}-world.json"
        raw = _write(target / filename, world_to_archive(world))
        descriptors[role.value] = {
            "path": filename, "sha256": sha256_bytes(raw),
            "generation_id": world.generation_id, "world_hash": world.world_hash,
        }
    base = json.loads((ROOT / "config/v5.1/base-hcf-en-1.0.json").read_text())
    base_raw = _write(target / "base-hcf.json", base)
    manifest = {
        "schema": "moth-runtime-foundation/5.1", "runtime": "5.1",
        "hcf_schema": "moth-hcf-field/5.1",
        "base_fields": [{
            "field_id": base["field_id"], "path": "base-hcf.json",
            "sha256": sha256_bytes(base_raw),
        }],
        "compiled_worlds": descriptors,
        "encoder": {"kind": "DETERMINISTIC", "fingerprint": encoder.fingerprint,
                    "thresholds": {}},
        "context": {"max_message_tokens": 128, "active_context_tokens": 4096},
        "surface": {"modes": ["concise", "detailed", "structured"]},
    }
    _write(target / "runtime-foundation.json", manifest)
    foundation = load_foundation(target)
    return {
        "foundation": str(target), "foundation_id": foundation.foundation_id,
        "foundation_hash": foundation.foundation_hash,
        "bundle_id": bundle.bundle_id,
        "manifest": str(target / "runtime-foundation.json"),
    }


# Compatibility alias for existing local scripts.
build_assets = build_foundation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination")
    args = parser.parse_args(argv)
    print(json.dumps(build_foundation(args.destination), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
