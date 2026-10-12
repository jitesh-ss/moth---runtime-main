"""SQLite WAL catalog for Runtime 5.3 conversations and layer revisions."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import time
import uuid
from typing import Any, Iterable

from moth_runtime_v5_3.legacy.canonical import canonical_bytes, digest, normalize_text

from ..energy.schema import Level, Runtime53Failure
from .objects import ObjectStore, TensorEnvelope


STORE_SCHEMA = "proof-energy-conversation-store/5.3"


class ConcurrentTurnError(RuntimeError):
    pass


def _tokens(value: str) -> int:
    return len(normalize_text(value).split())


class ConversationStore:
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self.catalog = self.root / "catalog.sqlite3"
        self.objects = ObjectStore(self.root)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.catalog, timeout=30)
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=FULL")
        return connection

    def initialize(
        self,
        *,
        artifact_id: str,
        artifact_hash: str,
        foundation: TensorEnvelope,
        kernel_foundation_hash: str,
    ) -> None:
        if self.root.exists() and self.root.is_file():
            raise Runtime53Failure(
                "STORE_VERSION_MISMATCH",
                "Runtime 5.3 store must be a directory",
            )
        self.root.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS knowledge_heads (
                    conversation_id TEXT PRIMARY KEY REFERENCES conversations(conversation_id),
                    revision_id TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS knowledge_revisions (
                    revision_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL REFERENCES conversations(conversation_id),
                    parent_id TEXT,
                    object_hash TEXT NOT NULL REFERENCES objects(file_hash),
                    turn_id TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS store_descriptor (
                    singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                    schema_id TEXT NOT NULL,
                    runtime_label TEXT NOT NULL,
                    artifact_id TEXT NOT NULL,
                    artifact_hash TEXT NOT NULL,
                    energy_foundation_logical_hash TEXT NOT NULL,
                    energy_foundation_file_hash TEXT NOT NULL,
                    kernel_foundation_hash TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS objects (
                    file_hash TEXT PRIMARY KEY,
                    logical_hash TEXT NOT NULL,
                    object_kind TEXT NOT NULL,
                    schema_id TEXT NOT NULL,
                    byte_length INTEGER NOT NULL CHECK(byte_length >= 0),
                    tensor_count INTEGER NOT NULL CHECK(tensor_count >= 0),
                    foundation_binding TEXT NOT NULL,
                    source_hash TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    head_sequence INTEGER NOT NULL CHECK(head_sequence >= 0),
                    system_revision_id TEXT NOT NULL,
                    context_revision_id TEXT NOT NULL,
                    created_ns INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS layer_revisions (
                    revision_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    level TEXT NOT NULL CHECK(level IN ('SYSTEM','CONTEXT')),
                    revision_number INTEGER NOT NULL CHECK(revision_number >= 0),
                    parent_revision_id TEXT,
                    layer_hash TEXT NOT NULL,
                    mutation_hash TEXT NOT NULL,
                    created_ns INTEGER NOT NULL,
                    UNIQUE(conversation_id,level,revision_number),
                    FOREIGN KEY(conversation_id) REFERENCES conversations(conversation_id)
                );
                CREATE TABLE IF NOT EXISTS layer_members (
                    revision_id TEXT NOT NULL,
                    attachment_key TEXT NOT NULL,
                    ordinal INTEGER NOT NULL CHECK(ordinal >= 0),
                    object_hash TEXT NOT NULL,
                    PRIMARY KEY(revision_id,attachment_key),
                    UNIQUE(revision_id,ordinal),
                    FOREIGN KEY(revision_id) REFERENCES layer_revisions(revision_id),
                    FOREIGN KEY(object_hash) REFERENCES objects(file_hash)
                );
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    turn_sequence INTEGER NOT NULL CHECK(turn_sequence >= 0),
                    ordinal INTEGER NOT NULL CHECK(ordinal >= 0),
                    role TEXT NOT NULL CHECK(role IN ('SYSTEM','USER','ASSISTANT')),
                    content TEXT NOT NULL,
                    token_count INTEGER NOT NULL CHECK(token_count >= 0),
                    hcf_object_hash TEXT NOT NULL,
                    message_hash TEXT NOT NULL,
                    UNIQUE(conversation_id,turn_sequence,ordinal),
                    FOREIGN KEY(conversation_id) REFERENCES conversations(conversation_id),
                    FOREIGN KEY(hcf_object_hash) REFERENCES objects(file_hash)
                );
                CREATE TABLE IF NOT EXISTS turns (
                    turn_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL CHECK(sequence >= 1),
                    user_message_id TEXT NOT NULL,
                    assistant_message_id TEXT NOT NULL,
                    system_revision_id TEXT NOT NULL,
                    context_revision_id TEXT NOT NULL,
                    result_hash TEXT NOT NULL,
                    result_bytes BLOB NOT NULL,
                    context_bytes BLOB NOT NULL,
                    hcf_bytes BLOB NOT NULL,
                    kernel_result_bytes BLOB,
                    UNIQUE(conversation_id,sequence),
                    FOREIGN KEY(conversation_id) REFERENCES conversations(conversation_id),
                    FOREIGN KEY(user_message_id) REFERENCES messages(message_id),
                    FOREIGN KEY(assistant_message_id) REFERENCES messages(message_id),
                    FOREIGN KEY(system_revision_id) REFERENCES layer_revisions(revision_id),
                    FOREIGN KEY(context_revision_id) REFERENCES layer_revisions(revision_id)
                );
                CREATE TABLE IF NOT EXISTS operational_metrics (
                    turn_id TEXT PRIMARY KEY,
                    metrics_bytes BLOB NOT NULL,
                    FOREIGN KEY(turn_id) REFERENCES turns(turn_id)
                );
                CREATE TABLE IF NOT EXISTS skill_compilations (
                    compilation_id TEXT PRIMARY KEY,
                    field_id TEXT NOT NULL,
                    field_hash TEXT NOT NULL,
                    policy_hash TEXT NOT NULL,
                    object_hash TEXT NOT NULL,
                    FOREIGN KEY(object_hash) REFERENCES objects(file_hash)
                );
                CREATE TABLE IF NOT EXISTS conversation_skills (
                    conversation_id TEXT NOT NULL,
                    ordinal INTEGER NOT NULL,
                    compilation_id TEXT NOT NULL,
                    policy_hash TEXT NOT NULL,
                    PRIMARY KEY(conversation_id,ordinal),
                    UNIQUE(conversation_id,compilation_id),
                    FOREIGN KEY(conversation_id) REFERENCES conversations(conversation_id),
                    FOREIGN KEY(compilation_id) REFERENCES skill_compilations(compilation_id)
                );
                CREATE TABLE IF NOT EXISTS skill_plans (
                    plan_hash TEXT PRIMARY KEY,
                    compilation_id TEXT NOT NULL,
                    plan_bytes BLOB NOT NULL,
                    FOREIGN KEY(compilation_id) REFERENCES skill_compilations(compilation_id)
                );
                """
            )
            expected = (
                STORE_SCHEMA,
                "5.3",
                artifact_id,
                artifact_hash,
                foundation.logical_hash,
                foundation.file_hash,
                kernel_foundation_hash,
            )
            row = connection.execute(
                "SELECT schema_id,runtime_label,artifact_id,artifact_hash,"
                "energy_foundation_logical_hash,energy_foundation_file_hash,"
                "kernel_foundation_hash FROM store_descriptor WHERE singleton=1"
            ).fetchone()
            if row is None:
                connection.execute(
                    "INSERT INTO store_descriptor VALUES (1,?,?,?,?,?,?,?)",
                    expected,
                )
            elif row != expected:
                raise Runtime53Failure(
                    "STORE_VERSION_MISMATCH",
                    "store belongs to another runtime or artifact",
                )
        self.register_object(foundation)

    def descriptor(self) -> dict[str, str]:
        if not self.catalog.is_file():
            raise Runtime53Failure(
                "STORE_VERSION_MISMATCH", "Runtime 5.3 store is not initialized"
            )
        with self._connect() as connection:
            row = connection.execute(
                "SELECT schema_id,runtime_label,artifact_id,artifact_hash,"
                "energy_foundation_logical_hash,energy_foundation_file_hash,"
                "kernel_foundation_hash FROM store_descriptor WHERE singleton=1"
            ).fetchone()
        if row is None or row[0] != STORE_SCHEMA or row[1] != "5.3":
            raise Runtime53Failure(
                "STORE_VERSION_MISMATCH", "cross-runtime store refused"
            )
        return dict(
            zip(
                (
                    "schema",
                    "runtime",
                    "artifact_id",
                    "artifact_hash",
                    "energy_foundation_logical_hash",
                    "energy_foundation_file_hash",
                    "kernel_foundation_hash",
                ),
                row,
            )
        )

    def register_object(self, envelope: TensorEnvelope) -> None:
        row = (
            envelope.file_hash,
            envelope.logical_hash,
            envelope.kind,
            envelope.schema,
            envelope.path.stat().st_size,
            len(envelope.tensors),
            envelope.metadata.get("foundation_hash", ""),
            envelope.metadata.get("source_hash", ""),
        )
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT logical_hash,object_kind,schema_id,byte_length,"
                "tensor_count,foundation_binding,source_hash FROM objects "
                "WHERE file_hash=?",
                (envelope.file_hash,),
            ).fetchone()
            if existing is None:
                connection.execute(
                    "INSERT INTO objects VALUES (?,?,?,?,?,?,?,?)", row
                )
            elif existing != row[1:]:
                raise Runtime53Failure(
                    "OBJECT_HASH_MISMATCH", "catalog object binding changed"
                )

    def register_skill_compilation(
        self,
        *,
        compilation_id: str,
        field_id: str,
        field_hash: str,
        policy_hash: str,
        object_hash: str,
    ) -> None:
        row = (
            compilation_id,
            field_id,
            field_hash,
            policy_hash,
            object_hash,
        )
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT field_id,field_hash,policy_hash,object_hash "
                "FROM skill_compilations WHERE compilation_id=?",
                (compilation_id,),
            ).fetchone()
            if existing is None:
                connection.execute(
                    "INSERT INTO skill_compilations VALUES (?,?,?,?,?)", row
                )
            elif existing != row[1:]:
                raise Runtime53Failure(
                    "OBJECT_HASH_MISMATCH",
                    "compiled skill catalog binding changed",
                )

    def skill_compilation(self, compilation_id: str) -> dict[str, str]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT compilation_id,field_id,field_hash,policy_hash,"
                "object_hash FROM skill_compilations WHERE compilation_id=?",
                (compilation_id,),
            ).fetchone()
        if row is None:
            raise KeyError(compilation_id)
        return dict(
            zip(
                (
                    "compilation_id",
                    "field_id",
                    "field_hash",
                    "policy_hash",
                    "object_hash",
                ),
                row,
            )
        )

    def list_skill_compilations(self) -> list[dict[str, str]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT compilation_id,field_id,field_hash,policy_hash,"
                "object_hash FROM skill_compilations ORDER BY compilation_id"
            ).fetchall()
        keys = (
            "compilation_id",
            "field_id",
            "field_hash",
            "policy_hash",
            "object_hash",
        )
        return [dict(zip(keys, row)) for row in rows]

    def store_skill_plan(self, plan: dict[str, Any]) -> None:
        plan_hash = plan.get("plan_hash")
        compilation_id = plan.get("compilation_id")
        if not isinstance(plan_hash, str) or not isinstance(
            compilation_id, str
        ):
            raise Runtime53Failure(
                "INTEGRITY_FAILURE", "skill plan identity is invalid"
            )
        raw = canonical_bytes(plan)
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT plan_bytes FROM skill_plans WHERE plan_hash=?",
                (plan_hash,),
            ).fetchone()
            if existing is None:
                connection.execute(
                    "INSERT INTO skill_plans VALUES (?,?,?)",
                    (plan_hash, compilation_id, raw),
                )
            elif bytes(existing[0]) != raw:
                raise Runtime53Failure(
                    "INTEGRITY_FAILURE", "skill plan identity collision"
                )

    def skill_plan(self, plan_hash: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT plan_bytes FROM skill_plans WHERE plan_hash=?",
                (plan_hash,),
            ).fetchone()
        if row is None:
            raise KeyError(plan_hash)
        return json.loads(bytes(row[0]))

    @staticmethod
    def message_identity(
        role: str, content: str, conversation_id: str, sequence: int
    ) -> str:
        return digest(
            "moth-message-id/5.3",
            {
                "role": role,
                "content": normalize_text(content),
                "conversation_id": conversation_id,
                "turn_sequence": sequence,
            },
        )

    @staticmethod
    def turn_identity(
        conversation_id: str, sequence: int, user_message_id: str
    ) -> str:
        return digest(
            "moth-turn-id/5.3",
            {
                "conversation_id": conversation_id,
                "sequence": sequence,
                "user_message_id": user_message_id,
            },
        )

    @staticmethod
    def _layer_payload(
        conversation_id: str,
        level: str,
        revision_number: int,
        parent_revision_id: str | None,
        members: Iterable[tuple[str, str]],
    ) -> dict[str, Any]:
        return {
            "conversation_id": conversation_id,
            "level": level,
            "revision_number": revision_number,
            "parent_revision_id": parent_revision_id,
            "members": [
                {"key": key, "object_hash": object_hash}
                for key, object_hash in sorted(members)
            ],
        }

    def _insert_revision(
        self,
        connection: sqlite3.Connection,
        conversation_id: str,
        level: str,
        revision_number: int,
        parent_revision_id: str | None,
        members: tuple[tuple[str, str], ...],
        mutation: dict[str, Any],
    ) -> tuple[str, str]:
        payload = self._layer_payload(
            conversation_id,
            level,
            revision_number,
            parent_revision_id,
            members,
        )
        layer_hash = digest("moth-layer-snapshot/5.3", payload)
        revision_id = digest(
            "moth-layer-revision-id/5.3",
            {**payload, "layer_hash": layer_hash},
        )
        mutation_hash = digest("moth-layer-mutation/5.3", mutation)
        connection.execute(
            "INSERT INTO layer_revisions VALUES (?,?,?,?,?,?,?,?)",
            (
                revision_id,
                conversation_id,
                level,
                revision_number,
                parent_revision_id,
                layer_hash,
                mutation_hash,
                time.time_ns(),
            ),
        )
        for ordinal, (key, object_hash) in enumerate(sorted(members)):
            connection.execute(
                "INSERT INTO layer_members VALUES (?,?,?,?)",
                (revision_id, key, ordinal, object_hash),
            )
        return revision_id, layer_hash

    def create_conversation(
        self,
        system_prompt: str,
        system_object: TensorEnvelope,
        *,
        skill_ids: tuple[str, ...] = (),
    ) -> str:
        self.register_object(system_object)
        descriptor = self.descriptor()
        conversation_id = digest(
            "moth-conversation-id/5.3",
            {
                "foundation_hash": descriptor[
                    "energy_foundation_logical_hash"
                ],
                "system_source_hash": system_object.metadata.get(
                    "source_hash", ""
                ),
                "nonce": uuid.uuid4().hex,
            },
        )
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "INSERT INTO conversations VALUES (?,?,?, ?,?)",
                (conversation_id, 0, "pending-system", "pending-context", time.time_ns()),
            )
            empty_system, _ = self._insert_revision(
                connection,
                conversation_id,
                "SYSTEM",
                0,
                None,
                (),
                {"operation": "CREATE", "level": "SYSTEM"},
            )
            empty_context, _ = self._insert_revision(
                connection,
                conversation_id,
                "CONTEXT",
                0,
                None,
                (),
                {"operation": "CREATE", "level": "CONTEXT"},
            )
            system_revision = empty_system
            if normalize_text(system_prompt):
                system_revision, _ = self._insert_revision(
                    connection,
                    conversation_id,
                    "SYSTEM",
                    1,
                    empty_system,
                    (("initial-system", system_object.file_hash),),
                    {
                        "operation": "UPSERT",
                        "key": "initial-system",
                        "object_hash": system_object.file_hash,
                    },
                )
            connection.execute(
                "UPDATE conversations SET system_revision_id=?,"
                "context_revision_id=? WHERE conversation_id=?",
                (system_revision, empty_context, conversation_id),
            )
            message_id = self.message_identity(
                "SYSTEM", system_prompt, conversation_id, 0
            )
            message_payload = {
                "message_id": message_id,
                "conversation_id": conversation_id,
                "turn_sequence": 0,
                "ordinal": 0,
                "role": "SYSTEM",
                "content": normalize_text(system_prompt),
                "token_count": _tokens(system_prompt),
                "hcf_object_hash": system_object.file_hash,
            }
            connection.execute(
                "INSERT INTO messages VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    message_id,
                    conversation_id,
                    0,
                    0,
                    "SYSTEM",
                    normalize_text(system_prompt),
                    _tokens(system_prompt),
                    system_object.file_hash,
                    digest("moth-message/5.3", message_payload),
                ),
            )
            for ordinal, compilation_id in enumerate(skill_ids):
                row = connection.execute(
                    "SELECT policy_hash FROM skill_compilations "
                    "WHERE compilation_id=?",
                    (compilation_id,),
                ).fetchone()
                if row is None:
                    raise KeyError(compilation_id)
                connection.execute(
                    "INSERT INTO conversation_skills VALUES (?,?,?,?)",
                    (conversation_id, ordinal, compilation_id, row[0]),
                )
            connection.commit()
        return conversation_id

    def conversation(self, conversation_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT head_sequence,system_revision_id,context_revision_id,"
                "created_ns FROM conversations WHERE conversation_id=?",
                (conversation_id,),
            ).fetchone()
        if row is None:
            raise KeyError(conversation_id)
        return {
            "conversation_id": conversation_id,
            "head_sequence": row[0],
            "system_revision_id": row[1],
            "context_revision_id": row[2],
            "created_ns": row[3],
        }

    def list_conversations(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT conversation_id,head_sequence,system_revision_id,"
                "context_revision_id,created_ns FROM conversations "
                "ORDER BY created_ns,conversation_id"
            ).fetchall()
        return [
            dict(
                zip(
                    (
                        "conversation_id",
                        "head_sequence",
                        "system_revision_id",
                        "context_revision_id",
                        "created_ns",
                    ),
                    row,
                )
            )
            for row in rows
        ]

    def conversation_skills(
        self, conversation_id: str
    ) -> list[dict[str, str]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT s.compilation_id,s.field_id,s.field_hash,"
                "s.policy_hash,s.object_hash FROM conversation_skills c "
                "JOIN skill_compilations s "
                "ON s.compilation_id=c.compilation_id "
                "WHERE c.conversation_id=? ORDER BY c.ordinal",
                (conversation_id,),
            ).fetchall()
        keys = (
            "compilation_id",
            "field_id",
            "field_hash",
            "policy_hash",
            "object_hash",
        )
        return [dict(zip(keys, row)) for row in rows]

    def layer_snapshot(
        self, conversation_id: str, level: Level | str, revision_id: str | None = None
    ) -> dict[str, Any]:
        name = level.name if isinstance(level, Level) else str(level).upper()
        if name not in {"SYSTEM", "CONTEXT"}:
            raise Runtime53Failure("INVALID_HCF_FIELD", "layer is not mutable")
        with self._connect() as connection:
            if revision_id is None:
                column = (
                    "system_revision_id"
                    if name == "SYSTEM"
                    else "context_revision_id"
                )
                row = connection.execute(
                    f"SELECT {column} FROM conversations WHERE conversation_id=?",
                    (conversation_id,),
                ).fetchone()
                if row is None:
                    raise KeyError(conversation_id)
                revision_id = row[0]
            revision = connection.execute(
                "SELECT revision_number,parent_revision_id,layer_hash,"
                "mutation_hash,created_ns FROM layer_revisions "
                "WHERE revision_id=? AND conversation_id=? AND level=?",
                (revision_id, conversation_id, name),
            ).fetchone()
            if revision is None:
                raise Runtime53Failure(
                    "INTEGRITY_FAILURE", "layer revision is missing"
                )
            members = connection.execute(
                "SELECT attachment_key,object_hash FROM layer_members "
                "WHERE revision_id=? ORDER BY ordinal",
                (revision_id,),
            ).fetchall()
        payload = self._layer_payload(
            conversation_id,
            name,
            revision[0],
            revision[1],
            tuple(members),
        )
        if digest("moth-layer-snapshot/5.3", payload) != revision[2]:
            raise Runtime53Failure(
                "INTEGRITY_FAILURE", "layer snapshot hash changed"
            )
        return {
            **payload,
            "revision_id": revision_id,
            "layer_hash": revision[2],
            "mutation_hash": revision[3],
            "created_ns": revision[4],
        }

    def layer_history(
        self, conversation_id: str, level: Level | str
    ) -> list[dict[str, Any]]:
        name = level.name if isinstance(level, Level) else str(level).upper()
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT revision_id FROM layer_revisions "
                "WHERE conversation_id=? AND level=? ORDER BY revision_number",
                (conversation_id, name),
            ).fetchall()
        return [
            self.layer_snapshot(conversation_id, name, row[0]) for row in rows
        ]

    def commit_layer(
        self,
        conversation_id: str,
        level: Level,
        expected_revision: int,
        members: Iterable[tuple[str, str]],
        mutation: dict[str, Any],
    ) -> dict[str, Any]:
        name = level.name
        ordered = tuple(sorted(members))
        if len({key for key, _ in ordered}) != len(ordered):
            raise Runtime53Failure(
                "INVALID_HCF_FIELD", "attachment keys are duplicated"
            )
        column = (
            "system_revision_id"
            if level is Level.SYSTEM
            else "context_revision_id"
        )
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                f"SELECT {column} FROM conversations WHERE conversation_id=?",
                (conversation_id,),
            ).fetchone()
            if row is None:
                raise KeyError(conversation_id)
            current = connection.execute(
                "SELECT revision_number FROM layer_revisions WHERE revision_id=?",
                (row[0],),
            ).fetchone()
            if current is None:
                raise Runtime53Failure(
                    "INTEGRITY_FAILURE", "current layer revision is missing"
                )
            if current[0] != expected_revision:
                raise Runtime53Failure(
                    "STALE_LAYER_REVISION",
                    "layer head changed",
                    {"expected": expected_revision, "actual": current[0]},
                )
            previous = tuple(
                connection.execute(
                    "SELECT attachment_key,object_hash FROM layer_members "
                    "WHERE revision_id=? ORDER BY attachment_key",
                    (row[0],),
                ).fetchall()
            )
            if previous == ordered:
                raise Runtime53Failure(
                    "NO_LAYER_CHANGE", "mutation does not change the layer"
                )
            revision_id, _ = self._insert_revision(
                connection,
                conversation_id,
                name,
                expected_revision + 1,
                row[0],
                ordered,
                mutation,
            )
            changed = connection.execute(
                f"UPDATE conversations SET {column}=? "
                f"WHERE conversation_id=? AND {column}=?",
                (revision_id, conversation_id, row[0]),
            ).rowcount
            if changed != 1:
                raise Runtime53Failure(
                    "STALE_LAYER_REVISION", "layer compare-and-swap failed"
                )
            connection.commit()
        return self.layer_snapshot(conversation_id, level, revision_id)

    def messages(self, conversation_id: str) -> list[dict[str, Any]]:
        self.conversation(conversation_id)
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT message_id,turn_sequence,ordinal,role,content,"
                "token_count,hcf_object_hash,message_hash FROM messages "
                "WHERE conversation_id=? ORDER BY turn_sequence,ordinal",
                (conversation_id,),
            ).fetchall()
        return [
            {
                "message_id": row[0],
                "conversation_id": conversation_id,
                "turn_sequence": row[1],
                "ordinal": row[2],
                "role": row[3],
                "content": row[4],
                "token_count": row[5],
                "hcf_object_hash": row[6],
                "message_hash": row[7],
            }
            for row in rows
        ]

    def append_turn(
        self,
        *,
        conversation_id: str,
        expected_head: int,
        expected_system_revision: str,
        expected_context_revision: str,
        user_message: dict[str, Any],
        assistant_message: dict[str, Any],
        result: dict[str, Any],
        context_receipt: dict[str, Any],
        hcf_trace: dict[str, Any],
        kernel_result: dict[str, Any] | None,
        metrics: dict[str, Any],
    ) -> None:
        def message_row(message: dict[str, Any]) -> tuple[Any, ...]:
            payload = {
                key: message[key]
                for key in (
                    "message_id",
                    "conversation_id",
                    "turn_sequence",
                    "ordinal",
                    "role",
                    "content",
                    "token_count",
                    "hcf_object_hash",
                )
            }
            return (
                message["message_id"],
                message["conversation_id"],
                message["turn_sequence"],
                message["ordinal"],
                message["role"],
                message["content"],
                message["token_count"],
                message["hcf_object_hash"],
                digest("moth-message/5.3", payload),
            )

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            current = connection.execute(
                "SELECT head_sequence,system_revision_id,context_revision_id "
                "FROM conversations WHERE conversation_id=?",
                (conversation_id,),
            ).fetchone()
            if current is None:
                raise KeyError(conversation_id)
            if current[0] != expected_head:
                raise ConcurrentTurnError(
                    f"conversation head changed from {expected_head} to {current[0]}"
                )
            if current[1:] != (
                expected_system_revision,
                expected_context_revision,
            ):
                raise Runtime53Failure(
                    "CONCURRENT_LAYER_REVISION",
                    "SYSTEM or CONTEXT changed during the turn",
                )
            connection.execute(
                "INSERT INTO messages VALUES (?,?,?,?,?,?,?,?,?)",
                message_row(user_message),
            )
            connection.execute(
                "INSERT INTO messages VALUES (?,?,?,?,?,?,?,?,?)",
                message_row(assistant_message),
            )
            connection.execute(
                "INSERT INTO turns VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    result["turn_id"],
                    conversation_id,
                    expected_head + 1,
                    user_message["message_id"],
                    assistant_message["message_id"],
                    expected_system_revision,
                    expected_context_revision,
                    result["replay"]["result_hash"],
                    canonical_bytes(result),
                    canonical_bytes(context_receipt),
                    canonical_bytes(hcf_trace),
                    canonical_bytes(kernel_result)
                    if kernel_result is not None
                    else None,
                ),
            )
            connection.execute(
                "INSERT INTO operational_metrics VALUES (?,?)",
                (result["turn_id"], canonical_bytes(metrics)),
            )
            changed = connection.execute(
                "UPDATE conversations SET head_sequence=? "
                "WHERE conversation_id=? AND head_sequence=?",
                (expected_head + 1, conversation_id, expected_head),
            ).rowcount
            if changed != 1:
                raise ConcurrentTurnError("conversation compare-and-swap failed")
            extension = result.get('conversation53')
            if extension is not None:
                old = connection.execute('SELECT revision_id FROM knowledge_heads WHERE conversation_id=?', (conversation_id,)).fetchone()
                if (old[0] if old else None) != extension['before_revision']:
                    raise ConcurrentTurnError('knowledge head changed')
                revision = extension['after_revision']
                connection.execute('INSERT INTO knowledge_revisions VALUES (?,?,?,?,?)',
                    (revision,conversation_id,extension['before_revision'],extension['after_object'],result['turn_id']))
                connection.execute('INSERT INTO knowledge_heads VALUES (?,?) ON CONFLICT(conversation_id) DO UPDATE SET revision_id=excluded.revision_id',
                    (conversation_id,revision))
            connection.commit()

    def turn(
        self,
        conversation_id: str,
        *,
        turn_id: str | None = None,
        sequence: int | None = None,
    ) -> dict[str, Any]:
        if (turn_id is None) == (sequence is None):
            raise ValueError("select exactly one turn identity")
        with self._connect() as connection:
            if turn_id is not None:
                row = connection.execute(
                    "SELECT turn_id,result_bytes,context_bytes,hcf_bytes,"
                    "kernel_result_bytes,system_revision_id,context_revision_id "
                    "FROM turns WHERE conversation_id=? AND turn_id=?",
                    (conversation_id, turn_id),
                ).fetchone()
            else:
                row = connection.execute(
                    "SELECT turn_id,result_bytes,context_bytes,hcf_bytes,"
                    "kernel_result_bytes,system_revision_id,context_revision_id "
                    "FROM turns WHERE conversation_id=? AND sequence=?",
                    (conversation_id, sequence),
                ).fetchone()
        if row is None:
            raise KeyError(turn_id if turn_id is not None else sequence)
        return {
            "turn_id": row[0],
            "result": json.loads(bytes(row[1])),
            "context": json.loads(bytes(row[2])),
            "hcf": json.loads(bytes(row[3])),
            "kernel_result": json.loads(bytes(row[4]))
            if row[4] is not None
            else None,
            "system_revision_id": row[5],
            "context_revision_id": row[6],
        }

    def replay(self, conversation_id: str, turn_id: str) -> bytes:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT result_bytes FROM turns "
                "WHERE conversation_id=? AND turn_id=?",
                (conversation_id, turn_id),
            ).fetchone()
        if row is None:
            raise KeyError(turn_id)
        return bytes(row[0])

    def previous_result_hash(
        self, conversation_id: str, head_sequence: int
    ) -> str | None:
        if head_sequence == 0:
            return None
        return self.turn(
            conversation_id, sequence=head_sequence
        )["result"]["replay"]["result_hash"]

    def metrics(self, turn_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT metrics_bytes FROM operational_metrics WHERE turn_id=?",
                (turn_id,),
            ).fetchone()
        if row is None:
            raise KeyError(turn_id)
        return json.loads(bytes(row[0]))

    def status(self) -> dict[str, Any]:
        descriptor = self.descriptor()
        with self._connect() as connection:
            counts = connection.execute(
                "SELECT "
                "(SELECT count(*) FROM objects),"
                "(SELECT count(*) FROM conversations),"
                "(SELECT count(*) FROM turns),"
                "(SELECT count(*) FROM layer_revisions),"
                "(SELECT count(*) FROM skill_compilations)"
            ).fetchone()
        return {
            "schema": "moth-runtime-status/5.3",
            "runtime": "5.3",
            "store": str(self.root),
            "artifact_id": descriptor["artifact_id"],
            "artifact_hash": descriptor["artifact_hash"],
            "objects": counts[0],
            "conversations": counts[1],
            "turns": counts[2],
            "layer_revisions": counts[3],
            "skill_compilations": counts[4],
        }

    def verify_storage(self, conversation_id: str | None = None) -> dict[str, Any]:
        descriptor = self.descriptor()
        with self._connect() as connection:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()
            foreign = connection.execute("PRAGMA foreign_key_check").fetchall()
            object_rows = connection.execute(
                "SELECT file_hash,logical_hash FROM objects ORDER BY file_hash"
            ).fetchall()
            conversations = connection.execute(
                "SELECT conversation_id FROM conversations "
                + ("WHERE conversation_id=?" if conversation_id else "")
                + " ORDER BY conversation_id",
                (conversation_id,) if conversation_id else (),
            ).fetchall()
            turn_count = connection.execute(
                "SELECT count(*) FROM turns"
                + (" WHERE conversation_id=?" if conversation_id else ""),
                (conversation_id,) if conversation_id else (),
            ).fetchone()[0]
        if integrity != ("ok",) or foreign:
            raise Runtime53Failure(
                "INTEGRITY_FAILURE", "SQLite integrity check failed"
            )
        for file_hash, logical_hash in object_rows:
            envelope = self.objects.open(file_hash)
            if envelope.logical_hash != logical_hash:
                raise Runtime53Failure(
                    "INTEGRITY_FAILURE", "catalog logical hash changed"
                )
        for (identity,) in conversations:
            conversation = self.conversation(identity)
            for level, key in (
                (Level.SYSTEM, "system_revision_id"),
                (Level.CONTEXT, "context_revision_id"),
            ):
                self.layer_snapshot(identity, level, conversation[key])
        return {
            "schema": "moth-store-verification/5.3",
            "runtime": descriptor["runtime"],
            "artifact_hash": descriptor["artifact_hash"],
            "object_count": len(object_rows),
            "conversation_count": len(conversations),
            "turn_count": int(turn_count),
            "verified": True,
        }
