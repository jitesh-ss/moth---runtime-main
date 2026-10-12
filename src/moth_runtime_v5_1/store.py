"""Append-only conversation store for Runtime 5.1."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import time
import uuid
from typing import Any

from moth_runtime_v5_0.canonical import canonical_bytes, digest, normalize_text
from moth_runtime_v5_0.model import IntegrityError

from .assets import RuntimeFoundation
from .canonical import verify_result_receipt
from .context import message_identity, token_count
from .hcf import HcfEntry, entry_from_dict


STORE_SCHEMA = "proof-energy-conversation-store/5.1"


class ConcurrentTurnError(RuntimeError):
    pass


class ConversationStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=FULL")
        return connection

    def init(self, foundation: RuntimeFoundation) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS descriptor (
                    singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                    schema_id TEXT NOT NULL,
                    runtime_label TEXT NOT NULL,
                    foundation_path TEXT NOT NULL,
                    manifest_hash TEXT NOT NULL,
                    foundation_id TEXT NOT NULL,
                    foundation_hash TEXT NOT NULL,
                    bundle_id TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    system_prompt TEXT NOT NULL,
                    system_hash TEXT NOT NULL,
                    system_entries_json BLOB NOT NULL,
                    head_sequence INTEGER NOT NULL CHECK(head_sequence >= 0),
                    created_ns INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    turn_sequence INTEGER NOT NULL CHECK(turn_sequence >= 0),
                    ordinal INTEGER NOT NULL CHECK(ordinal >= 0),
                    role TEXT NOT NULL CHECK(role IN ('SYSTEM','USER','ASSISTANT')),
                    content TEXT NOT NULL,
                    token_count INTEGER NOT NULL CHECK(token_count >= 0),
                    hcf_entries_json BLOB NOT NULL,
                    message_hash TEXT NOT NULL,
                    UNIQUE(conversation_id, turn_sequence, ordinal),
                    FOREIGN KEY(conversation_id) REFERENCES conversations(conversation_id)
                );
                CREATE TABLE IF NOT EXISTS turns (
                    turn_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL CHECK(sequence >= 1),
                    user_message_id TEXT NOT NULL,
                    assistant_message_id TEXT NOT NULL,
                    result_hash TEXT NOT NULL,
                    result_json BLOB NOT NULL,
                    context_json BLOB NOT NULL,
                    hcf_json BLOB NOT NULL,
                    kernel_result_json BLOB,
                    UNIQUE(conversation_id, sequence),
                    FOREIGN KEY(conversation_id) REFERENCES conversations(conversation_id),
                    FOREIGN KEY(user_message_id) REFERENCES messages(message_id),
                    FOREIGN KEY(assistant_message_id) REFERENCES messages(message_id)
                );
                CREATE TABLE IF NOT EXISTS operational_metrics (
                    turn_id TEXT PRIMARY KEY,
                    metrics_json BLOB NOT NULL,
                    FOREIGN KEY(turn_id) REFERENCES turns(turn_id)
                );
                CREATE TABLE IF NOT EXISTS artifact_descriptor (
                    singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                    artifact_path TEXT NOT NULL,
                    artifact_id TEXT NOT NULL,
                    artifact_hash TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS skill_compilations (
                    compilation_id TEXT PRIMARY KEY,
                    field_id TEXT NOT NULL,
                    field_hash TEXT NOT NULL,
                    policy_hash TEXT NOT NULL,
                    compilation_json BLOB NOT NULL
                );
                CREATE TABLE IF NOT EXISTS skill_plans (
                    plan_hash TEXT PRIMARY KEY,
                    compilation_id TEXT NOT NULL,
                    plan_json BLOB NOT NULL,
                    FOREIGN KEY(compilation_id) REFERENCES skill_compilations(compilation_id)
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
            """)
            row = connection.execute(
                "SELECT schema_id,runtime_label,foundation_path,manifest_hash,foundation_id,foundation_hash,bundle_id "
                "FROM descriptor WHERE singleton=1"
            ).fetchone()
            expected = (
                STORE_SCHEMA, "5.1", str(foundation.root), foundation.manifest_hash,
                foundation.foundation_id, foundation.foundation_hash,
                foundation.bundle.bundle_id,
            )
            if row is None:
                connection.execute(
                    "INSERT INTO descriptor VALUES (1,?,?,?,?,?,?,?)", expected,
                )
            elif row != expected:
                raise IntegrityError("cross-runtime store or Runtime 5.1 foundation mismatch")

    def descriptor(self) -> dict[str, str]:
        if not self.path.exists():
            raise IntegrityError("Runtime 5.1 store is not initialized")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT schema_id,runtime_label,foundation_path,manifest_hash,foundation_id,foundation_hash,bundle_id "
                "FROM descriptor WHERE singleton=1"
            ).fetchone()
        if row is None or row[0] != STORE_SCHEMA or row[1] != "5.1":
            raise IntegrityError("cross-runtime or malformed Runtime 5.1 store")
        return dict(zip(
            (
                "schema", "runtime", "foundation_path", "manifest_hash",
                "foundation_id", "foundation_hash", "bundle_id",
            ),
            row,
        ))

    def bind_artifact(self, artifact_path: str, artifact_id: str, artifact_hash: str) -> None:
        expected = (str(Path(artifact_path).resolve()), artifact_id, artifact_hash)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT artifact_path,artifact_id,artifact_hash FROM artifact_descriptor WHERE singleton=1"
            ).fetchone()
            if row is None:
                counts = connection.execute(
                    "SELECT (SELECT count(*) FROM conversations), (SELECT count(*) FROM turns)"
                ).fetchone()
                if counts != (0, 0):
                    raise IntegrityError("model artifact cannot be attached to a used foundation-only store")
                connection.execute(
                    "INSERT INTO artifact_descriptor VALUES (1,?,?,?)", expected,
                )
            elif row != expected:
                raise IntegrityError("Runtime 5.1 store is bound to a different model artifact")

    def artifact_descriptor(self) -> dict[str, str] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT artifact_path,artifact_id,artifact_hash FROM artifact_descriptor WHERE singleton=1"
            ).fetchone()
        if row is None:
            return None
        return dict(zip(("artifact_path", "artifact_id", "artifact_hash"), row))

    def store_skill_compilation(self, compilation: dict[str, Any]) -> None:
        required = ("compilation_id", "field_id", "field_hash", "policy_hash")
        if any(not isinstance(compilation.get(key), str) for key in required):
            raise IntegrityError("compiled skill cannot be stored without its bindings")
        row = tuple(compilation[key] for key in required) + (canonical_bytes(compilation),)
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT compilation_json FROM skill_compilations WHERE compilation_id=?",
                (compilation["compilation_id"],),
            ).fetchone()
            if existing is None:
                connection.execute(
                    "INSERT INTO skill_compilations VALUES (?,?,?,?,?)", row,
                )
            elif bytes(existing[0]) != canonical_bytes(compilation):
                raise IntegrityError("stored skill compilation identity collision")

    def skill_compilation(self, compilation_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT compilation_json FROM skill_compilations WHERE compilation_id=?",
                (compilation_id,),
            ).fetchone()
        if row is None:
            raise KeyError(compilation_id)
        return json.loads(bytes(row[0]))

    def list_skill_compilations(self) -> list[dict[str, str]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT compilation_id,field_id,field_hash,policy_hash,compilation_json "
                "FROM skill_compilations ORDER BY compilation_id"
            ).fetchall()
        result = []
        for row in rows:
            item = dict(zip(
                ("compilation_id", "field_id", "field_hash", "policy_hash"), row[:4],
            ))
            item["profile_id"] = str(json.loads(bytes(row[4]))["profile_id"])
            result.append(item)
        return result

    def store_skill_plan(self, plan: dict[str, Any]) -> None:
        plan_hash = plan.get("plan_hash")
        compilation_id = plan.get("compilation_id")
        if not isinstance(plan_hash, str) or not isinstance(compilation_id, str):
            raise IntegrityError("inert skill plan identity is invalid")
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT plan_json FROM skill_plans WHERE plan_hash=?", (plan_hash,),
            ).fetchone()
            if existing is None:
                connection.execute(
                    "INSERT INTO skill_plans VALUES (?,?,?)",
                    (plan_hash, compilation_id, canonical_bytes(plan)),
                )
            elif bytes(existing[0]) != canonical_bytes(plan):
                raise IntegrityError("stored inert plan identity collision")

    def skill_plan(self, plan_hash: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT plan_json FROM skill_plans WHERE plan_hash=?", (plan_hash,),
            ).fetchone()
        if row is None:
            raise KeyError(plan_hash)
        return json.loads(bytes(row[0]))

    def create_conversation(
        self, system_prompt: str, system_entries: tuple[HcfEntry, ...],
        skills: tuple[dict[str, Any], ...] = (),
    ) -> str:
        descriptor = self.descriptor()
        system_hash = digest("moth-system-layer/5.1", {
            "prompt": normalize_text(system_prompt),
            "entries": [item.canonical() for item in system_entries],
        })
        conversation_id = digest("moth-conversation-id/5.1", {
            "foundation_hash": descriptor["foundation_hash"],
            "system_hash": system_hash, "nonce": uuid.uuid4().hex,
        })
        raw_entries = canonical_bytes([item.canonical() for item in system_entries])
        system_message_id = message_identity("SYSTEM", system_prompt, conversation_id, 0)
        message_payload = {
            "message_id": system_message_id, "conversation_id": conversation_id,
            "turn_sequence": 0, "ordinal": 0, "role": "SYSTEM",
            "content": normalize_text(system_prompt), "token_count": token_count(system_prompt),
            "hcf_entries": [item.canonical() for item in system_entries],
        }
        message_hash = digest("moth-message/5.1", message_payload)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "INSERT INTO conversations VALUES (?,?,?,?,0,?)",
                (conversation_id, normalize_text(system_prompt), system_hash, raw_entries,
                 time.time_ns()),
            )
            connection.execute(
                "INSERT INTO messages VALUES (?,?,?,?,?,?,?,?,?)",
                (system_message_id, conversation_id, 0, 0, "SYSTEM",
                 normalize_text(system_prompt), token_count(system_prompt), raw_entries,
                 message_hash),
            )
            for ordinal, compilation in enumerate(skills):
                connection.execute(
                    "INSERT INTO conversation_skills VALUES (?,?,?,?)",
                    (
                        conversation_id, ordinal, compilation["compilation_id"],
                        compilation["policy_hash"],
                    ),
                )
            connection.commit()
        return conversation_id

    def conversation(self, conversation_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT system_prompt,system_hash,system_entries_json,head_sequence,created_ns "
                "FROM conversations WHERE conversation_id=?", (conversation_id,),
            ).fetchone()
        if row is None:
            raise KeyError(conversation_id)
        try:
            entries = [entry_from_dict(value) for value in json.loads(bytes(row[2]))]
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise IntegrityError("stored system layer is malformed") from exc
        expected_system_hash = digest("moth-system-layer/5.1", {
            "prompt": normalize_text(row[0]),
            "entries": [item.canonical() for item in entries],
        })
        if row[1] != expected_system_hash:
            raise IntegrityError("stored system layer hash changed")
        with self._connect() as connection:
            skill_rows = connection.execute(
                "SELECT compilation_id,policy_hash FROM conversation_skills "
                "WHERE conversation_id=? ORDER BY ordinal", (conversation_id,),
            ).fetchall()
        return {
            "conversation_id": conversation_id, "system_prompt": row[0],
            "system_hash": row[1], "system_entries": entries,
            "head_sequence": row[3], "created_ns": row[4],
            "skills": [{"compilation_id": item[0], "policy_hash": item[1]} for item in skill_rows],
        }

    def list_conversations(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT conversation_id,system_hash,head_sequence,created_ns "
                "FROM conversations ORDER BY created_ns,conversation_id"
            ).fetchall()
        return [{
            "conversation_id": row[0], "system_hash": row[1],
            "head_sequence": row[2], "created_ns": row[3],
        } for row in rows]

    def messages(self, conversation_id: str) -> list[dict[str, Any]]:
        self.conversation(conversation_id)
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT message_id,turn_sequence,ordinal,role,content,token_count,hcf_entries_json,message_hash "
                "FROM messages WHERE conversation_id=? ORDER BY turn_sequence,ordinal",
                (conversation_id,),
            ).fetchall()
        result = []
        for row in rows:
            try:
                entries = json.loads(bytes(row[6]))
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                raise IntegrityError("stored message HCF entries are malformed") from exc
            result.append({
                "message_id": row[0], "conversation_id": conversation_id,
                "turn_sequence": row[1], "ordinal": row[2], "role": row[3],
                "content": row[4], "token_count": row[5],
                "hcf_entries": entries, "message_hash": row[7],
            })
        return result

    @staticmethod
    def turn_identity(conversation_id: str, sequence: int, user_message_id: str) -> str:
        return digest("moth-turn-id/5.1", {
            "conversation_id": conversation_id, "sequence": sequence,
            "user_message_id": user_message_id,
        })

    def append_turn(
        self, *, conversation_id: str, expected_head: int,
        user_message: dict[str, Any], assistant_content: str,
        assistant_entries: tuple[HcfEntry, ...], result: dict[str, Any],
        context_receipt: dict[str, Any], hcf_trace: dict[str, Any],
        kernel_result: dict[str, Any] | None, metrics: dict[str, Any],
    ) -> None:
        sequence = expected_head + 1
        turn_id = str(result["turn_id"])
        expected_turn_id = self.turn_identity(
            conversation_id, sequence, str(user_message["message_id"]),
        )
        if turn_id != expected_turn_id:
            raise IntegrityError("Runtime 5.1 turn identity mismatch")
        assistant_id = message_identity("ASSISTANT", assistant_content, conversation_id, sequence)
        if result.get("assistant_message_id") != assistant_id:
            raise IntegrityError("Runtime 5.1 assistant message identity mismatch")

        def message_row(message: dict[str, Any]) -> tuple[Any, ...]:
            payload = {
                key: message[key] for key in (
                    "message_id", "conversation_id", "turn_sequence", "ordinal",
                    "role", "content", "token_count", "hcf_entries",
                )
            }
            return (
                message["message_id"], message["conversation_id"],
                message["turn_sequence"], message["ordinal"], message["role"],
                message["content"], message["token_count"],
                canonical_bytes(message["hcf_entries"]),
                digest("moth-message/5.1", payload),
            )

        assistant_message = {
            "message_id": assistant_id, "conversation_id": conversation_id,
            "turn_sequence": sequence, "ordinal": 1, "role": "ASSISTANT",
            "content": normalize_text(assistant_content),
            "token_count": token_count(assistant_content),
            "hcf_entries": [item.canonical() for item in assistant_entries],
        }
        verify_result_receipt(result)
        result_raw = canonical_bytes(result)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            current = connection.execute(
                "SELECT head_sequence FROM conversations WHERE conversation_id=?",
                (conversation_id,),
            ).fetchone()
            if current is None:
                connection.rollback()
                raise KeyError(conversation_id)
            if current[0] != expected_head:
                connection.rollback()
                raise ConcurrentTurnError("conversation head changed during turn execution")
            connection.execute("INSERT INTO messages VALUES (?,?,?,?,?,?,?,?,?)", message_row(user_message))
            connection.execute("INSERT INTO messages VALUES (?,?,?,?,?,?,?,?,?)", message_row(assistant_message))
            connection.execute(
                "INSERT INTO turns VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    turn_id, conversation_id, sequence, user_message["message_id"],
                    assistant_id, result["replay"]["result_hash"], result_raw,
                    canonical_bytes(context_receipt), canonical_bytes(hcf_trace),
                    canonical_bytes(kernel_result) if kernel_result is not None else None,
                ),
            )
            connection.execute(
                "INSERT INTO operational_metrics VALUES (?,?)",
                (turn_id, canonical_bytes(metrics)),
            )
            updated = connection.execute(
                "UPDATE conversations SET head_sequence=? WHERE conversation_id=? AND head_sequence=?",
                (sequence, conversation_id, expected_head),
            )
            if updated.rowcount != 1:
                connection.rollback()
                raise ConcurrentTurnError("conversation head changed during turn commit")
            connection.commit()

    def turn(self, conversation_id: str, turn_id: str | None = None,
             sequence: int | None = None) -> dict[str, Any]:
        if (turn_id is None) == (sequence is None):
            raise ValueError("select a turn by exactly one identifier")
        clause, parameter = (
            ("turn_id=?", turn_id) if turn_id is not None
            else ("conversation_id=? AND sequence=?", (conversation_id, sequence))
        )
        with self._connect() as connection:
            if isinstance(parameter, tuple):
                row = connection.execute(
                    "SELECT turn_id,result_json,context_json,hcf_json,kernel_result_json "
                    f"FROM turns WHERE {clause}", parameter,
                ).fetchone()
            else:
                row = connection.execute(
                    "SELECT turn_id,result_json,context_json,hcf_json,kernel_result_json "
                    f"FROM turns WHERE {clause} AND conversation_id=?",
                    (parameter, conversation_id),
                ).fetchone()
        if row is None:
            raise KeyError(turn_id if turn_id is not None else sequence)
        return {
            "turn_id": row[0], "result": json.loads(bytes(row[1])),
            "context": json.loads(bytes(row[2])), "hcf": json.loads(bytes(row[3])),
            "kernel_result": json.loads(bytes(row[4])) if row[4] is not None else None,
        }

    def metrics(self, turn_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT metrics_json FROM operational_metrics WHERE turn_id=?", (turn_id,),
            ).fetchone()
        if row is None:
            raise KeyError(turn_id)
        return json.loads(bytes(row[0]))

    def replay(self, conversation_id: str, turn_id: str) -> bytes:
        turn = self.turn(conversation_id, turn_id=turn_id)
        raw = canonical_bytes(turn["result"])
        try:
            verify_result_receipt(turn["result"])
        except ValueError as exc:
            raise IntegrityError("Runtime 5.1 archived result hash changed") from exc
        return raw

    def status(self) -> dict[str, Any]:
        descriptor = self.descriptor()
        with self._connect() as connection:
            conversation_count = connection.execute("SELECT count(*) FROM conversations").fetchone()[0]
            turn_count = connection.execute("SELECT count(*) FROM turns").fetchone()[0]
            message_count = connection.execute("SELECT count(*) FROM messages").fetchone()[0]
        return {
            **descriptor, "store": str(self.path.resolve()),
            "conversation_count": conversation_count, "turn_count": turn_count,
            "message_count": message_count,
        }

    def verify_storage(self, conversation_id: str | None = None) -> dict[str, Any]:
        query = "SELECT conversation_id,head_sequence FROM conversations"
        parameters: tuple[Any, ...] = ()
        if conversation_id is not None:
            query += " WHERE conversation_id=?"
            parameters = (conversation_id,)
        verified_turns = 0
        verified_messages = 0
        verified_skills = 0
        verified_plans = 0
        with self._connect() as connection:
            skill_rows = connection.execute(
                "SELECT compilation_id,field_id,field_hash,policy_hash,compilation_json "
                "FROM skill_compilations"
            ).fetchall()
            for compilation_id, field_id, field_hash, policy_hash, raw in skill_rows:
                compilation = json.loads(bytes(raw))
                body = {key: value for key, value in compilation.items() if key != "compilation_id"}
                if (
                    compilation.get("compilation_id") != compilation_id
                    or compilation.get("field_id") != field_id
                    or compilation.get("field_hash") != field_hash
                    or compilation.get("policy_hash") != policy_hash
                    or compilation_id != digest("moth-skill-compilation-id/5.1", body)
                    or policy_hash != digest("moth-compiled-skill-policy/5.1", compilation.get("policy"))
                    or compilation.get("trace_hash") != digest(
                        "moth-skill-compilation-trace/5.1", compilation.get("trace")
                    )
                ):
                    raise IntegrityError("stored skill compilation binding changed")
                verified_skills += 1
            artifact_row = connection.execute(
                "SELECT artifact_hash FROM artifact_descriptor WHERE singleton=1"
            ).fetchone()
            expected_artifact_hash = artifact_row[0] if artifact_row else None
            plan_rows = connection.execute(
                "SELECT sp.plan_hash,sp.compilation_id,sp.plan_json,sc.policy_hash "
                "FROM skill_plans sp JOIN skill_compilations sc "
                "ON sc.compilation_id=sp.compilation_id"
            ).fetchall()
            for plan_hash, compilation_id, raw, policy_hash in plan_rows:
                plan = json.loads(bytes(raw))
                body = {key: value for key, value in plan.items() if key != "plan_hash"}
                if (
                    plan.get("plan_hash") != plan_hash
                    or plan.get("compilation_id") != compilation_id
                    or plan.get("policy_hash") != policy_hash
                    or plan.get("model_artifact_hash") != expected_artifact_hash
                    or plan_hash != digest("moth-inert-skill-plan/5.1", body)
                    or plan.get("execution") != {"performed": False, "dispatch_count": 0, "writes": 0}
                ):
                    raise IntegrityError("stored inert skill plan binding changed")
                verified_plans += 1
            conversations = connection.execute(query, parameters).fetchall()
            if conversation_id is not None and not conversations:
                raise KeyError(conversation_id)
            for identifier, head in conversations:
                skill_bindings = connection.execute(
                    "SELECT cs.compilation_id,cs.policy_hash,sc.policy_hash "
                    "FROM conversation_skills cs JOIN skill_compilations sc "
                    "ON sc.compilation_id=cs.compilation_id WHERE cs.conversation_id=? "
                    "ORDER BY cs.ordinal", (identifier,),
                ).fetchall()
                if any(bound != stored for _, bound, stored in skill_bindings):
                    raise IntegrityError("conversation skill-policy binding changed")
                sequences = [row[0] for row in connection.execute(
                    "SELECT sequence FROM turns WHERE conversation_id=? ORDER BY sequence",
                    (identifier,),
                )]
                if sequences != list(range(1, head + 1)):
                    raise IntegrityError("conversation turn sequence is not contiguous")
                for message in self.messages(identifier):
                    payload = {key: message[key] for key in (
                        "message_id", "conversation_id", "turn_sequence", "ordinal",
                        "role", "content", "token_count", "hcf_entries",
                    )}
                    if message["message_hash"] != digest("moth-message/5.1", payload):
                        raise IntegrityError("stored message hash changed")
                    if message["message_id"] != message_identity(
                        message["role"], message["content"], identifier,
                        message["turn_sequence"],
                    ):
                        raise IntegrityError("stored message identity changed")
                    verified_messages += 1
                for sequence in sequences:
                    record = self.turn(identifier, sequence=sequence)
                    try:
                        verify_result_receipt(record["result"])
                    except ValueError as exc:
                        raise IntegrityError("stored turn result hash changed") from exc
                    verified_turns += 1
        return {
            "schema": STORE_SCHEMA, "runtime": "5.1", "verified": True,
            "conversation_count": len(conversations), "message_count": verified_messages,
            "turn_count": verified_turns, "skill_count": verified_skills,
            "plan_count": verified_plans,
        }
