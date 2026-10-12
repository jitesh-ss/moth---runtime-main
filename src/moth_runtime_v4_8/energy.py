"""Exact min-sum semantics and an independent result verifier.

There is deliberately no associative settlement, code execution, tool
dispatcher, or free-form generation in this module.
"""

from __future__ import annotations

import ast
from collections import defaultdict
from dataclasses import dataclass, replace
from typing import Any

from .canonical import canonical_bytes, digest, sha256_bytes
from .model import CompiledWorld, GroundedProgram, Meaning, MeaningType, RefusalCode, Settlement
from .structure import materialize

Q = 1_000_000


@dataclass(frozen=True)
class SettlementFailure(ValueError):
    code: RefusalCode
    message: str
    context: dict[str, Any]

    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"


def scalar_energy(*, grounded_slots: int, violations: int, grounding_cost: int) -> int:
    if grounded_slots < 0 or violations < 0 or not 0 <= grounding_cost <= grounded_slots * Q:
        raise ValueError("invalid energy coordinate")
    return (grounded_slots + 1) * Q * violations + grounding_cost


def _meaning(field: CompiledWorld, identifier: str, kind: MeaningType | None = None) -> Meaning:
    item = field.meanings.get(identifier)
    if item is None or (kind is not None and item.kind != kind):
        raise SettlementFailure(RefusalCode.INTEGRITY_FAILURE, "grounded meaning is absent or mistyped", {
            "meaning_id": identifier, "expected_kind": kind.value if kind else None,
        })
    return item


def _slot(program: GroundedProgram, name: str) -> str:
    if name not in program.slots:
        raise SettlementFailure(RefusalCode.UNSUPPORTED_PROGRAM, f"required slot {name} is missing", {})
    return program.slots[name]


def _edge_index(field: CompiledWorld) -> dict[tuple[str, str], tuple[Any, ...]]:
    rows: dict[tuple[str, str], list[Any]] = defaultdict(list)
    for edge in field.edges:
        if not edge.owners:
            raise SettlementFailure(RefusalCode.INTEGRITY_FAILURE, "semantic edge has no provenance", {
                "edge_id": edge.edge_id,
            })
        rows[(edge.relation_id, edge.source_id)].append(edge)
    return {key: tuple(sorted(value, key=lambda edge: (edge.destination_id, edge.edge_id)))
            for key, value in rows.items()}


def _unique_path(field: CompiledWorld, start_id: str, relations: list[str]) -> tuple[str, tuple[str, ...], int]:
    """Dynamic programming with semantic proof counts saturated at two."""
    index = _edge_index(field)
    frontier: dict[str, tuple[int, tuple[str, ...]]] = {start_id: (1, ())}
    for relation_id in relations:
        next_frontier: dict[str, tuple[int, tuple[str, ...]]] = {}
        for source_id, (count, proof) in sorted(frontier.items()):
            for edge in index.get((relation_id, source_id), ()):
                candidate = proof + (edge.edge_id,)
                prior_count, prior_proof = next_frontier.get(edge.destination_id, (0, ()))
                total = min(2, prior_count + count)
                chosen = candidate if prior_count == 0 or candidate < prior_proof else prior_proof
                next_frontier[edge.destination_id] = (total, chosen)
        if not next_frontier:
            raise SettlementFailure(RefusalCode.MISSING_PREMISE, "a required directional transition is absent", {
                "relation_id": relation_id,
            })
        frontier = next_frontier
    proof_count = min(2, sum(count for count, _ in frontier.values()))
    if proof_count != 1 or len(frontier) != 1:
        raise SettlementFailure(RefusalCode.AMBIGUOUS_PROOF, "the compiled field has multiple semantic proofs", {
            "proof_count": proof_count, "endpoint_count": len(frontier),
        })
    destination, (_, proof) = next(iter(frontier.items()))
    return destination, proof, 1


def exhaustive_paths(field: CompiledWorld, start_id: str,
                     relations: list[str]) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Independent small-field enumerator used only as an optimization oracle."""
    paths: list[tuple[str, tuple[str, ...]]] = [(start_id, ())]
    for relation_id in relations:
        expanded: list[tuple[str, tuple[str, ...]]] = []
        for source_id, proof in paths:
            for edge in field.edges:
                if edge.relation_id == relation_id and edge.source_id == source_id:
                    expanded.append((edge.destination_id, proof + (edge.edge_id,)))
        paths = expanded
    return tuple(sorted(paths, key=lambda row: (row[0], row[1])))


def _compiled_value(item: Meaning) -> Any:
    if item.kind in {MeaningType.VALUE, MeaningType.ENUM_MEMBER, MeaningType.LIST_VALUE}:
        return item.payload["value"]
    if item.kind in {MeaningType.ENTITY, MeaningType.CODE_SYMBOL, MeaningType.CODE_FILE}:
        return item.name
    raise SettlementFailure(RefusalCode.TYPE_MISMATCH, "meaning cannot serve as a structured value", {
        "meaning_id": item.meaning_id, "kind": item.kind.value,
    })


def _render_structure(field: CompiledWorld, program: GroundedProgram) -> Any:
    schema_id = program.slots.get("STRUCTURE")
    tool_id = program.slots.get("TOOL")
    if tool_id:
        tool = _meaning(field, tool_id, MeaningType.TOOL)
        tool_schema_id = str(tool.payload["schema_id"])
        if schema_id and schema_id != tool_schema_id:
            raise SettlementFailure(RefusalCode.TYPE_MISMATCH, "tool and requested schema differ", {})
        schema_id = tool_schema_id
    if not schema_id:
        raise SettlementFailure(RefusalCode.INVALID_SCHEMA, "compiled structured schema is missing", {})
    schema = _meaning(field, schema_id, MeaningType.STRUCTURED_SCHEMA)
    bindings: dict[str, Any] = {}
    for field_id, value_id in sorted(program.bindings.items()):
        field_item = _meaning(field, field_id, MeaningType.SCHEMA_FIELD)
        if str(field_item.payload["schema_id"]) != schema_id:
            raise SettlementFailure(RefusalCode.UNSUPPORTED_ARGUMENT, "field is not declared by selected schema", {
                "field_id": field_id,
            })
        value_item = _meaning(field, value_id)
        bindings[field_item.name] = _compiled_value(value_item)
        if tool_id:
            declared = [item for item in field.by_kind(MeaningType.TOOL_ARGUMENT)
                        if item.payload.get("tool_id") == tool_id and item.payload.get("field_id") == field_id]
            if not declared:
                raise SettlementFailure(RefusalCode.UNSUPPORTED_ARGUMENT, "field is not a compiled tool argument", {
                    "field_id": field_id,
                })
    try:
        return materialize(dict(schema.payload["schema"]), bindings)
    except TypeError as exc:
        raise SettlementFailure(RefusalCode.TYPE_MISMATCH, str(exc), {}) from exc
    except ValueError as exc:
        message = str(exc)
        code = RefusalCode.RESOURCE_LIMIT if message.startswith("RESOURCE_LIMIT") else RefusalCode.INVALID_SCHEMA
        if message.startswith("EXTRA_FIELD"):
            code = RefusalCode.UNSUPPORTED_ARGUMENT
        raise SettlementFailure(code, message, {}) from exc


def build_patch_plan(field: CompiledWorld,
                     requests: list[tuple[str, str, str | None]]) -> dict[str, Any]:
    """Validate 1..16 compiled, non-overlapping edits entirely in memory."""
    if not 1 <= len(requests) <= 16:
        raise SettlementFailure(RefusalCode.RESOURCE_LIMIT, "patch edit count is outside 1..16", {})
    grouped: dict[str, dict[str, Any]] = {}
    for span_id, template_id, fragment_id in requests:
        span = _meaning(field, span_id, MeaningType.CODE_SPAN)
        template = _meaning(field, template_id, MeaningType.PATCH_TEMPLATE)
        operation = str(template.payload["operation"])
        replacement = ""
        if operation != "DELETE_SPAN":
            if not fragment_id:
                raise SettlementFailure(RefusalCode.UNSUPPORTED_ARGUMENT, "patch operation needs a compiled fragment", {})
            replacement = str(_meaning(field, fragment_id, MeaningType.TEXT_FRAGMENT).payload["text"])
        file_item = _meaning(field, str(span.payload["file_id"]), MeaningType.CODE_FILE)
        source = field.sources.get("python/" + str(file_item.payload["path"]))
        if source is None or source.sha256 != file_item.payload["file_sha256"]:
            raise SettlementFailure(RefusalCode.STALE_SOURCE, "compiled code file hash is unavailable", {})
        raw = source.text.encode("utf-8")
        start, end = int(span.payload["start_byte"]), int(span.payload["end_byte"])
        if start < 0 or end < start or end > len(raw):
            raise SettlementFailure(RefusalCode.INVALID_PATCH_TARGET, "compiled span is outside the file", {})
        if sha256_bytes(raw[start:end]) != span.payload["span_sha256"]:
            raise SettlementFailure(RefusalCode.STALE_SOURCE, "compiled span hash changed", {})
        row = grouped.setdefault(file_item.meaning_id, {
            "file": file_item, "source": source, "raw": raw, "edits": [],
        })
        row["edits"].append({
            "operation": operation, "start_byte": start, "end_byte": end,
            "expected_span_sha256": str(span.payload["span_sha256"]),
            "replacement_fragment_id": fragment_id, "replacement_text": replacement,
        })

    files = []
    for file_id, row in sorted(grouped.items()):
        edits = sorted(row["edits"], key=lambda edit: (edit["start_byte"], edit["end_byte"], edit["operation"]))
        for prior, current in zip(edits, edits[1:]):
            if current["start_byte"] < prior["end_byte"] or (
                current["start_byte"] == prior["start_byte"] and current["end_byte"] == prior["end_byte"]
            ):
                raise SettlementFailure(RefusalCode.INVALID_PATCH_TARGET, "compiled patch spans overlap", {})
        candidate = row["raw"]
        for edit in reversed(edits):
            start, end = edit["start_byte"], edit["end_byte"]
            replacement = edit["replacement_text"].encode("utf-8")
            if edit["operation"] == "REPLACE_SPAN":
                candidate = candidate[:start] + replacement + candidate[end:]
            elif edit["operation"] == "INSERT_BEFORE":
                candidate = candidate[:start] + replacement + candidate[start:]
            elif edit["operation"] == "INSERT_AFTER":
                candidate = candidate[:end] + replacement + candidate[end:]
            elif edit["operation"] == "DELETE_SPAN":
                candidate = candidate[:start] + candidate[end:]
            else:
                raise SettlementFailure(RefusalCode.INVALID_PATCH_TARGET, "unsupported compiled patch operation", {})
        try:
            ast.parse(candidate.decode("utf-8", errors="strict"), type_comments=True)
        except (UnicodeDecodeError, SyntaxError) as exc:
            raise SettlementFailure(RefusalCode.INVALID_PATCH_TARGET, "in-memory patched Python does not parse", {}) from exc
        files.append({"file_id": file_id, "expected_file_sha256": row["source"].sha256,
                      "edits": edits})
    return {"target_generation": field.generation_id, "files": files}


def _patch_plan(field: CompiledWorld, program: GroundedProgram) -> dict[str, Any]:
    return build_patch_plan(field, [(
        _slot(program, "SPAN"), _slot(program, "PATCH"), program.slots.get("FRAGMENT"),
    )])


def _settle_primitive(field: CompiledWorld, program: GroundedProgram,
                      primitive: str) -> tuple[str, Any, tuple[str, ...], int]:
    if primitive == "LOOKUP":
        identifier = program.slots.get("ENTITY") or program.slots.get("SYMBOL") or program.slots.get("CODE_SYMBOL")
        if not identifier:
            raise SettlementFailure(RefusalCode.UNSUPPORTED_PROGRAM, "lookup target is missing", {})
        item = _meaning(field, identifier)
        return item.kind.value, {"meaning_id": item.meaning_id, "canonical_name": item.name}, (), 1
    if primitive in {"CHAIN_ADVANCE", "CODE_RELATION_QUERY"}:
        start = (program.slots.get("ENTITY") or program.slots.get("SYMBOL") or
                 program.slots.get("CODE_SYMBOL"))
        if not start:
            raise SettlementFailure(RefusalCode.UNSUPPORTED_PROGRAM, "relational start is missing", {})
        if "SEQUENCE" in program.slots or "RELATION_SEQUENCE" in program.slots:
            sequence_id = program.slots.get("SEQUENCE") or program.slots["RELATION_SEQUENCE"]
            sequence = _meaning(field, str(sequence_id), MeaningType.RELATION_SEQUENCE)
            relations = list(sequence.payload["relation_ids"])
        else:
            relation = _meaning(field, _slot(program, "RELATION"), MeaningType.RELATION)
            steps = 1
            if "NUMERAL" in program.slots:
                steps = int(_meaning(field, program.slots["NUMERAL"], MeaningType.NUMERAL).payload["steps"])
            relations = [relation.meaning_id] * steps
        destination, proof, count = _unique_path(field, start, relations)
        item = _meaning(field, destination)
        return item.kind.value, {"meaning_id": item.meaning_id, "canonical_name": item.name}, proof, count
    if primitive == "RELATION_SEQUENCE":
        start = _slot(program, "ENTITY")
        sequence = _meaning(field, program.slots.get("SEQUENCE", program.slots.get("RELATION_SEQUENCE", "")),
                            MeaningType.RELATION_SEQUENCE)
        destination, proof, count = _unique_path(field, start, list(sequence.payload["relation_ids"]))
        item = _meaning(field, destination)
        return item.kind.value, {"meaning_id": item.meaning_id, "canonical_name": item.name}, proof, count
    if primitive in {"VALIDATE_STRUCTURE", "RENDER_COMPILED_JSON"}:
        return "COMPILED_JSON", _render_structure(field, program), (), 1
    if primitive == "BUILD_PATCH_PLAN":
        return "PATCH_PLAN", _patch_plan(field, program), (), 1
    if primitive == "REALIZE_SEMANTIC_RESULT":
        semantic = program.grounding.get("semantic_result")
        if not isinstance(semantic, dict):
            raise SettlementFailure(
                RefusalCode.INTEGRITY_FAILURE,
                "Surface World semantic input is absent",
                {},
            )
        semantic_hash = digest("moth-world-semantic-result/4.8", semantic)
        if program.grounding.get("semantic_result_hash") != semantic_hash:
            raise SettlementFailure(
                RefusalCode.INTEGRITY_FAILURE,
                "Surface World semantic input hash changed",
                {},
            )
        required = {
            "semantic_kind", "value", "proof_ids", "proof_count",
            "source_generation_id",
        }
        if set(semantic) != required or semantic.get("proof_count") != 1:
            raise SettlementFailure(
                RefusalCode.INTEGRITY_FAILURE,
                "Surface World semantic input contract is invalid",
                {},
            )
        return "SURFACE_RESPONSE", {
            "kind": str(semantic["semantic_kind"]),
            "value": semantic["value"],
            "semantic_result_hash": semantic_hash,
        }, (), 1
    raise SettlementFailure(RefusalCode.UNSUPPORTED_OPERATION, f"operation {primitive} is unsupported", {})


def _pipeline(field: CompiledWorld, program: GroundedProgram) -> tuple[str, Any, tuple[str, ...], int]:
    if not 1 <= len(program.steps) <= 16:
        raise SettlementFailure(RefusalCode.UNSUPPORTED_PROGRAM, "pipeline step count is outside 1..16", {})
    proof: tuple[str, ...] = ()
    proof_count = 1
    output_kind = "NULL"
    output: Any = None
    current_meaning_id: str | None = None
    for step in program.steps:
        primitive = str(step.get("operation", ""))
        if primitive in {"LINEAR_PIPELINE"}:
            raise SettlementFailure(RefusalCode.AMBIGUOUS_PROGRAM, "recursive pipeline is unsupported", {})
        step_program = program
        if primitive in {"VALIDATE_STRUCTURE", "RENDER_COMPILED_JSON"} and "schema" in step:
            if current_meaning_id is None:
                raise SettlementFailure(RefusalCode.AMBIGUOUS_PROGRAM, "render step has no exact upstream value", {})
            schemas = field.resolve_exact(MeaningType.STRUCTURED_SCHEMA, str(step["schema"]))
            fields = field.resolve_exact(MeaningType.SCHEMA_FIELD, str(step.get("field", "")))
            if len(schemas) != 1 or len(fields) != 1:
                raise SettlementFailure(RefusalCode.INTEGRITY_FAILURE, "compiled program reference is unresolved", {})
            step_program = replace(
                program,
                slots={**program.slots, "STRUCTURE": schemas[0].meaning_id},
                bindings={fields[0].meaning_id: current_meaning_id},
            )
        output_kind, output, step_proof, step_count = _settle_primitive(field, step_program, primitive)
        if isinstance(output, dict) and isinstance(output.get("meaning_id"), str):
            current_meaning_id = output["meaning_id"]
        proof += step_proof
        proof_count = min(2, proof_count * step_count)
    return output_kind, output, proof, proof_count


def settle(field: CompiledWorld, program: GroundedProgram) -> Settlement:
    operation = _meaning(field, program.operation_id, MeaningType.OPERATION)
    if operation.payload.get("primitive") != program.operation:
        raise SettlementFailure(RefusalCode.UNSUPPORTED_OPERATION, "grounded operation does not match instruction", {})
    if program.operation == "LINEAR_PIPELINE":
        output_kind, output, proof, proof_count = _pipeline(field, program)
    else:
        output_kind, output, proof, proof_count = _settle_primitive(field, program, program.operation)
    if proof_count != 1:
        raise SettlementFailure(RefusalCode.AMBIGUOUS_PROOF, "settlement proof is not unique", {})
    grounded_slots = len(program.slots) + len(program.bindings)
    energy = scalar_energy(grounded_slots=grounded_slots, violations=0,
                           grounding_cost=program.grounding_cost_units)
    return Settlement(output_kind, output, proof, proof_count, energy, 0,
                      program.grounding_cost_units, field.generation_id)


def verify_settlement(field: CompiledWorld, program: GroundedProgram, candidate: Settlement) -> None:
    """Independently reconstruct a state; solver output never self-certifies."""
    expected = settle(field, program)
    if candidate != expected:
        raise SettlementFailure(RefusalCode.INTEGRITY_FAILURE, "settlement differs from independent reconstruction", {
            "expected_hash": sha256_bytes(canonical_bytes(expected.__dict__)),
            "candidate_hash": sha256_bytes(canonical_bytes(candidate.__dict__)),
        })
    edge_by_id = {edge.edge_id: edge for edge in field.edges}
    for edge_id in candidate.proof_ids:
        edge = edge_by_id.get(edge_id)
        if edge is None or not edge.owners:
            raise SettlementFailure(RefusalCode.INTEGRITY_FAILURE, "proof edge or provenance is missing", {
                "edge_id": edge_id,
            })
    grounded_slots = len(program.slots) + len(program.bindings)
    if candidate.total_energy_units != scalar_energy(
        grounded_slots=grounded_slots, violations=candidate.violation_count,
        grounding_cost=candidate.grounding_cost_units,
    ):
        raise SettlementFailure(RefusalCode.INTEGRITY_FAILURE, "reported scalar energy is invalid", {})
