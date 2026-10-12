"""Prompt-only autonomous JSON candidate using Runtime 5.2 settlement."""

from __future__ import annotations

import json
from typing import Any

from moth_runtime_v5_0.canonical import canonical_bytes, digest, normalize_text, sha256_bytes
from moth_runtime_v5_2.compile.hcf import compile_hcf_source
from moth_runtime_v5_2.energy.loader import load_hcf_field
from moth_runtime_v5_2.energy.schema import Level, Runtime52Failure
from moth_runtime_v5_2.energy.settlement import settle

from .compiler import Candidate52, TRIGGER
from .operations import JsonSkillFailure, depth, extract_source, realize, record_count, render, route


SCHEMA = "moth-autonomous-json-result/5.2-experiment"
REQUIRED_WORKFLOW = {
    "DETECT_JSON_INTENT",
    "PARSE_SOURCE_DATA",
    "BIND_OUTPUT_SHAPE",
    "PARSE_EMITTED_JSON",
    "VERIFY_EXACT_DATA",
    "VERIFY_REQUESTED_SHAPE",
    "BIND_HASHES",
    "EMIT_JSON",
}


def refusal(code: str, message: str, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    body = {
        "schema": SCHEMA,
        "status": "REFUSAL",
        "code": code,
        "message": message,
        "response": None,
        "value": None,
        "route": None,
        "hcf": None,
        "skill": None,
        "execution": {"network": 0, "tool_dispatches": 0, "code_executions": 0, "writes": 0},
        "evidence": evidence or {},
    }
    return {**body, "result_hash": digest(SCHEMA, body)}


def settle_json_prompt(
    candidate: Candidate52,
    prompt: str,
    *,
    skill_available: bool = True,
    router_enabled: bool = True,
) -> dict[str, Any]:
    raw_prompt = prompt.replace("\r\n", "\n").replace("\r", "\n").strip()
    prompt_hash = sha256_bytes(raw_prompt.encode("utf-8"))
    try:
        if not router_enabled:
            raise JsonSkillFailure("ROUTER_DISABLED", "autonomous routing is disabled")
        if not skill_available:
            raise JsonSkillFailure("SKILL_UNAVAILABLE", "JSON skill is not available")
        reopened_skill = candidate.store.open(candidate.skill.envelope.file_hash)
        reopened_field = candidate.store.open(candidate.field.envelope.file_hash)
        if reopened_skill.logical_hash != candidate.skill.envelope.logical_hash or reopened_field.logical_hash != candidate.field.envelope.logical_hash:
            raise JsonSkillFailure("INTEGRITY_FAILURE", "compiled JSON objects changed")
        if not REQUIRED_WORKFLOW.issubset(set(candidate.skill.workflow)):
            raise JsonSkillFailure("POLICY_INVALID", "compiled workflow lacks required verification operations")
        if len(raw_prompt.encode("utf-8")) > 32768:
            raise JsonSkillFailure("RESOURCE_LIMIT", "prompt exceeds byte limit")
        source, instruction = extract_source(raw_prompt)
        if depth(source) > 8 or record_count(source) > 256:
            raise JsonSkillFailure("RESOURCE_LIMIT", "source exceeds depth or record limit")
        operation = route(instruction)
        hcf_source = {
            "schema": "moth-hcf-source/5.2",
            "entries": [
                {
                    "meaning_id": f"prompt.{prompt_hash}.json-trigger",
                    "effect": "REQUIRE",
                    "scope": "skill.trigger",
                    "value": TRIGGER,
                }
            ],
            "activations": [],
        }
        hcf_envelope = compile_hcf_source(
            candidate.store, candidate.foundation, hcf_source, Level.CONTEXT
        )
        hcf_field = load_hcf_field(hcf_envelope, candidate.foundation)
        settlement = settle(candidate.foundation, (hcf_field,))
        if settlement.candidate_id != "skill.autonomous-json-formatting":
            raise JsonSkillFailure("SKILL_NOT_APPLICABLE", "JSON candidate was not selected")
        value, layout = realize(source, operation)
        response = render(value, layout)
        recovered = json.loads(response)
        if canonical_bytes(recovered) != canonical_bytes(value):
            raise JsonSkillFailure("VALUE_MISMATCH", "emitted JSON changed the planned value")
        route_body = {
            **operation,
            "source_hash": digest("moth-json-source/5.2-experiment", source),
            "layout": layout,
        }
        route_receipt = {
            **route_body,
            "route_hash": digest("moth-json-route/5.2-experiment", route_body),
        }
        body = {
            "schema": SCHEMA,
            "status": "ANSWER",
            "code": None,
            "message": None,
            "response": response,
            "value": recovered,
            "route": route_receipt,
            "hcf": settlement.trace,
            "skill": {
                "field_object_hash": candidate.field.envelope.file_hash,
                "compilation_id": candidate.skill.compilation_id,
                "policy_hash": candidate.skill.policy_hash,
                "skill_object_hash": candidate.skill.envelope.file_hash,
                "candidate_id": settlement.candidate_id,
            },
            "execution": {"network": 0, "tool_dispatches": 0, "code_executions": 0, "writes": 0},
            "evidence": {
                "prompt_hash": prompt_hash,
                "response_hash": sha256_bytes(response.encode("utf-8")),
                "hcf_object_hash": hcf_envelope.file_hash,
                "foundation_object_hash": candidate.foundation.file_hash,
            },
        }
        return {**body, "result_hash": digest(SCHEMA, body)}
    except JsonSkillFailure as exc:
        return refusal(exc.code, exc.message, {"prompt_hash": prompt_hash, **exc.context})
    except Runtime52Failure as exc:
        return refusal(exc.code, str(exc), {"prompt_hash": prompt_hash, **exc.context})

