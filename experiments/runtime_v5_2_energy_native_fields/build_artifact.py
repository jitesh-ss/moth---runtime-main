"""Build the deterministic, self-contained Runtime 5.2 tensor artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil

from moth_runtime_v5_0.archive import world_to_archive
from moth_runtime_v5_0.canonical import canonical_bytes, digest, sha256_bytes
from moth_runtime_v5_0.compiler import compile_sources
from moth_runtime_v5_0.encoder import DeterministicEncoder
from moth_runtime_v5_0.model import WorldRole
from moth_runtime_v5_2.artifact import ModelArtifact52
from moth_runtime_v5_2.assets import load_foundation
from moth_runtime_v5_2.compile.fields import compile_energy_foundation
from moth_runtime_v5_2.compile.skills import (
    compile_field_object,
    compile_skill_object,
)
from moth_runtime_v5_2.compiled_fields import (
    FieldKind,
    compile_field_archive,
    compile_skill_document,
    compose_skill_compilations,
    load_field_archive,
)
from moth_runtime_v5_2.persistence.objects import ObjectStore

from experiments.runtime_v5_0_compiled_surface_skill.worlds import (
    SURFACE_SOURCE,
    decision_source,
    semantic_source,
)


ROOT = Path(__file__).resolve().parents[2]

FIELD_SOURCES = (
    (
        FieldKind.INSTRUCTION,
        "bounded-agent-skill-en-1.0",
        ("SAFE_TEXT_PATCH", "EVIDENCE_LEDGER", "INERT_ACTION_PLAN"),
    ),
    (
        FieldKind.SURFACE_NATURAL,
        "bounded-natural-surface-en-1.0",
        ("NATURAL_RESPONSE",),
    ),
    (
        FieldKind.SURFACE_RICH,
        "runtime-v5-rich-output-surface-en-1.0",
        ("RICH_PROSE", "TONE", "MARKDOWN", "MIXED_RESPONSE"),
    ),
    (
        FieldKind.SURFACE_STRUCTURED,
        "bounded-json-python-surface-en-1.0",
        ("STRICT_JSON", "INERT_PYTHON_LITERAL"),
    ),
    (
        FieldKind.SURFACE_PYTHON,
        "bounded-python-function-surface-en-1.0",
        ("PYTHON_SOURCE",),
    ),
)

SKILL_SOURCES = (
    ("bounded-agent-skill-en-1.0", "safe-text-patch.md"),
    ("bounded-agent-skill-en-1.0", "evidence-ledger.md"),
    ("bounded-natural-surface-en-1.0", "natural-response.md"),
    ("runtime-v5-rich-output-surface-en-1.0", "prose-range.md"),
    ("runtime-v5-rich-output-surface-en-1.0", "tone-adaptation.md"),
    ("runtime-v5-rich-output-surface-en-1.0", "markdown-structure.md"),
    ("runtime-v5-rich-output-surface-en-1.0", "mixed-response.md"),
    ("bounded-json-python-surface-en-1.0", "structured-output.md"),
    (
        "bounded-python-function-surface-en-1.0",
        "python-function-output.md",
    ),
)


def _write_json(path: Path, value: object) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = canonical_bytes(value)
    path.write_bytes(raw)
    return raw


def _build_kernel_foundation(target: Path) -> None:
    encoder = DeterministicEncoder()
    worlds = {
        WorldRole.INPUT: compile_sources(
            {"input.moth": semantic_source("delivery", "deployment")},
            encoder=encoder,
            world_role=WorldRole.INPUT,
        ),
        WorldRole.MAIN: compile_sources(
            {"main.moth": decision_source()},
            encoder=encoder,
            world_role=WorldRole.MAIN,
        ),
        WorldRole.SURFACE: compile_sources(
            {"surface.moth": SURFACE_SOURCE},
            encoder=encoder,
            world_role=WorldRole.SURFACE,
        ),
    }
    descriptors = {}
    for role, world in worlds.items():
        relative = f"worlds/{role.value.casefold()}-world.json"
        raw = _write_json(target / relative, world_to_archive(world))
        descriptors[role.value] = {
            "path": relative,
            "sha256": sha256_bytes(raw),
            "generation_id": world.generation_id,
            "world_hash": world.world_hash,
        }
    manifest = {
        "schema": "moth-kernel-foundation/5.2",
        "runtime": "5.2",
        "kernel_runtime": "5.0",
        "compiled_worlds": descriptors,
        "encoder": {
            "kind": "DETERMINISTIC",
            "fingerprint": encoder.fingerprint,
            "thresholds": {},
        },
        "context": {
            "max_message_tokens": 128,
            "active_context_tokens": 4096,
        },
        "surface": {
            "modes": [
                "concise",
                "standard",
                "detailed",
                "compact_prose",
                "detailed_prose",
                "formal_tone",
                "conversational_tone",
                "markdown_bullets",
                "markdown_table",
                "explanation_json",
                "action_plan",
                "json_compact",
                "json_readable",
                "python_literal_compact",
                "python_literal_readable",
                "python_function",
            ]
        },
    }
    _write_json(target / "kernel-foundation.json", manifest)


def _copy_runtime(target: Path) -> dict:
    package_files: dict[str, str] = {}
    packages = (
        "moth_runtime_v5_0",
        "moth_runtime_v5_2",
    )
    for package in packages:
        source_root = ROOT / "src" / package
        for source in sorted(source_root.rglob("*.py")):
            relative = source.relative_to(ROOT / "src").as_posix()
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            package_files[relative] = sha256_bytes(destination.read_bytes())
    manifest = {
        "schema": "moth-runtime-package/5.2",
        "runtime": "5.2",
        "entrypoint": "moth_runtime_v5_2.cli:main",
        "packages": list(packages),
        "files": package_files,
    }
    _write_json(target / "runtime-package.json", manifest)
    return manifest


def _capability_modes(compilations: dict[str, dict]) -> list[dict]:
    def mode(
        name: str,
        profile: str,
        requests: list[str],
        cost: int,
    ) -> dict:
        compilation = compilations[profile]
        return {
            "mode": name,
            "field_id": compilation["field_id"],
            "compilation_id": compilation["compilation_id"],
            "requests": requests,
            "grounding_cost_units": cost,
        }

    return [
        mode(
            "concise",
            "NATURAL_RESPONSE",
            [
                "answer concisely",
                "give me the short version",
                "keep the answer brief",
            ],
            0,
        ),
        mode(
            "standard",
            "NATURAL_RESPONSE",
            ["", "use normal detail", "give a standard answer"],
            1,
        ),
        mode(
            "detailed",
            "NATURAL_RESPONSE",
            [
                "explain the result in detail",
                "give me a fuller explanation",
                "walk me through the decision",
            ],
            2,
        ),
        mode(
            "compact_prose",
            "PROSE_RANGE",
            ["compact natural prose", "return compact natural prose"],
            3,
        ),
        mode(
            "detailed_prose",
            "PROSE_RANGE",
            ["detailed explanation", "return a detailed explanation"],
            4,
        ),
        mode(
            "formal_tone",
            "TONE_ADAPTATION",
            ["formal professional tone", "use formal professional tone"],
            5,
        ),
        mode(
            "conversational_tone",
            "TONE_ADAPTATION",
            ["conversational explanation", "explain conversationally"],
            6,
        ),
        mode(
            "markdown_bullets",
            "MARKDOWN_STRUCTURE",
            ["markdown bullet list", "return a markdown bullet list"],
            7,
        ),
        mode(
            "markdown_table",
            "MARKDOWN_STRUCTURE",
            ["markdown table", "return a markdown table"],
            8,
        ),
        mode(
            "explanation_json",
            "MIXED_RESPONSE",
            ["explanation with json", "explain and include json"],
            9,
        ),
        mode(
            "action_plan",
            "MIXED_RESPONSE",
            ["action plan", "return an action plan"],
            10,
        ),
        mode(
            "json_compact",
            "STRUCTURED_OUTPUT",
            ["compact output", "single-line output", "return compact json"],
            11,
        ),
        mode(
            "json_readable",
            "STRUCTURED_OUTPUT",
            [
                "readable output",
                "multiline output",
                "return readable json",
            ],
            12,
        ),
        mode(
            "python_literal_compact",
            "STRUCTURED_OUTPUT",
            ["compact inert python literal", "return compact python"],
            13,
        ),
        mode(
            "python_literal_readable",
            "STRUCTURED_OUTPUT",
            ["readable inert python literal", "return readable python"],
            14,
        ),
        mode(
            "python_function",
            "PYTHON_FUNCTION_OUTPUT",
            [
                "actual python code",
                "compact function program",
                "readable function program",
                "return python with functions and variables",
                "return an actual python code block with functions and variables",
            ],
            15,
        ),
    ]


def build_artifact(destination: str | Path) -> dict:
    target = Path(destination).resolve()
    if target.exists() and any(target.iterdir()):
        raise RuntimeError("artifact destination must be empty")
    target.mkdir(parents=True, exist_ok=True)
    _build_kernel_foundation(target / "kernel-foundation")
    kernel = load_foundation(target / "kernel-foundation")
    package = _copy_runtime(target / "runtime")
    object_store = ObjectStore(target)

    fields = {}
    field_descriptors = []
    for kind, field_id, capabilities in FIELD_SOURCES:
        source_path = (
            ROOT / "config" / "v5.2" / "sources" / "fields"
            / field_id / "field.json"
        )
        source = json.loads(source_path.read_text(encoding="utf-8"))
        archive = compile_field_archive(source, kind, capabilities)
        field = load_field_archive(archive)
        compiled = compile_field_object(object_store, archive)
        fields[field_id] = field
        field_descriptors.append(
            {
                "field_id": field_id,
                "kind": kind.value,
                "field_hash": field.field_hash,
                "object_hash": compiled.envelope.file_hash,
                "logical_hash": compiled.envelope.logical_hash,
            }
        )

    by_profile: dict[str, dict] = {}
    for field_id, filename in SKILL_SOURCES:
        source_path = (
            ROOT / "config" / "v5.2" / "sources" / "skills"
            / field_id / filename
        )
        compilation = compile_skill_document(
            fields[field_id], source_path.read_text(encoding="utf-8")
        )
        by_profile[compilation["profile_id"]] = compilation
    composite = compose_skill_compilations(
        by_profile["SAFE_TEXT_PATCH"],
        by_profile["EVIDENCE_LEDGER"],
        fields["bounded-agent-skill-en-1.0"],
    )
    by_profile[composite["profile_id"]] = composite

    skill_descriptors = []
    for profile_id, compilation in sorted(by_profile.items()):
        compiled = compile_skill_object(object_store, compilation)
        skill_descriptors.append(
            {
                "compilation_id": compiled.compilation_id,
                "field_id": compiled.field_id,
                "profile_id": profile_id,
                "policy_hash": compiled.policy_hash,
                "object_hash": compiled.envelope.file_hash,
                "logical_hash": compiled.envelope.logical_hash,
            }
        )

    candidates = []
    for item in _capability_modes(by_profile):
        candidates.append(
            {
                "candidate_id": f"surface.{item['mode']}",
                "semantic": {
                    "response_mode": item["mode"],
                    "field_id": item["field_id"],
                    "compilation_id": item["compilation_id"],
                },
                "properties": {
                    "response.mode": item["mode"],
                    "surface.field_id": item["field_id"],
                    "surface.compilation_id": item["compilation_id"],
                    "runtime.network": False,
                    "runtime.tool_execution": False,
                    "runtime.world_management": False,
                },
                "field_id": item["field_id"],
                "skill_id": item["compilation_id"],
                "requests": item["requests"],
                "grounding_cost_units": item["grounding_cost_units"],
            }
        )
    base_source = json.loads(
        (
            ROOT / "config" / "v5.2" / "sources" / "base"
            / "base-hcf-en-1.0.json"
        ).read_text(encoding="utf-8")
    )
    energy = compile_energy_foundation(
        object_store, candidates, base_source
    )

    members = {
        path.relative_to(target).as_posix(): sha256_bytes(path.read_bytes())
        for path in sorted(target.rglob("*"))
        if path.is_file()
    }
    body = {
        "schema": "moth-model-artifact/5.2",
        "model_id": "moth-energy-native-model/5.2",
        "runtime": {
            "compatibility": "5.2",
            "kernel_compatibility": "5.0",
            "entrypoint": package["entrypoint"],
            "packages": package["packages"],
            "package_manifest": "runtime/runtime-package.json",
        },
        "kernel_foundation": {
            "path": "kernel-foundation",
            "manifest_hash": kernel.manifest_hash,
            "foundation_id": kernel.foundation_id,
            "foundation_hash": kernel.foundation_hash,
        },
        "energy_foundation": {
            "path": energy.path.relative_to(target).as_posix(),
            "file_hash": energy.file_hash,
            "logical_hash": energy.logical_hash,
        },
        "fields": sorted(
            field_descriptors, key=lambda item: item["field_id"]
        ),
        "skills": sorted(
            skill_descriptors, key=lambda item: item["compilation_id"]
        ),
        "members": members,
    }
    manifest = {
        **body,
        "artifact_hash": digest("moth-model-artifact/5.2", body),
    }
    _write_json(target / "model-artifact.json", manifest)
    return ModelArtifact52.open(target).verify()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination")
    args = parser.parse_args(argv)
    print(json.dumps(build_artifact(args.destination), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
