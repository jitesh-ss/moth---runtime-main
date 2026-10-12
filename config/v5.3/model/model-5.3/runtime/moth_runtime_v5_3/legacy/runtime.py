"""Fixed Input -> Main -> Surface orchestration for Runtime 5.0."""

from __future__ import annotations

from dataclasses import asdict, replace
from typing import Any

from .canonical import canonical_bytes, digest, normalize_text, sha256_bytes
from .energy import SettlementFailure, scalar_energy, settle, verify_settlement
from .grounding import GroundingFailure, QueryEncoder, ground_prompt
from .handoff import (
    handoff_from_dict, main_request_from_input, make_handoff,
    program_from_main_request, stage_receipt,
    surface_program_from_semantic_result, verify_bundle,
    verify_handoff,
)
from .model import (
    CompiledWorld, GroundedProgram, IntegrityError, RefusalCode, Settlement,
    WorldBundle, WorldHandoff, WorldRole, WorldStageReceipt,
)
from .semantic import semantic_graph_hash, verify_semantic_program

RESULT_SCHEMA = "moth-world-result/5.0"
RUNTIME_LABEL = "5.0"


def _input_hash(bundle: WorldBundle, prompt: str, modality: str) -> str:
    return digest("moth-world-input/5.0", {
        "bundle_id": bundle.bundle_id, "modality": modality,
        "prompt": normalize_text(prompt),
    })


def _result_receipt(result: dict[str, Any]) -> str:
    payload = {key: value for key, value in result.items() if key != "replay"}
    replay = dict(result.get("replay", {}))
    replay.pop("result_hash", None)
    payload["replay"] = replay
    return sha256_bytes(canonical_bytes(payload))


def _provenance(world: CompiledWorld, program: GroundedProgram,
                settlement: Settlement) -> dict[str, Any]:
    identifiers = sorted({
        program.instruction_id, program.operation_id, *program.slots.values(),
        *program.bindings.keys(), *program.bindings.values(),
    })
    interpretation = program.grounding.get("semantic_interpretation") if isinstance(program.grounding, dict) else None
    if isinstance(interpretation, dict):
        identifiers.append(str(interpretation["contract_id"]))
    selected = []
    for identifier in identifiers:
        meaning = world.meanings.get(identifier)
        if meaning is None:
            raise IntegrityError("selected meaning is absent from its World")
        selected.append({
            "meaning_id": identifier,
            "owners": [owner.canonical() for owner in meaning.owners],
        })
    edges = {edge.edge_id: edge for edge in world.edges}
    proof = []
    for identifier in settlement.proof_ids:
        edge = edges.get(identifier)
        if edge is None:
            raise IntegrityError("proof edge is absent from its World")
        proof.append({
            "semantic_edge_id": identifier,
            "owners": [owner.canonical() for owner in edge.owners],
        })
    return {"selected_meanings": selected, "proof_edges": proof}


def _stage_record(world: CompiledWorld, program: GroundedProgram,
                  settlement: Settlement, receipt: WorldStageReceipt) -> dict[str, Any]:
    return {
        "role": world.world_role.value,
        "generation_id": world.generation_id,
        "world_hash": world.world_hash,
        "program": asdict(program),
        "settlement": asdict(settlement),
        "receipt": receipt.canonical(),
        "provenance": _provenance(world, program, settlement),
    }


def _role_settlement(
    role: WorldRole, world: CompiledWorld, program: GroundedProgram, *,
    target_world: CompiledWorld | None = None,
) -> Settlement:
    """Project one independently verified kernel minimum into its World contract."""
    if role == WorldRole.INPUT:
        if target_world is None or target_world.world_role != WorldRole.MAIN:
            raise IntegrityError("Input settlement requires the active Main interface")
        verify_semantic_program(world, program)
        request = main_request_from_input(world, target_world, program)
        grounded_slots = len(program.slots) + len(program.bindings)
        energy = scalar_energy(
            grounded_slots=grounded_slots,
            violations=0,
            grounding_cost=program.grounding_cost_units,
        )
        return Settlement(
            "MAIN_REQUEST", request, (), 1, energy, 0,
            program.grounding_cost_units, world.generation_id,
        )
    raw = settle(world, program)
    verify_settlement(world, program, raw)
    if role == WorldRole.MAIN:
        semantic = {
            "semantic_kind": raw.output_kind,
            "value": raw.output,
            "proof_ids": list(raw.proof_ids),
            "proof_count": raw.proof_count,
            "source_generation_id": world.generation_id,
            "semantic_graph_hash": str(program.grounding.get("semantic_graph_hash", "")),
        }
        return replace(raw, output_kind="SEMANTIC_RESULT", output=semantic)
    if role == WorldRole.SURFACE:
        if raw.output_kind != "SURFACE_RESPONSE":
            raise IntegrityError("Surface operation did not produce SURFACE_RESPONSE")
        return raw
    raise IntegrityError("unsupported World role")


def _verify_role_settlement(
    role: WorldRole, world: CompiledWorld, program: GroundedProgram,
    candidate: Settlement, *, target_world: CompiledWorld | None = None,
) -> None:
    expected = _role_settlement(
        role, world, program, target_world=target_world,
    )
    if candidate != expected:
        raise IntegrityError(f"{role.value} contract settlement reconstruction mismatch")


def _base_result(bundle: WorldBundle, worlds: dict[WorldRole, CompiledWorld],
                 prompt: str, modality: str) -> tuple[dict[str, Any], str]:
    input_hash = _input_hash(bundle, prompt, modality)
    episode_id = digest("moth-world-episode/5.0", {"input_hash": input_hash})
    return {
        "schema": RESULT_SCHEMA,
        "runtime": RUNTIME_LABEL,
        "bundle_id": bundle.bundle_id,
        "bundle_hash": bundle.bundle_hash,
        "episode_id": episode_id,
        "worlds": {
            role.value: {
                "generation_id": worlds[role].generation_id,
                "world_hash": worlds[role].world_hash,
            }
            for role in WorldRole
        },
        "execution": {"performed": False, "dispatch_count": 0},
        "replay": {"input_hash": input_hash, "bundle_hash": bundle.bundle_hash},
    }, input_hash


def _finish(result: dict[str, Any]) -> dict[str, Any]:
    result["replay"]["result_hash"] = _result_receipt(result)
    return result


def _refusal(
    base: dict[str, Any], *, stage: str, code: RefusalCode, message: str,
    context: dict[str, Any], grounding: dict[str, Any] | None,
    stage_records: list[dict[str, Any]], handoffs: list[WorldHandoff],
) -> dict[str, Any]:
    base.update({
        "status": "REFUSAL",
        "stage": stage,
        "grounding": grounding,
        "stages": stage_records,
        "handoffs": [item.canonical() for item in handoffs],
        "refusal": {"code": code.value, "message": message, "grounded_context": context},
    })
    return _finish(base)


def query_worlds(
    worlds: dict[WorldRole, CompiledWorld], bundle: WorldBundle, prompt: str, *,
    encoder: QueryEncoder | None = None,
    thresholds: dict[str, dict[str, float]] | None = None,
    modality: str = "text",
) -> tuple[dict[str, Any], tuple[WorldStageReceipt, ...], tuple[WorldHandoff, ...]]:
    """Ground once, then settle and verify the three Worlds exactly once each."""
    normalized = normalize_text(prompt)
    try:
        verify_bundle(bundle, worlds)
        base, input_hash = _base_result(bundle, worlds, normalized, modality)
    except (IntegrityError, ValueError, OverflowError) as exc:
        # A bundle that cannot be verified has no trustworthy World identities
        # to expose in a normal result. Fail closed at the API boundary.
        raise IntegrityError("Runtime 5.0 active bundle failed verification") from exc
    records: list[dict[str, Any]] = []
    receipts: list[WorldStageReceipt] = []
    handoffs: list[WorldHandoff] = []
    grounding_record: dict[str, Any] | None = None

    try:
        if modality != "text":
            raise GroundingFailure(
                RefusalCode.UNSUPPORTED_MODALITY,
                "only the compiled text adapter is enabled", {},
            )
        token_counter = getattr(encoder, "token_count", None)
        token_count = token_counter(normalized) if token_counter else len(normalized.split())
        if token_count > 128:
            raise GroundingFailure(RefusalCode.RESOURCE_LIMIT, "prompt exceeds 128 tokens", {})
        input_world = worlds[WorldRole.INPUT]
        main_world = worlds[WorldRole.MAIN]
        input_program = ground_prompt(
            input_world, normalized, encoder=encoder, thresholds=thresholds,
        )
        graph_hash = semantic_graph_hash(input_program)
        base["episode_id"] = digest("moth-world-episode/5.0", {
            "input_hash": input_hash, "semantic_graph_hash": graph_hash,
        })
        grounding_record = {
            "phase": "INPUT_WORLD",
            "candidate_world": "INPUT",
            "program": asdict(input_program),
            "semantic_graph_hash": graph_hash,
            "grounding_hash": digest("moth-world-grounding/5.0", asdict(input_program)),
        }

        input_settlement = _role_settlement(
            WorldRole.INPUT, input_world, input_program, target_world=main_world,
        )
        _verify_role_settlement(
            WorldRole.INPUT, input_world, input_program, input_settlement,
            target_world=main_world,
        )
        input_receipt = stage_receipt(
            WorldRole.INPUT, input_world, input_program, input_settlement, bundle,
        )
        receipts.append(input_receipt)
        records.append(_stage_record(input_world, input_program, input_settlement, input_receipt))

        main_payload = input_settlement.output
        input_handoff = make_handoff(
            bundle, input_world, worlds[WorldRole.MAIN], input_receipt,
            payload_kind="MAIN_REQUEST", payload=main_payload,
        )
        handoffs.append(input_handoff)

        main_program = program_from_main_request(
            input_world, main_world, main_payload,
            handoff_hash=input_handoff.handoff_hash,
        )
        main_settlement = _role_settlement(
            WorldRole.MAIN, main_world, main_program,
        )
        _verify_role_settlement(
            WorldRole.MAIN, main_world, main_program, main_settlement,
        )
        main_receipt = stage_receipt(
            WorldRole.MAIN, main_world, main_program, main_settlement, bundle,
        )
        receipts.append(main_receipt)
        records.append(_stage_record(main_world, main_program, main_settlement, main_receipt))

        semantic_payload = main_settlement.output
        main_handoff = make_handoff(
            bundle, main_world, worlds[WorldRole.SURFACE], main_receipt,
            payload_kind="SEMANTIC_RESULT", payload=semantic_payload,
        )
        handoffs.append(main_handoff)

        surface_world = worlds[WorldRole.SURFACE]
        surface_program = surface_program_from_semantic_result(
            main_world, surface_world, semantic_payload,
            handoff_hash=main_handoff.handoff_hash,
        )
        surface_settlement = _role_settlement(
            WorldRole.SURFACE, surface_world, surface_program,
        )
        _verify_role_settlement(
            WorldRole.SURFACE, surface_world, surface_program, surface_settlement,
        )
        surface_response = surface_settlement.output
        semantic_result = semantic_payload
        if (
            surface_response.get("kind") != semantic_result.get("semantic_kind")
            or canonical_bytes(surface_response.get("value"))
            != canonical_bytes(semantic_result.get("value"))
            or surface_response.get("semantic_result_hash")
            != digest("moth-world-semantic-result/5.0", semantic_result)
        ):
            raise IntegrityError("Surface World changed the verified semantic result")
        surface_receipt = stage_receipt(
            WorldRole.SURFACE, surface_world, surface_program, surface_settlement, bundle,
        )
        receipts.append(surface_receipt)
        records.append(_stage_record(
            surface_world, surface_program, surface_settlement, surface_receipt,
        ))

    except GroundingFailure as exc:
        result = _refusal(
            base, stage="GROUNDING", code=exc.code, message=exc.message,
            context=exc.context, grounding=grounding_record,
            stage_records=records, handoffs=handoffs,
        )
        return result, tuple(receipts), tuple(handoffs)
    except SettlementFailure as exc:
        stage = (WorldRole.INPUT, WorldRole.MAIN, WorldRole.SURFACE)[min(len(receipts), 2)].value
        result = _refusal(
            base, stage=stage, code=exc.code, message=exc.message,
            context=exc.context, grounding=grounding_record,
            stage_records=records, handoffs=handoffs,
        )
        return result, tuple(receipts), tuple(handoffs)
    except (IntegrityError, ValueError, OverflowError) as exc:
        stage = (WorldRole.INPUT, WorldRole.MAIN, WorldRole.SURFACE)[min(len(receipts), 2)].value
        result = _refusal(
            base, stage=stage, code=RefusalCode.INTEGRITY_FAILURE,
            message="three-World query failed closed", context={"diagnostic": str(exc)},
            grounding=grounding_record, stage_records=records, handoffs=handoffs,
        )
        return result, tuple(receipts), tuple(handoffs)

    base.update({
        "status": "ANSWER",
        "grounding": grounding_record,
        "stages": records,
        "handoffs": [item.canonical() for item in handoffs],
        "output": {
            "kind": surface_settlement.output["kind"],
            "value": surface_settlement.output["value"],
        },
    })
    return _finish(base), tuple(receipts), tuple(handoffs)


def result_bytes(result: dict[str, Any]) -> bytes:
    return canonical_bytes(result)


def verify_result_receipt(result: dict[str, Any]) -> None:
    if result.get("schema") != RESULT_SCHEMA or result.get("runtime") != RUNTIME_LABEL:
        raise IntegrityError("cross-runtime result refused")
    replay = result.get("replay")
    if not isinstance(replay, dict) or replay.get("result_hash") != _result_receipt(result):
        raise IntegrityError("result receipt hash mismatch")


def _program(value: dict[str, Any]) -> GroundedProgram:
    return GroundedProgram(
        str(value["instruction_id"]), str(value["operation_id"]), str(value["operation"]),
        {str(k): str(v) for k, v in value["slots"].items()},
        {str(k): str(v) for k, v in value["bindings"].items()},
        tuple(value["steps"]), int(value["grounding_cost_units"]), value["grounding"],
    )


def _settlement(value: dict[str, Any]) -> Settlement:
    return Settlement(
        str(value["output_kind"]), value["output"], tuple(value["proof_ids"]),
        int(value["proof_count"]), int(value["total_energy_units"]),
        int(value["violation_count"]), int(value["grounding_cost_units"]),
        str(value["generation_id"]), value.get("factor_evidence"),
    )


def _receipt(value: dict[str, Any]) -> WorldStageReceipt:
    return WorldStageReceipt(
        WorldRole(str(value["role"])), str(value["bundle_id"]),
        str(value["generation_id"]),
        str(value["world_hash"]), str(value["input_hash"]),
        str(value["settlement_hash"]), str(value["provenance_hash"]),
        str(value["output_kind"]), str(value["output_hash"]),
        int(value["total_energy_units"]), int(value["violation_count"]),
        int(value["proof_count"]), bool(value["verified"]),
    )


def verify_archived_result(
    result: dict[str, Any], worlds: dict[WorldRole, CompiledWorld],
    bundle: WorldBundle,
) -> tuple[tuple[WorldStageReceipt, ...], tuple[WorldHandoff, ...]]:
    verify_result_receipt(result)
    verify_bundle(bundle, worlds)
    if result.get("bundle_id") != bundle.bundle_id or result.get("bundle_hash") != bundle.bundle_hash:
        raise IntegrityError("result bundle receipt mismatch")
    records = result.get("stages")
    if not isinstance(records, list):
        raise IntegrityError("result stage ledger is malformed")
    receipts: list[WorldStageReceipt] = []
    settlements: dict[WorldRole, Settlement] = {}
    programs: dict[WorldRole, GroundedProgram] = {}
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise IntegrityError("result stage entry is malformed")
        role = WorldRole(str(record["role"]))
        if role != tuple(WorldRole)[index]:
            raise IntegrityError("result stages are out of order")
        program = _program(record["program"])
        if role == WorldRole.INPUT:
            try:
                verify_semantic_program(worlds[role], program)
            except Exception as exc:
                raise IntegrityError("semantic Input evidence failed reconstruction") from exc
        candidate = _settlement(record["settlement"])
        _verify_role_settlement(
            role, worlds[role], program, candidate,
            target_world=worlds[WorldRole.MAIN] if role == WorldRole.INPUT else None,
        )
        expected = stage_receipt(role, worlds[role], program, candidate, bundle)
        stored = _receipt(record["receipt"])
        if stored != expected:
            raise IntegrityError("stage receipt differs from independent reconstruction")
        receipts.append(stored)
        settlements[role] = candidate
        programs[role] = program
    raw_handoffs = result.get("handoffs")
    if not isinstance(raw_handoffs, list):
        raise IntegrityError("result handoff ledger is malformed")
    handoffs = tuple(handoff_from_dict(value) for value in raw_handoffs)
    for handoff in handoffs:
        source_index = tuple(WorldRole).index(handoff.source_role)
        if source_index >= len(receipts):
            raise IntegrityError("handoff has no verified source stage")
        verify_handoff(
            handoff, bundle, worlds[handoff.source_role], worlds[handoff.target_role],
            receipts[source_index],
        )
    if handoffs:
        if handoffs[0].payload != settlements[WorldRole.INPUT].output:
            raise IntegrityError("archived MAIN_REQUEST differs from the verified Input stage")
        reconstructed = program_from_main_request(
            worlds[WorldRole.INPUT], worlds[WorldRole.MAIN], handoffs[0].payload,
            handoff_hash=handoffs[0].handoff_hash,
        )
        if WorldRole.MAIN in programs and programs[WorldRole.MAIN] != reconstructed:
            raise IntegrityError("Main program differs from the verified MAIN_REQUEST")
    if len(handoffs) == 2:
        if handoffs[1].payload != settlements[WorldRole.MAIN].output:
            raise IntegrityError("archived SEMANTIC_RESULT differs from the verified Main stage")
        reconstructed = surface_program_from_semantic_result(
            worlds[WorldRole.MAIN], worlds[WorldRole.SURFACE], handoffs[1].payload,
            handoff_hash=handoffs[1].handoff_hash,
        )
        if WorldRole.SURFACE in programs and programs[WorldRole.SURFACE] != reconstructed:
            raise IntegrityError("Surface program differs from the verified SEMANTIC_RESULT")
    if result.get("status") == "ANSWER":
        if len(receipts) != 3 or len(handoffs) != 2:
            raise IntegrityError("an answer requires three stages and two handoffs")
        output = result.get("output")
        surface = settlements[WorldRole.SURFACE]
        if surface.output_kind != "SURFACE_RESPONSE":
            raise IntegrityError("Surface stage did not settle to SURFACE_RESPONSE")
        expected_output = {
            "kind": surface.output.get("kind"),
            "value": surface.output.get("value"),
        }
        if not isinstance(output, dict) or canonical_bytes(output) != canonical_bytes(expected_output):
            raise IntegrityError("result output differs from Surface settlement")
    return tuple(receipts), handoffs
