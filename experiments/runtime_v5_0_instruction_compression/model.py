"""Canonical records for the isolated instruction-compression experiment."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import unicodedata
from typing import Any


POLICY_SCHEMA = "moth-compiled-skill-policy/1.0"
COMPILATION_SCHEMA = "moth-skill-compilation/1.0"
ARCHIVE_SCHEMA = "moth-instruction-instance-archive/1.0"


def normalize_text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).strip().split())


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


class FieldValidationError(ValueError):
    def __init__(self, layer: str, message: str):
        super().__init__(f"{layer}: {message}")
        self.layer = layer
        self.message = message


class CompilationFailure(ValueError):
    def __init__(self, code: str, message: str, context: dict[str, Any] | None = None):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.context = context or {}


class ExecutionFailure(RuntimeError):
    pass


@dataclass(frozen=True)
class Clause:
    section: str
    text: str
    line: int
    sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "section": self.section,
            "text": self.text,
            "line": self.line,
            "sha256": self.sha256,
        }


def policy_hash(policy: dict[str, Any]) -> str:
    return digest("moth-compiled-skill-policy/1.0", policy)


def make_archive(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": ARCHIVE_SCHEMA,
        "payload": payload,
        "payload_hash": digest("moth-instruction-instance-payload/1.0", payload),
    }


def verify_archive(archive: dict[str, Any]) -> bool:
    return (
        isinstance(archive, dict)
        and archive.get("schema") == ARCHIVE_SCHEMA
        and isinstance(archive.get("payload"), dict)
        and archive.get("payload_hash")
        == digest("moth-instruction-instance-payload/1.0", archive["payload"])
    )

