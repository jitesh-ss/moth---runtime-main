"""Canonical tensor schemas and hashing for Runtime 5.3."""

from __future__ import annotations

from enum import IntEnum
import hashlib
import struct
from typing import Any, Mapping, Sequence

import numpy as np

from moth_runtime_v5_3.legacy.canonical import canonical_bytes, sha256_bytes


RUNTIME = "5.3"
ENERGY_FOUNDATION_SCHEMA = "moth-energy-foundation/5.3"
HCF_FIELD_SCHEMA = "moth-hcf-field/5.3"
COMPILED_FIELD_SCHEMA = "moth-compiled-field/5.3"
COMPILED_SKILL_SCHEMA = "moth-compiled-skill/5.3"


class Runtime53Failure(ValueError):
    def __init__(self, code: str, message: str, context: dict[str, Any] | None = None):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.context = context or {}


class Level(IntEnum):
    BASE = 0
    SYSTEM = 1
    CONTEXT = 2


class Effect(IntEnum):
    REQUIRE = 0
    FORBID = 1
    DELEGATE = 2
    OBSERVE = 3


class ActivationState(IntEnum):
    DISABLE = 0
    ENABLE = 1


def hash_bytes(domain: str, value: Any) -> bytes:
    h = hashlib.sha256()
    encoded = domain.encode("utf-8")
    h.update(struct.pack("<Q", len(encoded)))
    h.update(encoded)
    payload = canonical_bytes(value)
    h.update(struct.pack("<Q", len(payload)))
    h.update(payload)
    return h.digest()


def value_hash(value: Any) -> bytes:
    return hashlib.sha256(canonical_bytes(value)).digest()


def source_hash(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def hash_matrix(values: Sequence[bytes]) -> np.ndarray:
    if any(len(value) != 32 for value in values):
        raise Runtime53Failure("TENSOR_SCHEMA_MISMATCH", "hash rows must be 32 bytes")
    if not values:
        return np.empty((0, 32), dtype=np.uint8)
    return np.frombuffer(b"".join(values), dtype=np.uint8).reshape(len(values), 32).copy()


def string_pool(labels: Sequence[str]) -> tuple[np.ndarray, np.ndarray]:
    raw = bytearray()
    offsets = [0]
    for label in labels:
        encoded = str(label).encode("utf-8")
        raw.extend(encoded)
        offsets.append(len(raw))
    return np.frombuffer(bytes(raw), dtype=np.uint8).copy(), np.asarray(offsets, dtype=np.int64)


def decode_string_pool(raw: np.ndarray, offsets: np.ndarray) -> tuple[str, ...]:
    if raw.dtype != np.uint8 or offsets.dtype != np.int64 or offsets.ndim != 1:
        raise Runtime53Failure("TENSOR_SCHEMA_MISMATCH", "invalid UTF-8 pool tensors")
    if len(offsets) == 0 or int(offsets[0]) != 0 or int(offsets[-1]) != len(raw):
        raise Runtime53Failure("TENSOR_SCHEMA_MISMATCH", "invalid UTF-8 pool offsets")
    if np.any(offsets[1:] < offsets[:-1]):
        raise Runtime53Failure("TENSOR_SCHEMA_MISMATCH", "UTF-8 offsets are not monotonic")
    blob = raw.tobytes()
    try:
        return tuple(
            blob[int(offsets[index]):int(offsets[index + 1])].decode("utf-8")
            for index in range(len(offsets) - 1)
        )
    except UnicodeDecodeError as exc:
        raise Runtime53Failure("TENSOR_SCHEMA_MISMATCH", "label pool is not UTF-8") from exc


def canonical_tensor(value: np.ndarray) -> np.ndarray:
    array = np.asarray(value)
    if array.dtype.hasobject or array.dtype.kind in {"O", "U", "S", "V"}:
        raise Runtime53Failure("TENSOR_SCHEMA_MISMATCH", "only numeric tensors are allowed")
    if array.dtype.byteorder == ">":
        raise Runtime53Failure("TENSOR_SCHEMA_MISMATCH", "big-endian tensors are refused")
    result = np.ascontiguousarray(array)
    result.setflags(write=False)
    return result


def logical_tensor_hash(schema: str, tensors: Mapping[str, np.ndarray]) -> str:
    h = hashlib.sha256()
    domain = b"moth-logical-tensor-object/5.3"
    h.update(struct.pack("<Q", len(domain)))
    h.update(domain)
    schema_raw = schema.encode("utf-8")
    h.update(struct.pack("<Q", len(schema_raw)))
    h.update(schema_raw)
    for name in sorted(tensors):
        array = canonical_tensor(tensors[name])
        name_raw = name.encode("utf-8")
        dtype_raw = array.dtype.str.encode("ascii")
        h.update(struct.pack("<Q", len(name_raw)))
        h.update(name_raw)
        h.update(struct.pack("<Q", len(dtype_raw)))
        h.update(dtype_raw)
        h.update(struct.pack("<Q", array.ndim))
        for dimension in array.shape:
            h.update(struct.pack("<q", int(dimension)))
        data = array.tobytes(order="C")
        h.update(struct.pack("<Q", len(data)))
        h.update(data)
    return h.hexdigest()


def readonly_tensors(tensors: Mapping[str, np.ndarray]) -> dict[str, np.ndarray]:
    return {name: canonical_tensor(value) for name, value in sorted(tensors.items())}
