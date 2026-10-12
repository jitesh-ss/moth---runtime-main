"""Atomic content-addressed Safetensors storage."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Mapping

import numpy as np
from safetensors import safe_open
from safetensors.numpy import save

from ..energy.schema import Runtime52Failure, logical_tensor_hash, readonly_tensors


@dataclass(frozen=True)
class TensorEnvelope:
    schema: str
    kind: str
    logical_hash: str
    file_hash: str
    metadata: Mapping[str, str]
    tensors: Mapping[str, np.ndarray]
    path: Path


class ObjectStore:
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self.objects = self.root / "objects" / "sha256"

    def path_for(self, file_hash: str) -> Path:
        if len(file_hash) != 64 or any(
            character not in "0123456789abcdef" for character in file_hash
        ):
            raise Runtime52Failure("OBJECT_NOT_FOUND", "invalid object hash")
        return self.objects / file_hash[:2] / f"{file_hash}.safetensors"

    def put(
        self,
        tensors: Mapping[str, np.ndarray],
        *,
        schema: str,
        kind: str,
        source_hash: str = "",
        foundation_hash: str = "",
    ) -> TensorEnvelope:
        canonical = readonly_tensors(tensors)
        logical_hash = logical_tensor_hash(schema, canonical)
        metadata_body = {
            "runtime": "5.2",
            "schema": schema,
            "kind": kind,
            "logical_hash": logical_hash,
            "source_hash": source_hash,
            "foundation_hash": foundation_hash,
        }
        # safetensors 0.8 stores metadata in a Rust HashMap whose emitted key
        # order is process-randomized.  A single canonical JSON metadata value
        # preserves exact-file determinism without changing tensor semantics.
        metadata = {
            "moth": json.dumps(
                metadata_body,
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
            )
        }
        raw = save(canonical, metadata=metadata)
        file_hash = hashlib.sha256(raw).hexdigest()
        destination = self.path_for(file_hash)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            if destination.read_bytes() != raw:
                raise Runtime52Failure(
                    "OBJECT_HASH_MISMATCH", "object identity collision"
                )
        else:
            descriptor, temporary = tempfile.mkstemp(
                prefix=".moth-", dir=destination.parent
            )
            try:
                with os.fdopen(descriptor, "wb") as handle:
                    handle.write(raw)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, destination)
                directory_fd = os.open(destination.parent, os.O_RDONLY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
        return self.open(file_hash)

    def import_file(
        self, source: str | Path, expected_hash: str
    ) -> TensorEnvelope:
        raw = Path(source).read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        if actual != expected_hash:
            raise Runtime52Failure(
                "OBJECT_HASH_MISMATCH", "artifact object hash changed"
            )
        destination = self.path_for(actual)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            descriptor, temporary = tempfile.mkstemp(
                prefix=".moth-", dir=destination.parent
            )
            try:
                with os.fdopen(descriptor, "wb") as handle:
                    handle.write(raw)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, destination)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
        elif destination.read_bytes() != raw:
            raise Runtime52Failure(
                "OBJECT_HASH_MISMATCH", "object identity collision"
            )
        return self.open(actual)

    def open(self, file_hash: str) -> TensorEnvelope:
        path = self.path_for(file_hash)
        if not path.is_file():
            raise Runtime52Failure(
                "OBJECT_NOT_FOUND",
                "compiled object is missing",
                {"hash": file_hash},
            )
        raw_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if raw_hash != file_hash:
            raise Runtime52Failure(
                "OBJECT_HASH_MISMATCH", "compiled object bytes changed"
            )
        try:
            with safe_open(path, framework="np", device="cpu") as handle:
                container_metadata = dict(handle.metadata() or {})
                tensors = {
                    name: handle.get_tensor(name) for name in sorted(handle.keys())
                }
        except Exception as exc:
            raise Runtime52Failure(
                "TENSOR_SCHEMA_MISMATCH", "Safetensors object cannot be opened"
            ) from exc
        try:
            if set(container_metadata) != {"moth"}:
                raise ValueError("metadata envelope changed")
            metadata = json.loads(container_metadata["moth"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise Runtime52Failure(
                "TENSOR_SCHEMA_MISMATCH", "Safetensors metadata is invalid"
            ) from exc
        if not isinstance(metadata, dict) or set(metadata) != {
            "runtime",
            "schema",
            "kind",
            "logical_hash",
            "source_hash",
            "foundation_hash",
        }:
            raise Runtime52Failure(
                "TENSOR_SCHEMA_MISMATCH", "Safetensors metadata schema changed"
            )
        if metadata.get("runtime") != "5.2":
            raise Runtime52Failure(
                "TENSOR_SCHEMA_MISMATCH", "cross-runtime tensor object refused"
            )
        schema = metadata.get("schema", "")
        logical_hash = logical_tensor_hash(schema, tensors)
        if logical_hash != metadata.get("logical_hash"):
            raise Runtime52Failure(
                "OBJECT_HASH_MISMATCH", "logical tensor hash changed"
            )
        return TensorEnvelope(
            schema,
            metadata.get("kind", ""),
            logical_hash,
            file_hash,
            metadata,
            readonly_tensors(tensors),
            path,
        )
