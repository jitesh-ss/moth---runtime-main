"""Stable symbol helpers shared by Runtime 5.3 compilers."""

from __future__ import annotations

from typing import Any

from ..energy.schema import hash_bytes, value_hash


def candidate_id(value: str) -> bytes:
    return hash_bytes("moth-candidate-id/5.3", str(value))


def semantic_id(value: Any) -> bytes:
    return hash_bytes("moth-candidate-semantic/5.3", value)


def symbol_id(value: str) -> bytes:
    return hash_bytes("moth-symbol/5.3", str(value))


__all__ = ["candidate_id", "semantic_id", "symbol_id", "value_hash"]
