"""Conversational Runtime 5.1 orchestration."""

from __future__ import annotations

import json
import resource
import time
from pathlib import Path
from typing import Any

from moth_runtime_v5_0.canonical import canonical_bytes, digest, normalize_text, sha256_bytes
from moth_runtime_v5_0.model import IntegrityError
from moth_runtime_v5_0.runtime import verify_archived_result

from .assets import RuntimeFoundation, load_foundation
from .artifact import ModelArtifact51
from .canonical import finish_result, verify_result_receipt
from .compiled_fields import (
    FieldFailure, compile_skill_document, plan_inert_skill,
    verify_skill_compilation,
)
from .context import (
    ContextFailure, message_identity, project_context, token_count,
    verify_context_receipt,
)
from .hcf import (
    HcfEffect, HcfEntry, HcfFailure, HierarchyLevel,
    compile_context_message, compile_system_prompt, entry_from_dict, make_entry,
    settle_candidates, validate_entries, verify_trace,
)
from .kernel import query_worlds_timed
from .store import ConversationStore
from .surface import realize_surface, verify_surface_artifact


TURN_SCHEMA = "moth-conversation-turn/5.1"


def _mode_candidates(
    foundation: RuntimeFoundation, artifact: ModelArtifact51 | None = None,
) -> list[dict[str, Any]]:
    if artifact is not None:
        return [{
            "candidate_id": f"surface.{item['mode']}",
            "semantic": {
                "response_mode": item["mode"], "field_id": item["field_id"],
                "compilation_id": item["compilation_id"],
            },
            "properties": {
                "response.mode": item["mode"],
                "surface.field_id": item["field_id"],
                "surface.compilation_id": item["compilation_id"],
                "runtime.network": False, "runtime.tool_execution": False,
                "runtime.world_management": False,
            },
            "grounding_cost_units": item["grounding_cost_units"],
        } for item in artifact.capability_index["surface_modes"]]
    return [{
        "candidate_id": f"surface.{mode}",
        "semantic": {"response_mode": mode},
        "properties": {
            "response.mode": mode,
            "runtime.network": False,
            "runtime.tool_execution": False,
            "runtime.world_management": False,
        },
        "grounding_cost_units": index,
    } for index, mode in enumerate(foundation.surface_modes)]


def _failure_evidence(kind: str, code: str, message: str,
                      context: dict[str, Any]) -> dict[str, Any]:
    body = {
        "schema": f"moth-{kind}-failure/5.1", "code": code,
        "message": message, "context": context,
    }
    return {**body, f"{kind}_hash": digest(f"moth-{kind}-failure/5.1", body)}


def _surface_value(kernel_result: dict[str, Any], mode: str) -> tuple[Any, str]:
    if kernel_result.get("status") == "REFUSAL":
        refusal = kernel_result["refusal"]
        text = f"{refusal['code']}: {refusal['message']}"
        return {"kind": "REFUSAL", "value": refusal}, text
    output = kernel_result["output"]
    value = output["value"]
    if mode == "structured":
        rendered = json.dumps(
            {"status": "ANSWER", "output": output}, ensure_ascii=False,
            sort_keys=True, separators=(",", ":"),
        )
    elif mode == "detailed":
        rendered_value = json.dumps(value, ensure_ascii=False, sort_keys=True)
        rendered = (
            f"The verified {output['kind']} result is {rendered_value}. "
            "It was produced by the bounded Input, Main, and Surface settlement pipeline."
        )
    elif isinstance(value, dict) and set(value) == {"meaning_id", "canonical_name"}:
        rendered = str(value["canonical_name"])
    elif isinstance(value, str):
        rendered = value
    else:
        rendered = json.dumps(value, ensure_ascii=False, sort_keys=True,
                              separators=(",", ":"))
    return output, rendered


class Runtime51:
    def __init__(
        self, store: ConversationStore, foundation: RuntimeFoundation,
        artifact: ModelArtifact51 | None = None,
    ):
        self.store = store
        self.foundation = foundation
        self.artifact = artifact
        # Compatibility alias for the first Runtime 5.1 draft.
        self.assets = foundation

    @classmethod
    def initialize(cls, store_path: str | Path, foundation_path: str | Path) -> "Runtime51":
        foundation = load_foundation(foundation_path)
        store = ConversationStore(store_path)
        store.init(foundation)
        return cls(store, foundation)

    @classmethod
    def initialize_from_artifact(
        cls, store_path: str | Path, artifact_path: str | Path,
    ) -> "Runtime51":
        artifact = ModelArtifact51.open(artifact_path)
        store = ConversationStore(store_path)
        store.init(artifact.foundation)
        store.bind_artifact(str(artifact.root), artifact.artifact_id, artifact.artifact_hash)
        for compilation in artifact.skills.values():
            store.store_skill_compilation(compilation)
        return cls(store, artifact.foundation, artifact)

    @classmethod
    def open(cls, store_path: str | Path) -> "Runtime51":
        store = ConversationStore(store_path)
        descriptor = store.descriptor()
        foundation = load_foundation(descriptor["foundation_path"])
        store.init(foundation)
        artifact_descriptor = store.artifact_descriptor()
        if artifact_descriptor is None:
            return cls(store, foundation)
        artifact = ModelArtifact51.open(artifact_descriptor["artifact_path"])
        if (
            artifact.artifact_id != artifact_descriptor["artifact_id"]
            or artifact.artifact_hash != artifact_descriptor["artifact_hash"]
            or artifact.foundation.foundation_hash != foundation.foundation_hash
        ):
            raise IntegrityError("Runtime 5.1 model artifact store binding changed")
        return cls(store, foundation, artifact)

    def _resolve_skills(self, skill_ids: tuple[str, ...]) -> tuple[dict[str, Any], ...]:
        if not skill_ids:
            return ()
        if self.artifact is None:
            raise FieldFailure("ARTIFACT_REQUIRED", "compiled skills require a model artifact")
        if len(set(skill_ids)) != len(skill_ids):
            raise FieldFailure("DUPLICATE_SKILL", "conversation skill is duplicated")
        result: list[dict[str, Any]] = []
        field_ids: set[str] = set()
        for identifier in skill_ids:
            direct = self.artifact.skills.get(identifier)
            matches = [
                value for value in self.artifact.skills.values()
                if value.get("profile_id") == identifier
            ]
            if direct is not None:
                matches = [direct]
            if len(matches) != 1:
                raise FieldFailure("UNKNOWN_SKILL", "skill does not resolve uniquely", {"skill": identifier})
            field_id = str(matches[0]["field_id"])
            if field_id in field_ids:
                raise FieldFailure(
                    "CONFLICTING_SKILLS", "multiple independent policies from one field require an L6 composite",
                    {"field_id": field_id},
                )
            field_ids.add(field_id)
            result.append(matches[0])
        return tuple(result)

    def create_conversation(
        self, system_prompt: str = "", skill_ids: tuple[str, ...] = (),
    ) -> str:
        skills = self._resolve_skills(skill_ids)
        entries = list(compile_system_prompt(system_prompt))
        for compilation in skills:
            entries.append(make_entry(
                meaning_id=f"skill.{compilation['profile_id']}",
                level=HierarchyLevel.SYSTEM, effect=HcfEffect.OBSERVE,
                scope="system.skill", value=compilation["compilation_id"],
                source_hash=compilation["policy_hash"],
                provenance={
                    "source": "model-artifact", "field_id": compilation["field_id"],
                    "compilation_id": compilation["compilation_id"],
                },
            ))
        entries = list(validate_entries(entries))
        validate_entries((*self.assets.base_entries, *entries))
        return self.store.create_conversation(system_prompt, tuple(entries), skills)

    def _previous_result_hash(self, conversation_id: str, head: int) -> str | None:
        if head == 0:
            return None
        return self.store.turn(conversation_id, sequence=head)["result"]["replay"]["result_hash"]

    def _presentation_entry(
        self, presentation: str, message_id: str,
    ) -> HcfEntry:
        if self.artifact is None:
            raise FieldFailure("ARTIFACT_REQUIRED", "compiled presentation requires a model artifact")
        normalized = normalize_text(presentation).casefold().rstrip(".!?")
        matches = [item for item in self.artifact.capability_index["surface_modes"] if any(
            normalize_text(str(request)).casefold().rstrip(".!?") == normalized
            for request in item["requests"]
        )]
        if len(matches) != 1:
            raise FieldFailure(
                "UNSUPPORTED_PRESENTATION" if not matches else "AMBIGUOUS_PRESENTATION",
                "presentation request does not resolve uniquely",
                {"presentation": presentation},
            )
        source_hash = sha256_bytes(normalize_text(presentation).encode("utf-8"))
        return make_entry(
            meaning_id=f"message.{message_id}.presentation",
            level=HierarchyLevel.CONTEXT, effect=HcfEffect.REQUIRE,
            scope="response.mode", value=matches[0]["mode"], source_hash=source_hash,
            provenance={"source": "presentation", "message_id": message_id},
        )

    def turn(
        self, conversation_id: str, message: str, presentation: str | None = None,
    ) -> dict[str, Any]:
        conversation = self.store.conversation(conversation_id)
        expected_head = int(conversation["head_sequence"])
        sequence = expected_head + 1
        normalized = normalize_text(message)
        message_tokens = token_count(normalized)
        user_message_id = message_identity("USER", normalized, conversation_id, sequence)
        turn_id = self.store.turn_identity(conversation_id, sequence, user_message_id)
        started = time.perf_counter_ns()
        usage_before = resource.getrusage(resource.RUSAGE_SELF)
        timings: dict[str, int] = {}

        try:
            if not normalized:
                raise ContextFailure("EMPTY_MESSAGE", "conversation message is empty")
            if message_tokens > self.assets.max_message_tokens:
                raise ContextFailure(
                    "RESOURCE_LIMIT", "message exceeds configured token limit",
                    {"tokens": message_tokens, "limit": self.assets.max_message_tokens},
                )
            phase = time.perf_counter_ns()
            context_entries = compile_context_message(
                normalized, role="USER", message_id=user_message_id,
            )
            if presentation is not None:
                context_entries = validate_entries((
                    *context_entries, self._presentation_entry(presentation, user_message_id),
                ))
            timings["context_compile_ns"] = time.perf_counter_ns() - phase
        except (HcfFailure, FieldFailure) as exc:
            context_entries = compile_context_message(
                normalized, role="ASSISTANT", message_id=user_message_id,
            )
            context_error: ContextFailure | HcfFailure | None = exc
        except ContextFailure as exc:
            safe = normalized or "empty-message"
            context_entries = compile_context_message(
                safe, role="ASSISTANT", message_id=user_message_id,
            )
            context_error = exc
        else:
            context_error = None

        user_message = {
            "message_id": user_message_id, "conversation_id": conversation_id,
            "turn_sequence": sequence, "ordinal": 0, "role": "USER",
            "content": normalized, "token_count": message_tokens,
            "hcf_entries": [item.canonical() for item in context_entries],
        }
        prior_messages = self.store.messages(conversation_id)
        kernel_result: dict[str, Any] | None = None
        surface_artifact: dict[str, Any] | None = None
        selected_mode = "concise"
        hcf_trace: dict[str, Any]
        context_receipt: dict[str, Any] | None = None

        if context_error is None:
            try:
                phase = time.perf_counter_ns()
                context_receipt, active_context_entries, effective_prompt = project_context(
                    prior_messages, current_message=user_message,
                    budget_tokens=self.assets.active_context_tokens,
                )
                timings["context_projection_ns"] = time.perf_counter_ns() - phase
                entries = validate_entries((
                    *self.assets.base_entries, *conversation["system_entries"],
                    *active_context_entries,
                ))
                phase = time.perf_counter_ns()
                candidates = _mode_candidates(self.assets, self.artifact)
                candidate, hcf_trace = settle_candidates(candidates, entries)
                timings["hcf_settlement_ns"] = time.perf_counter_ns() - phase
                selected_mode = str(candidate["properties"]["response.mode"])
                phase = time.perf_counter_ns()
                kernel_result, _, _, kernel_timings = query_worlds_timed(
                    self.assets.worlds, self.assets.bundle, effective_prompt,
                    encoder=self.assets.encoder, thresholds=self.assets.thresholds,
                )
                timings["kernel_ns"] = time.perf_counter_ns() - phase
                timings.update(kernel_timings)
                phase = time.perf_counter_ns()
                if self.artifact is not None and kernel_result.get("status") == "ANSWER":
                    compilation_id = str(candidate["properties"]["surface.compilation_id"])
                    compilation = self.artifact.skills[compilation_id]
                    field = self.artifact.fields[str(compilation["field_id"])]
                    output = kernel_result["output"]
                    surface_artifact = realize_surface(
                        output, mode=selected_mode, field_id=field.field_id,
                        field_hash=field.field_hash, policy_hash=compilation["policy_hash"],
                        artifact_hash=self.artifact.artifact_hash,
                    )
                    response = surface_artifact["text"]
                else:
                    output, response = _surface_value(kernel_result, selected_mode)
                timings["surface_render_ns"] = time.perf_counter_ns() - phase
                status = kernel_result["status"]
                refusal = kernel_result.get("refusal")
            except (ContextFailure, HcfFailure, FieldFailure) as exc:
                context_error = exc
            except (IntegrityError, ValueError, OverflowError) as exc:
                context_error = ContextFailure(
                    "INTEGRITY_FAILURE", "Runtime 5.1 execution failed closed",
                    {"diagnostic": str(exc)},
                )

        if context_error is not None:
            code = context_error.code
            detail = context_error.context
            if isinstance(context_error, HcfFailure) and isinstance(detail.get("trace"), dict):
                hcf_trace = detail["trace"]
                if context_receipt is None:
                    context_receipt = _failure_evidence(
                        "context", code, "context was compiled but HCF settlement refused", {},
                    )
            else:
                context_receipt = _failure_evidence(
                    "context", code, context_error.message, detail,
                )
                hcf_trace = _failure_evidence("hcf", code, context_error.message, detail)
            refusal = {"code": code, "message": context_error.message, "context": detail}
            output = {"kind": "REFUSAL", "value": refusal}
            response = f"{code}: {context_error.message}"
            status = "REFUSAL"

        assistant_message_id = message_identity(
            "ASSISTANT", response, conversation_id, sequence,
        )
        assistant_entries = compile_context_message(
            response, role="ASSISTANT", message_id=assistant_message_id,
        )
        deterministic = {
            "stored_message_count_before_turn": len(prior_messages),
            "active_context_tokens": context_receipt.get("active_tokens", 0),
            "active_context_message_count": len(context_receipt.get("selected_message_ids", [])) + 1,
            "base_activation_count": len(self.assets.base_entries),
            "system_activation_count": len(conversation["system_entries"]),
            "context_activation_count": len(context_entries),
            "candidate_count": len(_mode_candidates(self.assets, self.artifact)),
            "kernel_stage_count": len(kernel_result.get("stages", [])) if kernel_result else 0,
            "kernel_handoff_count": len(kernel_result.get("handoffs", [])) if kernel_result else 0,
            "dispatch_count": 0,
        }
        result: dict[str, Any] = {
            "schema": TURN_SCHEMA, "runtime": "5.1", "status": status,
            "conversation_id": conversation_id, "turn_id": turn_id,
            "sequence": sequence, "user_message_id": user_message_id,
            "assistant_message_id": assistant_message_id,
            "response_mode": selected_mode, "response": response, "output": output,
            "refusal": refusal if status == "REFUSAL" else None,
            "context": context_receipt, "hcf": hcf_trace,
            "kernel": kernel_result, "surface": surface_artifact,
            "deterministic": deterministic,
            "metrics_ref": turn_id,
            "replay": {
                "foundation_id": self.foundation.foundation_id,
                "foundation_hash": self.foundation.foundation_hash,
                "manifest_hash": self.foundation.manifest_hash,
                "base_field_hashes": list(self.foundation.base_field_hashes),
                "bundle_hash": self.assets.bundle.bundle_hash,
                "previous_result_hash": self._previous_result_hash(conversation_id, expected_head),
            },
        }
        if self.artifact is not None:
            result["replay"].update({
                "model_artifact_id": self.artifact.artifact_id,
                "model_artifact_hash": self.artifact.artifact_hash,
                "field_hashes": sorted(field.field_hash for field in self.artifact.fields.values()),
                "active_skill_policy_hashes": [item["policy_hash"] for item in conversation["skills"]],
            })
        finish_result(result)
        usage_after = resource.getrusage(resource.RUSAGE_SELF)
        timings["total_ns"] = time.perf_counter_ns() - started
        metrics = {
            "schema": "moth-operational-metrics/5.1", "turn_id": turn_id,
            "timings_ns": timings,
            "deterministic_counters": deterministic,
            "context": {
                "stored_messages_before_turn": len(prior_messages),
                "active_tokens": context_receipt.get("active_tokens", 0),
                "active_prior_messages": len(context_receipt.get("selected_message_ids", [])),
            },
            "hcf": {
                "winning_vector": hcf_trace.get("winning_vector"),
                "candidate_count": deterministic["candidate_count"],
                "base_activations": deterministic["base_activation_count"],
                "system_activations": deterministic["system_activation_count"],
                "context_activations": deterministic["context_activation_count"],
            },
            "compiled_capabilities": {
                "field_count": len(self.artifact.fields) if self.artifact else 0,
                "active_skill_count": len(conversation["skills"]),
                "surface_mode": selected_mode,
            },
            "integrity": {
                "result_hash": result["replay"]["result_hash"],
                "status": status,
                "refusal_code": refusal.get("code") if refusal else None,
            },
            "cpu_user_seconds_delta": usage_after.ru_utime - usage_before.ru_utime,
            "cpu_system_seconds_delta": usage_after.ru_stime - usage_before.ru_stime,
            "max_rss_observed": usage_after.ru_maxrss,
        }
        self.store.append_turn(
            conversation_id=conversation_id, expected_head=expected_head,
            user_message=user_message, assistant_content=response,
            assistant_entries=assistant_entries, result=result,
            context_receipt=context_receipt, hcf_trace=hcf_trace,
            kernel_result=kernel_result, metrics=metrics,
        )
        return result

    def inspect_context(self, conversation_id: str,
                        turn_id: str | None = None) -> dict[str, Any]:
        if turn_id is None:
            conversation = self.store.conversation(conversation_id)
            if conversation["head_sequence"] == 0:
                return {"conversation_id": conversation_id, "turn": None, "messages": []}
            record = self.store.turn(conversation_id, sequence=conversation["head_sequence"])
        else:
            record = self.store.turn(conversation_id, turn_id=turn_id)
        receipt = record["context"]
        selected = set(receipt.get("selected_message_ids", []))
        current = receipt.get("current_message_id")
        messages = [{
            "message_id": item["message_id"], "turn_sequence": item["turn_sequence"],
            "role": item["role"], "content": item["content"],
            "token_count": item["token_count"],
            "mandatory": item["message_id"] == current
            or item["message_id"] in selected,
        } for item in self.store.messages(conversation_id) if (
            item["message_id"] == current or item["message_id"] in selected
        )]
        return {**receipt, "messages": messages}

    def inspect_hcf(self, conversation_id: str, turn_id: str) -> dict[str, Any]:
        record = self.store.turn(conversation_id, turn_id=turn_id)
        trace = record["hcf"]
        hashes = set(trace.get("entry_hashes", []))
        conversation = self.store.conversation(conversation_id)
        entries: list[HcfEntry] = [*self.assets.base_entries, *conversation["system_entries"]]
        for message in self.store.messages(conversation_id):
            entries.extend(entry_from_dict(value) for value in message["hcf_entries"])
        return {
            "trace": trace,
            "entries": [item.canonical() for item in entries if item.entry_hash in hashes],
        }

    def inspect_foundation(self) -> dict[str, Any]:
        """Return the complete immutable attachment receipt, never member bytes."""
        return self.foundation.receipt()

    def inspect_artifact(self) -> dict[str, Any]:
        if self.artifact is None:
            raise FieldFailure("ARTIFACT_REQUIRED", "Runtime store is foundation-only")
        return self.artifact.receipt()

    def inspect_fields(self) -> list[dict[str, Any]]:
        if self.artifact is None:
            raise FieldFailure("ARTIFACT_REQUIRED", "Runtime store is foundation-only")
        return [{
            "field_id": field.field_id, "kind": field.kind.value,
            "field_hash": field.field_hash, "inventory": field.archive["inventory"],
            "capabilities": list(field.capabilities),
        } for field in sorted(self.artifact.fields.values(), key=lambda item: item.field_id)]

    def inspect_field(self, field_id: str) -> dict[str, Any]:
        if self.artifact is None or field_id not in self.artifact.fields:
            raise KeyError(field_id)
        return self.artifact.fields[field_id].archive

    def compile_skill(self, field_id: str, skill_text: str) -> dict[str, Any]:
        if self.artifact is None or field_id not in self.artifact.fields:
            raise KeyError(field_id)
        compilation = compile_skill_document(self.artifact.fields[field_id], skill_text)
        verify_skill_compilation(compilation, self.artifact.fields[field_id])
        self.store.store_skill_compilation(compilation)
        return compilation

    def inspect_skill(self, compilation_id: str) -> dict[str, Any]:
        compilation = self.store.skill_compilation(compilation_id)
        if self.artifact is None or compilation["field_id"] not in self.artifact.fields:
            raise IntegrityError("stored skill is detached from the model artifact")
        verify_skill_compilation(compilation, self.artifact.fields[compilation["field_id"]])
        return compilation

    def replay_skill(self, compilation_id: str) -> bytes:
        return canonical_bytes(self.inspect_skill(compilation_id))

    def plan_skill(self, compilation_id: str, task_snapshot: dict[str, Any]) -> dict[str, Any]:
        compilation = self.inspect_skill(compilation_id)
        plan = plan_inert_skill(
            compilation, task_snapshot,
            artifact_hash=self.artifact.artifact_hash if self.artifact else None,
        )
        self.store.store_skill_plan(plan)
        return plan

    def replay_turn(self, conversation_id: str, turn_id: str) -> bytes:
        return self.store.replay(conversation_id, turn_id)

    def verify_conversation(self, conversation_id: str) -> dict[str, Any]:
        storage = self.store.verify_storage(conversation_id)
        conversation = self.store.conversation(conversation_id)
        all_messages = self.store.messages(conversation_id)
        previous_hash = None
        for sequence in range(1, int(conversation["head_sequence"]) + 1):
            record = self.store.turn(conversation_id, sequence=sequence)
            result = record["result"]
            verify_result_receipt(result)
            if (
                result["replay"].get("foundation_id") != self.foundation.foundation_id
                or result["replay"].get("foundation_hash") != self.foundation.foundation_hash
                or result["replay"].get("manifest_hash") != self.foundation.manifest_hash
                or result["replay"].get("base_field_hashes") != list(self.foundation.base_field_hashes)
                or result["replay"].get("bundle_hash") != self.foundation.bundle.bundle_hash
            ):
                raise IntegrityError("Runtime 5.1 turn foundation binding changed")
            if self.artifact is not None:
                if (
                    result["replay"].get("model_artifact_id") != self.artifact.artifact_id
                    or result["replay"].get("model_artifact_hash") != self.artifact.artifact_hash
                    or result["replay"].get("field_hashes")
                    != sorted(field.field_hash for field in self.artifact.fields.values())
                    or result["replay"].get("active_skill_policy_hashes")
                    != [item["policy_hash"] for item in conversation["skills"]]
                ):
                    raise IntegrityError("Runtime 5.1 turn model artifact binding changed")
            if (
                canonical_bytes(record["context"]) != canonical_bytes(result["context"])
                or canonical_bytes(record["hcf"]) != canonical_bytes(result["hcf"])
                or canonical_bytes(record["kernel_result"]) != canonical_bytes(result["kernel"])
            ):
                raise IntegrityError("Runtime 5.1 turn evidence tables differ from the result")
            if result["replay"]["previous_result_hash"] != previous_hash:
                raise IntegrityError("Runtime 5.1 conversation result chain changed")
            current = next(item for item in all_messages if (
                item["turn_sequence"] == sequence and item["role"] == "USER"
            ))
            prior = [item for item in all_messages if item["turn_sequence"] < sequence]
            if record["context"].get("schema") == "moth-active-context/5.1":
                context_entries, _ = verify_context_receipt(
                    prior, current_message=current,
                    budget_tokens=self.assets.active_context_tokens,
                    candidate=record["context"],
                )
                entries = validate_entries((
                    *self.assets.base_entries, *conversation["system_entries"],
                    *context_entries,
                ))
                try:
                    verify_trace(_mode_candidates(self.assets, self.artifact), entries, record["hcf"])
                except HcfFailure as exc:
                    trace = exc.context.get("trace")
                    if result["status"] != "REFUSAL" or canonical_bytes(trace) != canonical_bytes(record["hcf"]):
                        raise
            if record["kernel_result"] is not None:
                verify_archived_result(
                    record["kernel_result"], self.assets.worlds, self.assets.bundle,
                )
                if canonical_bytes(record["kernel_result"]) != canonical_bytes(result["kernel"]):
                    raise IntegrityError("Runtime 5.1 kernel result archive changed")
            if result.get("surface") is not None:
                if self.artifact is None or record["kernel_result"] is None:
                    raise IntegrityError("Runtime 5.1 Surface artifact has no model binding")
                mode = str(result["surface"]["mode"])
                matches = [item for item in self.artifact.capability_index["surface_modes"] if item["mode"] == mode]
                if len(matches) != 1:
                    raise IntegrityError("Runtime 5.1 Surface mode no longer resolves")
                compilation = self.artifact.skills[matches[0]["compilation_id"]]
                field = self.artifact.fields[matches[0]["field_id"]]
                verify_surface_artifact(
                    result["surface"], record["kernel_result"]["output"],
                    field_hash=field.field_hash, policy_hash=compilation["policy_hash"],
                    artifact_hash=self.artifact.artifact_hash,
                )
            previous_hash = result["replay"]["result_hash"]
        return {**storage, "conversation_id": conversation_id,
                "verified_result_chain": True}

    def query(self, prompt: str) -> dict[str, Any]:
        conversation_id = self.create_conversation("")
        return self.turn(conversation_id, prompt)


ConversationalRuntime = Runtime51
