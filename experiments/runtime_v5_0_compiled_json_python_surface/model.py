"""Canonical artifact records for the JSON/Python Surface experiment."""

from __future__ import annotations

import hashlib
import json
from typing import Any


ARTIFACT_SCHEMA = "moth-experimental-structured-artifact/1.0"
ARCHIVE_SCHEMA = "moth-experimental-structured-archive/1.0"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest(domain: str, value: Any) -> str:
    return sha256_bytes(domain.encode("utf-8") + b"\0" + canonical_bytes(value))


class ArtifactFidelityFailure(ValueError):
    def __init__(self, code: str, message: str, context: dict[str, Any] | None = None):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.context = context or {}


def make_archive(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": ARCHIVE_SCHEMA,
        "payload": payload,
        "payload_hash": digest("moth-experimental-structured-payload/1.0", payload),
    }


def verify_archive_envelope(archive: dict[str, Any]) -> bool:
    return (
        isinstance(archive, dict)
        and archive.get("schema") == ARCHIVE_SCHEMA
        and isinstance(archive.get("payload"), dict)
        and archive.get("payload_hash")
        == digest("moth-experimental-structured-payload/1.0", archive["payload"])
    )

