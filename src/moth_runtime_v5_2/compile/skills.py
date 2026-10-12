"""Typed graph and opcode storage for compiled fields and inert skills."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

import numpy as np

from moth_runtime_v5_0.canonical import digest, sha256_bytes

from ..energy.schema import (
    COMPILED_FIELD_SCHEMA,
    COMPILED_SKILL_SCHEMA,
    Runtime52Failure,
    decode_string_pool,
    hash_bytes,
    hash_matrix,
    source_hash,
    string_pool,
)
from ..persistence.objects import ObjectStore, TensorEnvelope
from ..compiled_fields import FieldKind, compile_field_archive


_NULL, _BOOL, _INT, _STRING, _LIST, _DICT = range(6)


@dataclass(frozen=True)
class CompiledFieldObject:
    field_id: str
    kind: str
    field_hash: str
    envelope: TensorEnvelope
    archive: dict[str, Any]


@dataclass(frozen=True)
class CompiledSkillObject:
    compilation_id: str
    field_id: str
    profile_id: str
    policy_hash: str
    source_hash: str
    workflow: tuple[str, ...]
    completion: tuple[str, ...]
    envelope: TensorEnvelope


def _encode_graph(value: Any) -> tuple[dict[str, np.ndarray], list[str]]:
    kinds: list[int] = []
    parents: list[int] = []
    keys: list[int] = []
    text_values: list[int] = []
    int_values: list[int] = []
    labels: list[str] = []
    label_map: dict[str, int] = {}

    def label(text: str) -> int:
        if text not in label_map:
            label_map[text] = len(labels)
            labels.append(text)
        return label_map[text]

    def visit(item: Any, parent: int, key: str | None) -> int:
        index = len(kinds)
        parents.append(parent)
        keys.append(label(key) if key is not None else -1)
        text_values.append(-1)
        int_values.append(0)
        if item is None:
            kinds.append(_NULL)
        elif isinstance(item, bool):
            kinds.append(_BOOL)
            int_values[index] = int(item)
        elif isinstance(item, int):
            kinds.append(_INT)
            int_values[index] = item
        elif isinstance(item, str):
            kinds.append(_STRING)
            text_values[index] = label(item)
        elif isinstance(item, list):
            kinds.append(_LIST)
            for child in item:
                visit(child, index, None)
        elif isinstance(item, dict):
            kinds.append(_DICT)
            for child_key in sorted(item):
                visit(item[child_key], index, str(child_key))
        else:
            raise Runtime52Failure(
                "INVALID_FIELD",
                "compiled graph accepts JSON scalar types only",
                {"type": type(item).__name__},
            )
        return index

    visit(value, -1, None)
    if len(kinds) >= 2**15 or len(labels) >= 2**15:
        raise Runtime52Failure(
            "RESOURCE_LIMIT", "compiled field graph exceeds fixed tensor bounds"
        )
    if any(value < -(2**31) or value >= 2**31 for value in int_values):
        raise Runtime52Failure(
            "RESOURCE_LIMIT", "compiled field integer exceeds int32 bounds"
        )
    integer_indices = [
        index
        for index, kind in enumerate(kinds)
        if kind in (_BOOL, _INT)
    ]
    return {
        "node_kind": np.asarray(kinds, dtype=np.uint8),
        "node_parent": np.asarray(parents, dtype=np.int16),
        "node_key_label": np.asarray(keys, dtype=np.int16),
        "node_text_label": np.asarray(text_values, dtype=np.int16),
        "node_int_index": np.asarray(integer_indices, dtype=np.int16),
        "node_int_value": np.asarray(
            [int_values[index] for index in integer_indices], dtype=np.int32
        ),
    }, labels


def _decode_graph(tensors: dict[str, np.ndarray], labels: tuple[str, ...]) -> Any:
    kinds = tensors["node_kind"]
    parents = tensors["node_parent"]
    keys = tensors["node_key_label"]
    text = tensors["node_text_label"]
    integer_indices = tensors["node_int_index"]
    integer_values = tensors["node_int_value"]
    count = len(kinds)
    if not (
        parents.shape == keys.shape == text.shape == (count,)
        and count
        and int(parents[0]) == -1
    ):
        raise Runtime52Failure(
            "TENSOR_SCHEMA_MISMATCH", "compiled graph shape is invalid"
        )
    if (
        integer_indices.ndim != 1
        or integer_values.shape != integer_indices.shape
        or np.any(integer_indices < 0)
        or np.any(integer_indices >= count)
        or np.any(integer_indices[1:] <= integer_indices[:-1])
    ):
        raise Runtime52Failure(
            "TENSOR_SCHEMA_MISMATCH", "compiled integer operands are invalid"
        )
    integers = {
        int(index): int(value)
        for index, value in zip(integer_indices, integer_values)
    }
    children: list[list[int]] = [[] for _ in range(count)]
    for index in range(1, count):
        parent = int(parents[index])
        if parent < 0 or parent >= index:
            raise Runtime52Failure(
                "TENSOR_SCHEMA_MISMATCH", "compiled graph parent is invalid"
            )
        children[parent].append(index)

    def build(index: int) -> Any:
        kind = int(kinds[index])
        if kind == _NULL:
            return None
        if kind == _BOOL:
            if index not in integers:
                raise Runtime52Failure(
                    "TENSOR_SCHEMA_MISMATCH", "boolean operand is absent"
                )
            return bool(integers[index])
        if kind == _INT:
            if index not in integers:
                raise Runtime52Failure(
                    "TENSOR_SCHEMA_MISMATCH", "integer operand is absent"
                )
            return integers[index]
        if kind == _STRING:
            label_index = int(text[index])
            if label_index < 0 or label_index >= len(labels):
                raise Runtime52Failure(
                    "TENSOR_SCHEMA_MISMATCH", "text label is out of range"
                )
            return labels[label_index]
        if kind == _LIST:
            return [build(child) for child in children[index]]
        if kind == _DICT:
            result = {}
            for child in children[index]:
                key_index = int(keys[child])
                if key_index < 0 or key_index >= len(labels):
                    raise Runtime52Failure(
                        "TENSOR_SCHEMA_MISMATCH", "key label is out of range"
                    )
                key = labels[key_index]
                if key in result:
                    raise Runtime52Failure(
                        "TENSOR_SCHEMA_MISMATCH", "compiled key is duplicated"
                    )
                result[key] = build(child)
            return result
        raise Runtime52Failure(
            "TENSOR_SCHEMA_MISMATCH", "compiled graph opcode is invalid"
        )

    return build(0)


def compile_field_object(
    store: ObjectStore, archive: dict[str, Any]
) -> CompiledFieldObject:
    required = {"field_id", "kind", "field_hash", "source"}
    if not required <= set(archive):
        raise Runtime52Failure(
            "INVALID_FIELD", "compiled field archive is incomplete"
        )
    # The archive contains a human-source copy plus derived hashes and
    # inventories. Store the validated L1-L6 source graph once, as typed
    # numeric IR, and deterministically derive the redundant inspection view
    # only when a developer explicitly asks for it.
    graph, labels = _encode_graph(archive["source"])
    label_map = {value: index for index, value in enumerate(labels)}

    def label(value: str) -> int:
        text = str(value)
        if text not in label_map:
            if len(labels) >= 2**15 - 1:
                raise Runtime52Failure(
                    "RESOURCE_LIMIT", "compiled field label table is full"
                )
            label_map[text] = len(labels)
            labels.append(text)
        return label_map[text]

    binding_indices = [
        label(str(archive["field_id"])),
        label(str(archive["kind"])),
        label(str(archive["field_hash"])),
    ]
    capability_indices = [
        label(str(value)) for value in archive.get("capabilities", [])
    ]
    label_bytes, label_offsets = string_pool(labels)
    if len(label_bytes) >= 2**31:
        raise Runtime52Failure(
            "RESOURCE_LIMIT", "compiled field string pool exceeds int32 bounds"
        )
    label_offsets = label_offsets.astype(np.int32)
    tensors = {
        **graph,
        "label_bytes": label_bytes,
        "label_offsets": label_offsets,
        "binding_label_index": np.asarray(binding_indices, dtype=np.int16),
        "capability_label_index": np.asarray(
            capability_indices, dtype=np.int16
        ),
        "identity_hash": hash_matrix(
            [
                hash_bytes("moth-field-id/5.2", archive["field_id"]),
                bytes.fromhex(str(archive["field_hash"])),
            ]
        ),
    }
    envelope = store.put(
        tensors,
        schema=COMPILED_FIELD_SCHEMA,
        kind="COMPILED_FIELD",
        source_hash=str(archive.get("source_hash", source_hash(archive["source"]))),
    )
    return CompiledFieldObject(
        str(archive["field_id"]),
        str(archive["kind"]),
        str(archive["field_hash"]),
        envelope,
        archive,
    )


def load_field_object(envelope: TensorEnvelope) -> CompiledFieldObject:
    if envelope.schema != COMPILED_FIELD_SCHEMA:
        raise Runtime52Failure(
            "TENSOR_SCHEMA_MISMATCH", "object is not a compiled field"
        )
    required = {
        "node_kind",
        "node_parent",
        "node_key_label",
        "node_text_label",
        "node_int_index",
        "node_int_value",
        "label_bytes",
        "label_offsets",
        "binding_label_index",
        "capability_label_index",
        "identity_hash",
    }
    if set(envelope.tensors) != required:
        raise Runtime52Failure(
            "TENSOR_SCHEMA_MISMATCH", "compiled field tensor set changed"
        )
    if envelope.tensors["label_offsets"].dtype != np.dtype(np.int32):
        raise Runtime52Failure(
            "TENSOR_SCHEMA_MISMATCH", "compiled field offsets changed"
        )
    labels = decode_string_pool(
        envelope.tensors["label_bytes"],
        envelope.tensors["label_offsets"].astype(np.int64),
    )
    for name, dtype in (
        ("node_kind", np.uint8),
        ("node_parent", np.int16),
        ("node_key_label", np.int16),
        ("node_text_label", np.int16),
        ("node_int_index", np.int16),
        ("node_int_value", np.int32),
        ("binding_label_index", np.int16),
        ("capability_label_index", np.int16),
    ):
        if envelope.tensors[name].dtype != np.dtype(dtype):
            raise Runtime52Failure(
                "TENSOR_SCHEMA_MISMATCH", f"compiled field dtype changed: {name}"
            )
    source = _decode_graph(dict(envelope.tensors), labels)
    if not isinstance(source, dict):
        raise Runtime52Failure(
            "TENSOR_SCHEMA_MISMATCH", "compiled field root is invalid"
        )
    bindings = []
    for raw in envelope.tensors["binding_label_index"]:
        index = int(raw)
        if index < 0 or index >= len(labels):
            raise Runtime52Failure(
                "TENSOR_SCHEMA_MISMATCH", "field binding label is out of range"
            )
        bindings.append(labels[index])
    if len(bindings) != 3:
        raise Runtime52Failure(
            "TENSOR_SCHEMA_MISMATCH", "compiled field bindings are invalid"
        )
    capabilities = []
    for raw in envelope.tensors["capability_label_index"]:
        index = int(raw)
        if index < 0 or index >= len(labels):
            raise Runtime52Failure(
                "TENSOR_SCHEMA_MISMATCH", "field capability is out of range"
            )
        capabilities.append(labels[index])
    try:
        archive = compile_field_archive(
            source, FieldKind(bindings[1]), tuple(capabilities)
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise Runtime52Failure(
            "TENSOR_SCHEMA_MISMATCH", "compiled field IR is invalid"
        ) from exc
    if (
        archive["field_id"] != bindings[0]
        or archive["field_hash"] != bindings[2]
    ):
        raise Runtime52Failure(
            "OBJECT_HASH_MISMATCH", "compiled field binding changed"
        )
    identity = envelope.tensors["identity_hash"]
    if identity.shape != (2, 32) or identity.dtype != np.uint8:
        raise Runtime52Failure(
            "TENSOR_SCHEMA_MISMATCH", "compiled field identity is invalid"
        )
    if identity[0].tobytes() != hash_bytes(
        "moth-field-id/5.2", bindings[0]
    ) or identity[1].tobytes().hex() != bindings[2]:
        raise Runtime52Failure(
            "OBJECT_HASH_MISMATCH", "compiled field identity changed"
        )
    return CompiledFieldObject(
        str(archive["field_id"]),
        str(archive["kind"]),
        str(archive["field_hash"]),
        envelope,
        archive,
    )


def compile_skill_object(
    store: ObjectStore, compilation: dict[str, Any]
) -> CompiledSkillObject:
    policy = compilation.get("policy")
    if not isinstance(policy, dict):
        raise Runtime52Failure(
            "INVALID_FIELD", "compiled skill policy is absent"
        )
    workflow = tuple(str(value) for value in policy.get("workflow", []))
    completion = tuple(str(value) for value in policy.get("completion", []))
    labels: list[str] = []
    label_map: dict[str, int] = {}

    def label(value: str) -> int:
        text = str(value)
        if text not in label_map:
            label_map[text] = len(labels)
            labels.append(text)
        return label_map[text]

    bindings = (
        str(compilation["compilation_id"]),
        str(compilation["field_id"]),
        str(compilation["profile_id"]),
        str(compilation["policy_hash"]),
        str(compilation["source_hash"]),
        str(compilation.get("skill_name", "")),
    )
    binding_indices = [label(value) for value in bindings]
    workflow_indices = [label(value) for value in workflow]
    completion_indices = [label(value) for value in completion]
    edges = np.asarray(
        [
            [workflow_indices[index], workflow_indices[index + 1]]
            for index in range(max(0, len(workflow_indices) - 1))
        ],
        dtype=np.int32,
    ).reshape(-1, 2)
    label_bytes, label_offsets = string_pool(labels)
    if len(label_bytes) >= 2**31 or len(labels) >= 2**15:
        raise Runtime52Failure(
            "RESOURCE_LIMIT", "compiled skill exceeds fixed tensor bounds"
        )
    label_offsets = label_offsets.astype(np.int32)
    tensors = {
        "binding_label_index": np.asarray(binding_indices, dtype=np.int16),
        "workflow_label_index": np.asarray(workflow_indices, dtype=np.int16),
        "workflow_edge": edges,
        "completion_label_index": np.asarray(
            completion_indices, dtype=np.int16
        ),
        "policy_hash": hash_matrix(
            [bytes.fromhex(str(compilation["policy_hash"]))]
        ),
        "label_bytes": label_bytes,
        "label_offsets": label_offsets,
    }
    envelope = store.put(
        tensors,
        schema=COMPILED_SKILL_SCHEMA,
        kind="COMPILED_SKILL",
        source_hash=str(compilation["source_hash"]),
    )
    return CompiledSkillObject(
        bindings[0],
        bindings[1],
        bindings[2],
        bindings[3],
        bindings[4],
        workflow,
        completion,
        envelope,
    )


def load_skill_object(envelope: TensorEnvelope) -> CompiledSkillObject:
    if envelope.schema != COMPILED_SKILL_SCHEMA or set(envelope.tensors) != {
        "binding_label_index",
        "workflow_label_index",
        "workflow_edge",
        "completion_label_index",
        "policy_hash",
        "label_bytes",
        "label_offsets",
    }:
        raise Runtime52Failure(
            "TENSOR_SCHEMA_MISMATCH", "compiled skill tensor set changed"
        )
    if envelope.tensors["label_offsets"].dtype != np.dtype(np.int32):
        raise Runtime52Failure(
            "TENSOR_SCHEMA_MISMATCH", "compiled skill offsets changed"
        )
    labels = decode_string_pool(
        envelope.tensors["label_bytes"],
        envelope.tensors["label_offsets"].astype(np.int64),
    )

    def values(name: str) -> tuple[str, ...]:
        result = []
        for raw in envelope.tensors[name]:
            index = int(raw)
            if index < 0 or index >= len(labels):
                raise Runtime52Failure(
                    "TENSOR_SCHEMA_MISMATCH", "skill label is out of range"
                )
            result.append(labels[index])
        return tuple(result)

    bindings = values("binding_label_index")
    if len(bindings) != 6:
        raise Runtime52Failure(
            "TENSOR_SCHEMA_MISMATCH", "skill bindings are invalid"
        )
    policy_hash = envelope.tensors["policy_hash"]
    if policy_hash.shape != (1, 32) or policy_hash[0].tobytes().hex() != bindings[3]:
        raise Runtime52Failure(
            "OBJECT_HASH_MISMATCH", "compiled skill policy hash changed"
        )
    workflow = values("workflow_label_index")
    expected_edges = np.asarray(
        [
            [
                int(envelope.tensors["workflow_label_index"][index]),
                int(envelope.tensors["workflow_label_index"][index + 1]),
            ]
            for index in range(max(0, len(workflow) - 1))
        ],
        dtype=np.int32,
    ).reshape(-1, 2)
    if not np.array_equal(envelope.tensors["workflow_edge"], expected_edges):
        raise Runtime52Failure(
            "TENSOR_SCHEMA_MISMATCH", "compiled workflow edges changed"
        )
    return CompiledSkillObject(
        bindings[0],
        bindings[1],
        bindings[2],
        bindings[3],
        bindings[4],
        workflow,
        values("completion_label_index"),
        envelope,
    )


def plan_inert_skill(
    skill: CompiledSkillObject,
    task: dict[str, Any],
    *,
    artifact_hash: str,
) -> dict[str, Any]:
    target = task.get("target")
    files = task.get("files", {})
    status, code = "ACTION_PLAN", None
    patch = None
    if not isinstance(files, dict) or not isinstance(target, str) or not target:
        status, code = "REFUSAL", "TARGET_NOT_UNIQUE"
    else:
        path = PurePosixPath(target)
        if path.is_absolute() or ".." in path.parts:
            status, code = "REFUSAL", "SCOPE_VIOLATION"
        elif target in task.get("binary_files", []):
            status, code = "REFUSAL", "UNSUPPORTED_TARGET"
        elif target not in files:
            status, code = "REFUSAL", "TARGET_NOT_UNIQUE"
        elif path.suffix.casefold() not in {
            ".txt", ".md", ".json", ".toml", ".yaml", ".yml"
        }:
            status, code = "REFUSAL", "UNSUPPORTED_TARGET"
        elif task.get("extra_change"):
            status, code = "REFUSAL", "SCOPE_VIOLATION"
        elif task.get("protected") and not task.get("authorized"):
            status, code = "AUTHORITY_REQUIRED", "PROTECTED_TARGET"
        else:
            current, old, new = (
                files[target],
                task.get("old"),
                task.get("new"),
            )
            if not all(
                isinstance(value, str) for value in (current, old, new)
            ) or not old or old == new or current.count(old) != 1:
                status, code = "REFUSAL", "PRECONDITION_FAILED"
            else:
                proposed = current.replace(old, new, 1)
                patch = {
                    "path": target,
                    "old": old,
                    "new": new,
                    "before_sha256": sha256_bytes(current.encode("utf-8")),
                    "after_sha256": sha256_bytes(proposed.encode("utf-8")),
                    "proposed_text": proposed,
                }
    body = {
        "schema": "moth-inert-skill-plan/5.2",
        "status": status,
        "code": code,
        "task_hash": digest("moth-inert-skill-task/5.2", task),
        "compilation_id": skill.compilation_id,
        "policy_hash": skill.policy_hash,
        "model_artifact_hash": artifact_hash,
        "workflow": list(skill.workflow),
        "patch": patch,
        "verification_steps": list(skill.completion) if patch else [],
        "execution": {"performed": False, "dispatch_count": 0, "writes": 0},
    }
    return {
        **body,
        "plan_hash": digest("moth-inert-skill-plan/5.2", body),
    }
