"""Typed, content-addressed bridges between Runtime 4.9 Worlds."""

from __future__ import annotations

from dataclasses import asdict
import re
from typing import Any

from .canonical import canonical_bytes, digest, sha256_bytes
from .model import (
    CompiledWorld, GroundedProgram, IntegrityError, Meaning, MeaningType,
    Settlement, WorldBundle, WorldHandoff, WorldRole, WorldStageReceipt,
)

HANDOFF_SCHEMA = "moth-world-handoff/4.9"
BUNDLE_SCHEMA = "moth-world-bundle/4.9"

_ALLOWED = {
    (WorldRole.INPUT, WorldRole.MAIN): "MAIN_REQUEST",
    (WorldRole.MAIN, WorldRole.SURFACE): "SEMANTIC_RESULT",
}

_SLOT_TYPES = {
    "ENTITY": MeaningType.ENTITY,
    "RELATION": MeaningType.RELATION,
    "NUMERAL": MeaningType.NUMERAL,
    "SCHEMA": MeaningType.OUTPUT_SCHEMA,
    "OUTPUT_SCHEMA": MeaningType.OUTPUT_SCHEMA,
    "STRUCTURE": MeaningType.STRUCTURED_SCHEMA,
    "RELATION_SEQUENCE": MeaningType.RELATION_SEQUENCE,
    "SEQUENCE": MeaningType.RELATION_SEQUENCE,
    "PROGRAM": MeaningType.PROGRAM,
    "TOOL": MeaningType.TOOL,
    "CODE_SYMBOL": MeaningType.CODE_SYMBOL,
    "SYMBOL": MeaningType.CODE_SYMBOL,
    "CODE_FILE": MeaningType.CODE_FILE,
    "CODE_SPAN": MeaningType.CODE_SPAN,
    "SPAN": MeaningType.CODE_SPAN,
    "PATCH_TEMPLATE": MeaningType.PATCH_TEMPLATE,
    "PATCH": MeaningType.PATCH_TEMPLATE,
    "TEXT_FRAGMENT": MeaningType.TEXT_FRAGMENT,
    "FRAGMENT": MeaningType.TEXT_FRAGMENT,
}


def _meaning(world: CompiledWorld, identifier: str) -> Meaning:
    value = world.meanings.get(identifier)
    if value is None:
        raise IntegrityError(f"World reference is absent: {identifier}")
    return value


def _instruction_records(world: CompiledWorld) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for instruction in world.by_kind(MeaningType.INSTRUCTION):
        operation = world.meanings.get(str(instruction.payload.get("operation_id")))
        if operation is None or operation.kind != MeaningType.OPERATION:
            raise IntegrityError("compiled instruction operation is unavailable")
        records[instruction.meaning_id] = {
            "instruction_id": instruction.meaning_id,
            "operation_id": operation.meaning_id,
            "primitive": str(operation.payload.get("primitive")),
            "slot_types": sorted(set(re.findall(
                r"\{([A-Z_]+)\}", str(instruction.payload.get("template", "")),
            ))),
        }
    return records


def _input_main_interfaces(
    input_world: CompiledWorld, main_world: CompiledWorld,
) -> tuple[dict[str, Any], ...]:
    source = _instruction_records(input_world)
    target = _instruction_records(main_world)
    if not source:
        raise IntegrityError("Input World has no compiled instruction interface")
    mappings: list[dict[str, Any]] = []
    for instruction_id, record in sorted(source.items()):
        destination = target.get(instruction_id)
        if destination != record:
            raise IntegrityError("compiled Input to Main instruction interface is incompatible")
        mapping = {
            "source_instruction_id": instruction_id,
            "source_operation_id": record["operation_id"],
            "target_instruction_id": destination["instruction_id"],
            "target_operation_id": destination["operation_id"],
            "primitive": destination["primitive"],
            "slot_types": destination["slot_types"],
        }
        mapping["interface_id"] = digest("moth-world-input-main-map/4.9", mapping)
        mappings.append(mapping)
    return tuple(mappings)


def main_request_from_input(
    input_world: CompiledWorld, main_world: CompiledWorld, program: GroundedProgram,
) -> dict[str, Any]:
    """Project a verified grounded state into an ID-only compiled interface."""
    mappings = {
        row["source_instruction_id"]: row
        for row in _input_main_interfaces(input_world, main_world)
    }
    mapping = mappings.get(program.instruction_id)
    if (
        mapping is None
        or mapping["source_operation_id"] != program.operation_id
        or mapping["primitive"] != program.operation
    ):
        raise IntegrityError("grounded Input program is outside the active interface")
    expected_slots = set(mapping["slot_types"])
    if set(program.slots) != expected_slots - {"BINDINGS"}:
        raise IntegrityError("grounded Input slots differ from the compiled interface")
    if bool(program.bindings) != ("BINDINGS" in expected_slots):
        raise IntegrityError("grounded Input bindings differ from the compiled interface")
    selected_ids = {
        *program.slots.values(), *program.bindings.keys(), *program.bindings.values(),
    }
    for identifier in selected_ids:
        source = _meaning(input_world, identifier)
        target = main_world.meanings.get(identifier)
        if target is None or target.kind != source.kind:
            raise IntegrityError("MAIN_REQUEST identifier is unavailable in Main World")
    for slot, identifier in program.slots.items():
        if _SLOT_TYPES.get(slot) != input_world.meanings[identifier].kind:
            raise IntegrityError("grounded Input slot is mistyped")
    expected_steps: tuple[dict[str, Any], ...] = ()
    if "PROGRAM" in program.slots:
        program_meaning = _meaning(input_world, program.slots["PROGRAM"])
        if program_meaning.kind != MeaningType.PROGRAM:
            raise IntegrityError("grounded Input PROGRAM slot is mistyped")
        expected_steps = tuple(program_meaning.payload["steps"])
    if program.steps != expected_steps:
        raise IntegrityError("grounded Input program steps differ from compiled state")
    return {
        "schema": "moth-main-request/4.9",
        "interface_id": mapping["interface_id"],
        "instruction_id": mapping["target_instruction_id"],
        "operation_id": mapping["target_operation_id"],
        "primitive": mapping["primitive"],
        "slots": {key: value for key, value in sorted(program.slots.items())},
        "bindings": {key: value for key, value in sorted(program.bindings.items())},
    }


def program_from_main_request(
    input_world: CompiledWorld, world: CompiledWorld, payload: Any, *, handoff_hash: str,
) -> GroundedProgram:
    request = payload
    required = {
        "schema", "interface_id", "instruction_id", "operation_id",
        "primitive", "slots", "bindings",
    }
    if not isinstance(request, dict) or set(request) != required:
        raise IntegrityError("MAIN_REQUEST shape is invalid")
    if request["schema"] != "moth-main-request/4.9":
        raise IntegrityError("MAIN_REQUEST schema is invalid")
    mappings = {
        row["interface_id"]: row
        for row in _input_main_interfaces(input_world, world)
    }
    mapping = mappings.get(str(request["interface_id"]))
    if mapping is None:
        raise IntegrityError("MAIN_REQUEST interface is absent from active bundle")
    instruction = world.meanings.get(str(request["instruction_id"]))
    operation = world.meanings.get(str(request["operation_id"]))
    if instruction is None or operation is None:
        raise IntegrityError("MAIN_REQUEST target identifier is absent")
    if instruction.kind != MeaningType.INSTRUCTION or operation.kind != MeaningType.OPERATION:
        raise IntegrityError("MAIN_REQUEST instruction or operation type is invalid")
    primitive = str(request["primitive"])
    if (
        request["instruction_id"] != mapping["target_instruction_id"]
        or request["operation_id"] != mapping["target_operation_id"]
        or primitive != mapping["primitive"]
    ):
        raise IntegrityError("MAIN_REQUEST differs from its compiled interface")
    if instruction.payload.get("operation_id") != operation.meaning_id:
        raise IntegrityError("MAIN_REQUEST instruction-operation mapping changed")
    if operation.payload.get("primitive") != primitive:
        raise IntegrityError("MAIN_REQUEST kernel primitive changed")
    raw_slots = request["slots"]
    if not isinstance(raw_slots, dict) or any(not isinstance(key, str) for key in raw_slots):
        raise IntegrityError("MAIN_REQUEST slots are invalid")
    slots = {str(key): str(value) for key, value in sorted(raw_slots.items())}
    if any(identifier not in world.meanings for identifier in slots.values()):
        raise IntegrityError("MAIN_REQUEST slot identifier is absent")
    if any(_SLOT_TYPES.get(slot) != world.meanings[identifier].kind for slot, identifier in slots.items()):
        raise IntegrityError("MAIN_REQUEST slot identifier is mistyped")
    raw_bindings = request["bindings"]
    if not isinstance(raw_bindings, dict):
        raise IntegrityError("MAIN_REQUEST bindings are invalid")
    bindings = {str(key): str(value) for key, value in sorted(raw_bindings.items())}
    if any(identifier not in world.meanings for identifier in {*bindings, *bindings.values()}):
        raise IntegrityError("MAIN_REQUEST binding identifier is absent")
    expected_slots = set(mapping["slot_types"])
    if set(slots) != expected_slots - {"BINDINGS"}:
        raise IntegrityError("MAIN_REQUEST slots differ from its compiled interface")
    if bool(bindings) != ("BINDINGS" in expected_slots):
        raise IntegrityError("MAIN_REQUEST bindings differ from its compiled interface")
    steps: tuple[dict[str, Any], ...] = ()
    program_id = slots.get("PROGRAM")
    if program_id is not None:
        program_meaning = _meaning(world, program_id)
        if program_meaning.kind != MeaningType.PROGRAM:
            raise IntegrityError("MAIN_REQUEST PROGRAM slot is mistyped")
        steps = tuple(program_meaning.payload["steps"])
    return GroundedProgram(
        instruction.meaning_id, operation.meaning_id, primitive, slots, bindings,
        steps, 0, {"source": "INPUT_WORLD_HANDOFF", "handoff_hash": handoff_hash},
    )


def surface_program_from_semantic_result(
    main_world: CompiledWorld, surface_world: CompiledWorld, payload: Any,
    *, handoff_hash: str,
) -> GroundedProgram:
    """Bind a verified semantic result as transient input to one compiled realizer."""
    result = payload
    required = {
        "semantic_kind", "value", "proof_ids", "proof_count", "source_generation_id",
    }
    if not isinstance(result, dict) or set(result) != required:
        raise IntegrityError("SEMANTIC_RESULT is malformed")
    if result.get("source_generation_id") != main_world.generation_id:
        raise IntegrityError("SEMANTIC_RESULT source generation changed")
    if result.get("proof_count") != 1 or not isinstance(result.get("proof_ids"), list):
        raise IntegrityError("SEMANTIC_RESULT proof contract is invalid")
    realizer = _surface_realizer(surface_world)
    semantic_hash = digest("moth-world-semantic-result/4.9", result)
    return GroundedProgram(
        realizer["instruction_id"], realizer["operation_id"],
        "REALIZE_SEMANTIC_RESULT", {}, {}, (), 0,
        {
            "source": "MAIN_WORLD_HANDOFF",
            "handoff_hash": handoff_hash,
            "semantic_result_hash": semantic_hash,
            "semantic_result": result,
        },
    )


def _surface_realizer(world: CompiledWorld) -> dict[str, str]:
    operations = [
        item for item in world.by_kind(MeaningType.OPERATION)
        if item.payload.get("primitive") == "REALIZE_SEMANTIC_RESULT"
    ]
    if len(operations) != 1:
        raise IntegrityError("Surface World requires exactly one compiled semantic realizer")
    instructions = [
        item for item in world.by_kind(MeaningType.INSTRUCTION)
        if item.payload.get("operation_id") == operations[0].meaning_id
    ]
    if len(instructions) != 1:
        raise IntegrityError("Surface World semantic realizer instruction is incompatible")
    return {
        "instruction_id": instructions[0].meaning_id,
        "operation_id": operations[0].meaning_id,
    }


def interface_descriptor(worlds: dict[WorldRole, CompiledWorld]) -> dict[str, Any]:
    if set(worlds) != set(WorldRole):
        raise IntegrityError("a World bundle requires INPUT, MAIN, and SURFACE")
    for role, world in worlds.items():
        if world.world_role != role:
            raise IntegrityError("World role does not match bundle position")
    mappings = _input_main_interfaces(
        worlds[WorldRole.INPUT], worlds[WorldRole.MAIN],
    )
    realizer = _surface_realizer(worlds[WorldRole.SURFACE])

    # Any meaning that pre-World grounding may place in a request must resolve
    # uniquely and identically in both target Worlds before a bundle can activate.
    transferable_kinds = {
        MeaningType.ENTITY, MeaningType.RELATION, MeaningType.NUMERAL,
        MeaningType.OUTPUT_SCHEMA, MeaningType.SCALAR_TYPE, MeaningType.VALUE,
        MeaningType.ENUM_MEMBER, MeaningType.LIST_VALUE,
        MeaningType.STRUCTURED_SCHEMA, MeaningType.SCHEMA_FIELD,
        MeaningType.RELATION_SEQUENCE, MeaningType.PROGRAM, MeaningType.TOOL,
        MeaningType.TOOL_ARGUMENT, MeaningType.CODE_FILE, MeaningType.CODE_SYMBOL,
        MeaningType.FINITE_DOMAIN, MeaningType.FACTOR_TEMPLATE,
        MeaningType.CODE_SPAN, MeaningType.TEXT_FRAGMENT, MeaningType.PATCH_TEMPLATE,
    }
    transferable: list[tuple[str, str]] = []
    for item in sorted(
        worlds[WorldRole.INPUT].meanings.values(), key=lambda value: value.meaning_id,
    ):
        if item.kind not in transferable_kinds:
            continue
        target = worlds[WorldRole.MAIN].meanings.get(item.meaning_id)
        if target is None or target.kind != item.kind:
            raise IntegrityError("compiled Input to Main meaning interface is incompatible")
        transferable.append((item.kind.value, item.meaning_id))
    return {
        "input_main_programs": list(mappings),
        "transferable_meanings": [list(row) for row in transferable],
        "surface_realizer": realizer,
    }


def build_bundle(worlds: dict[WorldRole, CompiledWorld]) -> WorldBundle:
    interface_hash = digest("moth-world-interface/4.9", interface_descriptor(worlds))
    payload = {
        "schema": BUNDLE_SCHEMA,
        "generations": {role.value: worlds[role].generation_id for role in WorldRole},
        "world_hashes": {role.value: worlds[role].world_hash for role in WorldRole},
        "interface_hash": interface_hash,
    }
    bundle_hash = digest("moth-world-bundle/4.9", payload)
    bundle_id = digest("moth-world-bundle-id/4.9", {"bundle_hash": bundle_hash})
    return WorldBundle(
        bundle_id,
        worlds[WorldRole.INPUT].generation_id,
        worlds[WorldRole.MAIN].generation_id,
        worlds[WorldRole.SURFACE].generation_id,
        interface_hash,
        bundle_hash,
    )


def verify_bundle(bundle: WorldBundle, worlds: dict[WorldRole, CompiledWorld]) -> None:
    if bundle != build_bundle(worlds):
        raise IntegrityError("World bundle generation, interface, or hash mismatch")


def _program_ids(program: GroundedProgram) -> tuple[str, ...]:
    return tuple(sorted({
        program.instruction_id, program.operation_id, *program.slots.values(),
        *program.bindings.keys(), *program.bindings.values(),
    }))


def stage_receipt(
    role: WorldRole, world: CompiledWorld, program: GroundedProgram,
    settlement: Settlement, bundle: WorldBundle,
) -> WorldStageReceipt:
    if world.world_role != role or settlement.generation_id != world.generation_id:
        raise IntegrityError("settlement is bound to the wrong World generation")
    if settlement.violation_count != 0 or settlement.proof_count != 1:
        raise IntegrityError("only one zero-violation settlement may advance")
    selected_owners = []
    for identifier in _program_ids(program):
        selected_owners.extend(owner.canonical() for owner in _meaning(world, identifier).owners)
    edge_by_id = {edge.edge_id: edge for edge in world.edges}
    for identifier in settlement.proof_ids:
        edge = edge_by_id.get(identifier)
        if edge is None or not edge.owners:
            raise IntegrityError("settlement proof provenance is absent")
        selected_owners.extend(owner.canonical() for owner in edge.owners)
    provenance_hash = digest(
        "moth-world-provenance/4.9",
        sorted(selected_owners, key=lambda item: canonical_bytes(item)),
    )
    input_hash = digest("moth-world-stage-input/4.9", {
        "bundle_id": bundle.bundle_id,
        "program": asdict(program),
    })
    settlement_hash = digest("moth-world-settlement/4.9", asdict(settlement))
    return WorldStageReceipt(
        role, bundle.bundle_id, world.generation_id, world.world_hash,
        input_hash, settlement_hash,
        provenance_hash, settlement.output_kind,
        sha256_bytes(canonical_bytes(settlement.output)), settlement.total_energy_units,
        settlement.violation_count, settlement.proof_count, True,
    )


def make_handoff(
    bundle: WorldBundle, source_world: CompiledWorld, target_world: CompiledWorld,
    source_receipt: WorldStageReceipt, *, payload_kind: str, payload: Any,
) -> WorldHandoff:
    base = {
        "schema": HANDOFF_SCHEMA,
        "bundle_id": bundle.bundle_id,
        "source_role": source_world.world_role.value,
        "target_role": target_world.world_role.value,
        "source_generation_id": source_world.generation_id,
        "target_generation_id": target_world.generation_id,
        "payload_kind": payload_kind,
        "payload": payload,
        "source_settlement_hash": source_receipt.settlement_hash,
        "provenance_hash": source_receipt.provenance_hash,
    }
    value = WorldHandoff(
        bundle.bundle_id, source_world.world_role, target_world.world_role,
        source_world.generation_id, target_world.generation_id, payload_kind, payload,
        source_receipt.settlement_hash, source_receipt.provenance_hash,
        digest("moth-world-handoff/4.9", base),
    )
    verify_handoff(value, bundle, source_world, target_world, source_receipt)
    return value


def verify_handoff(
    handoff: WorldHandoff, bundle: WorldBundle, source_world: CompiledWorld,
    target_world: CompiledWorld, source_receipt: WorldStageReceipt,
) -> None:
    expected_kind = _ALLOWED.get((handoff.source_role, handoff.target_role))
    if expected_kind != handoff.payload_kind:
        raise IntegrityError("invalid World handoff direction or payload kind")
    if handoff.bundle_id != bundle.bundle_id:
        raise IntegrityError("World handoff bundle mismatch")
    if handoff.source_role != source_world.world_role or handoff.target_role != target_world.world_role:
        raise IntegrityError("World handoff role mismatch")
    if handoff.source_generation_id != source_world.generation_id:
        raise IntegrityError("World handoff source generation mismatch")
    if handoff.target_generation_id != target_world.generation_id:
        raise IntegrityError("World handoff target generation mismatch")
    if handoff.source_settlement_hash != source_receipt.settlement_hash:
        raise IntegrityError("World handoff settlement mismatch")
    if (
        source_receipt.role != source_world.world_role
        or source_receipt.bundle_id != bundle.bundle_id
        or source_receipt.generation_id != source_world.generation_id
        or source_receipt.world_hash != source_world.world_hash
        or not source_receipt.verified
    ):
        raise IntegrityError("World handoff source stage receipt is invalid")
    if handoff.provenance_hash != source_receipt.provenance_hash:
        raise IntegrityError("World handoff provenance mismatch")
    base = handoff.canonical()
    base.pop("handoff_hash")
    if handoff.handoff_hash != digest("moth-world-handoff/4.9", base):
        raise IntegrityError("World handoff hash mismatch")
    canonical_bytes(handoff.payload)


def handoff_from_dict(value: dict[str, Any]) -> WorldHandoff:
    if value.get("schema") != HANDOFF_SCHEMA:
        raise IntegrityError("cross-runtime World handoff refused")
    return WorldHandoff(
        str(value["bundle_id"]), WorldRole(str(value["source_role"])),
        WorldRole(str(value["target_role"])), str(value["source_generation_id"]),
        str(value["target_generation_id"]), str(value["payload_kind"]), value["payload"],
        str(value["source_settlement_hash"]), str(value["provenance_hash"]),
        str(value["handoff_hash"]),
    )
