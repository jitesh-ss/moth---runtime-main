"""Disposable Runtime 5.0 instance for the rich-output phase."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from moth_runtime_v5_0.canonical import canonical_bytes as runtime_bytes
from moth_runtime_v5_0.encoder import DeterministicEncoder
from moth_runtime_v5_0.model import WorldRole
from moth_runtime_v5_0.store import WorldStore

from experiments.runtime_v5_0_compiled_surface_skill.model import normalize_text
from experiments.runtime_v5_0_compiled_surface_skill.worlds import SURFACE_SOURCE, decision_source, semantic_source

from .model import OutputFidelityFailure, canonical_bytes, digest, make_archive, verify_archive_envelope
from .realizer import realize_artifact, verify_artifact


class RichSurfaceInstance:
    def __init__(
        self,
        instance_root: Path,
        *,
        project_root: Path,
        field: dict[str, Any],
        compilations: dict[str, dict[str, Any]],
        thresholds: dict[str, Any],
    ) -> None:
        self.instance_root = instance_root.resolve()
        self.project_root = project_root.resolve()
        production_data = (self.project_root / "data").resolve()
        if self.instance_root == production_data or production_data in self.instance_root.parents:
            raise OutputFidelityFailure("ISOLATION_FAILURE", "experimental instance is inside production data")
        self.instance_root.mkdir(parents=True, exist_ok=False)
        self.store_path = self.instance_root / "store-5.0.sqlite3"
        self.field = field
        self.compilations = compilations
        self.thresholds = thresholds
        self.encoder = DeterministicEncoder()
        self.store = WorldStore(self.store_path)
        self.store.publish(
            WorldRole.INPUT,
            {"input.moth": semantic_source("delivery", "deployment")},
            encoder=self.encoder,
        )
        self.store.publish(WorldRole.MAIN, {"main.moth": decision_source()}, encoder=self.encoder)
        self.store.publish(WorldRole.SURFACE, {"surface.moth": SURFACE_SOURCE}, encoder=self.encoder)
        self.bundle = self.store.activate()

    def query_runtime(self, prompt: str) -> dict[str, Any]:
        return self.store.query(prompt, encoder=self.encoder, thresholds=self.thresholds)

    def _route(self, request: str) -> tuple[str, dict[str, Any]]:
        normalized = normalize_text(request).casefold().rstrip(".!?")
        matches = [
            route
            for route in self.field["presentation_routes"]
            if normalized == normalize_text(str(route["request"])).casefold().rstrip(".!?")
        ]
        if len(matches) != 1:
            raise OutputFidelityFailure("UNSUPPORTED_PRESENTATION", "request has no unique rich-output route")
        profile = str(matches[0]["profile"])
        if profile not in self.compilations:
            raise OutputFidelityFailure("INVALID_SURFACE_POLICY", "route has no compiled skill")
        return profile, self.compilations[profile]

    def query(self, prompt: str, presentation_request: str) -> dict[str, Any]:
        runtime_result = self.query_runtime(prompt)
        if runtime_result.get("status") != "ANSWER":
            return {"runtime_result": runtime_result, "surface_applied": False, "artifact": None, "archive": None}
        profile, compilation = self._route(presentation_request)
        artifact = realize_artifact(runtime_result["output"], presentation_request, compilation, self.field)
        payload = {
            "runtime_episode_id": runtime_result["episode_id"],
            "runtime_result_hash": runtime_result["replay"]["result_hash"],
            "runtime_output": runtime_result["output"],
            "presentation_request": presentation_request,
            "profile": profile,
            "field_hash": compilation["field_hash"],
            "policy_hash": compilation["policy_hash"],
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
            raise OutputFidelityFailure("ARCHIVE_TAMPERED", "archive envelope changed")
        payload = archive["payload"]
        required = {
            "runtime_episode_id",
            "runtime_result_hash",
            "runtime_output",
            "presentation_request",
            "profile",
            "field_hash",
            "policy_hash",
            "artifact",
        }
        if set(payload) != required:
            raise OutputFidelityFailure("ARCHIVE_TAMPERED", "archive payload shape changed")
        profile = str(payload["profile"])
        compilation = self.compilations.get(profile)
        if compilation is None:
            raise OutputFidelityFailure("HASH_BINDING_INVALID", "archive profile is not compiled")
        if payload["field_hash"] != compilation["field_hash"] or payload["policy_hash"] != compilation["policy_hash"]:
            raise OutputFidelityFailure("HASH_BINDING_INVALID", "archive is detached from the compiled skill")
        runtime_replay = self.store.replay(str(payload["runtime_episode_id"]), encoder_free=True)
        runtime_result = json.loads(runtime_replay)
        if runtime_replay != runtime_bytes(runtime_result):
            raise OutputFidelityFailure("RUNTIME_REPLAY_FAILURE", "Runtime replay changed")
        if runtime_result["replay"]["result_hash"] != payload["runtime_result_hash"]:
            raise OutputFidelityFailure("HASH_BINDING_INVALID", "Runtime result hash changed")
        if runtime_result["output"] != payload["runtime_output"]:
            raise OutputFidelityFailure("SEMANTIC_DRIFT", "archived Runtime output changed")
        verify_artifact(payload["artifact"], payload["runtime_output"], compilation, self.field)
        regenerated = realize_artifact(
            payload["runtime_output"],
            str(payload["presentation_request"]),
            compilation,
            self.field,
        )
        if canonical_bytes(regenerated) != canonical_bytes(payload["artifact"]):
            raise OutputFidelityFailure("ARTIFACT_REPLAY_FAILURE", "artifact is not byte-stable")
        if archive["payload_hash"] != digest("moth-v5-rich-output-payload/1.0", payload):
            raise OutputFidelityFailure("ARCHIVE_TAMPERED", "archive payload hash changed")
        return canonical_bytes(archive)
