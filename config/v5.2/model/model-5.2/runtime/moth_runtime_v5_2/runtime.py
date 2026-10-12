"""Independent Runtime 5.2 conversation orchestration."""

from __future__ import annotations

import json
from pathlib import Path
import resource
import shutil
import time
from typing import Any

import numpy as np

from moth_runtime_v5_0.canonical import (
    canonical_bytes,
    digest,
    normalize_text,
    sha256_bytes,
)
from moth_runtime_v5_0.model import IntegrityError
from moth_runtime_v5_0.runtime import verify_archived_result

from .artifact import ModelArtifact52
from .canonical import finish_result, verify_result_receipt
from .compile.hcf import (
    compile_context_message,
    compile_hcf_source,
    compile_system_prompt,
)
from .compile.skills import (
    compile_skill_object,
    load_field_object,
    load_skill_object,
    plan_inert_skill,
)
from .compiled_fields import (
    compile_skill_document,
    load_field_archive,
)
from .conversation.context import ContextFailure, project_context, token_count
from .energy.loader import HcfTensorField, load_energy_foundation, load_hcf_field
from .energy.schema import Level, Runtime52Failure, hash_bytes
from .energy.settlement import settle
from .kernel import query_worlds_timed
from .persistence.layers import LayerManager
from .persistence.store import ConversationStore
from .surface import realize_surface, verify_surface_artifact


TURN_SCHEMA = "moth-conversation-turn/5.2"


def _failure_evidence(
    kind: str, code: str, message: str, context: dict[str, Any]
) -> dict[str, Any]:
    body = {
        "schema": f"moth-{kind}-failure/5.2",
        "code": code,
        "message": message,
        "context": context,
    }
    return {
        **body,
        f"{kind}_hash": digest(f"moth-{kind}-failure/5.2", body),
    }


def _surface_value(
    kernel_result: dict[str, Any], mode: str
) -> tuple[Any, str]:
    if kernel_result.get("status") == "REFUSAL":
        refusal = kernel_result["refusal"]
        return (
            {"kind": "REFUSAL", "value": refusal},
            f"{refusal['code']}: {refusal['message']}",
        )
    output = kernel_result["output"]
    value = output["value"]
    if mode == "structured":
        rendered = json.dumps(
            {"status": "ANSWER", "output": output},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    elif mode == "detailed":
        rendered_value = json.dumps(
            value, ensure_ascii=False, sort_keys=True
        )
        rendered = (
            f"The verified {output['kind']} result is {rendered_value}. "
            "It was produced by the bounded Input, Main, and Surface "
            "settlement pipeline."
        )
    elif isinstance(value, dict) and set(value) == {
        "meaning_id",
        "canonical_name",
    }:
        rendered = str(value["canonical_name"])
    elif isinstance(value, str):
        rendered = value
    else:
        rendered = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    return output, rendered


class Runtime52:
    def __init__(
        self,
        store: ConversationStore,
        artifact: ModelArtifact52,
    ):
        self.store = store
        self.artifact = artifact
        self.foundation = artifact.kernel_foundation
        energy_envelope = store.objects.open(
            store.descriptor()["energy_foundation_file_hash"]
        )
        self.energy = load_energy_foundation(energy_envelope)
        if (
            self.energy.logical_hash
            != artifact.energy_foundation.logical_hash
        ):
            raise Runtime52Failure(
                "FOUNDATION_BINDING_MISMATCH",
                "store and artifact energy foundations differ",
            )
        self.layers = LayerManager(store, self.energy)
        self.assets = self.foundation

    @classmethod
    def initialize(
        cls, store_dir: str | Path, artifact_path: str | Path
    ) -> "Runtime52":
        source_artifact = ModelArtifact52.open(artifact_path)
        root = Path(store_dir).resolve()
        root.mkdir(parents=True, exist_ok=True)
        destination = root / "artifact"
        if destination.exists():
            existing = ModelArtifact52.open(destination)
            if existing.artifact_hash != source_artifact.artifact_hash:
                raise Runtime52Failure(
                    "STORE_VERSION_MISMATCH",
                    "store contains another model artifact",
                )
        else:
            shutil.copytree(source_artifact.root, destination)
        artifact = ModelArtifact52.open(destination)
        store = ConversationStore(root)
        imported_energy = store.objects.import_file(
            artifact.energy_envelope.path,
            artifact.energy_envelope.file_hash,
        )
        store.initialize(
            artifact_id=artifact.artifact_id,
            artifact_hash=artifact.artifact_hash,
            foundation=imported_energy,
            kernel_foundation_hash=artifact.kernel_foundation.foundation_hash,
        )
        for descriptor in artifact.fields.values():
            envelope = store.objects.import_file(
                artifact.root
                / "objects"
                / "sha256"
                / descriptor["object_hash"][:2]
                / f"{descriptor['object_hash']}.safetensors",
                descriptor["object_hash"],
            )
            store.register_object(envelope)
        for descriptor in artifact.skills.values():
            envelope = store.objects.import_file(
                artifact.root
                / "objects"
                / "sha256"
                / descriptor["object_hash"][:2]
                / f"{descriptor['object_hash']}.safetensors",
                descriptor["object_hash"],
            )
            store.register_object(envelope)
            field_hash = artifact.fields[descriptor["field_id"]]["field_hash"]
            store.register_skill_compilation(
                compilation_id=descriptor["compilation_id"],
                field_id=descriptor["field_id"],
                field_hash=field_hash,
                policy_hash=descriptor["policy_hash"],
                object_hash=descriptor["object_hash"],
            )
        return cls(store, artifact)

    initialize_from_artifact = initialize

    @classmethod
    def open(cls, store_dir: str | Path) -> "Runtime52":
        store = ConversationStore(store_dir)
        descriptor = store.descriptor()
        artifact = ModelArtifact52.open(store.root / "artifact")
        if (
            artifact.artifact_id != descriptor["artifact_id"]
            or artifact.artifact_hash != descriptor["artifact_hash"]
            or artifact.kernel_foundation.foundation_hash
            != descriptor["kernel_foundation_hash"]
        ):
            raise Runtime52Failure(
                "ARTIFACT_VERSION_MISMATCH",
                "store artifact binding changed",
            )
        return cls(store, artifact)

    def _resolve_skills(
        self, skill_ids: tuple[str, ...]
    ) -> tuple[str, ...]:
        if len(set(skill_ids)) != len(skill_ids):
            raise Runtime52Failure(
                "INVALID_FIELD", "conversation skill is duplicated"
            )
        resolved: list[str] = []
        field_ids: set[str] = set()
        for identifier in skill_ids:
            direct = self.artifact.skills.get(identifier)
            matches = [
                value
                for value in self.artifact.skills.values()
                if value["profile_id"] == identifier
            ]
            if direct is not None:
                matches = [direct]
            if len(matches) != 1:
                raise Runtime52Failure(
                    "INVALID_FIELD",
                    "skill does not resolve uniquely",
                    {"skill": identifier},
                )
            field_id = str(matches[0]["field_id"])
            if field_id in field_ids:
                raise Runtime52Failure(
                    "INVALID_FIELD",
                    "multiple policies from one field require a composite",
                    {"field_id": field_id},
                )
            field_ids.add(field_id)
            resolved.append(str(matches[0]["compilation_id"]))
        return tuple(resolved)

    def create_conversation(
        self,
        system_prompt: str = "",
        skill_ids: tuple[str, ...] = (),
    ) -> str:
        skills = self._resolve_skills(skill_ids)
        system = compile_system_prompt(
            self.store.objects, self.energy, system_prompt
        )
        self.store.register_object(system)
        return self.store.create_conversation(
            system_prompt, system, skill_ids=skills
        )

    def compile_hcf_field(
        self, source: dict[str, Any], level: Level | str
    ) -> dict[str, Any]:
        compiled = compile_hcf_source(
            self.store.objects, self.energy, source, level
        )
        field = load_hcf_field(compiled, self.energy)
        self.store.register_object(compiled)
        return {
            "schema": "moth-compiled-object-receipt/5.2",
            "object_kind": compiled.kind,
            "object_hash": compiled.file_hash,
            "logical_hash": compiled.logical_hash,
            "source_hash": compiled.metadata["source_hash"],
            "foundation_hash": compiled.metadata["foundation_hash"],
            "level": field.level.name,
            "entry_count": len(field.tensors["entry_id"]),
            "activation_count": len(
                field.tensors["activation_candidate"]
            ),
            "verified": True,
        }

    def upsert_layer_field(
        self,
        conversation_id: str,
        level: Level | str,
        attachment_key: str,
        object_hash: str,
        expected_revision: int,
    ) -> dict[str, Any]:
        selected = Level[level] if isinstance(level, str) else Level(level)
        return self.layers.upsert(
            conversation_id,
            selected,
            attachment_key,
            object_hash,
            expected_revision,
        )

    def remove_layer_field(
        self,
        conversation_id: str,
        level: Level | str,
        attachment_key: str,
        expected_revision: int,
    ) -> dict[str, Any]:
        selected = Level[level] if isinstance(level, str) else Level(level)
        return self.layers.remove(
            conversation_id,
            selected,
            attachment_key,
            expected_revision,
        )

    def inspect_layer(
        self, conversation_id: str, level: Level | str
    ) -> dict[str, Any]:
        return self.store.layer_snapshot(conversation_id, level)

    def layer_history(
        self, conversation_id: str, level: Level | str
    ) -> list[dict[str, Any]]:
        return self.store.layer_history(conversation_id, level)

    def _persistent_fields(
        self,
        conversation_id: str,
        system_revision_id: str,
        context_revision_id: str,
    ) -> tuple[HcfTensorField, ...]:
        return (
            *self.layers.fields_for_revision(
                conversation_id, Level.SYSTEM, system_revision_id
            ),
            *self.layers.fields_for_revision(
                conversation_id, Level.CONTEXT, context_revision_id
            ),
        )

    def _presentation_mode(self, presentation: str) -> str:
        normalized = (
            normalize_text(presentation).casefold().rstrip(".!?")
        )
        target = np.frombuffer(
            hash_bytes(
                "moth-presentation-request/5.2", normalized
            ),
            dtype=np.uint8,
        )
        matches = np.flatnonzero(
            np.all(self.energy.tensors["request_hash"] == target, axis=1)
        )
        if len(matches) != 1:
            raise Runtime52Failure(
                "UNSUPPORTED_PRESENTATION"
                if len(matches) == 0
                else "AMBIGUOUS_PRESENTATION",
                "presentation request does not resolve uniquely",
                {"presentation": presentation},
            )
        candidate = int(
            self.energy.tensors["request_candidate_index"][int(matches[0])]
        )
        return self.energy.labels[
            int(self.energy.tensors["candidate_mode_index"][candidate])
        ]

    def _surface_bindings(
        self, candidate_index: int
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        field_hash = self.energy.tensors["candidate_field_hash"][
            candidate_index
        ].tobytes()
        skill_hash = self.energy.tensors["candidate_skill_hash"][
            candidate_index
        ].tobytes()
        fields = [
            descriptor
            for descriptor in self.artifact.fields.values()
            if hash_bytes(
                "moth-field-binding/5.2", descriptor["field_id"]
            )
            == field_hash
        ]
        skills = [
            descriptor
            for descriptor in self.artifact.skills.values()
            if hash_bytes(
                "moth-skill-binding/5.2",
                descriptor["compilation_id"],
            )
            == skill_hash
        ]
        if len(fields) != 1 or len(skills) != 1:
            raise Runtime52Failure(
                "INTEGRITY_FAILURE",
                "candidate surface binding does not resolve uniquely",
            )
        return fields[0], skills[0]

    def turn(
        self,
        conversation_id: str,
        message: str,
        presentation: str | None = None,
    ) -> dict[str, Any]:
        conversation = self.store.conversation(conversation_id)
        expected_head = int(conversation["head_sequence"])
        system_revision = str(conversation["system_revision_id"])
        context_revision = str(conversation["context_revision_id"])
        sequence = expected_head + 1
        normalized = normalize_text(message)
        user_message_id = self.store.message_identity(
            "USER", normalized, conversation_id, sequence
        )
        turn_id = self.store.turn_identity(
            conversation_id, sequence, user_message_id
        )
        started = time.perf_counter_ns()
        usage_before = resource.getrusage(resource.RUSAGE_SELF)
        timings: dict[str, int] = {}
        context_error: ContextFailure | Runtime52Failure | None = None
        presentation_field: HcfTensorField | None = None
        presentation_hash: str | None = None
        try:
            message_tokens = token_count(normalized)
            if not normalized:
                raise ContextFailure(
                    "EMPTY_MESSAGE", "conversation message is empty"
                )
            if message_tokens > self.foundation.max_message_tokens:
                raise ContextFailure(
                    "RESOURCE_LIMIT",
                    "message exceeds configured token limit",
                    {
                        "tokens": message_tokens,
                        "limit": self.foundation.max_message_tokens,
                    },
                )
            phase = time.perf_counter_ns()
            user_envelope = compile_context_message(
                self.store.objects,
                self.energy,
                normalized,
                role="USER",
                message_id=user_message_id,
            )
            self.store.register_object(user_envelope)
            user_field = load_hcf_field(user_envelope, self.energy)
            if presentation is not None:
                mode = self._presentation_mode(presentation)
                source = {
                    "schema": "moth-hcf-source/5.2",
                    "entries": [
                        {
                            "meaning_id": (
                                f"message.{user_message_id}.presentation"
                            ),
                            "effect": "REQUIRE",
                            "scope": "response.mode",
                            "value": mode,
                            "source_span": [1, 1, 1, 1],
                        }
                    ],
                    "activations": [],
                }
                presentation_envelope = compile_hcf_source(
                    self.store.objects,
                    self.energy,
                    source,
                    Level.CONTEXT,
                )
                self.store.register_object(presentation_envelope)
                presentation_field = load_hcf_field(
                    presentation_envelope, self.energy
                )
                presentation_hash = presentation_envelope.file_hash
            timings["context_compile_ns"] = (
                time.perf_counter_ns() - phase
            )
        except (ContextFailure, Runtime52Failure) as exc:
            context_error = exc
            safe = normalized or "empty-message"
            user_envelope = compile_context_message(
                self.store.objects,
                self.energy,
                safe,
                role="ASSISTANT",
                message_id=user_message_id,
            )
            self.store.register_object(user_envelope)
            user_field = load_hcf_field(user_envelope, self.energy)
            message_tokens = token_count(normalized)

        user_message = {
            "message_id": user_message_id,
            "conversation_id": conversation_id,
            "turn_sequence": sequence,
            "ordinal": 0,
            "role": "USER",
            "content": normalized,
            "token_count": message_tokens,
            "hcf_object_hash": user_envelope.file_hash,
        }
        prior_messages = self.store.messages(conversation_id)
        kernel_result: dict[str, Any] | None = None
        surface_artifact: dict[str, Any] | None = None
        selected_mode = "concise"
        context_receipt: dict[str, Any] | None = None
        settlement_result = None
        if context_error is None:
            try:
                phase = time.perf_counter_ns()
                context_receipt, effective_prompt = project_context(
                    prior_messages,
                    current_message=user_message,
                    budget_tokens=self.foundation.active_context_tokens,
                )
                transient_hashes = [user_envelope.file_hash]
                if presentation_hash is not None:
                    transient_hashes.append(presentation_hash)
                context_receipt = dict(context_receipt)
                context_receipt["transient_context_object_hashes"] = (
                    transient_hashes
                )
                context_body = {
                    key: value
                    for key, value in context_receipt.items()
                    if key != "context_hash"
                }
                context_receipt["context_hash"] = digest(
                    "moth-active-context/5.2", context_body
                )
                timings["context_projection_ns"] = (
                    time.perf_counter_ns() - phase
                )
                fields = [
                    *self._persistent_fields(
                        conversation_id,
                        system_revision,
                        context_revision,
                    ),
                    user_field,
                ]
                if presentation_field is not None:
                    fields.append(presentation_field)
                phase = time.perf_counter_ns()
                settlement_result = settle(self.energy, fields)
                hcf_trace = settlement_result.trace
                selected_mode = settlement_result.mode
                timings["hcf_settlement_ns"] = (
                    time.perf_counter_ns() - phase
                )
                phase = time.perf_counter_ns()
                kernel_result, _, _, kernel_timings = query_worlds_timed(
                    self.foundation.worlds,
                    self.foundation.bundle,
                    effective_prompt,
                    encoder=self.foundation.encoder,
                    thresholds=self.foundation.thresholds,
                )
                timings["kernel_ns"] = time.perf_counter_ns() - phase
                timings.update(kernel_timings)
                phase = time.perf_counter_ns()
                if kernel_result.get("status") == "ANSWER":
                    field_descriptor, skill_descriptor = (
                        self._surface_bindings(
                            settlement_result.candidate_index
                        )
                    )
                    output = kernel_result["output"]
                    surface_artifact = realize_surface(
                        output,
                        mode=selected_mode,
                        field_id=field_descriptor["field_id"],
                        field_hash=field_descriptor["field_hash"],
                        policy_hash=skill_descriptor["policy_hash"],
                        artifact_hash=self.artifact.artifact_hash,
                    )
                    response = surface_artifact["text"]
                else:
                    output, response = _surface_value(
                        kernel_result, selected_mode
                    )
                timings["surface_render_ns"] = (
                    time.perf_counter_ns() - phase
                )
                status = str(kernel_result["status"])
                refusal = kernel_result.get("refusal")
            except (ContextFailure, Runtime52Failure) as exc:
                context_error = exc
            except (IntegrityError, ValueError, OverflowError) as exc:
                context_error = ContextFailure(
                    "INTEGRITY_FAILURE",
                    "Runtime 5.2 execution failed closed",
                    {"diagnostic": str(exc)},
                )

        if context_error is not None:
            code = context_error.code
            detail = context_error.context
            if (
                isinstance(context_error, Runtime52Failure)
                and isinstance(detail.get("trace"), dict)
            ):
                hcf_trace = detail["trace"]
            else:
                hcf_trace = _failure_evidence(
                    "hcf", code, context_error.message, detail
                )
            if context_receipt is None:
                context_receipt = _failure_evidence(
                    "context", code, context_error.message, detail
                )
                context_receipt[
                    "transient_context_object_hashes"
                ] = [user_envelope.file_hash]
            refusal = {
                "code": code,
                "message": context_error.message,
                "context": detail,
            }
            output = {"kind": "REFUSAL", "value": refusal}
            response = f"{code}: {context_error.message}"
            status = "REFUSAL"

        assistant_message_id = self.store.message_identity(
            "ASSISTANT", response, conversation_id, sequence
        )
        assistant_envelope = compile_context_message(
            self.store.objects,
            self.energy,
            response,
            role="ASSISTANT",
            message_id=assistant_message_id,
        )
        self.store.register_object(assistant_envelope)
        assistant_message = {
            "message_id": assistant_message_id,
            "conversation_id": conversation_id,
            "turn_sequence": sequence,
            "ordinal": 1,
            "role": "ASSISTANT",
            "content": normalize_text(response),
            "token_count": token_count(response),
            "hcf_object_hash": assistant_envelope.file_hash,
        }
        system_snapshot = self.store.layer_snapshot(
            conversation_id, Level.SYSTEM, system_revision
        )
        context_snapshot = self.store.layer_snapshot(
            conversation_id, Level.CONTEXT, context_revision
        )
        active_skills = self.store.conversation_skills(conversation_id)
        deterministic = {
            "stored_message_count_before_turn": len(prior_messages),
            "active_context_tokens": context_receipt.get(
                "active_tokens", 0
            ),
            "active_context_message_count": len(
                context_receipt.get("selected_message_ids", [])
            )
            + 1,
            "base_activation_count": len(
                self.energy.tensors["base_entry_id"]
            ),
            "system_field_count": len(system_snapshot["members"]),
            "persistent_context_field_count": len(
                context_snapshot["members"]
            ),
            "transient_context_field_count": len(
                context_receipt.get(
                    "transient_context_object_hashes", []
                )
            ),
            "candidate_count": self.energy.candidate_count,
            "kernel_stage_count": len(
                kernel_result.get("stages", [])
            )
            if kernel_result
            else 0,
            "kernel_handoff_count": len(
                kernel_result.get("handoffs", [])
            )
            if kernel_result
            else 0,
            "candidate_dictionary_reconstructions": 0,
            "dispatch_count": 0,
        }
        result: dict[str, Any] = {
            "schema": TURN_SCHEMA,
            "runtime": "5.2",
            "status": status,
            "conversation_id": conversation_id,
            "turn_id": turn_id,
            "sequence": sequence,
            "user_message_id": user_message_id,
            "assistant_message_id": assistant_message_id,
            "response_mode": selected_mode,
            "response": response,
            "output": output,
            "refusal": refusal if status == "REFUSAL" else None,
            "context": context_receipt,
            "hcf": hcf_trace,
            "kernel": kernel_result,
            "surface": surface_artifact,
            "deterministic": deterministic,
            "metrics_ref": turn_id,
            "replay": {
                "model_artifact_id": self.artifact.artifact_id,
                "model_artifact_hash": self.artifact.artifact_hash,
                "kernel_foundation_id": self.foundation.foundation_id,
                "kernel_foundation_hash": self.foundation.foundation_hash,
                "kernel_manifest_hash": self.foundation.manifest_hash,
                "bundle_hash": self.foundation.bundle.bundle_hash,
                "energy_foundation_logical_hash": self.energy.logical_hash,
                "energy_foundation_file_hash": self.energy.file_hash,
                "system_revision_id": system_revision,
                "system_layer_hash": system_snapshot["layer_hash"],
                "context_revision_id": context_revision,
                "context_layer_hash": context_snapshot["layer_hash"],
                "transient_context_object_hashes": context_receipt.get(
                    "transient_context_object_hashes", []
                ),
                "candidate_id": settlement_result.candidate_id
                if settlement_result
                else None,
                "active_skill_policy_hashes": [
                    item["policy_hash"] for item in active_skills
                ],
                "previous_result_hash": self.store.previous_result_hash(
                    conversation_id, expected_head
                ),
            },
        }
        finish_result(result)
        usage_after = resource.getrusage(resource.RUSAGE_SELF)
        timings["total_ns"] = time.perf_counter_ns() - started
        metrics = {
            "schema": "moth-operational-metrics/5.2",
            "turn_id": turn_id,
            "timings_ns": timings,
            "deterministic_counters": deterministic,
            "hcf": {
                "winning_vector": hcf_trace.get("winning_energy"),
                "candidate_count": self.energy.candidate_count,
            },
            "integrity": {
                "result_hash": result["replay"]["result_hash"],
                "status": status,
                "refusal_code": refusal.get("code")
                if refusal
                else None,
            },
            "cpu_user_seconds_delta": (
                usage_after.ru_utime - usage_before.ru_utime
            ),
            "cpu_system_seconds_delta": (
                usage_after.ru_stime - usage_before.ru_stime
            ),
            "max_rss_observed": usage_after.ru_maxrss,
        }
        self.store.append_turn(
            conversation_id=conversation_id,
            expected_head=expected_head,
            expected_system_revision=system_revision,
            expected_context_revision=context_revision,
            user_message=user_message,
            assistant_message=assistant_message,
            result=result,
            context_receipt=context_receipt,
            hcf_trace=hcf_trace,
            kernel_result=kernel_result,
            metrics=metrics,
        )
        return result

    def inspect_foundation(self) -> dict[str, Any]:
        return {
            "kernel": self.foundation.receipt(),
            "energy": {
                "schema": "moth-energy-foundation/5.2",
                "logical_hash": self.energy.logical_hash,
                "file_hash": self.energy.file_hash,
                "candidate_count": self.energy.candidate_count,
                "scope_count": self.energy.scope_count,
                "base_entry_count": len(
                    self.energy.tensors["base_entry_id"]
                ),
            },
        }

    def inspect_artifact(self) -> dict[str, Any]:
        return self.artifact.receipt()

    def inspect_fields(self) -> list[dict[str, Any]]:
        return [
            dict(descriptor)
            for descriptor in sorted(
                self.artifact.fields.values(),
                key=lambda item: item["field_id"],
            )
        ]

    def inspect_field(self, field_id: str) -> dict[str, Any]:
        descriptor = self.artifact.fields.get(field_id)
        if descriptor is None:
            raise KeyError(field_id)
        field = load_field_object(
            self.store.objects.open(descriptor["object_hash"])
        )
        return {
            **descriptor,
            "source_hash": field.envelope.metadata["source_hash"],
            "inventory": field.archive["inventory"],
            "capabilities": field.archive["capabilities"],
            "tensor_count": len(field.envelope.tensors),
        }

    def compile_skill(
        self, field_id: str, skill_text: str
    ) -> dict[str, Any]:
        descriptor = self.artifact.fields.get(field_id)
        if descriptor is None:
            raise KeyError(field_id)
        field_object = load_field_object(
            self.store.objects.open(descriptor["object_hash"])
        )
        field = load_field_archive(field_object.archive)
        compilation = compile_skill_document(field, skill_text)
        compiled = compile_skill_object(
            self.store.objects, compilation
        )
        self.store.register_object(compiled.envelope)
        self.store.register_skill_compilation(
            compilation_id=compiled.compilation_id,
            field_id=compiled.field_id,
            field_hash=field.field_hash,
            policy_hash=compiled.policy_hash,
            object_hash=compiled.envelope.file_hash,
        )
        return self.inspect_skill(compiled.compilation_id)

    def inspect_skill(
        self, compilation_id: str
    ) -> dict[str, Any]:
        descriptor = self.store.skill_compilation(compilation_id)
        skill = load_skill_object(
            self.store.objects.open(descriptor["object_hash"])
        )
        return {
            "schema": "moth-compiled-skill-receipt/5.2",
            **descriptor,
            "profile_id": skill.profile_id,
            "source_hash": skill.source_hash,
            "workflow": list(skill.workflow),
            "completion": list(skill.completion),
            "logical_hash": skill.envelope.logical_hash,
            "verified": True,
        }

    def replay_skill(self, compilation_id: str) -> bytes:
        return canonical_bytes(self.inspect_skill(compilation_id))

    def plan_skill(
        self,
        compilation_id: str,
        task_snapshot: dict[str, Any],
    ) -> dict[str, Any]:
        descriptor = self.store.skill_compilation(compilation_id)
        skill = load_skill_object(
            self.store.objects.open(descriptor["object_hash"])
        )
        plan = plan_inert_skill(
            skill,
            task_snapshot,
            artifact_hash=self.artifact.artifact_hash,
        )
        self.store.store_skill_plan(plan)
        return plan

    def inspect_context(
        self,
        conversation_id: str,
        turn_id: str | None = None,
    ) -> dict[str, Any]:
        if turn_id is None:
            conversation = self.store.conversation(conversation_id)
            if conversation["head_sequence"] == 0:
                return {
                    "conversation_id": conversation_id,
                    "turn": None,
                    "messages": [],
                }
            record = self.store.turn(
                conversation_id,
                sequence=conversation["head_sequence"],
            )
        else:
            record = self.store.turn(
                conversation_id, turn_id=turn_id
            )
        receipt = record["context"]
        selected = set(receipt.get("selected_message_ids", []))
        current = receipt.get("current_message_id")
        messages = [
            {
                "message_id": item["message_id"],
                "turn_sequence": item["turn_sequence"],
                "role": item["role"],
                "content": item["content"],
                "token_count": item["token_count"],
                "mandatory": item["message_id"] == current
                or item["message_id"] in selected,
            }
            for item in self.store.messages(conversation_id)
            if item["message_id"] == current
            or item["message_id"] in selected
        ]
        return {**receipt, "messages": messages}

    def inspect_hcf(
        self, conversation_id: str, turn_id: str
    ) -> dict[str, Any]:
        record = self.store.turn(
            conversation_id, turn_id=turn_id
        )
        return {
            "trace": record["hcf"],
            "system_revision": self.store.layer_snapshot(
                conversation_id,
                Level.SYSTEM,
                record["system_revision_id"],
            ),
            "context_revision": self.store.layer_snapshot(
                conversation_id,
                Level.CONTEXT,
                record["context_revision_id"],
            ),
            "transient_context_object_hashes": record["result"][
                "replay"
            ]["transient_context_object_hashes"],
        }

    def replay_turn(
        self, conversation_id: str, turn_id: str
    ) -> bytes:
        return self.store.replay(conversation_id, turn_id)

    def verify_conversation(
        self, conversation_id: str
    ) -> dict[str, Any]:
        storage = self.store.verify_storage(conversation_id)
        conversation = self.store.conversation(conversation_id)
        previous_hash = None
        for sequence in range(
            1, int(conversation["head_sequence"]) + 1
        ):
            record = self.store.turn(
                conversation_id, sequence=sequence
            )
            result = record["result"]
            verify_result_receipt(result)
            replay = result["replay"]
            if (
                replay["model_artifact_hash"]
                != self.artifact.artifact_hash
                or replay["kernel_foundation_hash"]
                != self.foundation.foundation_hash
                or replay["energy_foundation_logical_hash"]
                != self.energy.logical_hash
                or replay["previous_result_hash"] != previous_hash
                or replay["system_revision_id"]
                != record["system_revision_id"]
                or replay["context_revision_id"]
                != record["context_revision_id"]
            ):
                raise Runtime52Failure(
                    "INTEGRITY_FAILURE",
                    "turn replay binding changed",
                )
            system_snapshot = self.store.layer_snapshot(
                conversation_id,
                Level.SYSTEM,
                record["system_revision_id"],
            )
            context_snapshot = self.store.layer_snapshot(
                conversation_id,
                Level.CONTEXT,
                record["context_revision_id"],
            )
            if (
                system_snapshot["layer_hash"]
                != replay["system_layer_hash"]
                or context_snapshot["layer_hash"]
                != replay["context_layer_hash"]
            ):
                raise Runtime52Failure(
                    "INTEGRITY_FAILURE", "turn layer hash changed"
                )
            fields = [
                *self._persistent_fields(
                    conversation_id,
                    record["system_revision_id"],
                    record["context_revision_id"],
                )
            ]
            for object_hash in replay[
                "transient_context_object_hashes"
            ]:
                fields.append(
                    load_hcf_field(
                        self.store.objects.open(object_hash),
                        self.energy,
                    )
                )
            try:
                expected_settlement = settle(self.energy, fields)
            except Runtime52Failure as exc:
                if result["status"] != "REFUSAL":
                    raise
                if exc.code != result["refusal"]["code"]:
                    raise Runtime52Failure(
                        "INTEGRITY_FAILURE",
                        "replayed refusal code changed",
                    ) from exc
                if isinstance(exc.context.get("trace"), dict):
                    if canonical_bytes(exc.context["trace"]) != canonical_bytes(
                        record["hcf"]
                    ):
                        raise Runtime52Failure(
                            "INTEGRITY_FAILURE",
                            "replayed refusal trace changed",
                        )
            else:
                if canonical_bytes(
                    expected_settlement.trace
                ) != canonical_bytes(record["hcf"]):
                    raise Runtime52Failure(
                        "INTEGRITY_FAILURE",
                        "replayed HCF trace changed",
                    )
            if record["kernel_result"] is not None:
                verify_archived_result(
                    record["kernel_result"],
                    self.foundation.worlds,
                    self.foundation.bundle,
                )
            if result.get("surface") is not None:
                if record["kernel_result"] is None:
                    raise Runtime52Failure(
                        "INTEGRITY_FAILURE",
                        "surface has no kernel result",
                    )
                field_descriptor, skill_descriptor = (
                    self._surface_bindings(
                        expected_settlement.candidate_index
                    )
                )
                verify_surface_artifact(
                    result["surface"],
                    record["kernel_result"]["output"],
                    field_hash=field_descriptor["field_hash"],
                    policy_hash=skill_descriptor["policy_hash"],
                    artifact_hash=self.artifact.artifact_hash,
                )
            previous_hash = replay["result_hash"]
        return {
            **storage,
            "conversation_id": conversation_id,
            "verified_result_chain": True,
        }

    def query(self, prompt: str) -> dict[str, Any]:
        conversation_id = self.create_conversation("")
        return self.turn(conversation_id, prompt)


ConversationalRuntime = Runtime52
