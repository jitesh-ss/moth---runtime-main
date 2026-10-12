"""Build the deterministic, self-contained, weight-free Model 5.1 image."""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import shutil

from moth_runtime_v5_0.archive import world_to_archive
from moth_runtime_v5_0.canonical import canonical_bytes, digest, sha256_bytes
from moth_runtime_v5_0.compiler import compile_sources
from moth_runtime_v5_0.encoder import DeterministicEncoder
from moth_runtime_v5_0.model import WorldRole
from moth_runtime_v5_1.artifact import ModelArtifact51
from moth_runtime_v5_1.assets import load_foundation
from moth_runtime_v5_1.compiled_fields import (
    FieldKind,
    compile_field_archive,
    compile_skill_document,
    compose_skill_compilations,
    load_field_archive,
)

from experiments.runtime_v5_0_compiled_surface_skill.worlds import (
    SURFACE_SOURCE,
    decision_source,
    semantic_source,
)


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = Path(__file__).resolve().parent

FIELD_SOURCES = (
    (FieldKind.INSTRUCTION, "experiments/runtime_v5_0_instruction_compression/fixtures/base-field-en-1.0.json", ("SAFE_TEXT_PATCH", "EVIDENCE_LEDGER", "INERT_ACTION_PLAN")),
    (FieldKind.SURFACE_NATURAL, "experiments/runtime_v5_0_compiled_surface_skill/fixtures/surface-base-field-en-1.0.json", ("NATURAL_RESPONSE",)),
    (FieldKind.SURFACE_RICH, "experiments/runtime_v5_0_output_fidelity_mega_campaign/fixtures/rich-surface-field-en-1.0.json", ("RICH_PROSE", "TONE", "MARKDOWN", "MIXED_RESPONSE")),
    (FieldKind.SURFACE_STRUCTURED, "experiments/runtime_v5_0_compiled_json_python_surface/fixtures/structured-surface-field-en-1.0.json", ("STRICT_JSON", "INERT_PYTHON_LITERAL")),
    (FieldKind.SURFACE_PYTHON, "experiments/runtime_v5_0_compiled_python_function_surface/fixtures/python-function-surface-field-en-1.0.json", ("PYTHON_SOURCE",)),
)

SKILL_SOURCES = (
    ("bounded-agent-skill-en-1.0", "experiments/runtime_v5_0_instruction_compression/fixtures/safe-text-patch/SKILL.md"),
    ("bounded-agent-skill-en-1.0", "experiments/runtime_v5_0_instruction_compression/fixtures/evidence-ledger/SKILL.md"),
    ("bounded-natural-surface-en-1.0", "experiments/runtime_v5_0_compiled_surface_skill/fixtures/natural-response/SKILL.md"),
    ("runtime-v5-rich-output-surface-en-1.0", "experiments/runtime_v5_0_output_fidelity_mega_campaign/fixtures/prose-range/SKILL.md"),
    ("runtime-v5-rich-output-surface-en-1.0", "experiments/runtime_v5_0_output_fidelity_mega_campaign/fixtures/tone-adaptation/SKILL.md"),
    ("runtime-v5-rich-output-surface-en-1.0", "experiments/runtime_v5_0_output_fidelity_mega_campaign/fixtures/markdown-structure/SKILL.md"),
    ("runtime-v5-rich-output-surface-en-1.0", "experiments/runtime_v5_0_output_fidelity_mega_campaign/fixtures/mixed-response/SKILL.md"),
    ("bounded-json-python-surface-en-1.0", "experiments/runtime_v5_0_compiled_json_python_surface/fixtures/structured-output/SKILL.md"),
    ("bounded-python-function-surface-en-1.0", "experiments/runtime_v5_0_compiled_python_function_surface/fixtures/python-function-output/SKILL.md"),
)

QUALIFICATION_SOURCES = (
    "experiments/runtime_v5_0_instruction_compression/compiler.py",
    "experiments/runtime_v5_0_instruction_compression/fixtures/campaign-1.0.json",
    "experiments/runtime_v5_0_instruction_compression/fixtures/granular-oracle-1.0.json",
    "experiments/runtime_v5_0_instruction_compression/fixtures/safe-text-patch-paraphrase/SKILL.md",
    "experiments/runtime_v5_0_compiled_surface_skill/compiler.py",
    "experiments/runtime_v5_0_compiled_surface_skill/worlds.py",
    "experiments/runtime_v5_0_compiled_surface_skill/fixtures/campaign-en-1.0.json",
    "experiments/runtime_v5_0_compiled_surface_skill/fixtures/granular-surface-oracle-1.0.json",
    "experiments/runtime_v5_0_compiled_surface_skill/fixtures/natural-response-paraphrase/SKILL.md",
    "experiments/runtime_v5_0_output_fidelity_mega_campaign/fixtures/campaign-en-1.0.json",
    "experiments/runtime_v5_0_output_fidelity_mega_campaign/fixtures/granular-policy-oracle-en-1.0.json",
    "experiments/runtime_v5_0_output_fidelity_mega_campaign/fixtures/prose-range-paraphrase/SKILL.md",
    "experiments/runtime_v5_0_output_fidelity_mega_campaign/fixtures/tone-adaptation-paraphrase/SKILL.md",
    "experiments/runtime_v5_0_output_fidelity_mega_campaign/fixtures/markdown-structure-paraphrase/SKILL.md",
    "experiments/runtime_v5_0_output_fidelity_mega_campaign/fixtures/mixed-response-paraphrase/SKILL.md",
    "experiments/runtime_v5_0_compiled_json_python_surface/fixtures/campaign-en-1.0.json",
    "experiments/runtime_v5_0_compiled_json_python_surface/fixtures/granular-structured-oracle-1.0.json",
    "experiments/runtime_v5_0_compiled_json_python_surface/fixtures/structured-output-paraphrase/SKILL.md",
    "experiments/runtime_v5_0_compiled_python_function_surface/fixtures/campaign-en-1.0.json",
    "experiments/runtime_v5_0_compiled_python_function_surface/fixtures/granular-python-function-oracle-1.0.json",
    "experiments/runtime_v5_0_compiled_python_function_surface/fixtures/python-function-output-paraphrase/SKILL.md",
)


def _write(path: Path, value: object) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = canonical_bytes(value)
    path.write_bytes(raw)
    return raw


def _source_hashes() -> dict[str, str]:
    paths = [path for _, path, _ in FIELD_SOURCES] + [path for _, path in SKILL_SOURCES]
    paths += ["config/v5.1/base-hcf-en-1.0.json", *QUALIFICATION_SOURCES]
    return {path: sha256_bytes((ROOT / path).read_bytes()) for path in sorted(paths)}


def _verify_frozen_sources() -> None:
    frozen = json.loads((EXPERIMENT / "fixtures/SOURCE-MANIFEST.json").read_text())
    if frozen != {"schema": "moth-artifact-source-freeze/5.1", "sources": _source_hashes()}:
        raise RuntimeError("qualified artifact source freeze changed")


def _build_foundation(target: Path) -> None:
    encoder = DeterministicEncoder()
    worlds = {
        WorldRole.INPUT: compile_sources(
            {"input.moth": semantic_source("delivery", "deployment")},
            encoder=encoder, world_role=WorldRole.INPUT,
        ),
        WorldRole.MAIN: compile_sources(
            {"main.moth": decision_source()}, encoder=encoder, world_role=WorldRole.MAIN,
        ),
        WorldRole.SURFACE: compile_sources(
            {"surface.moth": SURFACE_SOURCE}, encoder=encoder, world_role=WorldRole.SURFACE,
        ),
    }
    descriptors = {}
    for role, world in worlds.items():
        relative = f"worlds/{role.value.casefold()}-world.json"
        raw = _write(target / relative, world_to_archive(world))
        descriptors[role.value] = {
            "path": relative, "sha256": sha256_bytes(raw),
            "generation_id": world.generation_id, "world_hash": world.world_hash,
        }
    base = json.loads((ROOT / "config/v5.1/base-hcf-en-1.0.json").read_text())
    base_raw = _write(target / "base-fields/base-hcf-en-1.0.json", base)
    manifest = {
        "schema": "moth-runtime-foundation/5.1", "runtime": "5.1",
        "hcf_schema": "moth-hcf-field/5.1",
        "base_fields": [{
            "field_id": base["field_id"], "path": "base-fields/base-hcf-en-1.0.json",
            "sha256": sha256_bytes(base_raw),
        }],
        "compiled_worlds": descriptors,
        "encoder": {"kind": "DETERMINISTIC", "fingerprint": encoder.fingerprint, "thresholds": {}},
        "context": {"max_message_tokens": 128, "active_context_tokens": 4096},
        "surface": {"modes": ["concise", "detailed", "structured"]},
    }
    _write(target / "runtime-foundation.json", manifest)


def _copy_runtime(target: Path) -> dict:
    package_files: dict[str, str] = {}
    for package in ("moth_runtime_v5_0", "moth_runtime_v5_1", "moth_launcher_v5_1"):
        for source in sorted((ROOT / "src" / package).glob("*.py")):
            relative = f"{package}/{source.name}"
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            package_files[relative] = sha256_bytes(destination.read_bytes())
    package_manifest = {
        "schema": "moth-runtime-package/5.1", "runtime": "5.1",
        "entrypoint": "moth_launcher_v5_1.cli:main",
        "packages": ["moth_runtime_v5_0", "moth_runtime_v5_1", "moth_launcher_v5_1"],
        "files": package_files,
    }
    _write(target / "runtime-package.json", package_manifest)
    return package_manifest


def _capability_modes(compilations: dict[str, dict]) -> list[dict]:
    def mode(name: str, profile: str, requests: list[str], cost: int) -> dict:
        compilation = compilations[profile]
        return {
            "mode": name, "field_id": compilation["field_id"],
            "compilation_id": compilation["compilation_id"], "requests": requests,
            "semantic_kinds": ["ANSWER_WITH_PROOF"], "grounding_cost_units": cost,
        }
    return [
        mode("concise", "NATURAL_RESPONSE", ["answer concisely", "give me the short version", "keep the answer brief"], 0),
        mode("standard", "NATURAL_RESPONSE", ["", "use normal detail", "give a standard answer"], 1),
        mode("detailed", "NATURAL_RESPONSE", ["explain the result in detail", "give me a fuller explanation", "walk me through the decision"], 2),
        mode("compact_prose", "PROSE_RANGE", ["compact natural prose", "return compact natural prose"], 3),
        mode("detailed_prose", "PROSE_RANGE", ["detailed explanation", "return a detailed explanation"], 4),
        mode("formal_tone", "TONE_ADAPTATION", ["formal professional tone", "use formal professional tone"], 5),
        mode("conversational_tone", "TONE_ADAPTATION", ["conversational explanation", "explain conversationally"], 6),
        mode("markdown_bullets", "MARKDOWN_STRUCTURE", ["markdown bullet list", "return a markdown bullet list"], 7),
        mode("markdown_table", "MARKDOWN_STRUCTURE", ["markdown table", "return a markdown table"], 8),
        mode("explanation_json", "MIXED_RESPONSE", ["explanation with json", "explain and include json"], 9),
        mode("action_plan", "MIXED_RESPONSE", ["action plan", "return an action plan"], 10),
        mode("json_compact", "STRUCTURED_OUTPUT", ["compact output", "single-line output", "return compact json"], 11),
        mode("json_readable", "STRUCTURED_OUTPUT", ["readable output", "multiline output", "return readable json"], 12),
        mode("python_literal_compact", "STRUCTURED_OUTPUT", ["compact inert python literal", "return compact python"], 13),
        mode("python_literal_readable", "STRUCTURED_OUTPUT", ["readable inert python literal", "return readable python"], 14),
        mode("python_function", "PYTHON_FUNCTION_OUTPUT", ["actual python code", "compact function program", "readable function program", "return python with functions and variables", "return an actual python code block with functions and variables"], 15),
    ]


def build_artifact(destination: str | Path) -> dict:
    _verify_frozen_sources()
    target = Path(destination).resolve()
    if target.exists() and any(target.iterdir()):
        raise RuntimeError("artifact destination must be empty")
    target.mkdir(parents=True, exist_ok=True)
    _build_foundation(target / "foundation")
    foundation = load_foundation(target / "foundation")
    _copy_runtime(target / "runtime")

    field_descriptors, fields = [], {}
    for kind, source_path, capabilities in FIELD_SOURCES:
        archive = compile_field_archive(json.loads((ROOT / source_path).read_text()), kind, capabilities)
        field = load_field_archive(archive)
        relative = f"compiled-fields/{field.field_id}.json"
        raw = _write(target / relative, archive)
        field_descriptors.append({
            "field_id": field.field_id, "kind": field.kind.value, "path": relative,
            "sha256": sha256_bytes(raw), "field_hash": field.field_hash,
        })
        fields[field.field_id] = field

    skill_descriptors, by_profile = [], {}
    for field_id, source_path in SKILL_SOURCES:
        compilation = compile_skill_document(fields[field_id], (ROOT / source_path).read_text())
        by_profile[compilation["profile_id"]] = compilation
    composite = compose_skill_compilations(
        by_profile["SAFE_TEXT_PATCH"], by_profile["EVIDENCE_LEDGER"],
        fields["bounded-agent-skill-en-1.0"],
    )
    by_profile[composite["profile_id"]] = composite
    for profile_id, compilation in sorted(by_profile.items()):
        relative = f"compiled-skills/{profile_id.casefold().replace('_', '-')}.json"
        raw = _write(target / relative, compilation)
        skill_descriptors.append({
            "compilation_id": compilation["compilation_id"], "field_id": compilation["field_id"],
            "profile_id": profile_id, "policy_hash": compilation["policy_hash"],
            "path": relative, "sha256": sha256_bytes(raw),
        })

    capability_index = {"schema": "moth-capability-index/5.1", "surface_modes": _capability_modes(by_profile)}
    capability_raw = _write(target / "capability-index.json", capability_index)
    members = {
        path.relative_to(target).as_posix(): sha256_bytes(path.read_bytes())
        for path in sorted(target.rglob("*")) if path.is_file()
    }
    body = {
        "schema": "moth-model-artifact/5.1", "model_id": "moth-compiled-model/5.1-dev",
        "runtime": {
            "compatibility": "5.1", "entrypoint": "moth_launcher_v5_1.cli:main",
            "packages": ["moth_runtime_v5_0", "moth_runtime_v5_1", "moth_launcher_v5_1"],
            "package_manifest": "runtime/runtime-package.json",
        },
        "foundation": {
            "path": "foundation", "manifest_hash": foundation.manifest_hash,
            "foundation_id": foundation.foundation_id, "foundation_hash": foundation.foundation_hash,
        },
        "fields": field_descriptors, "skills": skill_descriptors,
        "capability_index": {"path": "capability-index.json", "sha256": sha256_bytes(capability_raw)},
        "members": members,
    }
    manifest = {**body, "artifact_hash": digest("moth-model-artifact/5.1", body)}
    _write(target / "model-artifact.json", manifest)
    artifact = ModelArtifact51.open(target)
    return artifact.verify()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination")
    args = parser.parse_args(argv)
    print(json.dumps(build_artifact(args.destination), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
