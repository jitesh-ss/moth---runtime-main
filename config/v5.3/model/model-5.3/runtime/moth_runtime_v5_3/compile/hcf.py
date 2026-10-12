"""Compile SYSTEM and CONTEXT source directly into HCF tensor objects."""

from __future__ import annotations

import re
from typing import Any

import numpy as np

from moth_runtime_v5_3.legacy.canonical import normalize_text

from ..energy.loader import EnergyFoundation
from ..energy.schema import (
    ActivationState,
    Effect,
    HCF_FIELD_SCHEMA,
    Level,
    Runtime53Failure,
    hash_bytes,
    hash_matrix,
    source_hash,
    string_pool,
    value_hash,
)
from ..persistence.objects import ObjectStore, TensorEnvelope
from .symbols import candidate_id


_DIRECTIVE = re.compile(
    r"^(require|forbid)\s+([a-z][a-z0-9_.-]*)\s*=\s*([A-Za-z0-9_.:-]+)\.?$",
    re.IGNORECASE,
)
_DELEGATE = re.compile(
    r"^delegate\s+([a-z][a-z0-9_.-]*)\s+to\s+(system|context)(\s+redelegable)?\.?$",
    re.IGNORECASE,
)
_COMMON = {
    "respond concisely": ("REQUIRE", "response.mode", "concise"),
    "respond in detail": ("REQUIRE", "response.mode", "detailed"),
    "use structured responses": ("REQUIRE", "response.mode", "structured"),
    "do not use the network": ("FORBID", "runtime.network", True),
    "allow the conversation to choose response detail": (
        "DELEGATE",
        "response.mode",
        None,
    ),
}
_CONTEXT_MODES = (
    (
        re.compile(r"\b(be|keep it|respond) concise(ly)?\b", re.IGNORECASE),
        "concise",
    ),
    (
        re.compile(
            r"\b(explain|respond|answer).{0,16}\b(in detail|detailed)\b",
            re.IGNORECASE,
        ),
        "detailed",
    ),
    (
        re.compile(
            r"\b(structured output|respond as json|use json)\b",
            re.IGNORECASE,
        ),
        "structured",
    ),
)


def _scope_lookup(foundation: EnergyFoundation, scope: str) -> int:
    target = np.frombuffer(
        hash_bytes("moth-scope/5.3", scope), dtype=np.uint8
    )
    matches = np.flatnonzero(
        np.all(foundation.tensors["scope_hash"] == target, axis=1)
    )
    if len(matches) != 1:
        raise Runtime53Failure(
            "INVALID_HCF_ENTRY", "unknown HCF scope", {"scope": scope}
        )
    return int(matches[0])


def compile_hcf_source(
    store: ObjectStore,
    foundation: EnergyFoundation,
    source: dict[str, Any],
    level: Level | str,
) -> TensorEnvelope:
    level = Level[level] if isinstance(level, str) else Level(level)
    if level is Level.BASE:
        raise Runtime53Failure(
            "INVALID_HCF_FIELD", "BASE cannot be compiled as a mutable field"
        )
    entries = source.get("entries", [])
    activations = source.get("activations", [])
    if not isinstance(entries, list) or not isinstance(activations, list):
        raise Runtime53Failure(
            "INVALID_HCF_FIELD", "entries and activations must be lists"
        )
    digest = source_hash(source)
    ids: list[bytes] = []
    hashes: list[bytes] = []
    effects: list[int] = []
    scopes: list[int] = []
    values: list[bytes] = []
    targets: list[int] = []
    redelegable: list[int] = []
    sources: list[bytes] = []
    spans: list[list[int]] = []
    labels: list[str] = []
    seen_entries: set[bytes] = set()
    for index, raw in enumerate(entries, 1):
        if not isinstance(raw, dict):
            raise Runtime53Failure(
                "INVALID_HCF_ENTRY", "entry must be an object"
            )
        effect_name = str(raw.get("effect", "")).upper()
        scope = str(raw.get("scope", ""))
        if effect_name not in Effect.__members__:
            raise Runtime53Failure(
                "INVALID_HCF_ENTRY", "unknown HCF effect"
            )
        effect = Effect[effect_name]
        target_name = raw.get("target_level")
        try:
            target = (
                int(Level[str(target_name).upper()]) if target_name else -1
            )
        except KeyError as exc:
            raise Runtime53Failure(
                "INVALID_DELEGATION", "delegation target is invalid"
            ) from exc
        if effect is Effect.DELEGATE and (
            target < 0 or target <= int(level)
        ):
            raise Runtime53Failure(
                "INVALID_DELEGATION",
                "delegation must target a lower hierarchy",
            )
        if effect is not Effect.DELEGATE and (
            target_name is not None or raw.get("redelegable")
        ):
            raise Runtime53Failure(
                "INVALID_HCF_ENTRY",
                "only delegations can name a target",
            )
        if effect in {Effect.REQUIRE, Effect.FORBID} and "value" not in raw:
            raise Runtime53Failure(
                "INVALID_HCF_ENTRY", "constraint value is required"
            )
        span = raw.get("source_span", [index, 1, index, 1])
        if (
            not isinstance(span, list)
            or len(span) != 4
            or not all(isinstance(value, int) for value in span)
        ):
            raise Runtime53Failure(
                "INVALID_HCF_ENTRY", "source span is invalid"
            )
        payload = {
            "meaning_id": str(raw.get("meaning_id", f"entry.{index}")),
            "level": level.name,
            "effect": effect.name,
            "scope": scope,
            "value": raw.get("value"),
            "target_level": Level(target).name if target >= 0 else None,
            "redelegable": bool(raw.get("redelegable", False)),
            "source_hash": digest,
            "source_span": span,
        }
        entry_id = hash_bytes("moth-hcf-entry-id/5.3", payload)
        if entry_id in seen_entries:
            raise Runtime53Failure(
                "INVALID_HCF_FIELD", "duplicate HCF entry"
            )
        seen_entries.add(entry_id)
        ids.append(entry_id)
        hashes.append(
            hash_bytes(
                "moth-hcf-entry/5.3",
                {"entry_id": entry_id.hex(), **payload},
            )
        )
        effects.append(int(effect))
        scopes.append(_scope_lookup(foundation, scope))
        values.append(value_hash(raw.get("value")))
        targets.append(target)
        redelegable.append(int(bool(raw.get("redelegable", False))))
        sources.append(bytes.fromhex(digest))
        spans.append(span)
        labels.extend([payload["meaning_id"], scope])

    activation_rows: dict[bytes, tuple[int, int]] = {}
    for raw in activations:
        state_name = (
            str(raw.get("state", "")).upper()
            if isinstance(raw, dict)
            else ""
        )
        if state_name not in ActivationState.__members__:
            raise Runtime53Failure(
                "INVALID_HCF_FIELD", "activation directive is invalid"
            )
        identity = candidate_id(str(raw.get("candidate_id", "")))
        foundation.candidate_index(identity)
        state = int(ActivationState[state_name])
        activation_scope = _scope_lookup(
            foundation, str(raw.get("scope", "candidate.activation"))
        )
        compiled_activation = (state, activation_scope)
        if (
            identity in activation_rows
            and activation_rows[identity] != compiled_activation
        ):
            raise Runtime53Failure(
                "AMBIGUOUS_HCF",
                "field contains contradictory activation",
            )
        activation_rows[identity] = compiled_activation
    ordered_activations = sorted(activation_rows.items())
    row_count = len(ids)
    label_bytes, label_offsets = string_pool(labels)
    tensors = {
        "declared_level": np.asarray([int(level)], dtype=np.int8),
        "entry_id": hash_matrix(ids),
        "entry_hash": hash_matrix(hashes),
        "level": np.full(row_count, int(level), dtype=np.uint8),
        "effect": np.asarray(effects, dtype=np.uint8),
        "scope_index": np.asarray(scopes, dtype=np.int32),
        "value_hash": hash_matrix(values),
        "target_level": np.asarray(targets, dtype=np.int8),
        "redelegable": np.asarray(redelegable, dtype=np.uint8),
        "source_hash": hash_matrix(sources),
        "source_span": np.asarray(spans, dtype=np.int32).reshape(row_count, 4),
        "activation_candidate": hash_matrix(
            [identity for identity, _ in ordered_activations]
        ),
        "activation_state": np.asarray(
            [compiled[0] for _, compiled in ordered_activations],
            dtype=np.int8,
        ),
        "activation_scope_index": np.asarray(
            [compiled[1] for _, compiled in ordered_activations],
            dtype=np.int32,
        ),
        "label_bytes": label_bytes,
        "label_offsets": label_offsets,
    }
    return store.put(
        tensors,
        schema=HCF_FIELD_SCHEMA,
        kind="HCF_FIELD",
        source_hash=digest,
        foundation_hash=foundation.logical_hash,
    )


def _prompt_source(
    prompt: str,
    level: Level,
    *,
    role: str = "SYSTEM",
    message_id: str = "",
) -> dict[str, Any]:
    normalized = (
        prompt.replace("\r\n", "\n").replace("\r", "\n").strip()
    )
    if len(normalized.encode("utf-8")) > 16_384:
        raise Runtime53Failure(
            "RESOURCE_LIMIT", "HCF source exceeds 16384 bytes"
        )
    entries: list[dict[str, Any]] = []
    if level is Level.SYSTEM:
        for line_number, raw in enumerate(normalized.splitlines(), 1):
            line = normalize_text(raw)
            if not line:
                continue
            key = line.casefold().removesuffix(".")
            common = _COMMON.get(key)
            direct = _DIRECTIVE.fullmatch(line)
            delegation = _DELEGATE.fullmatch(line)
            if common:
                effect, scope, value = common
                target = "CONTEXT" if effect == "DELEGATE" else None
                can_redelegate = False
            elif direct:
                effect = direct.group(1).upper()
                scope = direct.group(2).casefold()
                value = direct.group(3).casefold()
                target = None
                can_redelegate = False
            elif delegation:
                effect = "DELEGATE"
                scope = delegation.group(1).casefold()
                value = None
                target = delegation.group(2).upper()
                can_redelegate = bool(delegation.group(3))
            else:
                raise Runtime53Failure(
                    "UNSUPPORTED_SYSTEM_PROMPT",
                    "system prompt line has no compiled interpretation",
                    {"line": line_number, "text": line},
                )
            entry: dict[str, Any] = {
                "meaning_id": f"system.line.{line_number}",
                "effect": effect,
                "scope": scope,
                "source_span": [
                    line_number,
                    1,
                    line_number,
                    max(1, len(raw) + 1),
                ],
            }
            if effect in {"REQUIRE", "FORBID"}:
                entry["value"] = value
            if target:
                entry.update(
                    {
                        "target_level": target,
                        "redelegable": can_redelegate,
                    }
                )
            entries.append(entry)
    else:
        entries.append(
            {
                "meaning_id": f"message.{message_id}",
                "effect": "OBSERVE",
                "scope": "conversation.message",
                "value": normalized,
                "source_span": [1, 1, 1, max(1, len(normalized) + 1)],
            }
        )
        if role.upper() == "USER":
            modes = {
                mode
                for pattern, mode in _CONTEXT_MODES
                if pattern.search(normalized)
            }
            if len(modes) > 1:
                raise Runtime53Failure(
                    "AMBIGUOUS_HCF",
                    "message requests conflicting response modes",
                )
            if modes:
                entries.append(
                    {
                        "meaning_id": f"message.{message_id}.response-mode",
                        "effect": "REQUIRE",
                        "scope": "response.mode",
                        "value": next(iter(modes)),
                        "source_span": [
                            1,
                            1,
                            1,
                            max(1, len(normalized) + 1),
                        ],
                    }
                )
    return {
        "schema": "moth-hcf-source/5.3",
        "level": level.name,
        "entries": entries,
        "activations": [],
    }


def compile_system_prompt(
    store: ObjectStore, foundation: EnergyFoundation, prompt: str
) -> TensorEnvelope:
    return compile_hcf_source(
        store, foundation, _prompt_source(prompt, Level.SYSTEM), Level.SYSTEM
    )


def compile_context_message(
    store: ObjectStore,
    foundation: EnergyFoundation,
    content: str,
    *,
    role: str,
    message_id: str,
) -> TensorEnvelope:
    return compile_hcf_source(
        store,
        foundation,
        _prompt_source(
            content, Level.CONTEXT, role=role, message_id=message_id
        ),
        Level.CONTEXT,
    )
