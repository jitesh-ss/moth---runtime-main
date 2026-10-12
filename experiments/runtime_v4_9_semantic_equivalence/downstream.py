"""Disposable unmodified Runtime 4.9 factor cascade for semantic outputs."""

from __future__ import annotations

import json

from moth_runtime_v4_9.compiler import compile_sources
from moth_runtime_v4_9.encoder import DeterministicEncoder
from moth_runtime_v4_9.energy import settle, verify_settlement
from moth_runtime_v4_9.grounding import ground_prompt
from moth_runtime_v4_9.model import CompiledWorld, WorldRole


def _quoted_json(value) -> str:
    return json.dumps(json.dumps(value, separators=(",", ":")))


def source() -> str:
    input_schema = {
        "type": "object",
        "properties": {"fact": {"type": "string"}},
        "required": ["fact"],
        "additionalProperties": False,
    }
    effect = {
        "ports": [
            {"name": "fact", "domain": "semantic-fact"},
            {"name": "outcome", "domain": "plan-outcome"},
        ],
        "allowed_tuples": [
            ["direct-courier-lacks-cold-storage", "plan-invalid"],
            ["direct-courier-has-cold-storage", "plan-valid"],
        ],
    }
    steps = [
        {"opcode": "CREATE_VARIABLE", "instance": "fact", "domain": "semantic-fact"},
        {"opcode": "CREATE_VARIABLE", "instance": "outcome", "domain": "plan-outcome"},
        {"opcode": "INSTANTIATE_FACTOR", "instance": "effect", "template": "capability-effect"},
        {"opcode": "BIND_PORT", "factor": "effect", "port": "fact", "variable": "fact"},
        {"opcode": "BIND_PORT", "factor": "effect", "port": "outcome", "variable": "outcome"},
        {"opcode": "CLAMP_FROM_PROMPT", "variable": "fact", "field": "fact"},
        {"opcode": "EXPOSE_OUTPUT", "variable": "outcome", "ordinal": 0, "label": "outcome"},
    ]
    return "\n".join([
        'Scalar type "symbol" selects kernel type "STRING".',
        f'Value "direct-courier-lacks-cold-storage" has type "symbol" and canonical JSON {_quoted_json("NEGATIVE_CAPABILITY")}.',
        f'Value "direct-courier-has-cold-storage" has type "symbol" and canonical JSON {_quoted_json("POSITIVE_CAPABILITY")}.',
        f'Value "plan-invalid" has type "symbol" and canonical JSON {_quoted_json("PLAN_INVALID")}.',
        f'Value "plan-valid" has type "symbol" and canonical JSON {_quoted_json("PLAN_VALID")}.',
        f'Structured schema "inputs" is canonical JSON Schema {_quoted_json(input_schema)}.',
        'Schema field "fact" in schema "inputs" has type "symbol" and is required.',
        f'Finite domain "semantic-fact" is canonical value JSON {_quoted_json(["direct-courier-lacks-cold-storage", "direct-courier-has-cold-storage"])}.',
        f'Finite domain "plan-outcome" is canonical value JSON {_quoted_json(["plan-invalid", "plan-valid"])}.',
        f'Factor template "capability-effect" is canonical table JSON {_quoted_json(effect)}.',
        f'Factor program "evaluate-capability" is canonical instruction JSON {_quoted_json(steps)}.',
        'Operation "factor-settle" selects kernel primitive "FACTOR_SETTLEMENT".',
        'Output schema "answer-json" selects kernel schema "ANSWER_WITH_PROOF".',
        'Instruction "factor-settle" selects operation "factor-settle" accepts "Settle {PROGRAM} with {BINDINGS} using {SCHEMA}.".',
        "",
    ])


def compile_downstream_world() -> tuple[CompiledWorld, DeterministicEncoder]:
    encoder = DeterministicEncoder()
    world = compile_sources(
        {"semantic-effect.moth": source()},
        encoder=encoder,
        world_role=WorldRole.MAIN,
    )
    return world, encoder


def settle_downstream(
    world: CompiledWorld,
    encoder: DeterministicEncoder,
    semantic_meaning_key: str,
):
    prompt = (
        "Settle evaluate-capability with fact = "
        f"{semantic_meaning_key} using answer-json."
    )
    program = ground_prompt(world, prompt, encoder=encoder)
    result = settle(world, program)
    verify_settlement(world, program, result)
    return result
