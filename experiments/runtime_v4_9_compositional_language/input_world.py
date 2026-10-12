"""Compiled multi-clause semantic Input settlement and typed handoff."""

from __future__ import annotations

import re
from typing import Any

from moth_runtime_v4_9.canonical import canonical_bytes, digest, normalize_text

from .model import (
    DecisionFact,
    DomainContract,
    InputSettlement,
    LanguageContract,
    LanguageRefusal,
    LanguageRefusalCode,
    TypedHandoff,
)

INPUT_SCHEMA = "moth-compositional-input-settlement/1.0"
HANDOFF_SCHEMA = "moth-compositional-input-main-handoff/1.0"


def _clean(value: str) -> str:
    return normalize_text(value).casefold().strip(" .,!?:;\"'")


def _clauses(prompt: str) -> list[str]:
    return [value for part in re.split(r"[.!?;]+", normalize_text(prompt)) if (value := _clean(part))]


def _domain_score(domain: DomainContract, prompt: str) -> tuple[int, tuple[str, ...]]:
    surfaces = {
        *domain.domain_surfaces,
        *(surface for item in domain.candidates for surface in item.surfaces),
        *(surface for item in domain.capabilities for surface in item.surfaces),
    }
    matches = tuple(sorted(surface for surface in surfaces if re.search(rf"\b{re.escape(surface)}\b", prompt)))
    return len(matches), matches


def resolve_domain(contract: LanguageContract, prompt: str) -> tuple[DomainContract, dict[str, Any]]:
    normalized = _clean(prompt)
    ranked = sorted(
        [(*_domain_score(domain, normalized), domain) for domain in contract.domains],
        key=lambda row: (-row[0], row[2].domain_id),
    )
    if not ranked or ranked[0][0] == 0 or (len(ranked) > 1 and ranked[0][0] == ranked[1][0]):
        raise LanguageRefusal(
            LanguageRefusalCode.UNKNOWN_DOMAIN,
            "prompt does not uniquely select a compiled domain",
            {"scores": {row[2].key: row[0] for row in ranked}},
        )
    top = ranked[0]
    return top[2], {
        "selected_domain": top[2].key,
        "scores": {row[2].key: row[0] for row in ranked},
        "matched_surfaces": {row[2].key: list(row[1]) for row in ranked},
    }


def _candidate_mentions(domain: DomainContract, clause: str) -> list[tuple[str, str]]:
    matches: list[tuple[str, str]] = []
    for candidate in domain.candidates:
        for surface in candidate.surfaces:
            if re.search(rf"\b{re.escape(surface)}\b", clause):
                matches.append((candidate.role, surface))
    roles = {role for role, _ in matches}
    return [
        (role, max((surface for found_role, surface in matches if found_role == role), key=len))
        for role in sorted(roles)
    ]


def _resolve_candidate(
    domain: DomainContract,
    clause: str,
    *,
    last_role: str | None,
    reference_ambiguous: bool,
) -> tuple[str, dict[str, Any]]:
    mentions = _candidate_mentions(domain, clause)
    if len(mentions) == 1:
        return mentions[0][0], {"method": "explicit", "surface": mentions[0][1], "role": mentions[0][0]}
    if len(mentions) > 1:
        raise LanguageRefusal(
            LanguageRefusalCode.AMBIGUOUS_REFERENCE,
            "fact clause mentions more than one candidate",
            {"clause": clause, "roles": [role for role, _ in mentions]},
        )
    if re.match(r"^it\b", clause):
        if last_role is None or reference_ambiguous:
            raise LanguageRefusal(
                LanguageRefusalCode.AMBIGUOUS_REFERENCE,
                "singular reference has no unique compiled antecedent",
                {"clause": clause},
            )
        return last_role, {"method": "anaphora", "surface": "it", "role": last_role}
    raise LanguageRefusal(
        LanguageRefusalCode.UNKNOWN_ENTITY,
        "fact clause does not identify a compiled candidate",
        {"clause": clause},
    )


def _capability(domain: DomainContract, clause: str):
    matches = [
        (capability, surface)
        for capability in domain.capabilities
        for surface in capability.surfaces
        if re.search(rf"\b{re.escape(surface)}\b", clause)
    ]
    keys = {item.key for item, _ in matches}
    if len(keys) > 1:
        raise LanguageRefusal(
            LanguageRefusalCode.UNKNOWN_CAPABILITY,
            "fact clause mentions multiple compiled capabilities",
            {"clause": clause, "capability_keys": sorted(keys)},
        )
    if not matches:
        return None
    item = matches[0][0]
    surface = max((surface for found, surface in matches if found.key == item.key), key=len)
    return item, surface


def _contains_any(clause: str, values: tuple[str, ...]) -> str | None:
    matches = [value for value in values if re.search(rf"\b{re.escape(value)}\b", clause)]
    return max(matches, key=len) if matches else None


def _extract_fact(
    contract: LanguageContract,
    domain: DomainContract,
    clause: str,
    role: str,
) -> tuple[DecisionFact, dict[str, Any]]:
    laws = contract.language_laws
    deadline_phrase = _contains_any(clause, domain.deadline_phrases)
    if deadline_phrase is not None:
        negative = _contains_any(clause, laws["negative_deadline"])
        positive = _contains_any(clause, laws["positive_deadline"])
        if negative is None and positive is None:
            raise LanguageRefusal(LanguageRefusalCode.UNSUPPORTED_LANGUAGE, "deadline clause lacks polarity", {"clause": clause})
        satisfied = negative is None
        return DecisionFact(role, "DEADLINE", satisfied), {
            "law": "negative_deadline" if negative else "positive_deadline",
            "surface": negative or positive,
            "deadline_phrase": deadline_phrase,
        }

    negative_permission = _contains_any(clause, laws["negative_permission"])
    positive_permission = _contains_any(clause, laws["positive_permission"])
    if negative_permission or positive_permission:
        satisfied = negative_permission is None
        return DecisionFact(role, "PERMISSION", satisfied), {
            "law": "negative_permission" if negative_permission else "positive_permission",
            "surface": negative_permission or positive_permission,
        }

    capability_match = _capability(domain, clause)
    if capability_match is None:
        raise LanguageRefusal(
            LanguageRefusalCode.UNKNOWN_CAPABILITY,
            "fact clause does not identify a compiled capability or deadline",
            {"clause": clause},
        )
    capability, capability_surface = capability_match
    negative = _contains_any(clause, laws["negative_possession"])
    positive = _contains_any(clause, laws["positive_possession"])
    unavailable = _contains_any(clause, laws["positive_unavailability"])
    if unavailable:
        negative = unavailable
    if negative is None and positive is None:
        raise LanguageRefusal(
            LanguageRefusalCode.UNSUPPORTED_LANGUAGE,
            "capability clause lacks a compiled possession law",
            {"clause": clause},
        )
    satisfied = negative is None
    return DecisionFact(role, capability.requirement, satisfied), {
        "law": "negative_possession" if negative else "positive_possession",
        "surface": negative or positive,
        "capability": capability.key,
        "capability_surface": capability_surface,
    }


def settle_input(contract: LanguageContract, prompt: str, *, enable_anaphora: bool = True) -> InputSettlement:
    normalized = normalize_text(prompt)
    clauses = _clauses(normalized)
    if len(clauses) < 2:
        raise LanguageRefusal(LanguageRefusalCode.UNSUPPORTED_LANGUAGE, "prompt is not compositional", {})
    domain, domain_evidence = resolve_domain(contract, normalized)
    intent_clause = clauses[-1]
    if intent_clause not in contract.intent_surfaces:
        raise LanguageRefusal(
            LanguageRefusalCode.UNSUPPORTED_INTENT,
            "prompt does not select the compiled validation-and-selection intent",
            {"clause": intent_clause},
        )

    fact_values: dict[tuple[str, str], bool] = {}
    clause_evidence: list[dict[str, Any]] = []
    last_role: str | None = None
    reference_ambiguous = False
    for index, clause in enumerate(clauses[:-1]):
        mentions = _candidate_mentions(domain, clause)
        if len(mentions) > 1:
            last_role = None
            reference_ambiguous = True
            clause_evidence.append({
                "index": index,
                "clause": clause,
                "discourse_only": True,
                "mentioned_roles": [role for role, _ in mentions],
            })
            continue
        role, reference = _resolve_candidate(
            domain,
            clause,
            last_role=last_role if enable_anaphora else None,
            reference_ambiguous=reference_ambiguous or not enable_anaphora,
        )
        fact, law = _extract_fact(contract, domain, clause, role)
        coordinate = (fact.candidate, fact.requirement)
        if coordinate in fact_values and fact_values[coordinate] != fact.satisfied:
            raise LanguageRefusal(
                LanguageRefusalCode.CONFLICTING_FACTS,
                "prompt asserts both truth values for one decision coordinate",
                {"candidate": fact.candidate, "requirement": fact.requirement},
            )
        fact_values[coordinate] = fact.satisfied
        if reference["method"] == "explicit":
            last_role = role
            reference_ambiguous = False
        clause_evidence.append({
            "index": index,
            "clause": clause,
            "reference": reference,
            "law": law,
            "fact": fact.canonical(),
        })

    required = {(role, requirement) for role in contract.candidate_roles for requirement in contract.requirements}
    missing = sorted(required - set(fact_values))
    if missing:
        raise LanguageRefusal(
            LanguageRefusalCode.INCOMPLETE_FACT_GRAPH,
            "prompt does not settle every required decision coordinate",
            {"missing": [{"candidate": role, "requirement": requirement} for role, requirement in missing]},
        )
    facts = tuple(sorted(DecisionFact(role, requirement, fact_values[(role, requirement)]) for role, requirement in required))
    input_hash = digest("moth-compositional-language-input/1.0", {
        "contract_hash": contract.contract_hash,
        "prompt": normalized,
    })
    trace = {
        "schema": "moth-compositional-input-trace/1.0",
        "contract_hash": contract.contract_hash,
        "input_hash": input_hash,
        "domain": domain_evidence,
        "clauses": clause_evidence,
        "intent": {"value": contract.intent, "surface": intent_clause},
        "fact_graph": [item.canonical() for item in facts],
    }
    trace_hash = digest("moth-compositional-input-trace/1.0", trace)
    return InputSettlement(
        schema=INPUT_SCHEMA,
        contract_hash=contract.contract_hash,
        input_hash=input_hash,
        domain=domain.key,
        domain_id=domain.domain_id,
        intent=contract.intent,
        facts=facts,
        trace=trace,
        trace_hash=trace_hash,
    )


def verify_input(contract: LanguageContract, prompt: str, settlement: InputSettlement) -> None:
    if settlement.schema != INPUT_SCHEMA or settlement.contract_hash != contract.contract_hash:
        raise LanguageRefusal(LanguageRefusalCode.INTEGRITY_FAILURE, "Input settlement identity changed", {})
    if settlement.trace_hash != digest("moth-compositional-input-trace/1.0", settlement.trace):
        raise LanguageRefusal(LanguageRefusalCode.INTEGRITY_FAILURE, "Input trace hash changed", {})
    expected = settle_input(contract, prompt)
    if canonical_bytes(expected.canonical()) != canonical_bytes(settlement.canonical()):
        raise LanguageRefusal(LanguageRefusalCode.INTEGRITY_FAILURE, "Input settlement differs from reconstruction", {})


def make_handoff(settlement: InputSettlement) -> TypedHandoff:
    bindings = {
        f"{fact.candidate.casefold()}-{fact.requirement.casefold()}": "yes" if fact.satisfied else "no"
        for fact in settlement.facts
    }
    provisional = TypedHandoff(
        schema=HANDOFF_SCHEMA,
        contract_hash=settlement.contract_hash,
        input_hash=settlement.input_hash,
        domain=settlement.domain,
        intent=settlement.intent,
        bindings=bindings,
        input_trace_hash=settlement.trace_hash,
        handoff_hash="",
    )
    return TypedHandoff(**{
        **provisional.__dict__,
        "handoff_hash": digest("moth-compositional-input-main-handoff/1.0", provisional.canonical_without_hash()),
    })


def verify_handoff(settlement: InputSettlement, handoff: TypedHandoff) -> None:
    expected = make_handoff(settlement)
    if canonical_bytes(expected.canonical()) != canonical_bytes(handoff.canonical()):
        raise LanguageRefusal(LanguageRefusalCode.INTEGRITY_FAILURE, "typed handoff differs from verified Input", {})
