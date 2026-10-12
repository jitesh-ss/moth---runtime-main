"""Compilation of the immutable candidate and BASE energy foundation."""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np

from ..energy.schema import (
    ENERGY_FOUNDATION_SCHEMA,
    Effect,
    Level,
    Runtime52Failure,
    hash_bytes,
    hash_matrix,
    source_hash,
    string_pool,
    value_hash,
)
from ..persistence.objects import ObjectStore, TensorEnvelope
from .symbols import candidate_id, semantic_id


def _request_key(value: str) -> str:
    return " ".join(str(value).split()).casefold().rstrip(".!?")


def _entry_rows(
    entries: Sequence[dict[str, Any]],
    scopes: dict[str, int],
    source_digest: str,
) -> dict[str, np.ndarray]:
    ids: list[bytes] = []
    hashes: list[bytes] = []
    effects: list[int] = []
    scope_indices: list[int] = []
    values: list[bytes] = []
    targets: list[int] = []
    redelegable: list[int] = []
    sources: list[bytes] = []
    spans: list[list[int]] = []
    for index, raw in enumerate(entries, 1):
        effect_name = str(raw.get("effect", "")).upper()
        scope = str(raw.get("scope", ""))
        if effect_name not in Effect.__members__ or scope not in scopes:
            raise Runtime52Failure("INVALID_HCF_ENTRY", "BASE entry is invalid")
        effect = Effect[effect_name]
        target_name = raw.get("target_level")
        target = int(Level[str(target_name).upper()]) if target_name else -1
        if effect is Effect.DELEGATE and (
            target < 0 or target <= int(Level.BASE)
        ):
            raise Runtime52Failure(
                "INVALID_DELEGATION", "BASE delegation target is invalid"
            )
        payload = {
            "meaning_id": str(raw.get("meaning_id", f"base.{index}")),
            "level": "BASE",
            "effect": effect_name,
            "scope": scope,
            "value": raw.get("value"),
            "target_level": target_name,
            "redelegable": bool(raw.get("redelegable", False)),
            "source_hash": source_digest,
            "span": [index, 1, index, 1],
        }
        entry_id = hash_bytes("moth-hcf-entry-id/5.2", payload)
        ids.append(entry_id)
        hashes.append(
            hash_bytes(
                "moth-hcf-entry/5.2",
                {"entry_id": entry_id.hex(), **payload},
            )
        )
        effects.append(int(effect))
        scope_indices.append(scopes[scope])
        values.append(value_hash(raw.get("value")))
        targets.append(target)
        redelegable.append(int(bool(raw.get("redelegable", False))))
        sources.append(bytes.fromhex(source_digest))
        spans.append([index, 1, index, 1])
    row_count = len(ids)
    return {
        "base_entry_id": hash_matrix(ids),
        "base_entry_hash": hash_matrix(hashes),
        "base_effect": np.asarray(effects, dtype=np.uint8),
        "base_scope_index": np.asarray(scope_indices, dtype=np.int32),
        "base_value_hash": hash_matrix(values),
        "base_target_level": np.asarray(targets, dtype=np.int8),
        "base_redelegable": np.asarray(redelegable, dtype=np.uint8),
        "base_source_hash": hash_matrix(sources),
        "base_source_span": np.asarray(spans, dtype=np.int32).reshape(
            row_count, 4
        ),
    }


def compile_energy_foundation(
    store: ObjectStore,
    candidates: Sequence[dict[str, Any]],
    base_source: dict[str, Any],
) -> TensorEnvelope:
    if not candidates:
        raise Runtime52Failure(
            "NO_CANDIDATE", "energy foundation requires candidates"
        )
    ordered = sorted(candidates, key=lambda item: str(item.get("candidate_id", "")))
    identities = [str(item.get("candidate_id", "")) for item in ordered]
    if "" in identities or len(set(identities)) != len(identities):
        raise Runtime52Failure(
            "INVALID_FIELD", "candidate identifiers are empty or duplicated"
        )
    base_entries = base_source.get("entries", [])
    if not isinstance(base_entries, list):
        raise Runtime52Failure(
            "INVALID_HCF_FIELD", "BASE entries must be a list"
        )
    scope_names = sorted(
        {
            str(scope)
            for item in ordered
            for scope in item.get("properties", {})
        }
        | {str(item.get("scope", "")) for item in base_entries}
        | {"candidate.activation", "conversation.message"}
    )
    if "" in scope_names:
        raise Runtime52Failure("INVALID_FIELD", "candidate scope is empty")
    scopes = {name: index for index, name in enumerate(scope_names)}

    labels: list[str] = []
    label_indices: dict[str, int] = {}

    def label(value: str) -> int:
        text = str(value)
        if text not in label_indices:
            label_indices[text] = len(labels)
            labels.append(text)
        return label_indices[text]

    for name in scope_names:
        label(name)
    n, s = len(ordered), len(scope_names)
    present = np.zeros((n, s), dtype=np.uint8)
    property_values = np.zeros((n, s, 32), dtype=np.uint8)
    candidate_ids: list[bytes] = []
    semantics: list[bytes] = []
    fields: list[bytes] = []
    skills: list[bytes] = []
    payloads: list[bytes] = []
    enabled: list[int] = []
    costs: list[int] = []
    modalities: list[int] = []
    candidate_labels: list[int] = []
    mode_labels: list[int] = []
    requests: dict[bytes, int] = {}
    for row, candidate in enumerate(ordered):
        identity = str(candidate["candidate_id"])
        properties = candidate.get("properties")
        cost = candidate.get("grounding_cost_units")
        if (
            not isinstance(properties, dict)
            or not isinstance(cost, int)
            or cost < 0
        ):
            raise Runtime52Failure("INVALID_FIELD", "candidate shape is invalid")
        candidate_ids.append(candidate_id(identity))
        semantics.append(semantic_id(candidate.get("semantic")))
        fields.append(
            hash_bytes(
                "moth-field-binding/5.2", candidate.get("field_id", "")
            )
        )
        skills.append(
            hash_bytes(
                "moth-skill-binding/5.2", candidate.get("skill_id", "")
            )
        )
        payloads.append(
            hash_bytes(
                "moth-payload-handle/5.2", candidate.get("payload", identity)
            )
        )
        enabled.append(int(bool(candidate.get("enabled", True))))
        costs.append(cost)
        modalities.append(0)
        candidate_labels.append(label(identity))
        mode_labels.append(label(str(properties.get("response.mode", identity))))
        for scope, value in properties.items():
            column = scopes[str(scope)]
            present[row, column] = 1
            property_values[row, column] = np.frombuffer(
                value_hash(value), dtype=np.uint8
            )
            label(str(value))
        for request in candidate.get("requests", []):
            request_hash = hash_bytes(
                "moth-presentation-request/5.2", _request_key(str(request))
            )
            previous = requests.get(request_hash)
            if previous is not None and previous != row:
                raise Runtime52Failure(
                    "INVALID_FIELD", "presentation request is ambiguous"
                )
            requests[request_hash] = row
    label_bytes, label_offsets = string_pool(labels)
    base_digest = source_hash(base_source)
    tensors = {
        "candidate_id": hash_matrix(candidate_ids),
        "semantic_id": hash_matrix(semantics),
        "candidate_enabled_default": np.asarray(enabled, dtype=np.uint8),
        "grounding_cost_units": np.asarray(costs, dtype=np.int64),
        "modality": np.asarray(modalities, dtype=np.uint8),
        "scope_hash": hash_matrix(
            [hash_bytes("moth-scope/5.2", name) for name in scope_names]
        ),
        "candidate_property_present": present,
        "candidate_property_value_hash": property_values,
        "candidate_field_hash": hash_matrix(fields),
        "candidate_skill_hash": hash_matrix(skills),
        "payload_handle": hash_matrix(payloads),
        "candidate_label_index": np.asarray(candidate_labels, dtype=np.int32),
        "candidate_mode_index": np.asarray(mode_labels, dtype=np.int32),
        "request_hash": hash_matrix(sorted(requests)),
        "request_candidate_index": np.asarray(
            [requests[key] for key in sorted(requests)], dtype=np.int32
        ),
        "label_bytes": label_bytes,
        "label_offsets": label_offsets,
        **_entry_rows(base_entries, scopes, base_digest),
    }
    aggregate_source = source_hash(
        {"base": base_source, "candidates": ordered}
    )
    return store.put(
        tensors,
        schema=ENERGY_FOUNDATION_SCHEMA,
        kind="ENERGY_FOUNDATION",
        source_hash=aggregate_source,
    )
