"""Immutable semantic contracts for independent Runtime 4.8 Worlds."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class WorldRole(StrEnum):
    INPUT = "INPUT"
    MAIN = "MAIN"
    SURFACE = "SURFACE"


class MeaningType(StrEnum):
    ENTITY = "ENTITY"
    RELATION = "RELATION"
    NUMERAL = "NUMERAL"
    OPERATION = "OPERATION"
    INSTRUCTION = "INSTRUCTION"
    INSTRUCTION_PROTOTYPE = "INSTRUCTION_PROTOTYPE"
    RELATION_FORM = "RELATION_FORM"
    OUTPUT_SCHEMA = "OUTPUT_SCHEMA"
    ALIAS = "ALIAS"
    SCALAR_TYPE = "SCALAR_TYPE"
    VALUE = "VALUE"
    ENUM_MEMBER = "ENUM_MEMBER"
    LIST_VALUE = "LIST_VALUE"
    STRUCTURED_SCHEMA = "STRUCTURED_SCHEMA"
    SCHEMA_FIELD = "SCHEMA_FIELD"
    RELATION_SEQUENCE = "RELATION_SEQUENCE"
    PROGRAM = "PROGRAM"
    PROGRAM_STEP = "PROGRAM_STEP"
    TOOL = "TOOL"
    TOOL_ARGUMENT = "TOOL_ARGUMENT"
    CODE_FILE = "CODE_FILE"
    CODE_SYMBOL = "CODE_SYMBOL"
    CODE_SPAN = "CODE_SPAN"
    TEXT_FRAGMENT = "TEXT_FRAGMENT"
    PATCH_TEMPLATE = "PATCH_TEMPLATE"


class RefusalCode(StrEnum):
    WORLD_NOT_READY = "WORLD_NOT_READY"
    WORLD_INTERFACE_MISMATCH = "WORLD_INTERFACE_MISMATCH"
    UNKNOWN_ENTITY = "UNKNOWN_ENTITY"
    UNSUPPORTED_RELATION = "UNSUPPORTED_RELATION"
    UNKNOWN_NUMERAL = "UNKNOWN_NUMERAL"
    UNSUPPORTED_INSTRUCTION = "UNSUPPORTED_INSTRUCTION"
    UNSUPPORTED_OPERATION = "UNSUPPORTED_OPERATION"
    UNSUPPORTED_OUTPUT = "UNSUPPORTED_OUTPUT"
    UNSUPPORTED_PROGRAM = "UNSUPPORTED_PROGRAM"
    UNSUPPORTED_MODALITY = "UNSUPPORTED_MODALITY"
    AMBIGUOUS_GROUNDING = "AMBIGUOUS_GROUNDING"
    MISSING_PREMISE = "MISSING_PREMISE"
    AMBIGUOUS_PROOF = "AMBIGUOUS_PROOF"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"
    RESOURCE_LIMIT = "RESOURCE_LIMIT"
    COMPILATION_ERROR = "COMPILATION_ERROR"
    UNKNOWN_TOOL = "UNKNOWN_TOOL"
    UNSUPPORTED_ARGUMENT = "UNSUPPORTED_ARGUMENT"
    UNKNOWN_VALUE = "UNKNOWN_VALUE"
    TYPE_MISMATCH = "TYPE_MISMATCH"
    INVALID_SCHEMA = "INVALID_SCHEMA"
    AMBIGUOUS_PROGRAM = "AMBIGUOUS_PROGRAM"
    INVALID_PATCH_TARGET = "INVALID_PATCH_TARGET"
    STALE_SOURCE = "STALE_SOURCE"
    UNSUPPORTED_CODE_LANGUAGE = "UNSUPPORTED_CODE_LANGUAGE"


OPERATIONS = {
    "LOOKUP", "CHAIN_ADVANCE", "RELATION_SEQUENCE", "VALIDATE_STRUCTURE",
    "RENDER_COMPILED_JSON", "LINEAR_PIPELINE", "CODE_RELATION_QUERY",
    "BUILD_PATCH_PLAN", "REALIZE_SEMANTIC_RESULT",
}


@dataclass(frozen=True, order=True)
class Provenance:
    source_id: str
    source_sha256: str
    statement_sha256: str
    char_start: int
    char_end: int
    byte_start: int
    byte_end: int
    line: int
    column: int
    compiler_version: str = "4.8.1"

    def canonical(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Source:
    source_id: str
    text: str
    sha256: str


@dataclass(frozen=True)
class Meaning:
    meaning_id: str
    kind: MeaningType
    name: str
    payload: dict[str, Any]
    owners: tuple[Provenance, ...]

    def canonical(self, *, include_owners: bool = True) -> dict[str, Any]:
        value = {
            "meaning_id": self.meaning_id,
            "kind": self.kind.value,
            "name": self.name,
            "payload": self.payload,
        }
        if include_owners:
            value["owners"] = [owner.canonical() for owner in self.owners]
        return value


@dataclass(frozen=True)
class SemanticEdge:
    edge_id: str
    relation_id: str
    source_id: str
    destination_id: str
    owners: tuple[Provenance, ...]

    def canonical(self) -> dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "relation_id": self.relation_id,
            "source_id": self.source_id,
            "destination_id": self.destination_id,
            "owners": [owner.canonical() for owner in self.owners],
        }


@dataclass(frozen=True)
class VectorRecord:
    meaning_id: str
    text: str
    vector_hash: str
    vector: tuple[float, ...] = field(repr=False)


@dataclass(frozen=True)
class CompiledWorld:
    sources: dict[str, Source]
    meanings: dict[str, Meaning]
    names: dict[str, dict[str, tuple[str, ...]]]
    aliases: dict[str, dict[str, tuple[str, ...]]]
    edges: tuple[SemanticEdge, ...]
    vectors: dict[str, VectorRecord]
    world_hash: str
    compiler_hash: str
    encoder_hash: str
    generation_id: str
    capability_level: str
    world_role: WorldRole

    def by_kind(self, kind: MeaningType) -> tuple[Meaning, ...]:
        return tuple(item for _, item in sorted(self.meanings.items()) if item.kind == kind)

    def resolve_exact(self, kind: MeaningType, surface: str) -> tuple[Meaning, ...]:
        key = surface.casefold()
        identifiers = set(self.names.get(kind.value, {}).get(key, ()))
        identifiers.update(self.aliases.get(kind.value, {}).get(key, ()))
        return tuple(self.meanings[value] for value in sorted(identifiers) if value in self.meanings)

    def relation_edges(self, relation_id: str) -> tuple[SemanticEdge, ...]:
        return tuple(edge for edge in self.edges if edge.relation_id == relation_id)


@dataclass(frozen=True)
class GroundedProgram:
    instruction_id: str
    operation_id: str
    operation: str
    slots: dict[str, str]
    bindings: dict[str, str]
    steps: tuple[dict[str, Any], ...]
    grounding_cost_units: int
    grounding: dict[str, Any]


@dataclass(frozen=True)
class Settlement:
    output_kind: str
    output: Any
    proof_ids: tuple[str, ...]
    proof_count: int
    total_energy_units: int
    violation_count: int
    grounding_cost_units: int
    generation_id: str


@dataclass(frozen=True)
class WorldBundle:
    bundle_id: str
    input_generation_id: str
    main_generation_id: str
    surface_generation_id: str
    interface_hash: str
    bundle_hash: str

    def generation_for(self, role: WorldRole) -> str:
        return {
            WorldRole.INPUT: self.input_generation_id,
            WorldRole.MAIN: self.main_generation_id,
            WorldRole.SURFACE: self.surface_generation_id,
        }[role]

    def canonical(self) -> dict[str, Any]:
        value = asdict(self)
        value["schema"] = "moth-world-bundle/4.8"
        return value


@dataclass(frozen=True)
class WorldHandoff:
    bundle_id: str
    source_role: WorldRole
    target_role: WorldRole
    source_generation_id: str
    target_generation_id: str
    payload_kind: str
    payload: Any
    source_settlement_hash: str
    provenance_hash: str
    handoff_hash: str

    def canonical(self) -> dict[str, Any]:
        value = asdict(self)
        value["schema"] = "moth-world-handoff/4.8"
        return value


@dataclass(frozen=True)
class WorldStageReceipt:
    role: WorldRole
    bundle_id: str
    generation_id: str
    world_hash: str
    input_hash: str
    settlement_hash: str
    provenance_hash: str
    output_kind: str
    output_hash: str
    total_energy_units: int
    violation_count: int
    proof_count: int
    verified: bool = True

    def canonical(self) -> dict[str, Any]:
        return asdict(self)


class CompilationError(ValueError):
    pass


class IntegrityError(ValueError):
    pass
