"""Disposable Runtime 5.0 instance with a structured-output Surface overlay."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from moth_runtime_v5_0.canonical import canonical_bytes as runtime_bytes
from moth_runtime_v5_0.encoder import DeterministicEncoder
from moth_runtime_v5_0.model import WorldRole
from moth_runtime_v5_0.store import WorldStore

from experiments.runtime_v5_0_compiled_surface_skill.worlds import (
    SURFACE_SOURCE,
    decision_source,
    semantic_source,
)

from .model import (
    ArtifactFidelityFailure,
    canonical_bytes,
    digest,
    make_archive,
    verify_archive_envelope,
)
from .serializer import serialize_artifact, verify_artifact


class StructuredSurfaceInstance:
    def __init__(
        self,
        instance_root: Path,
        *,
        project_root: Path,
        field: dict[str, Any],
        compilation: dict[str, Any],
        thresholds: dict[str, Any],
    ) -> None:
        self.instance_root = instance_root.resolve()
        self.project_root = project_root.resolve()
        production_data = (self.project_root / "data").resolve()
        if self.instance_root == production_data or production_data in self.instance_root.parents:
            raise ArtifactFidelityFailure("ISOLATION_FAILURE", "experimental instance is inside production data")
        self.instance_root.mkdir(parents=True, exist_ok=False)
        self.store_path = self.instance_root / "store-5.0.sqlite3"
        self.field = field
        self.compilation = compilation
        self.thresholds = thresholds
        self.encoder = DeterministicEncoder()
        self.store = WorldStore(self.store_path)
        self.store.publish(
            WorldRole.INPUT,
            {"input.moth": semantic_source("delivery", "deployment")},
            encoder=self.encoder,
        )
        self.store.publish(
            WorldRole.MAIN,
            {"main.moth": decision_source()},
            encoder=self.encoder,
        )
        self.store.publish(
            WorldRole.SURFACE,
            {"surface.moth": SURFACE_SOURCE},
            encoder=self.encoder,
        )
        self.bundle = self.store.activate()

    def query_runtime(self, prompt: str) -> dict[str, Any]:
        return self.store.query(prompt, encoder=self.encoder, thresholds=self.thresholds)

    def query(self, prompt: str, presentation_request: str) -> dict[str, Any]:
        runtime_result = self.query_runtime(prompt)
        if runtime_result.get("status") != "ANSWER":
            return {
                "runtime_result": runtime_result,
                "surface_applied": False,
                "artifact": None,
                "archive": None,
            }
        artifact = serialize_artifact(
            runtime_result["output"],
            presentation_request,
            self.compilation,
            self.field,
        )
        payload = {
            "runtime_episode_id": runtime_result["episode_id"],
            "runtime_result_hash": runtime_result["replay"]["result_hash"],
            "runtime_output": runtime_result["output"],
            "presentation_request": presentation_request,
            "field_hash": self.compilation["field_hash"],
            "policy_hash": self.compilation["policy_hash"],
            "artifact": artifact,
        }
        return {
            "runtime_result": runtime_result,
            "surface_applied": True,
            "artifact": artifact,
            "archive": make_archive(payload),
        }

    def replay(self, archive: dict[str, Any]) -> bytes:
        if not verify_archive_envelope(archive):
            raise ArtifactFidelityFailure("ARCHIVE_TAMPERED", "structured archive envelope changed")
        payload = archive["payload"]
        required = {
            "runtime_episode_id",
            "runtime_result_hash",
            "runtime_output",
            "presentation_request",
            "field_hash",
            "policy_hash",
            "artifact",
        }
        if set(payload) != required:
            raise ArtifactFidelityFailure("ARCHIVE_TAMPERED", "structured archive payload shape changed")
        if payload["field_hash"] != self.compilation["field_hash"] or payload["policy_hash"] != self.compilation["policy_hash"]:
            raise ArtifactFidelityFailure("HASH_BINDING_INVALID", "archive is detached from the compiled skill")
        runtime_replay = self.store.replay(str(payload["runtime_episode_id"]), encoder_free=True)
        runtime_result = json.loads(runtime_replay)
        if runtime_replay != runtime_bytes(runtime_result):
            raise ArtifactFidelityFailure("RUNTIME_REPLAY_FAILURE", "Runtime 5.0 replay changed")
        if runtime_result["replay"]["result_hash"] != payload["runtime_result_hash"]:
            raise ArtifactFidelityFailure("HASH_BINDING_INVALID", "archive Runtime result hash changed")
        if runtime_result["output"] != payload["runtime_output"]:
            raise ArtifactFidelityFailure("SEMANTIC_DRIFT", "archive Runtime output changed")
        verify_artifact(payload["artifact"], payload["runtime_output"], self.compilation, self.field)
        regenerated = serialize_artifact(
            payload["runtime_output"],
            str(payload["presentation_request"]),
            self.compilation,
            self.field,
        )
        if canonical_bytes(regenerated) != canonical_bytes(payload["artifact"]):
            raise ArtifactFidelityFailure("ARTIFACT_REPLAY_FAILURE", "structured artifact is not byte-stable")
        if archive["payload_hash"] != digest("moth-experimental-structured-payload/1.0", payload):
            raise ArtifactFidelityFailure("ARCHIVE_TAMPERED", "structured archive hash changed")
        return canonical_bytes(archive)
