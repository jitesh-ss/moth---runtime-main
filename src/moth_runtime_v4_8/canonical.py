"""Canonical serialization and content addressing for Runtime 4.8."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import unicodedata
from typing import Any

RUNTIME = "4.8"


def normalize_text(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("text must be a string")
    value.encode("utf-8", errors="strict")
    return " ".join(unicodedata.normalize("NFC", value).split())


def _clean(value: Any) -> Any:
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("canonical payload contains a non-finite number")
        return value
    if isinstance(value, dict):
        return {str(key): _clean(item) for key, item in sorted(value.items())}
    if isinstance(value, (tuple, list)):
        return [_clean(item) for item in value]
    return value


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        _clean(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: str | Path) -> str:
    result = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def digest(domain: str, value: Any) -> str:
    return sha256_bytes(domain.encode("utf-8") + b"\0" + canonical_bytes(value))


def meaning_id(kind: str, payload: Any) -> str:
    return digest("moth-world-meaning/4.8", {
        "runtime": RUNTIME, "kind": kind, "payload": payload,
    })


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_canonical(path: str | Path, value: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(canonical_bytes(value) + b"\n")
