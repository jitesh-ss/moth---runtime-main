"""Independent Runtime 5.3 conversation orchestration."""

from __future__ import annotations

import json
from pathlib import Path
import resource
import shutil
import time
from typing import Any

import numpy as np

from moth_runtime_v5_3.legacy.canonical import (
    canonical_bytes,
    digest,
    normalize_text,
    sha256_bytes,
)
from moth_runtime_v5_3.legacy.model import IntegrityError
from moth_runtime_v5_3.legacy.runtime import verify_archived_result

from .artifact import ModelArtifact53
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
from .energy.schema import Level, Runtime53Failure, hash_bytes
from .energy.settlement import settle
from .kernel import query_worlds_timed
from .persistence.layers import LayerManager
from .persistence.store import ConversationStore
from .surface import realize_surface, verify_surface_artifact


TURN_SCHEMA = "moth-conversation-turn/5.3"


def _failure_evidence(
    kind: str, code: str, message: str, context: dict[str, Any]
) -> dict[str, Any]:
    body = {
        "schema": f"moth-{kind}-failure/5.3",
        "code": code,
        "message": message,
        "context": context,
    }
    return {
        **body,
        f"{kind}_hash": digest(f"moth-{kind}-failure/5.3", body),
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


class CompatibilityRuntime53:
    def __init__(
        self,
        store: ConversationStore,
        artifact: ModelArtifact53,
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
            raise Runtime53Failure(
                "FOUNDATION_BINDING_MISMATCH",
                "store and artifact energy foundations differ",
            )
        self.layers = LayerManager(store, self.energy)
        self.assets = self.foundation

    @classmethod
    def initialize(
        cls, store_dir: str | Path, artifact_path: str | Path
    ) -> "Runtime53":
        source_artifact = ModelArtifact53.open(artifact_path)
        root = Path(store_dir).resolve()
        root.mkdir(parents=True, exist_ok=True)
        destination = root / "artifact"
        if destination.exists():
            existing = ModelArtifact53.open(destination)
            if existing.artifact_hash != source_artifact.artifact_hash:
                raise Runtime53Failure(
                    "STORE_VERSION_MISMATCH",
                    "store contains another model artifact",
                )
        else:
            shutil.copytree(source_artifact.root, destination)
        artifact = ModelArtifact53.open(destination)
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
    def open(cls, store_dir: str | Path) -> "Runtime53":
        store = ConversationStore(store_dir)
        descriptor = store.descriptor()
        artifact = ModelArtifact53.open(store.root / "artifact")
        if (
            artifact.artifact_id != descriptor["artifact_id"]
            or artifact.artifact_hash != descriptor["artifact_hash"]
            or artifact.kernel_foundation.foundation_hash
            != descriptor["kernel_foundation_hash"]
        ):
            raise Runtime53Failure(
                "ARTIFACT_VERSION_MISMATCH",
                "store artifact binding changed",
            )
        return cls(store, artifact)

    def _resolve_skills(
        self, skill_ids: tuple[str, ...]
    ) -> tuple[str, ...]:
        if len(set(skill_ids)) != len(skill_ids):
            raise Runtime53Failure(
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
                raise Runtime53Failure(
                    "INVALID_FIELD",
                    "skill does not resolve uniquely",
                    {"skill": identifier},
                )
            field_id = str(matches[0]["field_id"])
            if field_id in field_ids:
                raise Runtime53Failure(
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
            "schema": "moth-compiled-object-receipt/5.3",
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
                "moth-presentation-request/5.3", normalized
            ),
            dtype=np.uint8,
        )
        matches = np.flatnonzero(
            np.all(self.energy.tensors["request_hash"] == target, axis=1)
        )
        if len(matches) != 1:
            raise Runtime53Failure(
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
                "moth-field-binding/5.3", descriptor["field_id"]
            )
            == field_hash
        ]
        skills = [
            descriptor
            for descriptor in self.artifact.skills.values()
            if hash_bytes(
                "moth-skill-binding/5.3",
                descriptor["compilation_id"],
            )
            == skill_hash
        ]
        if len(fields) != 1 or len(skills) != 1:
            raise Runtime53Failure(
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
        context_error: ContextFailure | Runtime53Failure | None = None
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
                    "schema": "moth-hcf-source/5.3",
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
        except (ContextFailure, Runtime53Failure) as exc:
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
                    "moth-active-context/5.3", context_body
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
            except (ContextFailure, Runtime53Failure) as exc:
                context_error = exc
            except (IntegrityError, ValueError, OverflowError) as exc:
                context_error = ContextFailure(
                    "INTEGRITY_FAILURE",
                    "Runtime 5.3 execution failed closed",
                    {"diagnostic": str(exc)},
                )

        if context_error is not None:
            code = context_error.code
            detail = context_error.context
            if (
                isinstance(context_error, Runtime53Failure)
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
            "runtime": "5.3",
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
        result['compatibility53'] = {'presentation': presentation}
        finish_result(result)
        usage_after = resource.getrusage(resource.RUSAGE_SELF)
        timings["total_ns"] = time.perf_counter_ns() - started
        metrics = {
            "schema": "moth-operational-metrics/5.3",
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
                "schema": "moth-energy-foundation/5.3",
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
            "schema": "moth-compiled-skill-receipt/5.3",
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
                raise Runtime53Failure(
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
                raise Runtime53Failure(
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
            except Runtime53Failure as exc:
                if result["status"] != "REFUSAL":
                    raise
                if exc.code != result["refusal"]["code"]:
                    raise Runtime53Failure(
                        "INTEGRITY_FAILURE",
                        "replayed refusal code changed",
                    ) from exc
                if isinstance(exc.context.get("trace"), dict):
                    if canonical_bytes(exc.context["trace"]) != canonical_bytes(
                        record["hcf"]
                    ):
                        raise Runtime53Failure(
                            "INTEGRITY_FAILURE",
                            "replayed refusal trace changed",
                        )
            else:
                if canonical_bytes(
                    expected_settlement.trace
                ) != canonical_bytes(record["hcf"]):
                    raise Runtime53Failure(
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
                    raise Runtime53Failure(
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


ConversationalRuntime = CompatibilityRuntime53

# Public 5.3 conversation orchestration. The compatibility engine above is owned
# by this package and remains available for the previously qualified queries.
from dataclasses import asdict
from copy import deepcopy
from .tensor_data import put_data, read_data
from .knowledge import initial_knowledge, active_facts
from . import chat
from .reasoning import ReasoningRequest, ReasoningResult
from .checker import verify as verify_reasoning
from .legacy.grounding import ground_prompt, GroundingFailure
from .legacy.model import WorldRole
from .persistence.objects import ObjectStore

class Runtime53(CompatibilityRuntime53):
    def __init__(self, store, artifact):
        super().__init__(store,artifact)
        descriptor=json.loads((artifact.root/'conversation-foundation.json').read_text())
        envelope=ObjectStore(artifact.root).open(descriptor['object_hash'])
        self.chat_source=read_data(envelope,'conversation-foundation')
        from .language import validate_source
        validate_source(self.chat_source)
        self.chat_hash=envelope.logical_hash

    def _knowledge(self,conversation_id):
        self.store.conversation(conversation_id)
        with self.store._connect() as db:
            row=db.execute('SELECT r.revision_id,r.object_hash FROM knowledge_heads h JOIN knowledge_revisions r ON h.revision_id=r.revision_id WHERE h.conversation_id=?',(conversation_id,)).fetchone()
        if row is None:return None,initial_knowledge(self.chat_source)
        return row[0],read_data(self.store.objects.open(row[1]),'knowledge')

    def inspect_knowledge(self,conversation_id):
        revision,knowledge=self._knowledge(conversation_id)
        return {'revision':revision,**knowledge,'active_facts':active_facts(knowledge)}

    def inspect_reasoning(self,conversation_id,turn_id):
        return self.store.turn(conversation_id,turn_id=turn_id)['result'].get('conversation53')

    def prepare(self,conversation_id,message,presentation=None):
        conversation=self.store.conversation(conversation_id)
        revision,knowledge=self._knowledge(conversation_id)
        sequence=conversation['head_sequence']+1
        normalized=normalize_text(message)
        mid=self.store.message_identity('USER',normalized,conversation_id,sequence)
        turn_id=self.store.turn_identity(conversation_id,sequence,mid)
        bindings={'artifact':self.artifact.artifact_hash,'foundation':self.chat_hash,'knowledge_revision':revision,
                  'system_revision':conversation['system_revision_id'],'context_revision':conversation['context_revision_id'],
                  'conversation':conversation_id,'sequence':sequence,'message_id':mid}
        next,prepared=chat.prepare(self.chat_source,knowledge,normalized,mid,bindings)
        before=put_data(self.store.objects,knowledge,'knowledge');self.store.register_object(before)
        return dict(conversation=conversation,revision=revision,knowledge=knowledge,next=next,prepared=prepared,
                    bindings=bindings,message=normalized,message_id=mid,turn_id=turn_id,before_object=before.file_hash,
                    presentation=presentation)

    def solve(self,prepared):
        return chat.solve(prepared['prepared'])

    def verify(self,solved):
        if solved['reasoning']:
            raw=solved['reasoning']
            verify_reasoning(ReasoningRequest(**solved['request']),ReasoningResult(**raw))
        return True

    def _policy53(self,prepared):
        c=prepared['conversation']
        envelope=compile_context_message(self.store.objects,self.energy,prepared['message'],role='USER',message_id=prepared['message_id'])
        self.store.register_object(envelope)
        hashes=[envelope.file_hash]
        fields=list(self._persistent_fields(c['conversation_id'],c['system_revision_id'],c['context_revision_id']))
        fields.append(load_hcf_field(envelope,self.energy))
        if prepared['presentation']:
            mode=self._presentation_mode(prepared['presentation'])
            obj=compile_hcf_source(self.store.objects,self.energy,{'schema':'moth-hcf-source/5.3','entries':[{
                'meaning_id':'presentation','effect':'REQUIRE','scope':'response.mode','value':mode,'source_span':[1,1,1,1]}],'activations':[]},Level.CONTEXT)
            self.store.register_object(obj);hashes.append(obj.file_hash);fields.append(load_hcf_field(obj,self.energy))
        policy=settle(self.energy,fields)
        return hashes,policy

    def commit(self,prepared,solved,hashes,policy):
        self.verify(solved)
        rendered=chat.surface(solved,policy.mode);chat.verify_surface(rendered,solved)
        c=prepared['conversation'];cid=c['conversation_id'];sequence=c['head_sequence']+1
        after=deepcopy(prepared['next'])
        if solved['status'] not in ('CLARIFICATION_REQUIRED','ACKNOWLEDGED') and 'previous' not in solved['detail']:
            # A compact prior result avoids recursively embedding the entire history.
            after['last_result']={'turn_id':prepared['turn_id'],'status':solved['status'],'response':rendered['text'],
                                  'request_hash':solved['reasoning']['request_hash'] if solved['reasoning'] else None}
        obj=put_data(self.store.objects,after,'knowledge');self.store.register_object(obj)
        revision=digest('moth-knowledge-revision/5.3',{'parent':prepared['revision'],'object':obj.file_hash,'turn_id':prepared['turn_id']})
        assistant_id=self.store.message_identity('ASSISTANT',rendered['text'],cid,sequence)
        assistant=compile_context_message(self.store.objects,self.energy,rendered['text'],role='ASSISTANT',message_id=assistant_id)
        self.store.register_object(assistant)
        def msg(role,content,identifier,object_hash,ordinal):
            return dict(message_id=identifier,conversation_id=cid,turn_sequence=sequence,ordinal=ordinal,role=role,
                        content=normalize_text(content),token_count=token_count(content),hcf_object_hash=object_hash)
        extension={'before_revision':prepared['revision'],'before_object':prepared['before_object'],
                   'after_revision':revision,'after_object':obj.file_hash,'bindings':prepared['bindings'],
                   'message':prepared['message'],'solved':solved,'surface':rendered,'transient_hashes':hashes,
                   'presentation':prepared['presentation'],'policy_failure':prepared.get('policy_failure')}
        result={'schema':TURN_SCHEMA,'runtime':'5.3','status':solved['status'],'conversation_id':cid,'turn_id':prepared['turn_id'],
                'sequence':sequence,'user_message_id':prepared['message_id'],'assistant_message_id':assistant_id,
                'response':rendered['text'],'response_mode':policy.mode,'output':{'kind':'CONVERSATION','value':solved['detail']},
                'context':{'knowledge_revision':prepared['revision'],'current_message_id':prepared['message_id'],
                'selected_message_ids':sorted({f['source'] for f in (solved['request']['facts'] if solved['request'] else []) if f['source']!='foundation'})},'hcf':policy.trace,'kernel':None,'surface':None,
                'conversation53':extension,'replay':{'previous_result_hash':self.store.previous_result_hash(cid,c['head_sequence']),
                'model_artifact_hash':self.artifact.artifact_hash,'transient_context_object_hashes':hashes},'deterministic':{'dispatch_count':0,'task_writes':0},'metrics_ref':prepared['turn_id']}
        finish_result(result)
        self.store.append_turn(conversation_id=cid,expected_head=c['head_sequence'],expected_system_revision=c['system_revision_id'],
            expected_context_revision=c['context_revision_id'],user_message=msg('USER',prepared['message'],prepared['message_id'],hashes[0],0),
            assistant_message=msg('ASSISTANT',rendered['text'],assistant_id,assistant.file_hash,1),result=result,
            context_receipt=result['context'],hcf_trace=policy.trace,kernel_result=None,metrics={'dispatch_count':0,'timings_ns':prepared.get('timings',{}),'reasoning':solved.get('reasoning',{}).get('detail',{}) if solved.get('reasoning') else {}})
        return result

    def turn(self,conversation_id,message,presentation=None):
        # Only a successful existing grounding selects the compatibility path.
        try:
            ground_prompt(self.foundation.worlds[WorldRole.INPUT],normalize_text(message),encoder=self.foundation.encoder,thresholds=self.foundation.thresholds)
        except GroundingFailure:
            pass
        else:
            return super().turn(conversation_id,message,presentation)
        started=time.perf_counter_ns()
        prepared=self.prepare(conversation_id,message,presentation)
        prepared['timings']={'prepare_ns':time.perf_counter_ns()-started}
        phase=time.perf_counter_ns()
        try:
            hashes,policy=self._policy53(prepared)
        except Runtime53Failure as exc:
            # A policy refusal is a recorded turn, with no semantic update.
            from types import SimpleNamespace
            obj=compile_context_message(self.store.objects,self.energy,('message-sha256:'+sha256_bytes(prepared['message'].encode('utf-8'))),role='ASSISTANT',message_id=prepared['message_id'])
            self.store.register_object(obj)
            hashes=[obj.file_hash]
            policy=SimpleNamespace(mode='concise',trace={'failure':exc.code,'detail':exc.context})
            prepared['next']=deepcopy(prepared['knowledge'])
            solved={**prepared['prepared'],'status':'REFUSAL','detail':{'reason':exc.message,'code':exc.code},'request':None,'reasoning':None}
            prepared['policy_failure']={'code':exc.code,'message':exc.message,'context':exc.context}
        else:
            prepared['timings']['policy_ns']=time.perf_counter_ns()-phase
            phase=time.perf_counter_ns()
            solved=self.solve(prepared)
            prepared['timings']['solve_and_verify_ns']=time.perf_counter_ns()-phase
        prepared['timings']['precommit_ns']=time.perf_counter_ns()-started
        return self.commit(prepared,solved,hashes,policy)

    def reexecute(self,conversation_id,turn_id):
        record=self.store.turn(conversation_id,turn_id=turn_id);result=record['result']
        verify_result_receipt(result)
        ext=result.get('conversation53')
        if ext is None:
            return self._reexecute_compatibility(conversation_id,record)
        if ext['bindings']['artifact']!=self.artifact.artifact_hash or ext['bindings']['foundation']!=self.chat_hash:
            raise IntegrityError('historical foundation changed')
        expected_mid=self.store.message_identity('USER',ext['message'],conversation_id,result['sequence'])
        if expected_mid!=result['user_message_id'] or expected_mid!=ext['bindings']['message_id']:
            raise IntegrityError('historical message binding changed')
        with self.store._connect() as db:
            stored_message=db.execute('SELECT content FROM messages WHERE message_id=?',(expected_mid,)).fetchone()
            if not stored_message or stored_message[0]!=ext['message']:
                raise IntegrityError('message source differs')
            row=db.execute('SELECT conversation_id,parent_id,object_hash,turn_id FROM knowledge_revisions WHERE revision_id=?',(ext['after_revision'],)).fetchone()
            if row!=(conversation_id,ext['before_revision'],ext['after_object'],turn_id):
                raise IntegrityError('knowledge revision binding differs')
            if ext['before_revision']:
                parent=db.execute('SELECT conversation_id,object_hash FROM knowledge_revisions WHERE revision_id=?',(ext['before_revision'],)).fetchone()
                if parent!=(conversation_id,ext['before_object']):
                    raise IntegrityError('knowledge parent differs')
        before=read_data(self.store.objects.open(ext['before_object']),'knowledge')
        if ext['before_revision'] is None and canonical_bytes(before)!=canonical_bytes(initial_knowledge(self.chat_source)):
            raise IntegrityError('initial knowledge differs from the foundation')
        next,prepared=chat.prepare(self.chat_source,before,ext['message'],ext['bindings']['message_id'],ext['bindings'])
        failure=ext.get('policy_failure')
        if failure:
            # Independently repeat policy compilation in an ephemeral CAS.
            import tempfile
            from types import SimpleNamespace
            with tempfile.TemporaryDirectory(prefix='moth53-policy-') as directory:
                objects=ObjectStore(directory)
                try:
                    obj=compile_context_message(objects,self.energy,ext['message'],role='USER',message_id=ext['bindings']['message_id'])
                    fields=list(self._persistent_fields(conversation_id,ext['bindings']['system_revision'],ext['bindings']['context_revision']))
                    fields.append(load_hcf_field(obj,self.energy))
                    if ext.get('presentation'):
                        mode=self._presentation_mode(ext['presentation'])
                        source={'schema':'moth-hcf-source/5.3','entries':[{'meaning_id':'presentation','effect':'REQUIRE','scope':'response.mode','value':mode,'source_span':[1,1,1,1]}],'activations':[]}
                        fields.append(load_hcf_field(compile_hcf_source(objects,self.energy,source,Level.CONTEXT),self.energy))
                    settle(self.energy,fields)
                except Runtime53Failure as exc:
                    if failure!={'code':exc.code,'message':exc.message,'context':exc.context}:raise IntegrityError('policy refusal changed')
                else:raise IntegrityError('policy refusal no longer reproduces')
            solved={**prepared,'status':'REFUSAL','detail':{'reason':failure['message'],'code':failure['code']},'request':None,'reasoning':None}
            next=deepcopy(before)
        else:
            solved=chat.solve(prepared)
        self.verify(solved)
        if canonical_bytes(solved)!=canonical_bytes(ext['solved']):raise IntegrityError('reasoning reexecution differs')
        fields=list(self._persistent_fields(conversation_id,ext['bindings']['system_revision'],ext['bindings']['context_revision']))
        fields.extend(load_hcf_field(self.store.objects.open(h),self.energy) for h in ext['transient_hashes'])
        if failure:
            from types import SimpleNamespace
            policy=SimpleNamespace(mode='concise',trace={'failure':failure['code'],'detail':failure['context']})
        else:
            policy=settle(self.energy,fields)
        if canonical_bytes(policy.trace)!=canonical_bytes(result['hcf']):raise IntegrityError('historical policy differs')
        rendered=chat.surface(solved,policy.mode);chat.verify_surface(ext['surface'],solved)
        if rendered['text']!=result['response']:raise IntegrityError('historical response changed')
        if solved['status'] not in ('CLARIFICATION_REQUIRED','ACKNOWLEDGED') and 'previous' not in solved['detail']:
            next['last_result']={'turn_id':turn_id,'status':solved['status'],'response':rendered['text'],
                'request_hash':solved['reasoning']['request_hash'] if solved['reasoning'] else None}
        if canonical_bytes(next)!=canonical_bytes(read_data(self.store.objects.open(ext['after_object']),'knowledge')):
            raise IntegrityError('knowledge reexecution differs')
        expected=digest('moth-knowledge-revision/5.3',{'parent':ext['before_revision'],'object':ext['after_object'],'turn_id':turn_id})
        if expected!=ext['after_revision']:raise IntegrityError('knowledge revision changed')
        return {'turn_id':turn_id,'verified':True,'result_hash':result['replay']['result_hash'],'reexecuted':True}

    def _reexecute_compatibility(self,conversation_id,record):
        # Clone into a temporary store; the original store remains untouched.
        import tempfile,sqlite3
        with tempfile.TemporaryDirectory(prefix='moth53-reexecute-') as directory:
            root=Path(directory)
            shutil.copytree(self.store.root/'artifact',root/'artifact')
            shutil.copytree(self.store.root/'objects',root/'objects')
            with self.store._connect() as source,sqlite3.connect(root/'catalog.sqlite3') as target:source.backup(target)
            replay=Runtime53.open(root)
            sequence=record['result']['sequence'];result=record['result']
            with replay.store._connect() as db:
                db.execute('PRAGMA foreign_keys=OFF')
                db.execute('DELETE FROM operational_metrics WHERE turn_id IN (SELECT turn_id FROM turns WHERE conversation_id=? AND sequence>=?)',(conversation_id,sequence))
                db.execute('DELETE FROM turns WHERE conversation_id=? AND sequence>=?',(conversation_id,sequence))
                db.execute('DELETE FROM messages WHERE conversation_id=? AND turn_sequence>=?',(conversation_id,sequence))
                db.execute('UPDATE conversations SET head_sequence=?,system_revision_id=?,context_revision_id=? WHERE conversation_id=?',
                    (sequence-1,record['system_revision_id'],record['context_revision_id'],conversation_id))
            message=next(m['content'] for m in self.store.messages(conversation_id) if m['message_id']==result['user_message_id'])
            rerun=CompatibilityRuntime53.turn(replay,conversation_id,message,result.get('compatibility53',{}).get('presentation'))
            # Explicit presentation can differ from an implicit request: retry the original implicit path.
            if canonical_bytes(rerun)!=canonical_bytes(result):
                raise IntegrityError('compatibility reexecution differs')
        return {'turn_id':result['turn_id'],'verified':True,'reexecuted':True}

    def verify_conversation(self,conversation_id):
        storage=self.store.verify_storage(conversation_id)
        previous=None
        latest=None
        for sequence in range(1,self.store.conversation(conversation_id)['head_sequence']+1):
            result=self.store.turn(conversation_id,sequence=sequence)['result']
            if result['replay']['previous_result_hash']!=previous:raise IntegrityError('result chain differs')
            self.reexecute(conversation_id,result['turn_id']);previous=result['replay']['result_hash']
            if result.get('conversation53'):latest=(result['conversation53']['after_revision'],)
        with self.store._connect() as db:
            head=db.execute('SELECT revision_id FROM knowledge_heads WHERE conversation_id=?',(conversation_id,)).fetchone()
        if latest!=head:raise IntegrityError('knowledge head does not match committed turns')
        return {**storage,'verified_result_chain':True,'reexecuted':True}

ConversationalRuntime=Runtime53
