"""Independent immutable SQLite store for Runtime 4.7 generations."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Any

from .archive import archive_bytes, field_from_archive
from .canonical import canonical_bytes, digest, normalize_text, sha256_bytes
from .compiler import PassageEncoder, compile_sources
from .model import CompiledField, IntegrityError
from .runtime import query, result_bytes, verify_result_receipt

STORE_SCHEMA = "proof-energy-capability-store/4.7"


class ConcurrentHeadError(RuntimeError):
    pass


class CapabilityStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def _connect(self) -> sqlite3.Connection:
        if self.path.is_dir():
            raise IntegrityError("Runtime 4.7 requires its own SQLite store file; directory stores are not migrated")
        connection = sqlite3.connect(self.path)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=FULL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def init(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS descriptor (
                    singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
                    schema_id TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS generations (
                    generation_id TEXT PRIMARY KEY,
                    parent_id TEXT,
                    capability_level TEXT NOT NULL,
                    field_hash TEXT NOT NULL,
                    archive_sha256 TEXT NOT NULL,
                    archive_json BLOB NOT NULL,
                    FOREIGN KEY(parent_id) REFERENCES generations(generation_id)
                );
                CREATE TABLE IF NOT EXISTS head (
                    singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
                    generation_id TEXT,
                    FOREIGN KEY(generation_id) REFERENCES generations(generation_id)
                );
                CREATE TABLE IF NOT EXISTS episodes (
                    episode_id TEXT PRIMARY KEY,
                    generation_id TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    modality TEXT NOT NULL,
                    input_hash TEXT NOT NULL,
                    result_sha256 TEXT NOT NULL,
                    result_json BLOB NOT NULL,
                    FOREIGN KEY(generation_id) REFERENCES generations(generation_id)
                );
                CREATE TABLE IF NOT EXISTS purge_receipts (
                    receipt_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    prior_generation_id TEXT NOT NULL,
                    new_generation_id TEXT NOT NULL,
                    receipt_json BLOB NOT NULL
                );
            """)
            row = connection.execute("SELECT schema_id FROM descriptor WHERE singleton=1").fetchone()
            if row is None:
                connection.execute("INSERT INTO descriptor VALUES (1, ?)", (STORE_SCHEMA,))
                connection.execute("INSERT OR IGNORE INTO head VALUES (1, NULL)")
            elif row[0] != STORE_SCHEMA:
                raise IntegrityError("cross-runtime store schema refused")

    def _assert_schema(self, connection: sqlite3.Connection) -> None:
        row = connection.execute("SELECT schema_id FROM descriptor WHERE singleton=1").fetchone()
        if row is None or row[0] != STORE_SCHEMA:
            raise IntegrityError("cross-runtime store schema refused")

    def head_id(self) -> str | None:
        self.init()
        with self._connect() as connection:
            self._assert_schema(connection)
            row = connection.execute("SELECT generation_id FROM head WHERE singleton=1").fetchone()
            return row[0] if row else None

    def publish(
        self, source_texts: dict[str, str], *, encoder: PassageEncoder | None,
        capability_level: str, code_root: str | Path | None = None,
        expected_head: str | None = None,
    ) -> CompiledField:
        """Compile before the immediate transaction, then atomically move head."""
        self.init()
        snapshot = self.head_id() if expected_head is None else expected_head
        field = compile_sources(
            source_texts, encoder=encoder, generation_parent=snapshot,
            capability_level=capability_level, code_root=code_root,
        )
        raw = archive_bytes(field)
        with self._connect() as connection:
            self._assert_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            current = connection.execute("SELECT generation_id FROM head WHERE singleton=1").fetchone()[0]
            if current != snapshot:
                connection.rollback()
                raise ConcurrentHeadError("store head changed during compilation")
            connection.execute(
                "INSERT OR IGNORE INTO generations VALUES (?, ?, ?, ?, ?, ?)",
                (field.generation_id, snapshot, capability_level, field.field_hash,
                 sha256_bytes(raw), raw),
            )
            connection.execute("UPDATE head SET generation_id=? WHERE singleton=1", (field.generation_id,))
            connection.commit()
        return field

    def active_language_sources(self) -> dict[str, str]:
        """Return only authoritative controlled-language sources at the head."""
        if self.head_id() is None:
            return {}
        field = self.load()
        return {
            source_id: source.text
            for source_id, source in sorted(field.sources.items())
            if source_id.endswith(".moth")
        }

    def sync(self, directory: str | Path, *, encoder: PassageEncoder) -> CompiledField:
        root = Path(directory).resolve()
        if not root.is_dir():
            raise FileNotFoundError(root)
        sources: dict[str, str] = {}
        for path in sorted(root.rglob("*.moth")):
            if path.is_symlink() or not path.is_file():
                continue
            sources[path.relative_to(root).as_posix()] = path.read_text(encoding="utf-8")
        if not sources:
            raise ValueError("sync directory contains no .moth source")
        code_root = root if any(path.is_file() and not path.is_symlink() for path in root.rglob("*.py")) else None
        return self.publish(sources, encoder=encoder, capability_level="L8", code_root=code_root)

    def add(self, source_id: str, text: str, *, encoder: PassageEncoder) -> CompiledField:
        if not source_id.endswith(".moth"):
            raise ValueError("Runtime 4.7 add accepts controlled-language .moth sources")
        sources = self.active_language_sources()
        sources[source_id] = text
        return self.publish(sources, encoder=encoder, capability_level="L8")

    def remove(self, source_id: str, *, encoder: PassageEncoder) -> CompiledField:
        sources = self.active_language_sources()
        if source_id not in sources:
            raise KeyError(source_id)
        del sources[source_id]
        if not sources:
            raise ValueError("cannot publish a generation without a controlled-language source")
        return self.publish(sources, encoder=encoder, capability_level="L8")

    def purge(self, source_id: str, *, encoder: PassageEncoder) -> dict[str, Any]:
        prior = self.head_id()
        if prior is None:
            raise IntegrityError("store has no compiled generation")
        field = self.remove(source_id, encoder=encoder)
        receipt = {
            "schema": "moth-source-purge-receipt/4.7",
            "source_id": source_id,
            "prior_generation_id": prior,
            "new_generation_id": field.generation_id,
        }
        receipt_id = digest("moth-source-purge/4.7", receipt)
        with self._connect() as connection:
            self._assert_schema(connection)
            connection.execute(
                "INSERT INTO purge_receipts VALUES (?, ?, ?, ?, ?)",
                (receipt_id, source_id, prior, field.generation_id, canonical_bytes(receipt)),
            )
        return {**receipt, "receipt_id": receipt_id}

    def export(self, destination: str | Path) -> dict[str, Any]:
        self.verify()
        target = Path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise FileExistsError(target)
        with self._connect() as source, sqlite3.connect(target) as output:
            source.backup(output)
        return {
            "schema": "moth-proof-energy-export/4.7",
            "path": str(target.resolve()),
            "sha256": sha256_bytes(target.read_bytes()),
            "head": self.head_id(),
        }

    def load(self, generation_id: str | None = None) -> CompiledField:
        self.init()
        with self._connect() as connection:
            self._assert_schema(connection)
            selected = generation_id or connection.execute(
                "SELECT generation_id FROM head WHERE singleton=1"
            ).fetchone()[0]
            if selected is None:
                raise IntegrityError("store has no compiled generation")
            row = connection.execute(
                "SELECT archive_sha256, archive_json FROM generations WHERE generation_id=?", (selected,)
            ).fetchone()
        if row is None or sha256_bytes(row[1]) != row[0]:
            raise IntegrityError("generation archive is missing or corrupted")
        value = json.loads(bytes(row[1]).decode("utf-8"))
        field = field_from_archive(value)
        if field.generation_id != selected:
            raise IntegrityError("generation identifier mismatch")
        return field

    def query(self, prompt: str, *, encoder=None, thresholds=None,
              generation_id: str | None = None, modality: str = "text") -> dict[str, Any]:
        field = self.load(generation_id)
        result = query(field, prompt, encoder=encoder, thresholds=thresholds, modality=modality)
        raw = result_bytes(result)
        with self._connect() as connection:
            self._assert_schema(connection)
            connection.execute(
                "INSERT OR REPLACE INTO episodes VALUES (?, ?, ?, ?, ?, ?, ?)",
                (result["episode_id"], field.generation_id, prompt, modality,
                 result["replay"]["input_hash"], sha256_bytes(raw), raw),
            )
        return result

    def replay(self, episode_id: str, *, encoder_free: bool) -> bytes:
        if not encoder_free:
            raise ValueError("Runtime 4.7 replay requires --encoder-free")
        self.init()
        with self._connect() as connection:
            self._assert_schema(connection)
            row = connection.execute(
                "SELECT generation_id, prompt, modality, input_hash, result_sha256, result_json "
                "FROM episodes WHERE episode_id=?", (episode_id,),
            ).fetchone()
        if row is None:
            raise KeyError(episode_id)
        generation_id, prompt, modality, input_hash, expected_hash, raw = row
        raw = bytes(raw)
        if sha256_bytes(raw) != expected_hash:
            raise IntegrityError("episode result bytes changed")
        result = json.loads(raw.decode("utf-8"))
        verify_result_receipt(result)
        field = self.load(generation_id)
        expected_input = digest("moth-capability-input/4.7", {
            "generation_id": field.generation_id, "modality": modality,
            "prompt": normalize_text(prompt),
        })
        if expected_input != input_hash or result["replay"]["field_hash"] != field.field_hash:
            raise IntegrityError("episode input or field receipt changed")
        if canonical_bytes(result) != raw:
            raise IntegrityError("episode JSON is not canonical")
        return raw

    def history(self) -> list[dict[str, Any]]:
        self.init()
        with self._connect() as connection:
            self._assert_schema(connection)
            rows = connection.execute(
                "SELECT generation_id, parent_id, capability_level, field_hash FROM generations ORDER BY rowid"
            ).fetchall()
        return [{"generation_id": row[0], "parent_id": row[1],
                 "capability_level": row[2], "field_hash": row[3]} for row in rows]

    def verify(self) -> dict[str, Any]:
        self.init()
        with self._connect() as connection:
            self._assert_schema(connection)
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            generations = connection.execute("SELECT generation_id FROM generations ORDER BY generation_id").fetchall()
            episodes = connection.execute("SELECT episode_id FROM episodes ORDER BY episode_id").fetchall()
        if integrity != "ok":
            raise IntegrityError(f"SQLite integrity check failed: {integrity}")
        for (generation_id,) in generations:
            self.load(generation_id)
        return {"schema": STORE_SCHEMA, "integrity": "ok", "generations": len(generations),
                "episodes": len(episodes), "head": self.head_id()}
