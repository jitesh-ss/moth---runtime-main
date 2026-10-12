"""Closed-world prompt grounding for Runtime 4.8.

The prompt can select compiled meanings. It cannot manufacture a value: every
captured slot and every binding is resolved to an identifier already present in
the selected immutable Input World generation.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
import re
from typing import Any, Protocol

import numpy as np

from .canonical import normalize_text
from .model import CompiledWorld, GroundedProgram, Meaning, MeaningType, RefusalCode

Q = 1_000_000


class QueryEncoder(Protocol):
    def encode_query(self, text: str, *, token_limit: int = 128): ...


@dataclass(frozen=True)
class GroundingFailure(ValueError):
    code: RefusalCode
    message: str
    context: dict[str, Any]

    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"


SLOT_TYPES: dict[str, MeaningType] = {
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

UNKNOWN_FOR_KIND: dict[MeaningType, RefusalCode] = {
    MeaningType.ENTITY: RefusalCode.UNKNOWN_ENTITY,
    MeaningType.RELATION: RefusalCode.UNSUPPORTED_RELATION,
    MeaningType.NUMERAL: RefusalCode.UNKNOWN_NUMERAL,
    MeaningType.OUTPUT_SCHEMA: RefusalCode.UNSUPPORTED_OUTPUT,
    MeaningType.STRUCTURED_SCHEMA: RefusalCode.INVALID_SCHEMA,
    MeaningType.PROGRAM: RefusalCode.UNSUPPORTED_PROGRAM,
    MeaningType.TOOL: RefusalCode.UNKNOWN_TOOL,
    MeaningType.VALUE: RefusalCode.UNKNOWN_VALUE,
    MeaningType.ENUM_MEMBER: RefusalCode.UNKNOWN_VALUE,
    MeaningType.LIST_VALUE: RefusalCode.UNKNOWN_VALUE,
    MeaningType.CODE_SYMBOL: RefusalCode.UNKNOWN_ENTITY,
    MeaningType.CODE_FILE: RefusalCode.INVALID_PATCH_TARGET,
    MeaningType.CODE_SPAN: RefusalCode.INVALID_PATCH_TARGET,
}


def _surface(value: str) -> str:
    value = normalize_text(value)
    if len(value) >= 2 and value[0] == value[-1] == '"':
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return value
        if isinstance(decoded, str):
            return normalize_text(decoded)
    return value


def _template_regex(template: str) -> re.Pattern[str]:
    expression = re.escape(template)
    slots = re.findall(r"\{([A-Z_]+)\}", template)
    for slot in slots:
        expression = expression.replace(
            re.escape("{" + slot + "}"), rf"(?P<{slot.lower()}>.+?)", 1
        )
    return re.compile("^" + expression + "$")


def _cost(score: float) -> int:
    return round(Q * (1.0 - max(-1.0, min(1.0, score))) / 2.0)


def _resolve(
    field: CompiledWorld, kind: MeaningType, raw: str, *, encoder: QueryEncoder | None,
    thresholds: dict[str, dict[str, float]],
) -> tuple[Meaning, dict[str, Any], int]:
    surface = _surface(raw)
    exact = field.resolve_exact(kind, surface)
    if len(exact) == 1:
        return exact[0], {"method": "exact", "surface": surface, "score": 1.0, "margin": 1.0}, 0
    if len(exact) > 1:
        raise GroundingFailure(
            RefusalCode.AMBIGUOUS_GROUNDING, f"ambiguous {kind.value} surface",
            {"kind": kind.value, "surface": surface, "candidate_ids": [item.meaning_id for item in exact]},
        )
    candidates = [item for item in field.by_kind(kind) if item.meaning_id in field.vectors]
    if encoder is None or not candidates:
        raise GroundingFailure(
            UNKNOWN_FOR_KIND.get(kind, RefusalCode.AMBIGUOUS_GROUNDING),
            f"no compiled {kind.value} matches the prompt span",
            {"kind": kind.value, "surface": surface},
        )
    query = np.asarray(encoder.encode_query(surface, token_limit=128), dtype=np.float32)
    ranked: list[tuple[float, Meaning]] = []
    for item in candidates:
        vector = np.asarray(field.vectors[item.meaning_id].vector, dtype=np.float32)
        score = round(float(np.dot(query, vector)), 6)
        if not math.isfinite(score):
            raise GroundingFailure(RefusalCode.INTEGRITY_FAILURE, "non-finite grounding score", {})
        ranked.append((score, item))
    ranked.sort(key=lambda pair: (-pair[0], pair[1].meaning_id))
    top_score, top = ranked[0]
    second_score = ranked[1][0] if len(ranked) > 1 else -1.0
    margin = round(top_score - second_score, 6)
    gate = thresholds.get(kind.value, thresholds.get("default", {"score": 1.0, "margin": 1.0}))
    if top_score == gate["score"] or margin == gate["margin"]:
        raise GroundingFailure(RefusalCode.AMBIGUOUS_GROUNDING, "grounding lies on a frozen boundary", {
            "kind": kind.value, "score": top_score, "margin": margin,
        })
    if top_score < gate["score"]:
        raise GroundingFailure(UNKNOWN_FOR_KIND.get(kind, RefusalCode.AMBIGUOUS_GROUNDING),
                               f"unsupported {kind.value} span", {"score": top_score, "margin": margin})
    if margin < gate["margin"]:
        raise GroundingFailure(RefusalCode.AMBIGUOUS_GROUNDING, "vector grounding is not unique", {
            "kind": kind.value, "score": top_score, "margin": margin,
        })
    return top, {"method": "vector", "surface": surface, "score": top_score, "margin": margin,
                 "threshold": gate}, _cost(top_score)


def _parse_bindings(raw: str) -> list[tuple[str, str]]:
    if not raw.strip():
        return []
    rows: list[tuple[str, str]] = []
    seen: set[str] = set()
    for part in raw.split(","):
        if part.count("=") != 1:
            raise GroundingFailure(RefusalCode.UNSUPPORTED_ARGUMENT, "bindings require field = value syntax", {})
        left, right = (_surface(value) for value in part.split("=", 1))
        key = left.casefold()
        if not left or not right or key in seen:
            raise GroundingFailure(RefusalCode.UNSUPPORTED_ARGUMENT, "empty or duplicate binding", {"field": left})
        seen.add(key)
        rows.append((left, right))
    return rows


def _resolve_value(field: CompiledWorld, raw: str, *, encoder: QueryEncoder | None,
                   thresholds: dict[str, dict[str, float]]) -> tuple[Meaning, dict[str, Any], int]:
    found: list[Meaning] = []
    for kind in (MeaningType.VALUE, MeaningType.ENUM_MEMBER, MeaningType.LIST_VALUE,
                 MeaningType.ENTITY, MeaningType.CODE_SYMBOL):
        found.extend(field.resolve_exact(kind, _surface(raw)))
    unique = {item.meaning_id: item for item in found}
    if len(unique) == 1:
        item = next(iter(unique.values()))
        return item, {"method": "exact", "surface": _surface(raw), "score": 1.0, "margin": 1.0}, 0
    if len(unique) > 1:
        raise GroundingFailure(RefusalCode.AMBIGUOUS_GROUNDING, "value has multiple compiled meanings", {
            "surface": raw, "candidate_ids": sorted(unique),
        })
    # A vector fallback is safe only when all value-like kinds agree on one top identifier.
    candidates: list[tuple[Meaning, dict[str, Any], int]] = []
    for kind in (MeaningType.VALUE, MeaningType.ENUM_MEMBER, MeaningType.LIST_VALUE):
        try:
            candidates.append(_resolve(field, kind, raw, encoder=encoder, thresholds=thresholds))
        except GroundingFailure:
            pass
    if len(candidates) != 1:
        raise GroundingFailure(RefusalCode.UNKNOWN_VALUE if not candidates else RefusalCode.AMBIGUOUS_GROUNDING,
                               "value is not uniquely compiled", {"surface": raw})
    return candidates[0]


def ground_prompt(
    field: CompiledWorld, prompt: str, *, encoder: QueryEncoder | None = None,
    thresholds: dict[str, dict[str, float]] | None = None,
) -> GroundedProgram:
    prompt = normalize_text(prompt)
    if len(prompt.split()) > 128:
        raise GroundingFailure(RefusalCode.RESOURCE_LIMIT, "prompt exceeds 128 tokens", {})
    thresholds = thresholds or {"default": {"score": 0.82, "margin": 0.05}}

    envelopes: list[tuple[Meaning, re.Match[str], str]] = []
    for instruction in field.by_kind(MeaningType.INSTRUCTION):
        if match := _template_regex(str(instruction.payload["template"])).fullmatch(prompt):
            envelopes.append((instruction, match, "instruction"))
    for prototype in field.by_kind(MeaningType.INSTRUCTION_PROTOTYPE):
        if match := _template_regex(str(prototype.payload["template"])).fullmatch(prompt):
            instruction = field.meanings[str(prototype.payload["instruction_id"])]
            envelopes.append((instruction, match, "prototype"))
    if not envelopes:
        raise GroundingFailure(RefusalCode.UNSUPPORTED_INSTRUCTION, "no compiled instruction envelope matches", {})
    distinct = {(item.meaning_id, tuple(sorted(match.groupdict().items()))) for item, match, _ in envelopes}
    if len(distinct) != 1:
        raise GroundingFailure(RefusalCode.AMBIGUOUS_GROUNDING, "multiple compiled instructions match", {
            "instruction_ids": sorted({item.meaning_id for item, _, _ in envelopes}),
        })
    instruction, match, envelope_method = envelopes[0]
    operation = field.meanings.get(str(instruction.payload["operation_id"]))
    if operation is None or operation.kind != MeaningType.OPERATION:
        raise GroundingFailure(RefusalCode.INTEGRITY_FAILURE, "instruction operation is missing", {})
    primitive = str(operation.payload["primitive"])

    slots: dict[str, str] = {}
    bindings: dict[str, str] = {}
    grounding: dict[str, Any] = {
        "instruction": {"meaning_id": instruction.meaning_id, "method": envelope_method},
    }
    cost = 0
    for slot_name, raw in match.groupdict().items():
        canonical_slot = slot_name.upper()
        if canonical_slot == "BINDINGS":
            for field_surface, value_surface in _parse_bindings(raw):
                field_item, field_evidence, field_cost = _resolve(
                    field, MeaningType.SCHEMA_FIELD, field_surface,
                    encoder=encoder, thresholds=thresholds,
                )
                value_item, value_evidence, value_cost = _resolve_value(
                    field, value_surface, encoder=encoder, thresholds=thresholds,
                )
                if field_item.meaning_id in bindings:
                    raise GroundingFailure(RefusalCode.UNSUPPORTED_ARGUMENT, "duplicate field binding", {})
                bindings[field_item.meaning_id] = value_item.meaning_id
                grounding[f"binding:{field_item.meaning_id}"] = {
                    "field": field_evidence, "value": value_evidence,
                }
                cost += field_cost + value_cost
            continue
        kind = SLOT_TYPES.get(canonical_slot)
        if kind is None:
            raise GroundingFailure(RefusalCode.UNSUPPORTED_PROGRAM, f"unsupported instruction slot {canonical_slot}", {})
        item, evidence, item_cost = _resolve(field, kind, raw, encoder=encoder, thresholds=thresholds)
        slots[canonical_slot] = item.meaning_id
        grounding[canonical_slot] = {"meaning_id": item.meaning_id, **evidence}
        cost += item_cost

    steps: tuple[dict[str, Any], ...] = ()
    if "PROGRAM" in slots:
        program = field.meanings[slots["PROGRAM"]]
        steps = tuple(program.payload["steps"])
    return GroundedProgram(
        instruction.meaning_id, operation.meaning_id, primitive, slots, bindings,
        steps, cost, grounding,
    )
