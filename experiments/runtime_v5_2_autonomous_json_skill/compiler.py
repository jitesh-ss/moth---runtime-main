"""Compile the autonomous JSON candidate into Runtime 5.2 Safetensors."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from moth_runtime_v5_2.compile.fields import compile_energy_foundation
from moth_runtime_v5_2.compile.skills import (
    CompiledFieldObject,
    CompiledSkillObject,
    compile_field_object,
    compile_skill_object,
    load_field_object,
    load_skill_object,
)
from moth_runtime_v5_2.compiled_fields import (
    FieldKind,
    compile_field_archive,
    compile_skill_document,
    load_field_archive,
    verify_skill_compilation,
)
from moth_runtime_v5_2.energy.loader import EnergyFoundation, load_energy_foundation
from moth_runtime_v5_2.persistence.objects import ObjectStore


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ORACLE_FIXTURES = ROOT / "experiments/runtime_v5_1_autonomous_json_skill/fixtures"
FIELD_PATH = ORACLE_FIXTURES / "json-formatting-field-en-1.0.json"
SKILL_PATH = ORACLE_FIXTURES / "json-formatting/SKILL.md"
TRIGGER = "NATURAL_JSON_FORMAT_REQUEST"


@dataclass(frozen=True)
class Candidate52:
    store: ObjectStore
    field: CompiledFieldObject
    skill: CompiledSkillObject
    foundation: EnergyFoundation


def compile_candidate(root: str | Path) -> Candidate52:
    store = ObjectStore(root)
    source = json.loads(FIELD_PATH.read_text(encoding="utf-8"))
    archive = compile_field_archive(
        source,
        FieldKind.SURFACE_STRUCTURED,
        ("AUTONOMOUS_JSON_FORMATTING", "STRICT_JSON", "PROMPT_ROUTING"),
    )
    field_model = load_field_archive(archive)
    compilation = compile_skill_document(
        field_model, SKILL_PATH.read_text(encoding="utf-8")
    )
    verify_skill_compilation(compilation, field_model)
    field = compile_field_object(store, archive)
    skill = compile_skill_object(store, compilation)
    candidates = [
        {
            "candidate_id": "skill.autonomous-json-formatting",
            "semantic": {
                "compilation_id": skill.compilation_id,
                "trigger": TRIGGER,
            },
            "properties": {
                "skill.trigger": TRIGGER,
                "response.mode": "structured",
                "runtime.network": False,
                "runtime.tool_execution": False,
                "runtime.world_management": False,
            },
            "field_id": field.field_id,
            "skill_id": skill.compilation_id,
            "payload": "bounded-json-interpreter/5.2-experiment",
            "grounding_cost_units": 0,
        },
        {
            "candidate_id": "skill.none",
            "semantic": {"compilation_id": None, "trigger": None},
            "properties": {
                "skill.trigger": None,
                "response.mode": "concise",
                "runtime.network": False,
                "runtime.tool_execution": False,
                "runtime.world_management": False,
            },
            "field_id": "none",
            "skill_id": "none",
            "payload": "none",
            "grounding_cost_units": 1,
        },
    ]
    base = {
        "schema": "moth-hcf-base-field/5.2-experiment",
        "entries": [
            {"meaning_id": "base.no-network", "effect": "REQUIRE", "scope": "runtime.network", "value": False},
            {"meaning_id": "base.no-tools", "effect": "REQUIRE", "scope": "runtime.tool_execution", "value": False},
            {"meaning_id": "base.no-writes", "effect": "REQUIRE", "scope": "runtime.world_management", "value": False},
        ],
    }
    foundation_envelope = compile_energy_foundation(store, candidates, base)
    reopened_field = load_field_object(store.open(field.envelope.file_hash))
    reopened_skill = load_skill_object(store.open(skill.envelope.file_hash))
    foundation = load_energy_foundation(store.open(foundation_envelope.file_hash))
    return Candidate52(store, reopened_field, reopened_skill, foundation)


def deterministic_compilation(repetitions: int = 3) -> dict:
    builds = []
    with TemporaryDirectory(prefix="moth52-json-determinism-") as temporary:
        parent = Path(temporary)
        for index in range(repetitions):
            candidate = compile_candidate(parent / str(index))
            builds.append(
                (
                    candidate.field.envelope.file_hash,
                    candidate.skill.envelope.file_hash,
                    candidate.foundation.file_hash,
                )
            )
    if len(set(builds)) != 1:
        raise AssertionError("Runtime 5.2 JSON candidate is not byte deterministic")
    field_hash, skill_hash, foundation_hash = builds[0]
    return {
        "repetitions": repetitions,
        "field_object_hash": field_hash,
        "skill_object_hash": skill_hash,
        "foundation_object_hash": foundation_hash,
        "identical": True,
    }

