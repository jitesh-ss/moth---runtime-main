"""Deterministic compiler for domain and language contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from moth_runtime_v4_9.canonical import canonical_bytes, digest, normalize_text, sha256_bytes

from .model import Candidate, Capability, DomainContract, LanguageContract

SCHEMA = "moth-compositional-language-contract/1.0"
FIXTURE = Path(__file__).resolve().parent / "fixtures/domain-contracts-en-1.0.json"


def _surfaces(values: list[Any]) -> tuple[str, ...]:
    result = tuple(sorted({normalize_text(str(value)).casefold() for value in values}))
    if not result or any(not value for value in result):
        raise ValueError("compiled surfaces must be non-empty")
    return result


def compile_contract(source: dict[str, Any]) -> LanguageContract:
    if source.get("schema") != SCHEMA:
        raise ValueError("unsupported language contract schema")
    roles = tuple(str(value) for value in source.get("candidate_roles", []))
    requirements = tuple(str(value) for value in source.get("requirements", []))
    if roles != ("PROPOSED", "BACKUP") or requirements != ("RESOURCE", "PERMISSION", "DEADLINE"):
        raise ValueError("experiment requires the frozen two-candidate three-requirement coordinates")
    intent = str(source.get("intent", ""))
    if intent != "VALIDATE_AND_SELECT":
        raise ValueError("unexpected compiled intent")

    domains: list[DomainContract] = []
    domain_keys: set[str] = set()
    for row in source.get("domains", []):
        key = str(row.get("key", ""))
        if not key or key in domain_keys:
            raise ValueError("duplicate or empty domain key")
        domain_keys.add(key)
        candidates = tuple(Candidate(
            role=str(item["role"]),
            key=str(item["key"]),
            surfaces=_surfaces(item["surfaces"]),
        ) for item in row.get("candidates", []))
        capabilities = tuple(Capability(
            requirement=str(item["requirement"]),
            key=str(item["key"]),
            surfaces=_surfaces(item["surfaces"]),
        ) for item in row.get("capabilities", []))
        if {item.role for item in candidates} != set(roles):
            raise ValueError(f"domain {key} lacks a candidate role")
        if {item.requirement for item in capabilities} != {"RESOURCE", "PERMISSION"}:
            raise ValueError(f"domain {key} lacks a compiled capability")
        candidate_surfaces = [surface for item in candidates for surface in item.surfaces]
        capability_surfaces = [surface for item in capabilities for surface in item.surfaces]
        if len(candidate_surfaces) != len(set(candidate_surfaces)):
            raise ValueError(f"domain {key} has ambiguous candidate surfaces")
        if len(capability_surfaces) != len(set(capability_surfaces)):
            raise ValueError(f"domain {key} has ambiguous capability surfaces")
        provisional = {
            "key": key,
            "domain_surfaces": list(_surfaces(row.get("domain_surfaces", []))),
            "candidates": [item.canonical() for item in candidates],
            "capabilities": [item.canonical() for item in capabilities],
            "deadline_phrases": list(_surfaces(row.get("deadline_phrases", []))),
        }
        domains.append(DomainContract(
            key=key,
            domain_id=digest("moth-compositional-domain/1.0", provisional),
            domain_surfaces=tuple(provisional["domain_surfaces"]),
            candidates=tuple(sorted(candidates, key=lambda item: item.role)),
            capabilities=tuple(sorted(capabilities, key=lambda item: item.requirement)),
            deadline_phrases=tuple(provisional["deadline_phrases"]),
        ))
    if len(domains) != 2:
        raise ValueError("frozen experiment requires two domains")

    raw_laws = source.get("language_laws")
    if not isinstance(raw_laws, dict):
        raise ValueError("language laws are missing")
    language_laws = {str(key): _surfaces(value) for key, value in raw_laws.items()}
    required_laws = {
        "positive_possession", "negative_possession", "positive_permission",
        "negative_permission", "positive_deadline", "negative_deadline",
        "positive_unavailability",
    }
    if set(language_laws) != required_laws:
        raise ValueError("language law set differs from frozen contract")
    intent_surfaces = _surfaces(source.get("intent_surfaces", []))
    source_hash = sha256_bytes(canonical_bytes(source))
    provisional_contract = LanguageContract(
        schema=SCHEMA,
        source_hash=source_hash,
        contract_hash="",
        candidate_roles=roles,
        requirements=requirements,
        intent=intent,
        domains=tuple(sorted(domains, key=lambda item: item.domain_id)),
        language_laws=language_laws,
        intent_surfaces=intent_surfaces,
    )
    contract_hash = digest("moth-compositional-language-contract/1.0", provisional_contract.canonical())
    return LanguageContract(**{**provisional_contract.__dict__, "contract_hash": contract_hash})


def load_contract(path: str | Path = FIXTURE) -> LanguageContract:
    return compile_contract(json.loads(Path(path).read_text(encoding="utf-8")))
