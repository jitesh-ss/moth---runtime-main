"""Strict read-only views over Runtime 5.3 tensor objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np

from .schema import (
    ENERGY_FOUNDATION_SCHEMA,
    HCF_FIELD_SCHEMA,
    Effect,
    Level,
    Runtime53Failure,
    decode_string_pool,
)


FOUNDATION_TENSORS = {
    "candidate_id",
    "semantic_id",
    "candidate_enabled_default",
    "grounding_cost_units",
    "modality",
    "scope_hash",
    "candidate_property_present",
    "candidate_property_value_hash",
    "candidate_field_hash",
    "candidate_skill_hash",
    "payload_handle",
    "candidate_label_index",
    "candidate_mode_index",
    "request_hash",
    "request_candidate_index",
    "base_entry_id",
    "base_entry_hash",
    "base_effect",
    "base_scope_index",
    "base_value_hash",
    "base_target_level",
    "base_redelegable",
    "base_source_hash",
    "base_source_span",
    "label_bytes",
    "label_offsets",
}

HCF_TENSORS = {
    "declared_level",
    "entry_id",
    "entry_hash",
    "level",
    "effect",
    "scope_index",
    "value_hash",
    "target_level",
    "redelegable",
    "source_hash",
    "source_span",
    "activation_candidate",
    "activation_scope_index",
    "activation_state",
    "label_bytes",
    "label_offsets",
}


def _shape(array: np.ndarray, expected: tuple[int | None, ...], name: str) -> None:
    if array.ndim != len(expected) or any(
        wanted is not None and actual != wanted
        for actual, wanted in zip(array.shape, expected)
    ):
        raise Runtime53Failure(
            "TENSOR_SCHEMA_MISMATCH",
            f"invalid tensor shape: {name}",
            {"actual": list(array.shape), "expected": list(expected)},
        )


def _dtype(array: np.ndarray, expected: np.dtype, name: str) -> None:
    if array.dtype != np.dtype(expected):
        raise Runtime53Failure(
            "TENSOR_SCHEMA_MISMATCH",
            f"invalid tensor dtype: {name}",
            {"actual": str(array.dtype), "expected": str(np.dtype(expected))},
        )


@dataclass(frozen=True)
class EnergyFoundation:
    logical_hash: str
    file_hash: str
    tensors: Mapping[str, np.ndarray]
    labels: tuple[str, ...]

    @property
    def candidate_count(self) -> int:
        return int(self.tensors["candidate_id"].shape[0])

    @property
    def scope_count(self) -> int:
        return int(self.tensors["scope_hash"].shape[0])

    def candidate_index(self, candidate_id: bytes) -> int:
        if len(candidate_id) != 32:
            raise Runtime53Failure("UNKNOWN_CANDIDATE_REFERENCE", "candidate hash is invalid")
        target = np.frombuffer(candidate_id, dtype=np.uint8)
        matches = np.all(self.tensors["candidate_id"] == target, axis=1)
        indices = np.flatnonzero(matches)
        if len(indices) != 1:
            raise Runtime53Failure(
                "UNKNOWN_CANDIDATE_REFERENCE", "candidate is not in foundation"
            )
        return int(indices[0])


@dataclass(frozen=True)
class HcfTensorField:
    logical_hash: str
    file_hash: str
    foundation_hash: str
    source_hash: str
    tensors: Mapping[str, np.ndarray]
    labels: tuple[str, ...]

    @property
    def level(self) -> Level:
        return Level(int(self.tensors["declared_level"][0]))


def load_energy_foundation(envelope: object) -> EnergyFoundation:
    schema = getattr(envelope, "schema")
    tensors = getattr(envelope, "tensors")
    if schema != ENERGY_FOUNDATION_SCHEMA or set(tensors) != FOUNDATION_TENSORS:
        raise Runtime53Failure(
            "TENSOR_SCHEMA_MISMATCH", "energy foundation tensor set changed"
        )
    n = len(tensors["candidate_id"])
    s = len(tensors["scope_hash"])
    r = len(tensors["base_entry_id"])
    if n == 0 or s == 0:
        raise Runtime53Failure(
            "TENSOR_SCHEMA_MISMATCH", "energy foundation is empty"
        )
    for name in (
        "candidate_id",
        "semantic_id",
        "candidate_field_hash",
        "candidate_skill_hash",
        "payload_handle",
    ):
        _dtype(tensors[name], np.uint8, name)
        _shape(tensors[name], (n, 32), name)
    for name, dtype in (
        ("candidate_enabled_default", np.uint8),
        ("modality", np.uint8),
        ("grounding_cost_units", np.int64),
        ("candidate_label_index", np.int32),
        ("candidate_mode_index", np.int32),
    ):
        _dtype(tensors[name], dtype, name)
        _shape(tensors[name], (n,), name)
    if np.any(tensors["candidate_enabled_default"] > 1):
        raise Runtime53Failure(
            "TENSOR_SCHEMA_MISMATCH", "candidate activation mask is invalid"
        )
    if np.any(tensors["grounding_cost_units"] < 0):
        raise Runtime53Failure(
            "TENSOR_SCHEMA_MISMATCH", "grounding cost is negative"
        )
    _dtype(tensors["scope_hash"], np.uint8, "scope_hash")
    _shape(tensors["scope_hash"], (s, 32), "scope_hash")
    _dtype(tensors["candidate_property_present"], np.uint8, "candidate_property_present")
    _shape(tensors["candidate_property_present"], (n, s), "candidate_property_present")
    _dtype(
        tensors["candidate_property_value_hash"],
        np.uint8,
        "candidate_property_value_hash",
    )
    _shape(
        tensors["candidate_property_value_hash"],
        (n, s, 32),
        "candidate_property_value_hash",
    )
    for name in (
        "base_entry_id",
        "base_entry_hash",
        "base_value_hash",
        "base_source_hash",
    ):
        _dtype(tensors[name], np.uint8, name)
        _shape(tensors[name], (r, 32), name)
    for name, dtype in (
        ("base_effect", np.uint8),
        ("base_scope_index", np.int32),
        ("base_target_level", np.int8),
        ("base_redelegable", np.uint8),
    ):
        _dtype(tensors[name], dtype, name)
        _shape(tensors[name], (r,), name)
    _dtype(tensors["base_source_span"], np.int32, "base_source_span")
    _shape(tensors["base_source_span"], (r, 4), "base_source_span")
    if np.any(tensors["base_scope_index"] < 0) or np.any(
        tensors["base_scope_index"] >= s
    ):
        raise Runtime53Failure(
            "TENSOR_SCHEMA_MISMATCH", "BASE scope index is out of range"
        )
    if np.any(tensors["base_effect"] > int(Effect.OBSERVE)):
        raise Runtime53Failure(
            "TENSOR_SCHEMA_MISMATCH", "BASE effect opcode is invalid"
        )
    labels = decode_string_pool(tensors["label_bytes"], tensors["label_offsets"])
    for name in ("candidate_label_index", "candidate_mode_index"):
        if np.any(tensors[name] < 0) or np.any(tensors[name] >= len(labels)):
            raise Runtime53Failure(
                "TENSOR_SCHEMA_MISMATCH", f"{name} is out of range"
            )
    request_count = len(tensors["request_hash"])
    _dtype(tensors["request_hash"], np.uint8, "request_hash")
    _shape(tensors["request_hash"], (request_count, 32), "request_hash")
    _dtype(tensors["request_candidate_index"], np.int32, "request_candidate_index")
    _shape(tensors["request_candidate_index"], (request_count,), "request_candidate_index")
    if np.any(tensors["request_candidate_index"] < 0) or np.any(
        tensors["request_candidate_index"] >= n
    ):
        raise Runtime53Failure(
            "TENSOR_SCHEMA_MISMATCH", "presentation request candidate is out of range"
        )
    return EnergyFoundation(
        getattr(envelope, "logical_hash"),
        getattr(envelope, "file_hash"),
        tensors,
        labels,
    )


def load_hcf_field(envelope: object, foundation: EnergyFoundation) -> HcfTensorField:
    schema = getattr(envelope, "schema")
    tensors = getattr(envelope, "tensors")
    metadata = getattr(envelope, "metadata")
    foundation_hash = metadata.get("foundation_hash", "")
    if schema != HCF_FIELD_SCHEMA or set(tensors) != HCF_TENSORS:
        raise Runtime53Failure(
            "TENSOR_SCHEMA_MISMATCH", "HCF field tensor set changed"
        )
    if foundation_hash != foundation.logical_hash:
        raise Runtime53Failure(
            "FOUNDATION_BINDING_MISMATCH", "HCF field targets another foundation"
        )
    r = len(tensors["entry_id"])
    a = len(tensors["activation_candidate"])
    _dtype(tensors["declared_level"], np.int8, "declared_level")
    _shape(tensors["declared_level"], (1,), "declared_level")
    if int(tensors["declared_level"][0]) not in (
        int(Level.SYSTEM),
        int(Level.CONTEXT),
    ):
        raise Runtime53Failure(
            "TENSOR_SCHEMA_MISMATCH", "declared HCF level is invalid"
        )
    for name in ("entry_id", "entry_hash", "value_hash", "source_hash"):
        _dtype(tensors[name], np.uint8, name)
        _shape(tensors[name], (r, 32), name)
    for name, dtype in (
        ("level", np.uint8),
        ("effect", np.uint8),
        ("scope_index", np.int32),
        ("target_level", np.int8),
        ("redelegable", np.uint8),
    ):
        _dtype(tensors[name], dtype, name)
        _shape(tensors[name], (r,), name)
    _dtype(tensors["source_span"], np.int32, "source_span")
    _shape(tensors["source_span"], (r, 4), "source_span")
    _dtype(tensors["activation_candidate"], np.uint8, "activation_candidate")
    _shape(tensors["activation_candidate"], (a, 32), "activation_candidate")
    _dtype(tensors["activation_scope_index"], np.int32, "activation_scope_index")
    _shape(tensors["activation_scope_index"], (a,), "activation_scope_index")
    _dtype(tensors["activation_state"], np.int8, "activation_state")
    _shape(tensors["activation_state"], (a,), "activation_state")
    if np.any(tensors["scope_index"] < 0) or np.any(
        tensors["scope_index"] >= foundation.scope_count
    ):
        raise Runtime53Failure(
            "TENSOR_SCHEMA_MISMATCH", "HCF scope index is out of range"
        )
    if np.any(tensors["level"] > int(Level.CONTEXT)) or np.any(
        tensors["effect"] > int(Effect.OBSERVE)
    ):
        raise Runtime53Failure("TENSOR_SCHEMA_MISMATCH", "HCF opcode is invalid")
    if np.any(
        (tensors["activation_state"] != 0) & (tensors["activation_state"] != 1)
    ):
        raise Runtime53Failure(
            "TENSOR_SCHEMA_MISMATCH", "activation state is invalid"
        )
    if np.any(tensors["activation_scope_index"] < 0) or np.any(
        tensors["activation_scope_index"] >= foundation.scope_count
    ):
        raise Runtime53Failure(
            "TENSOR_SCHEMA_MISMATCH", "activation scope index is out of range"
        )
    for row in tensors["activation_candidate"]:
        foundation.candidate_index(row.tobytes())
    labels = decode_string_pool(tensors["label_bytes"], tensors["label_offsets"])
    return HcfTensorField(
        getattr(envelope, "logical_hash"),
        getattr(envelope, "file_hash"),
        foundation_hash,
        metadata.get("source_hash", ""),
        tensors,
        labels,
    )
