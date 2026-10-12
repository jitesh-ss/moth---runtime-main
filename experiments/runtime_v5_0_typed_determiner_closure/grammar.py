"""Compile the sealed typed-determiner extension over the frozen base field."""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any

from moth_runtime_v5_0.canonical import digest, normalize_text
from moth_runtime_v5_0.model import CompilationError
from experiments.runtime_v5_0_blind_compositional_closure.field import CompiledField


EXTENSION_SCHEMA = "moth-v5-typed-determiner-extension/1.0"
COMPILED_SCHEMA = "moth-v5-typed-determiner-field/1.0"


def compile_determiner_extension(
    base: CompiledField, source: dict[str, Any], *, base_field_sha256: str,
) -> CompiledField:
    if not isinstance(source, dict) or set(source) != {
        "schema", "frozen_before_new_prompts", "base_field_sha256", "operator",
    } or source.get("schema") != EXTENSION_SCHEMA:
        raise CompilationError("unsupported typed-determiner extension schema")
    if source.get("frozen_before_new_prompts") is not True or source.get("base_field_sha256") != base_field_sha256:
        raise CompilationError("typed-determiner extension is not bound to the sealed base field")
    operator = source["operator"]
    if not isinstance(operator, dict) or set(operator) != {
        "id", "grammar", "determiners", "roles", "maximum_prefixes",
        "semantic_contribution", "existing_determiner_policy",
    }:
        raise CompilationError("typed-determiner operator shape is invalid")
    if (
        operator["grammar"] != "DETERMINER? + COMPILED_CAPABILITY_SURFACE"
        or operator["maximum_prefixes"] != 1
        or operator["semantic_contribution"] != "NONE"
        or operator["existing_determiner_policy"] != "EXACT_ONLY"
    ):
        raise CompilationError("typed-determiner operator exceeds its frozen grammar")
    determiners = sorted({normalize_text(str(value)).casefold() for value in operator["determiners"]})
    if not determiners or any(not re.fullmatch(r"[a-z]+", value) for value in determiners):
        raise CompilationError("typed determiners are empty or unsafe")
    roles = sorted({normalize_text(str(value)).upper() for value in operator["roles"]})
    compiled_roles = {row["role"] for row in base.payload["capabilities"]}
    if not roles or set(roles) - compiled_roles:
        raise CompilationError("typed-determiner roles are not compiled capabilities")
    payload = deepcopy(base.payload)
    payload["noun_phrase_operator"] = {
        "id": normalize_text(str(operator["id"])),
        "grammar": operator["grammar"], "determiners": determiners,
        "roles": roles, "maximum_prefixes": 1,
        "semantic_contribution": "NONE", "existing_determiner_policy": "EXACT_ONLY",
        "base_field_hash": base.field_hash, "base_field_sha256": base_field_sha256,
    }
    field_hash = digest(COMPILED_SCHEMA, payload)
    return CompiledField(payload, field_hash)

