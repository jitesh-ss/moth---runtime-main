"""Immutable contracts for the compositional-language cascade experiment."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class LanguageRefusalCode(StrEnum):
    UNKNOWN_DOMAIN = "UNKNOWN_DOMAIN"
    UNKNOWN_ENTITY = "UNKNOWN_ENTITY"
    UNKNOWN_CAPABILITY = "UNKNOWN_CAPABILITY"
    AMBIGUOUS_REFERENCE = "AMBIGUOUS_REFERENCE"
    UNSUPPORTED_LANGUAGE = "UNSUPPORTED_LANGUAGE"
    UNSUPPORTED_INTENT = "UNSUPPORTED_INTENT"
    INCOMPLETE_FACT_GRAPH = "INCOMPLETE_FACT_GRAPH"
    CONFLICTING_FACTS = "CONFLICTING_FACTS"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"


@dataclass(frozen=True)
class LanguageRefusal(ValueError):
    code: LanguageRefusalCode
    message: str
    context: dict[str, Any]

    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"


@dataclass(frozen=True)
class Candidate:
    role: str
    key: str
    surfaces: tuple[str, ...]

    def canonical(self) -> dict[str, Any]:
        return {"role": self.role, "key": self.key, "surfaces": list(self.surfaces)}


@dataclass(frozen=True)
class Capability:
    requirement: str
    key: str
    surfaces: tuple[str, ...]

    def canonical(self) -> dict[str, Any]:
        return {"requirement": self.requirement, "key": self.key, "surfaces": list(self.surfaces)}


@dataclass(frozen=True)
class DomainContract:
    key: str
    domain_id: str
    domain_surfaces: tuple[str, ...]
    candidates: tuple[Candidate, ...]
    capabilities: tuple[Capability, ...]
    deadline_phrases: tuple[str, ...]

    def canonical(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "domain_id": self.domain_id,
            "domain_surfaces": list(self.domain_surfaces),
            "candidates": [item.canonical() for item in self.candidates],
            "capabilities": [item.canonical() for item in self.capabilities],
            "deadline_phrases": list(self.deadline_phrases),
        }


@dataclass(frozen=True)
class LanguageContract:
    schema: str
    source_hash: str
    contract_hash: str
    candidate_roles: tuple[str, ...]
    requirements: tuple[str, ...]
    intent: str
    domains: tuple[DomainContract, ...]
    language_laws: dict[str, tuple[str, ...]]
    intent_surfaces: tuple[str, ...]

    def canonical(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "source_hash": self.source_hash,
            "candidate_roles": list(self.candidate_roles),
            "requirements": list(self.requirements),
            "intent": self.intent,
            "domains": [item.canonical() for item in self.domains],
            "language_laws": {
                key: list(values) for key, values in sorted(self.language_laws.items())
            },
            "intent_surfaces": list(self.intent_surfaces),
        }


@dataclass(frozen=True, order=True)
class DecisionFact:
    candidate: str
    requirement: str
    satisfied: bool

    def canonical(self) -> dict[str, Any]:
        return {
            "candidate": self.candidate,
            "requirement": self.requirement,
            "satisfied": self.satisfied,
        }


@dataclass(frozen=True)
class InputSettlement:
    schema: str
    contract_hash: str
    input_hash: str
    domain: str
    domain_id: str
    intent: str
    facts: tuple[DecisionFact, ...]
    trace: dict[str, Any]
    trace_hash: str

    def canonical(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "contract_hash": self.contract_hash,
            "input_hash": self.input_hash,
            "domain": self.domain,
            "domain_id": self.domain_id,
            "intent": self.intent,
            "facts": [item.canonical() for item in self.facts],
            "trace": self.trace,
            "trace_hash": self.trace_hash,
        }


@dataclass(frozen=True)
class TypedHandoff:
    schema: str
    contract_hash: str
    input_hash: str
    domain: str
    intent: str
    bindings: dict[str, str]
    input_trace_hash: str
    handoff_hash: str

    def canonical_without_hash(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "contract_hash": self.contract_hash,
            "input_hash": self.input_hash,
            "domain": self.domain,
            "intent": self.intent,
            "bindings": dict(sorted(self.bindings.items())),
            "input_trace_hash": self.input_trace_hash,
        }

    def canonical(self) -> dict[str, Any]:
        return {**self.canonical_without_hash(), "handoff_hash": self.handoff_hash}
