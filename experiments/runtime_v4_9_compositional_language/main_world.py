"""One generic disposable Main factor World compiled by unmodified Runtime 4.9."""

from __future__ import annotations

import json

from moth_runtime_v4_9.compiler import compile_sources
from moth_runtime_v4_9.encoder import DeterministicEncoder
from moth_runtime_v4_9.energy import settle, verify_settlement
from moth_runtime_v4_9.grounding import ground_prompt
from moth_runtime_v4_9.model import CompiledWorld, Settlement, WorldRole

from .model import TypedHandoff


def _quoted(value) -> str:
    return json.dumps(json.dumps(value, separators=(",", ":")))


def source() -> str:
    values = [
        ("yes", "true"), ("no", "false"),
        ("proposed", "PROPOSED"), ("backup", "BACKUP"), ("none", "NONE"),
        ("reason-none", "NONE"), ("reason-resource", "RESOURCE"),
        ("reason-permission", "PERMISSION"), ("reason-deadline", "DEADLINE"),
    ]
    fields = [
        "proposed-resource", "proposed-permission", "proposed-deadline",
        "backup-resource", "backup-permission", "backup-deadline",
    ]
    schema = {
        "type": "object",
        "properties": {name: {"type": "string"} for name in fields},
        "required": fields,
        "additionalProperties": False,
    }
    validity_rows = []
    diagnosis_rows = []
    for resource in ("no", "yes"):
        for permission in ("no", "yes"):
            for deadline in ("no", "yes"):
                valid = "yes" if resource == permission == deadline == "yes" else "no"
                validity_rows.append([resource, permission, deadline, valid])
                reason = (
                    "reason-resource" if resource == "no" else
                    "reason-permission" if permission == "no" else
                    "reason-deadline" if deadline == "no" else "reason-none"
                )
                diagnosis_rows.append([resource, permission, deadline, reason])
    validity = {
        "ports": [
            {"name": "resource", "domain": "boolean"},
            {"name": "permission", "domain": "boolean"},
            {"name": "deadline", "domain": "boolean"},
            {"name": "valid", "domain": "boolean"},
        ],
        "allowed_tuples": validity_rows,
    }
    selection = {
        "ports": [
            {"name": "proposed-valid", "domain": "boolean"},
            {"name": "backup-valid", "domain": "boolean"},
            {"name": "selected", "domain": "selection"},
        ],
        "allowed_tuples": [
            ["yes", "yes", "proposed"], ["yes", "no", "proposed"],
            ["no", "yes", "backup"], ["no", "no", "none"],
        ],
    }
    diagnosis = {
        "ports": [
            {"name": "resource", "domain": "boolean"},
            {"name": "permission", "domain": "boolean"},
            {"name": "deadline", "domain": "boolean"},
            {"name": "reason", "domain": "failure-reason"},
        ],
        "allowed_tuples": diagnosis_rows,
    }
    steps: list[dict] = []
    for field in fields:
        steps.append({"opcode": "CREATE_VARIABLE", "instance": field, "domain": "boolean"})
    for name, domain in (
        ("proposed-valid", "boolean"), ("backup-valid", "boolean"),
        ("selected-plan", "selection"), ("failure-reason", "failure-reason"),
    ):
        steps.append({"opcode": "CREATE_VARIABLE", "instance": name, "domain": domain})
    for candidate in ("proposed", "backup"):
        factor = f"{candidate}-validity"
        steps.append({"opcode": "INSTANTIATE_FACTOR", "instance": factor, "template": "validity"})
        for port in ("resource", "permission", "deadline"):
            steps.append({"opcode": "BIND_PORT", "factor": factor, "port": port, "variable": f"{candidate}-{port}"})
        steps.append({"opcode": "BIND_PORT", "factor": factor, "port": "valid", "variable": f"{candidate}-valid"})
    steps.append({"opcode": "INSTANTIATE_FACTOR", "instance": "selection", "template": "selection"})
    for port, variable in (
        ("proposed-valid", "proposed-valid"), ("backup-valid", "backup-valid"), ("selected", "selected-plan"),
    ):
        steps.append({"opcode": "BIND_PORT", "factor": "selection", "port": port, "variable": variable})
    steps.append({"opcode": "INSTANTIATE_FACTOR", "instance": "diagnosis", "template": "diagnosis"})
    for port in ("resource", "permission", "deadline"):
        steps.append({"opcode": "BIND_PORT", "factor": "diagnosis", "port": port, "variable": f"proposed-{port}"})
    steps.append({"opcode": "BIND_PORT", "factor": "diagnosis", "port": "reason", "variable": "failure-reason"})
    for field in fields:
        steps.append({"opcode": "CLAMP_FROM_PROMPT", "variable": field, "field": field})
    for ordinal, (variable, label) in enumerate((
        ("proposed-valid", "proposed-valid"),
        ("backup-valid", "backup-valid"),
        ("selected-plan", "selected-plan"),
        ("failure-reason", "failure-reason"),
    )):
        steps.append({"opcode": "EXPOSE_OUTPUT", "variable": variable, "ordinal": ordinal, "label": label})

    lines = ['Scalar type "symbol" selects kernel type "STRING".']
    lines += [f'Value "{name}" has type "symbol" and canonical JSON {_quoted(value)}.' for name, value in values]
    lines += [
        f'Structured schema "decision-input" is canonical JSON Schema {_quoted(schema)}.',
        *[f'Schema field "{field}" in schema "decision-input" has type "symbol" and is required.' for field in fields],
        f'Finite domain "boolean" is canonical value JSON {_quoted(["no", "yes"])}.',
        f'Finite domain "selection" is canonical value JSON {_quoted(["proposed", "backup", "none"])}.',
        f'Finite domain "failure-reason" is canonical value JSON {_quoted(["reason-none", "reason-resource", "reason-permission", "reason-deadline"])}.',
        f'Factor template "validity" is canonical table JSON {_quoted(validity)}.',
        f'Factor template "selection" is canonical table JSON {_quoted(selection)}.',
        f'Factor template "diagnosis" is canonical table JSON {_quoted(diagnosis)}.',
        f'Factor program "validate-and-select" is canonical instruction JSON {_quoted(steps)}.',
        'Operation "factor-settle" selects kernel primitive "FACTOR_SETTLEMENT".',
        'Output schema "answer-json" selects kernel schema "ANSWER_WITH_PROOF".',
        'Instruction "factor-settle" selects operation "factor-settle" accepts "Settle {PROGRAM} with {BINDINGS} using {SCHEMA}.".',
        "",
    ]
    return "\n".join(lines)


def compile_main_world() -> tuple[CompiledWorld, DeterministicEncoder]:
    encoder = DeterministicEncoder()
    return compile_sources(
        {"generic-decision.moth": source()}, encoder=encoder, world_role=WorldRole.MAIN,
    ), encoder


def settle_main(world: CompiledWorld, encoder: DeterministicEncoder, handoff: TypedHandoff) -> Settlement:
    bindings = ", ".join(f"{key} = {value}" for key, value in sorted(handoff.bindings.items()))
    prompt = f"Settle validate-and-select with {bindings} using answer-json."
    program = ground_prompt(world, prompt, encoder=encoder)
    result = settle(world, program)
    verify_settlement(world, program, result)
    return result
