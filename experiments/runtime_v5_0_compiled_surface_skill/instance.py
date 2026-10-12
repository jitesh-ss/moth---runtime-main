"""Disposable Runtime 5.0 instance with an experiment-local compiled Surface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from moth_runtime_v5_0.canonical import canonical_bytes as runtime_bytes
from moth_runtime_v5_0.encoder import DeterministicEncoder
from moth_runtime_v5_0.model import WorldRole
from moth_runtime_v5_0.store import WorldStore

from .model import (
    SurfaceFidelityFailure,
    canonical_bytes,
    digest,
    make_archive,
    verify_archive_envelope,
)
from .realizer import realize, verify_response
from .worlds import SURFACE_SOURCE, decision_source, semantic_source


class IsolatedSurfaceInstance:
    """Own one temporary three-World store and its non-production Surface overlay."""

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
            raise SurfaceFidelityFailure("ISOLATION_FAILURE", "experimental instance is inside production data")
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
                "surface_response": None,
                "archive": None,
            }
        response = realize(
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
            "surface_response": response,
        }
        archive = make_archive(payload)
        return {
            "runtime_result": runtime_result,
            "surface_applied": True,
            "surface_response": response,
            "archive": archive,
        }

    def replay(self, archive: dict[str, Any]) -> bytes:
        if not verify_archive_envelope(archive):
            raise SurfaceFidelityFailure("ARCHIVE_TAMPERED", "Surface archive envelope changed")
        payload = archive["payload"]
        required = {
            "runtime_episode_id",
            "runtime_result_hash",
            "runtime_output",
            "presentation_request",
            "field_hash",
            "policy_hash",
            "surface_response",
        }
        if set(payload) != required:
            raise SurfaceFidelityFailure("ARCHIVE_TAMPERED", "Surface archive payload shape changed")
        if payload["field_hash"] != self.compilation["field_hash"] or payload["policy_hash"] != self.compilation["policy_hash"]:
            raise SurfaceFidelityFailure("HASH_BINDING_INVALID", "archive is detached from the compiled skill")
        runtime_replay = self.store.replay(str(payload["runtime_episode_id"]), encoder_free=True)
        runtime_result = json.loads(runtime_replay)
        if runtime_replay != runtime_bytes(runtime_result):
            raise SurfaceFidelityFailure("RUNTIME_REPLAY_FAILURE", "Runtime 5.0 replay changed")
        if runtime_result["replay"]["result_hash"] != payload["runtime_result_hash"]:
            raise SurfaceFidelityFailure("HASH_BINDING_INVALID", "archive Runtime result hash changed")
        if runtime_result["output"] != payload["runtime_output"]:
            raise SurfaceFidelityFailure("SEMANTIC_DRIFT", "archive Runtime output changed")
        verify_response(
            payload["surface_response"],
            payload["runtime_output"],
            self.compilation,
            self.field,
        )
        regenerated = realize(
            payload["runtime_output"],
            str(payload["presentation_request"]),
            self.compilation,
            self.field,
        )
        if canonical_bytes(regenerated) != canonical_bytes(payload["surface_response"]):
            raise SurfaceFidelityFailure("SURFACE_REPLAY_FAILURE", "Surface response is not byte-stable")
        if archive["payload_hash"] != digest("moth-experimental-surface-payload/1.0", payload):
            raise SurfaceFidelityFailure("ARCHIVE_TAMPERED", "Surface archive hash changed")
        return canonical_bytes(archive)
