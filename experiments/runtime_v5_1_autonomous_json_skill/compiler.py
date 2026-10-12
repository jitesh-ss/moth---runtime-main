"""Compile the experiment's generic JSON field and its single detailed skill."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from moth_runtime_v5_0.canonical import canonical_bytes
from moth_runtime_v5_1.compiled_fields import (
    FieldKind,
    compile_field_archive,
    compile_skill_document,
    load_field_archive,
    verify_skill_compilation,
)


HERE = Path(__file__).resolve().parent
FIELD_PATH = HERE / "fixtures/json-formatting-field-en-1.0.json"
SKILL_PATH = HERE / "fixtures/json-formatting/SKILL.md"


def compile_candidate() -> tuple[Any, dict[str, Any]]:
    source = json.loads(FIELD_PATH.read_text())
    archive = compile_field_archive(
        source,
        FieldKind.SURFACE_STRUCTURED,
        ("AUTONOMOUS_JSON_FORMATTING", "STRICT_JSON", "PROMPT_ROUTING"),
    )
    field = load_field_archive(archive)
    skill = compile_skill_document(field, SKILL_PATH.read_text())
    verify_skill_compilation(skill, field)
    return field, skill


def verify_deterministic_compilation(repetitions: int = 10) -> dict[str, Any]:
    builds = [compile_candidate() for _ in range(repetitions)]
    field_bytes = {canonical_bytes(field.archive) for field, _ in builds}
    skill_bytes = {canonical_bytes(skill) for _, skill in builds}
    if len(field_bytes) != 1 or len(skill_bytes) != 1:
        raise AssertionError("candidate field or skill compilation is not deterministic")
    field, skill = builds[0]
    return {
        "repetitions": repetitions,
        "field_id": field.field_id,
        "field_hash": field.field_hash,
        "compilation_id": skill["compilation_id"],
        "policy_hash": skill["policy_hash"],
        "profile_id": skill["profile_id"],
        "normative_clause_count": skill["trace"]["normative_clause_count"],
        "graph_unit_count": skill["trace"]["graph_unit_count"],
    }

