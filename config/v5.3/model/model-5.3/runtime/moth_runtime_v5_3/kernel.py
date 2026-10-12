"""Timed orchestration of the frozen Runtime 5.0 settlement primitives."""

from __future__ import annotations

from dataclasses import asdict
import time
from typing import Any

from moth_runtime_v5_3.legacy.canonical import canonical_bytes, digest, normalize_text
from moth_runtime_v5_3.legacy.energy import SettlementFailure
from moth_runtime_v5_3.legacy.grounding import GroundingFailure, QueryEncoder, ground_prompt
from moth_runtime_v5_3.legacy.handoff import (
    make_handoff, main_request_from_input, program_from_main_request,
    stage_receipt, surface_program_from_semantic_result, verify_bundle,
)
from moth_runtime_v5_3.legacy.model import (
    CompiledWorld, IntegrityError, RefusalCode, WorldBundle, WorldHandoff,
    WorldRole, WorldStageReceipt,
)
from moth_runtime_v5_3.legacy.runtime import (
    _base_result, _finish, _refusal, _role_settlement, _stage_record,
    _verify_role_settlement,
)
from moth_runtime_v5_3.legacy.semantic import semantic_graph_hash


def query_worlds_timed(
    worlds: dict[WorldRole, CompiledWorld], bundle: WorldBundle, prompt: str, *,
    encoder: QueryEncoder | None = None,
    thresholds: dict[str, dict[str, float]] | None = None,
    modality: str = "text",
) -> tuple[
    dict[str, Any], tuple[WorldStageReceipt, ...], tuple[WorldHandoff, ...],
    dict[str, int],
]:
    timings: dict[str, int] = {}
    normalized = normalize_text(prompt)
    phase = time.perf_counter_ns()
    try:
        verify_bundle(bundle, worlds)
        base, input_hash = _base_result(bundle, worlds, normalized, modality)
    except (IntegrityError, ValueError, OverflowError) as exc:
        raise IntegrityError("Runtime 5.3 asset bundle failed verification") from exc
    timings["bundle_verification_ns"] = time.perf_counter_ns() - phase
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
        count = token_counter(normalized) if token_counter else len(normalized.split())
        if count > 128:
            raise GroundingFailure(RefusalCode.RESOURCE_LIMIT, "prompt exceeds 128 tokens", {})
        input_world = worlds[WorldRole.INPUT]
        main_world = worlds[WorldRole.MAIN]

        phase = time.perf_counter_ns()
        input_program = ground_prompt(
            input_world, normalized, encoder=encoder, thresholds=thresholds,
        )
        graph_hash = semantic_graph_hash(input_program)
        base["episode_id"] = digest("moth-world-episode/5.0", {
            "input_hash": input_hash, "semantic_graph_hash": graph_hash,
        })
        grounding_record = {
            "phase": "INPUT_WORLD", "candidate_world": "INPUT",
            "program": asdict(input_program), "semantic_graph_hash": graph_hash,
            "grounding_hash": digest("moth-world-grounding/5.0", asdict(input_program)),
        }
        timings["input_grounding_ns"] = time.perf_counter_ns() - phase

        phase = time.perf_counter_ns()
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
        records.append(_stage_record(
            input_world, input_program, input_settlement, input_receipt,
        ))
        timings["input_settlement_ns"] = time.perf_counter_ns() - phase

        phase = time.perf_counter_ns()
        input_handoff = make_handoff(
            bundle, input_world, main_world, input_receipt,
            payload_kind="MAIN_REQUEST", payload=input_settlement.output,
        )
        handoffs.append(input_handoff)
        main_program = program_from_main_request(
            input_world, main_world, input_settlement.output,
            handoff_hash=input_handoff.handoff_hash,
        )
        timings["input_main_handoff_ns"] = time.perf_counter_ns() - phase

        phase = time.perf_counter_ns()
        main_settlement = _role_settlement(WorldRole.MAIN, main_world, main_program)
        _verify_role_settlement(WorldRole.MAIN, main_world, main_program, main_settlement)
        main_receipt = stage_receipt(
            WorldRole.MAIN, main_world, main_program, main_settlement, bundle,
        )
        receipts.append(main_receipt)
        records.append(_stage_record(main_world, main_program, main_settlement, main_receipt))
        timings["main_settlement_ns"] = time.perf_counter_ns() - phase

        phase = time.perf_counter_ns()
        main_handoff = make_handoff(
            bundle, main_world, worlds[WorldRole.SURFACE], main_receipt,
            payload_kind="SEMANTIC_RESULT", payload=main_settlement.output,
        )
        handoffs.append(main_handoff)
        surface_world = worlds[WorldRole.SURFACE]
        surface_program = surface_program_from_semantic_result(
            main_world, surface_world, main_settlement.output,
            handoff_hash=main_handoff.handoff_hash,
        )
        timings["main_surface_handoff_ns"] = time.perf_counter_ns() - phase

        phase = time.perf_counter_ns()
        surface_settlement = _role_settlement(
            WorldRole.SURFACE, surface_world, surface_program,
        )
        _verify_role_settlement(
            WorldRole.SURFACE, surface_world, surface_program, surface_settlement,
        )
        surface_response = surface_settlement.output
        semantic_result = main_settlement.output
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
        timings["surface_settlement_ns"] = time.perf_counter_ns() - phase
    except GroundingFailure as exc:
        result = _refusal(
            base, stage="GROUNDING", code=exc.code, message=exc.message,
            context=exc.context, grounding=grounding_record,
            stage_records=records, handoffs=handoffs,
        )
        return result, tuple(receipts), tuple(handoffs), timings
    except SettlementFailure as exc:
        stage = (WorldRole.INPUT, WorldRole.MAIN, WorldRole.SURFACE)[min(len(receipts), 2)].value
        result = _refusal(
            base, stage=stage, code=exc.code, message=exc.message,
            context=exc.context, grounding=grounding_record,
            stage_records=records, handoffs=handoffs,
        )
        return result, tuple(receipts), tuple(handoffs), timings
    except (IntegrityError, ValueError, OverflowError) as exc:
        stage = (WorldRole.INPUT, WorldRole.MAIN, WorldRole.SURFACE)[min(len(receipts), 2)].value
        result = _refusal(
            base, stage=stage, code=RefusalCode.INTEGRITY_FAILURE,
            message="three-World query failed closed", context={"diagnostic": str(exc)},
            grounding=grounding_record, stage_records=records, handoffs=handoffs,
        )
        return result, tuple(receipts), tuple(handoffs), timings

    base.update({
        "status": "ANSWER", "grounding": grounding_record, "stages": records,
        "handoffs": [item.canonical() for item in handoffs],
        "output": {"kind": surface_settlement.output["kind"],
                   "value": surface_settlement.output["value"]},
    })
    return _finish(base), tuple(receipts), tuple(handoffs), timings


# Stable public 5.3 reasoning interface.
from .reasoning import Kernel53, ReasoningRequest, ReasoningResult
