"""Public canonical query interface for the capability lab."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .canonical import canonical_bytes, digest, normalize_text, sha256_bytes
from .energy import SettlementFailure, settle, verify_settlement
from .grounding import GroundingFailure, QueryEncoder, ground_prompt
from .model import CompiledField, IntegrityError, RefusalCode

RESULT_SCHEMA = "moth-capability-result/4.7"
RUNTIME_LABEL = "4.7"


def _receipt(result: dict[str, Any]) -> dict[str, Any]:
    payload = {key: value for key, value in result.items() if key != "replay"}
    replay = dict(result.get("replay", {}))
    replay.pop("result_hash", None)
    payload["replay"] = replay
    replay["result_hash"] = sha256_bytes(canonical_bytes(payload))
    return replay


def _episode(field: CompiledField, prompt: str, modality: str) -> tuple[str, str]:
    input_hash = digest("moth-capability-input/4.7", {
        "generation_id": field.generation_id, "modality": modality, "prompt": prompt,
    })
    return digest("moth-capability-episode/4.7", {"input_hash": input_hash}), input_hash


def _refusal(field: CompiledField, prompt: str, modality: str, code: RefusalCode,
             message: str, context: dict[str, Any]) -> dict[str, Any]:
    episode_id, input_hash = _episode(field, prompt, modality)
    result: dict[str, Any] = {
        "schema": RESULT_SCHEMA,
        "runtime": RUNTIME_LABEL,
        "capability_level": field.capability_level,
        "status": "REFUSAL",
        "generation_id": field.generation_id,
        "episode_id": episode_id,
        "refusal": {"code": code.value, "message": message, "grounded_context": context},
        "execution": {"performed": False, "dispatch_count": 0},
        "replay": {"input_hash": input_hash, "field_hash": field.field_hash},
    }
    result["replay"] = _receipt(result)
    return result


def query(
    field: CompiledField, prompt: str, *, encoder: QueryEncoder | None = None,
    thresholds: dict[str, dict[str, float]] | None = None, modality: str = "text",
) -> dict[str, Any]:
    """Ground, minimize, verify, and render one isolated transient episode."""
    normalized = normalize_text(prompt)
    # Frozen refusal precedence begins with integrity, then resource, modality.
    if any(source.sha256 != sha256_bytes(source.text.encode("utf-8"))
           for source in field.sources.values()):
        return _refusal(field, normalized, modality, RefusalCode.INTEGRITY_FAILURE,
                        "compiled source hash mismatch", {})
    if any(edge.relation_id not in field.meanings or edge.source_id not in field.meanings or
           edge.destination_id not in field.meanings or not edge.owners for edge in field.edges):
        return _refusal(field, normalized, modality, RefusalCode.INTEGRITY_FAILURE,
                        "semantic edge closure or provenance failed", {})
    token_counter = getattr(encoder, "token_count", None)
    token_count = token_counter(normalized) if token_counter is not None else len(normalized.split())
    if token_count > 128:
        return _refusal(field, normalized, modality, RefusalCode.RESOURCE_LIMIT,
                        "prompt exceeds 128 tokens", {})
    if modality != "text":
        return _refusal(field, normalized, modality, RefusalCode.UNSUPPORTED_MODALITY,
                        "only the compiled text adapter is enabled", {})
    try:
        program = ground_prompt(field, normalized, encoder=encoder, thresholds=thresholds)
        candidate = settle(field, program)
        verify_settlement(field, program, candidate)
    except GroundingFailure as exc:
        return _refusal(field, normalized, modality, exc.code, exc.message, exc.context)
    except SettlementFailure as exc:
        return _refusal(field, normalized, modality, exc.code, exc.message, exc.context)
    except IntegrityError as exc:
        return _refusal(field, normalized, modality, RefusalCode.INTEGRITY_FAILURE, str(exc), {})
    except (ValueError, OverflowError) as exc:
        return _refusal(field, normalized, modality, RefusalCode.INTEGRITY_FAILURE,
                        "query failed closed", {"diagnostic": str(exc)})

    episode_id, input_hash = _episode(field, normalized, modality)
    edge_by_id = {edge.edge_id: edge for edge in field.edges}
    provenance = []
    for edge_id in candidate.proof_ids:
        edge = edge_by_id[edge_id]
        provenance.append({
            "semantic_edge_id": edge_id,
            "owners": [owner.canonical() for owner in edge.owners],
        })
    result: dict[str, Any] = {
        "schema": RESULT_SCHEMA,
        "runtime": RUNTIME_LABEL,
        "capability_level": field.capability_level,
        "status": "ANSWER",
        "generation_id": field.generation_id,
        "episode_id": episode_id,
        "grounded_program": {
            "instruction_id": program.instruction_id,
            "operation_id": program.operation_id,
            "operation": program.operation,
            "slots": dict(sorted(program.slots.items())),
            "bindings": dict(sorted(program.bindings.items())),
            "steps": list(program.steps),
            "grounding": program.grounding,
        },
        "output": {"kind": candidate.output_kind, "value": candidate.output},
        "energy": {
            "total_units": candidate.total_energy_units,
            "violation_count": candidate.violation_count,
            "grounding_cost_units": candidate.grounding_cost_units,
        },
        "proof": {
            "proof_count": candidate.proof_count,
            "semantic_edge_ids": list(candidate.proof_ids),
            "provenance": provenance,
        },
        "execution": {"performed": False, "dispatch_count": 0},
        "replay": {"input_hash": input_hash, "field_hash": field.field_hash},
    }
    result["replay"] = _receipt(result)
    return result


def result_bytes(result: dict[str, Any]) -> bytes:
    return canonical_bytes(result)


def verify_result_receipt(result: dict[str, Any]) -> None:
    replay = result.get("replay")
    if not isinstance(replay, dict) or replay.get("result_hash") != _receipt(result).get("result_hash"):
        raise IntegrityError("result receipt hash mismatch")

