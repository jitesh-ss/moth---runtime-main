"""Three-level Hierarchical Context Functions for Runtime 5.1.

HCF entries are inert, compiled field records.  They never execute callbacks;
they constrain a finite candidate set and produce independently verifiable
lexicographic energy evidence.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
import re
from typing import Any, Iterable

from moth_runtime_v5_0.canonical import canonical_bytes, digest, normalize_text, sha256_bytes


HCF_SCHEMA = "moth-hcf-field/5.1"
TRACE_SCHEMA = "moth-hcf-settlement/5.1"


class HierarchyLevel(StrEnum):
    BASE = "BASE"
    SYSTEM = "SYSTEM"
    CONTEXT = "CONTEXT"


LEVEL_ORDER = {
    HierarchyLevel.BASE: 0,
    HierarchyLevel.SYSTEM: 1,
    HierarchyLevel.CONTEXT: 2,
}


class HcfEffect(StrEnum):
    REQUIRE = "REQUIRE"
    FORBID = "FORBID"
    DELEGATE = "DELEGATE"
    OBSERVE = "OBSERVE"


class HcfFailure(ValueError):
    def __init__(self, code: str, message: str, context: dict[str, Any] | None = None):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.context = context or {}


@dataclass(frozen=True)
class HcfEntry:
    entry_id: str
    meaning_id: str
    level: HierarchyLevel
    effect: HcfEffect
    scope: str
    value: Any
    activation: str
    target_level: HierarchyLevel | None
    redelegable: bool
    source_hash: str
    provenance: dict[str, Any]
    entry_hash: str

    def canonical(self) -> dict[str, Any]:
        value = asdict(self)
        value["level"] = self.level.value
        value["effect"] = self.effect.value
        value["target_level"] = self.target_level.value if self.target_level else None
        return value


@dataclass(frozen=True, order=True)
class EnergyVector:
    base_violations: int
    system_violations: int
    context_violations: int
    grounding_cost_units: int

    def canonical(self) -> dict[str, int]:
        return {
            "base_violations": self.base_violations,
            "system_violations": self.system_violations,
            "context_violations": self.context_violations,
            "grounding_cost_units": self.grounding_cost_units,
        }

    @property
    def compatibility_scalar(self) -> int:
        return (
            self.base_violations * 10**18
            + self.system_violations * 10**12
            + self.context_violations * 10**6
            + self.grounding_cost_units
        )

    @property
    def has_violations(self) -> bool:
        return any((self.base_violations, self.system_violations, self.context_violations))


def _entry_payload(
    *, meaning_id: str, level: HierarchyLevel, effect: HcfEffect, scope: str,
    value: Any, target_level: HierarchyLevel | None, redelegable: bool,
    source_hash: str, provenance: dict[str, Any],
) -> dict[str, Any]:
    return {
        "meaning_id": meaning_id,
        "level": level.value,
        "effect": effect.value,
        "scope": scope,
        "value": value,
        "activation": "ALWAYS",
        "target_level": target_level.value if target_level else None,
        "redelegable": redelegable,
        "source_hash": source_hash,
        "provenance": provenance,
    }


def make_entry(
    *, meaning_id: str, level: HierarchyLevel, effect: HcfEffect, scope: str,
    value: Any = None, target_level: HierarchyLevel | None = None,
    redelegable: bool = False, source_hash: str,
    provenance: dict[str, Any] | None = None,
) -> HcfEntry:
    if not meaning_id or not re.fullmatch(r"[A-Za-z0-9_.:-]+", meaning_id):
        raise HcfFailure("INVALID_HCF_ENTRY", "meaning identifier is invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", source_hash):
        raise HcfFailure("INVALID_HCF_ENTRY", "source hash is invalid")
    if not scope or not re.fullmatch(r"[a-z][a-z0-9_.-]*", scope):
        raise HcfFailure("INVALID_HCF_ENTRY", "scope is invalid", {"scope": scope})
    if effect in {HcfEffect.REQUIRE, HcfEffect.FORBID} and value is None:
        raise HcfFailure("INVALID_HCF_ENTRY", "constraint value is required")
    if effect == HcfEffect.DELEGATE:
        if target_level is None or LEVEL_ORDER[target_level] <= LEVEL_ORDER[level]:
            raise HcfFailure("INVALID_DELEGATION", "delegation must target a lower level")
    elif target_level is not None or redelegable:
        raise HcfFailure("INVALID_HCF_ENTRY", "only delegation entries may name a target")
    provenance = dict(provenance or {})
    payload = _entry_payload(
        meaning_id=meaning_id, level=level, effect=effect, scope=scope,
        value=value, target_level=target_level, redelegable=redelegable,
        source_hash=source_hash, provenance=provenance,
    )
    entry_id = digest("moth-hcf-entry-id/5.1", payload)
    entry_hash = digest("moth-hcf-entry/5.1", {"entry_id": entry_id, **payload})
    return HcfEntry(entry_id, meaning_id, level, effect, scope, value, "ALWAYS",
                    target_level, redelegable, source_hash, provenance, entry_hash)


def entry_from_dict(value: dict[str, Any]) -> HcfEntry:
    try:
        if not isinstance(value.get("redelegable"), bool):
            raise TypeError("redelegable must be boolean")
        entry = HcfEntry(
            str(value["entry_id"]), str(value["meaning_id"]),
            HierarchyLevel(str(value["level"])), HcfEffect(str(value["effect"])),
            str(value["scope"]), value.get("value"), str(value["activation"]),
            HierarchyLevel(str(value["target_level"])) if value.get("target_level") else None,
            value["redelegable"], str(value["source_hash"]),
            dict(value["provenance"]), str(value["entry_hash"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise HcfFailure("INVALID_HCF_ENTRY", "compiled entry shape is invalid") from exc
    rebuilt = make_entry(
        meaning_id=entry.meaning_id, level=entry.level, effect=entry.effect,
        scope=entry.scope, value=entry.value, target_level=entry.target_level,
        redelegable=entry.redelegable, source_hash=entry.source_hash,
        provenance=entry.provenance,
    )
    if entry != rebuilt:
        raise HcfFailure("INTEGRITY_FAILURE", "compiled HCF entry hash changed")
    return entry


def validate_entries(entries: Iterable[HcfEntry]) -> tuple[HcfEntry, ...]:
    canonical = tuple(sorted(entries, key=lambda item: (LEVEL_ORDER[item.level], item.entry_id)))
    if len({item.entry_id for item in canonical}) != len(canonical):
        raise HcfFailure("INVALID_HCF_FIELD", "duplicate HCF entry")
    for level in HierarchyLevel:
        scopes = {item.scope for item in canonical if item.level == level}
        for scope in scopes:
            rules = [item for item in canonical if item.level == level and item.scope == scope]
            required = {canonical_bytes(item.value) for item in rules if item.effect == HcfEffect.REQUIRE}
            forbidden = {canonical_bytes(item.value) for item in rules if item.effect == HcfEffect.FORBID}
            if len(required) > 1 or required & forbidden:
                raise HcfFailure(
                    "AMBIGUOUS_HCF", "same-level compiled entries conflict",
                    {"level": level.value, "scope": scope},
                )
    return canonical


def compile_base_field(value: dict[str, Any], *, source_hash: str) -> tuple[HcfEntry, ...]:
    field_id = value.get("field_id")
    if (
        value.get("schema") != "moth-hcf-base-field/5.1"
        or not isinstance(field_id, str) or not field_id
        or not isinstance(value.get("entries"), list)
    ):
        raise HcfFailure("INVALID_HCF_FIELD", "base HCF field schema is invalid")
    entries: list[HcfEntry] = []
    for index, raw in enumerate(value["entries"], 1):
        if not isinstance(raw, dict):
            raise HcfFailure("INVALID_HCF_FIELD", "base HCF entry is not an object")
        effect = HcfEffect(str(raw.get("effect")))
        target = raw.get("target_level")
        entries.append(make_entry(
            meaning_id=str(raw.get("meaning_id", "")), level=HierarchyLevel.BASE,
            effect=effect, scope=str(raw.get("scope", "")), value=raw.get("value"),
            target_level=HierarchyLevel(str(target)) if target else None,
            redelegable=bool(raw.get("redelegable", False)), source_hash=source_hash,
            provenance={"source": "base-field", "field_id": field_id, "entry": index},
        ))
    return validate_entries(entries)


_DIRECTIVE = re.compile(
    r"^(require|forbid)\s+([a-z][a-z0-9_.-]*)\s*=\s*([A-Za-z0-9_.:-]+)\.?$",
    re.IGNORECASE,
)
_DELEGATE = re.compile(
    r"^delegate\s+([a-z][a-z0-9_.-]*)\s+to\s+(system|context)(\s+redelegable)?\.?$",
    re.IGNORECASE,
)
_COMMON_SYSTEM = {
    "respond concisely.": (HcfEffect.REQUIRE, "response.mode", "concise"),
    "respond concisely": (HcfEffect.REQUIRE, "response.mode", "concise"),
    "respond in detail.": (HcfEffect.REQUIRE, "response.mode", "detailed"),
    "respond in detail": (HcfEffect.REQUIRE, "response.mode", "detailed"),
    "use structured responses.": (HcfEffect.REQUIRE, "response.mode", "structured"),
    "use structured responses": (HcfEffect.REQUIRE, "response.mode", "structured"),
    "do not use the network.": (HcfEffect.FORBID, "runtime.network", True),
    "do not use the network": (HcfEffect.FORBID, "runtime.network", True),
    "allow the conversation to choose response detail.": (
        HcfEffect.DELEGATE, "response.mode", None,
    ),
    "allow the conversation to choose response detail": (
        HcfEffect.DELEGATE, "response.mode", None,
    ),
}


def compile_system_prompt(prompt: str) -> tuple[HcfEntry, ...]:
    normalized_document = prompt.replace("\r\n", "\n").replace("\r", "\n").strip()
    if len(normalized_document.encode("utf-8")) > 16_384:
        raise HcfFailure("RESOURCE_LIMIT", "system prompt exceeds 16384 bytes")
    source_hash = sha256_bytes(normalized_document.encode("utf-8"))
    entries: list[HcfEntry] = []
    for line_number, raw in enumerate(normalized_document.splitlines(), 1):
        line = normalize_text(raw)
        if not line:
            continue
        common = _COMMON_SYSTEM.get(line.casefold())
        match = _DIRECTIVE.fullmatch(line)
        delegation = _DELEGATE.fullmatch(line)
        if common:
            effect, scope, value = common
            target = HierarchyLevel.CONTEXT if effect == HcfEffect.DELEGATE else None
            redelegable = False
        elif match:
            effect = HcfEffect(match.group(1).upper())
            scope, value = match.group(2).casefold(), match.group(3).casefold()
            target, redelegable = None, False
        elif delegation:
            effect, scope, value = HcfEffect.DELEGATE, delegation.group(1).casefold(), None
            target = HierarchyLevel(delegation.group(2).upper())
            redelegable = bool(delegation.group(3))
        else:
            raise HcfFailure(
                "UNSUPPORTED_SYSTEM_PROMPT", "system prompt line has no compiled interpretation",
                {"line": line_number, "text": line},
            )
        entries.append(make_entry(
            meaning_id=f"system.line.{line_number}", level=HierarchyLevel.SYSTEM,
            effect=effect, scope=scope, value=value, target_level=target,
            redelegable=redelegable, source_hash=source_hash,
            provenance={"source": "system-prompt", "line": line_number},
        ))
    return validate_entries(entries)


_CONTEXT_MODES = (
    (re.compile(r"\b(be|keep it|respond) concise(ly)?\b", re.IGNORECASE), "concise"),
    (re.compile(r"\b(explain|respond|answer).{0,16}\b(in detail|detailed)\b", re.IGNORECASE), "detailed"),
    (re.compile(r"\b(structured output|respond as json|use json)\b", re.IGNORECASE), "structured"),
)


def compile_context_message(content: str, *, role: str, message_id: str) -> tuple[HcfEntry, ...]:
    normalized = normalize_text(content)
    source_hash = sha256_bytes(normalized.encode("utf-8"))
    entries = [make_entry(
        meaning_id=f"message.{message_id}", level=HierarchyLevel.CONTEXT,
        effect=HcfEffect.OBSERVE, scope="conversation.message", value=normalized,
        source_hash=source_hash, provenance={"source": "conversation", "role": role,
                                           "message_id": message_id},
    )]
    if role.upper() == "USER":
        modes = {mode for pattern, mode in _CONTEXT_MODES if pattern.search(normalized)}
        if len(modes) > 1:
            raise HcfFailure("AMBIGUOUS_HCF", "message requests conflicting response modes")
        if modes:
            mode = next(iter(modes))
            entries.append(make_entry(
                meaning_id=f"message.{message_id}.response-mode",
                level=HierarchyLevel.CONTEXT, effect=HcfEffect.REQUIRE,
                scope="response.mode", value=mode, source_hash=source_hash,
                provenance={"source": "conversation", "role": role,
                            "message_id": message_id},
            ))
    return validate_entries(entries)


def _constraint_satisfied(entry: HcfEntry, properties: dict[str, Any]) -> bool:
    actual = properties.get(entry.scope)
    if entry.effect == HcfEffect.REQUIRE:
        return canonical_bytes(actual) == canonical_bytes(entry.value)
    if entry.effect == HcfEffect.FORBID:
        return canonical_bytes(actual) != canonical_bytes(entry.value)
    return True


def _delegation_for(
    entries: tuple[HcfEntry, ...], owner: HierarchyLevel,
    target: HierarchyLevel, scope: str,
) -> tuple[HcfEntry, ...]:
    direct = tuple(item for item in entries if (
        item.level == owner and item.effect == HcfEffect.DELEGATE
        and item.scope == scope and item.target_level == target
    ))
    if direct:
        return direct
    if owner == HierarchyLevel.BASE and target == HierarchyLevel.CONTEXT:
        first = tuple(item for item in entries if (
            item.level == HierarchyLevel.BASE and item.effect == HcfEffect.DELEGATE
            and item.scope == scope and item.target_level == HierarchyLevel.SYSTEM
            and item.redelegable
        ))
        second = tuple(item for item in entries if (
            item.level == HierarchyLevel.SYSTEM and item.effect == HcfEffect.DELEGATE
            and item.scope == scope and item.target_level == HierarchyLevel.CONTEXT
        ))
        if first and second:
            return first + second
    return ()


def _candidate_energy(
    candidate: dict[str, Any], entries: tuple[HcfEntry, ...],
) -> tuple[EnergyVector, list[dict[str, Any]], list[str]]:
    properties = candidate.get("properties")
    grounding_cost = candidate.get("grounding_cost_units")
    if not isinstance(properties, dict) or not isinstance(grounding_cost, int) or grounding_cost < 0:
        raise HcfFailure("INVALID_CANDIDATE", "HCF candidate shape is invalid")
    violations = {level: 0 for level in HierarchyLevel}
    evaluations: list[dict[str, Any]] = []
    used_delegations: set[str] = set()
    constraints = tuple(item for item in entries if item.effect in {HcfEffect.REQUIRE, HcfEffect.FORBID})
    for entry in constraints:
        satisfied = _constraint_satisfied(entry, properties)
        delegated = False
        grants: tuple[HcfEntry, ...] = ()
        if not satisfied:
            for lower in constraints:
                if (
                    LEVEL_ORDER[lower.level] > LEVEL_ORDER[entry.level]
                    and lower.scope == entry.scope
                    and _constraint_satisfied(lower, properties)
                ):
                    grants = _delegation_for(entries, entry.level, lower.level, entry.scope)
                    if grants:
                        delegated = True
                        used_delegations.update(item.entry_id for item in grants)
                        break
        if not satisfied and not delegated:
            violations[entry.level] += 1
        evaluations.append({
            "entry_id": entry.entry_id, "level": entry.level.value,
            "scope": entry.scope, "satisfied": satisfied, "delegated": delegated,
            "delegation_entry_ids": [item.entry_id for item in grants],
        })
    vector = EnergyVector(
        violations[HierarchyLevel.BASE], violations[HierarchyLevel.SYSTEM],
        violations[HierarchyLevel.CONTEXT], grounding_cost,
    )
    return vector, evaluations, sorted(used_delegations)


def settle_candidates(
    candidates: list[dict[str, Any]], entries: Iterable[HcfEntry],
) -> tuple[dict[str, Any], dict[str, Any]]:
    compiled = validate_entries(entries)
    if not candidates:
        raise HcfFailure("NO_CANDIDATE", "HCF settlement has no candidates")
    rows = []
    for candidate in candidates:
        vector, evaluations, delegations = _candidate_energy(candidate, compiled)
        rows.append((vector, str(candidate.get("candidate_id", "")), candidate,
                     evaluations, delegations))
    minimum = min(row[0] for row in rows)
    winners = [row for row in rows if row[0] == minimum]
    semantic_groups = {canonical_bytes(row[2].get("semantic")) for row in winners}
    if len(semantic_groups) > 1:
        raise HcfFailure(
            "AMBIGUOUS_HCF", "distinct candidates share the minimum HCF energy",
            {"energy": minimum.canonical(), "candidate_ids": sorted(row[1] for row in winners)},
        )
    winner = min(winners, key=lambda row: row[1])
    trace_body = {
        "schema": TRACE_SCHEMA,
        "entry_hashes": [item.entry_hash for item in compiled],
        "candidates": [{
            "candidate_id": row[1], "energy": row[0].canonical(),
            "compatibility_scalar": row[0].compatibility_scalar,
            "evaluations": row[3], "delegation_entry_ids": row[4],
        } for row in sorted(rows, key=lambda item: item[1])],
        "winner_id": winner[1], "winning_energy": minimum.canonical(),
    }
    trace = {**trace_body, "trace_hash": digest("moth-hcf-trace/5.1", trace_body)}
    if minimum.has_violations:
        raise HcfFailure(
            "HCF_CONFLICT", "minimum candidate retains a non-delegated hierarchy violation",
            {"trace": trace},
        )
    return winner[2], trace


def verify_trace(
    candidates: list[dict[str, Any]], entries: Iterable[HcfEntry], trace: dict[str, Any],
) -> dict[str, Any]:
    candidate, expected = settle_candidates(candidates, entries)
    if canonical_bytes(trace) != canonical_bytes(expected):
        raise HcfFailure("INTEGRITY_FAILURE", "HCF trace differs from reconstruction")
    return candidate
