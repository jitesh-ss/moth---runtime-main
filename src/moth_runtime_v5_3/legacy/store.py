"""Independent immutable SQLite store for Runtime 5.0 World bundles."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Any

from .archive import archive_bytes, world_from_archive
from .canonical import canonical_bytes, digest, normalize_text, sha256_bytes
from .compiler import PassageEncoder, compile_sources
from .handoff import build_bundle, verify_bundle
from .model import (
    CompiledWorld, IntegrityError, RefusalCode, WorldBundle, WorldHandoff,
    WorldRole, WorldStageReceipt,
)
from .runtime import query_worlds, result_bytes, verify_archived_result, verify_result_receipt

STORE_SCHEMA = "proof-energy-world-store/5.0"


class ConcurrentHeadError(RuntimeError):
    pass


class WorldStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def _preflight(self) -> None:
        if self.path.is_dir():
            raise IntegrityError("Runtime 5.0 requires its own SQLite store file")
        if not self.path.exists() or self.path.stat().st_size == 0:
            return
        with sqlite3.connect(self.path) as connection:
            table = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='descriptor'"
            ).fetchone()
            if table is None:
                raise IntegrityError("existing SQLite file is not a Runtime 5.0 store")
            try:
                row = connection.execute(
                    "SELECT schema_id FROM descriptor WHERE singleton=1"
                ).fetchone()
            except sqlite3.DatabaseError as exc:
                raise IntegrityError("existing store descriptor is malformed") from exc
            if row is None or row[0] != STORE_SCHEMA:
                raise IntegrityError("cross-runtime store schema refused")

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=FULL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    @staticmethod
    def _assert_schema(connection: sqlite3.Connection) -> None:
        try:
            row = connection.execute(
                "SELECT schema_id FROM descriptor WHERE singleton=1"
            ).fetchone()
        except sqlite3.DatabaseError as exc:
            raise IntegrityError("Runtime 5.0 store descriptor is unavailable") from exc
        if row is None or row[0] != STORE_SCHEMA:
            raise IntegrityError("cross-runtime store schema refused")

    def init(self) -> None:
        self._preflight()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS descriptor (
                    singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
                    schema_id TEXT NOT NULL,
                    runtime_label TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS world_generations (
                    generation_id TEXT PRIMARY KEY,
                    role TEXT NOT NULL CHECK(role IN ('INPUT','MAIN','SURFACE')),
                    parent_generation_id TEXT,
                    capability_level TEXT NOT NULL,
                    world_hash TEXT NOT NULL,
                    archive_sha256 TEXT NOT NULL,
                    archive_json BLOB NOT NULL,
                    FOREIGN KEY(parent_generation_id) REFERENCES world_generations(generation_id)
                );
                CREATE TABLE IF NOT EXISTS world_heads (
                    role TEXT PRIMARY KEY CHECK(role IN ('INPUT','MAIN','SURFACE')),
                    generation_id TEXT,
                    FOREIGN KEY(generation_id) REFERENCES world_generations(generation_id)
                );
                CREATE TABLE IF NOT EXISTS bundles (
                    bundle_id TEXT PRIMARY KEY,
                    bundle_hash TEXT NOT NULL,
                    interface_hash TEXT NOT NULL,
                    input_generation_id TEXT NOT NULL,
                    main_generation_id TEXT NOT NULL,
                    surface_generation_id TEXT NOT NULL,
                    bundle_json BLOB NOT NULL,
                    FOREIGN KEY(input_generation_id) REFERENCES world_generations(generation_id),
                    FOREIGN KEY(main_generation_id) REFERENCES world_generations(generation_id),
                    FOREIGN KEY(surface_generation_id) REFERENCES world_generations(generation_id)
                );
                CREATE TABLE IF NOT EXISTS active_bundle (
                    singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
                    bundle_id TEXT,
                    FOREIGN KEY(bundle_id) REFERENCES bundles(bundle_id)
                );
                CREATE TABLE IF NOT EXISTS episodes (
                    episode_id TEXT PRIMARY KEY,
                    bundle_id TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    modality TEXT NOT NULL,
                    input_hash TEXT NOT NULL,
                    result_sha256 TEXT NOT NULL,
                    result_json BLOB NOT NULL,
                    FOREIGN KEY(bundle_id) REFERENCES bundles(bundle_id)
                );
                CREATE TABLE IF NOT EXISTS settlement_receipts (
                    episode_id TEXT NOT NULL,
                    stage_order INTEGER NOT NULL CHECK(stage_order BETWEEN 1 AND 3),
                    role TEXT NOT NULL,
                    receipt_json BLOB NOT NULL,
                    PRIMARY KEY(episode_id, stage_order),
                    FOREIGN KEY(episode_id) REFERENCES episodes(episode_id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS handoff_receipts (
                    episode_id TEXT NOT NULL,
                    handoff_order INTEGER NOT NULL CHECK(handoff_order BETWEEN 1 AND 2),
                    source_role TEXT NOT NULL,
                    target_role TEXT NOT NULL,
                    receipt_json BLOB NOT NULL,
                    PRIMARY KEY(episode_id, handoff_order),
                    FOREIGN KEY(episode_id) REFERENCES episodes(episode_id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS purge_receipts (
                    receipt_id TEXT PRIMARY KEY,
                    receipt_json BLOB NOT NULL
                );
                CREATE TABLE IF NOT EXISTS export_receipts (
                    receipt_id TEXT PRIMARY KEY,
                    receipt_json BLOB NOT NULL
                );
            """)
            row = connection.execute(
                "SELECT schema_id, runtime_label FROM descriptor WHERE singleton=1"
            ).fetchone()
            if row is None:
                connection.execute(
                    "INSERT INTO descriptor VALUES (1, ?, '5.0')", (STORE_SCHEMA,)
                )
            elif row != (STORE_SCHEMA, "5.0"):
                raise IntegrityError("cross-runtime store schema refused")
            for role in WorldRole:
                connection.execute(
                    "INSERT OR IGNORE INTO world_heads VALUES (?, NULL)", (role.value,)
                )
            connection.execute(
                "INSERT OR IGNORE INTO active_bundle VALUES (1, NULL)"
            )

    def head_id(self, role: WorldRole | str) -> str | None:
        role = WorldRole(str(role).upper())
        self.init()
        with self._connect() as connection:
            self._assert_schema(connection)
            row = connection.execute(
                "SELECT generation_id FROM world_heads WHERE role=?", (role.value,)
            ).fetchone()
        if row is None:
            raise IntegrityError("World head is absent")
        return row[0]

    def heads(self) -> dict[WorldRole, str | None]:
        return {role: self.head_id(role) for role in WorldRole}

    def publish(
        self, role: WorldRole | str, source_texts: dict[str, str], *,
        encoder: PassageEncoder | None, capability_level: str = "L9",
        code_root: str | Path | None = None, expected_head: str | None = None,
    ) -> CompiledWorld:
        role = WorldRole(str(role).upper())
        self.init()
        snapshot = self.head_id(role) if expected_head is None else expected_head
        world = compile_sources(
            source_texts, encoder=encoder, generation_parent=snapshot,
            capability_level=capability_level, code_root=code_root, world_role=role,
        )
        raw = archive_bytes(world, parent_generation_id=snapshot)
        with self._connect() as connection:
            self._assert_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            current = connection.execute(
                "SELECT generation_id FROM world_heads WHERE role=?", (role.value,)
            ).fetchone()[0]
            if current != snapshot:
                connection.rollback()
                raise ConcurrentHeadError(f"{role.value} World head changed during compilation")
            connection.execute(
                "INSERT OR IGNORE INTO world_generations VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    world.generation_id, role.value, snapshot, world.capability_level,
                    world.world_hash, sha256_bytes(raw), raw,
                ),
            )
            stored = connection.execute(
                "SELECT role, parent_generation_id, capability_level, world_hash, "
                "archive_sha256, archive_json FROM world_generations WHERE generation_id=?",
                (world.generation_id,),
            ).fetchone()
            try:
                stored_identity = (*stored[:5], bytes(stored[5])) if stored is not None else None
            except (TypeError, ValueError) as exc:
                connection.rollback()
                raise IntegrityError("stored World archive bytes are malformed") from exc
            if stored_identity != (
                role.value, snapshot, world.capability_level, world.world_hash,
                sha256_bytes(raw), raw,
            ):
                connection.rollback()
                raise IntegrityError("generation identifier collides with different World bytes")
            connection.execute(
                "UPDATE world_heads SET generation_id=? WHERE role=?",
                (world.generation_id, role.value),
            )
            connection.commit()
        return world

    def load_world(self, generation_id: str) -> CompiledWorld:
        self.init()
        with self._connect() as connection:
            self._assert_schema(connection)
            row = connection.execute(
                "SELECT role, parent_generation_id, capability_level, world_hash, "
                "archive_sha256, archive_json FROM world_generations "
                "WHERE generation_id=?", (generation_id,),
            ).fetchone()
        if row is None:
            raise KeyError(generation_id)
        role, parent_id, capability_level, world_hash, archive_sha, stored_raw = row
        try:
            raw = bytes(stored_raw)
        except (TypeError, ValueError) as exc:
            raise IntegrityError("World archive bytes are malformed") from exc
        if sha256_bytes(raw) != archive_sha:
            raise IntegrityError("World archive bytes changed")
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise IntegrityError("World archive is not valid UTF-8 JSON") from exc
        try:
            canonical = canonical_bytes(value)
        except (TypeError, ValueError) as exc:
            raise IntegrityError("World archive has invalid canonical values") from exc
        if canonical != raw:
            raise IntegrityError("World archive bytes are not canonical")
        try:
            world = world_from_archive(value)
        except IntegrityError:
            raise
        except (KeyError, TypeError, ValueError) as exc:
            raise IntegrityError("World archive is malformed") from exc
        if (
            world.generation_id != generation_id
            or world.world_role.value != role
            or value.get("parent_generation_id") != parent_id
            or world.capability_level != capability_level
            or world.world_hash != world_hash
        ):
            raise IntegrityError("World generation identity or role mismatch")
        return world

    def load_head(self, role: WorldRole | str) -> CompiledWorld:
        role = WorldRole(str(role).upper())
        selected = self.head_id(role)
        if selected is None:
            raise IntegrityError(f"{role.value} World head is empty")
        world = self.load_world(selected)
        if world.world_role != role:
            raise IntegrityError("World head refers to a generation with the wrong role")
        return world

    def active_sources(self, role: WorldRole | str) -> dict[str, str]:
        role = WorldRole(str(role).upper())
        if self.head_id(role) is None:
            return {}
        world = self.load_head(role)
        return {
            source_id: source.text
            for source_id, source in sorted(world.sources.items())
            if source_id.endswith(".moth")
        }

    def sync(self, role: WorldRole | str, directory: str | Path, *,
             encoder: PassageEncoder) -> CompiledWorld:
        root = Path(directory).resolve()
        if not root.is_dir():
            raise FileNotFoundError(root)
        sources = {
            path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
            for path in sorted(root.rglob("*.moth"))
            if path.is_file() and not path.is_symlink()
        }
        if not sources:
            raise ValueError("sync directory contains no .moth source")
        code_root = root if any(
            path.is_file() and not path.is_symlink() for path in root.rglob("*.py")
        ) else None
        return self.publish(role, sources, encoder=encoder, code_root=code_root)

    def add(self, role: WorldRole | str, source_id: str, text: str, *,
            encoder: PassageEncoder) -> CompiledWorld:
        if not source_id.endswith(".moth"):
            raise ValueError("Runtime 5.0 add accepts controlled-language .moth sources")
        sources = self.active_sources(role)
        sources[source_id] = text
        return self.publish(role, sources, encoder=encoder)

    def remove(self, role: WorldRole | str, source_id: str, *,
               encoder: PassageEncoder) -> CompiledWorld:
        sources = self.active_sources(role)
        if source_id not in sources:
            raise KeyError(source_id)
        del sources[source_id]
        if not sources:
            raise ValueError("cannot publish a World generation without source language")
        return self.publish(role, sources, encoder=encoder)

    def activate(self) -> WorldBundle:
        self.init()
        snapshot = self.heads()
        if any(identifier is None for identifier in snapshot.values()):
            raise IntegrityError("Runtime 5.0 requires Input, Main, and Surface World heads")
        worlds = {
            role: self.load_world(str(identifier))
            for role, identifier in snapshot.items()
        }
        bundle = build_bundle(worlds)
        raw = canonical_bytes(bundle.canonical())
        with self._connect() as connection:
            self._assert_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            current = dict(connection.execute(
                "SELECT role, generation_id FROM world_heads ORDER BY role"
            ).fetchall())
            expected = {role.value: identifier for role, identifier in snapshot.items()}
            if current != expected:
                connection.rollback()
                raise ConcurrentHeadError("a World head changed during bundle activation")
            connection.execute(
                "INSERT OR IGNORE INTO bundles VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    bundle.bundle_id, bundle.bundle_hash, bundle.interface_hash,
                    bundle.input_generation_id, bundle.main_generation_id,
                    bundle.surface_generation_id, raw,
                ),
            )
            stored = connection.execute(
                "SELECT bundle_hash, interface_hash, input_generation_id, "
                "main_generation_id, surface_generation_id, bundle_json "
                "FROM bundles WHERE bundle_id=?", (bundle.bundle_id,),
            ).fetchone()
            try:
                stored_identity = (*stored[:5], bytes(stored[5])) if stored is not None else None
            except (TypeError, ValueError) as exc:
                connection.rollback()
                raise IntegrityError("stored World bundle bytes are malformed") from exc
            if stored_identity != (
                bundle.bundle_hash, bundle.interface_hash, bundle.input_generation_id,
                bundle.main_generation_id, bundle.surface_generation_id, raw,
            ):
                connection.rollback()
                raise IntegrityError("bundle identifier collides with different bundle bytes")
            connection.execute(
                "UPDATE active_bundle SET bundle_id=? WHERE singleton=1",
                (bundle.bundle_id,),
            )
            connection.commit()
        return bundle

    def load_bundle(self, bundle_id: str) -> WorldBundle:
        self.init()
        with self._connect() as connection:
            self._assert_schema(connection)
            row = connection.execute(
                "SELECT bundle_hash, interface_hash, input_generation_id, "
                "main_generation_id, surface_generation_id, bundle_json "
                "FROM bundles WHERE bundle_id=?", (bundle_id,)
            ).fetchone()
        if row is None:
            raise KeyError(bundle_id)
        try:
            raw = bytes(row[5])
        except (TypeError, ValueError) as exc:
            raise IntegrityError("World bundle bytes are malformed") from exc
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise IntegrityError("World bundle is not valid UTF-8 JSON") from exc
        try:
            canonical = canonical_bytes(value)
        except (TypeError, ValueError) as exc:
            raise IntegrityError("World bundle has invalid canonical values") from exc
        if canonical != raw or not isinstance(value, dict) or value.get("schema") != "moth-world-bundle/5.0":
            raise IntegrityError("World bundle bytes are not canonical")
        try:
            if set(value) != {
                "schema", "bundle_id", "input_generation_id", "main_generation_id",
                "surface_generation_id", "interface_hash", "bundle_hash",
            }:
                raise IntegrityError("World bundle shape is invalid")
            bundle = WorldBundle(
                str(value["bundle_id"]), str(value["input_generation_id"]),
                str(value["main_generation_id"]), str(value["surface_generation_id"]),
                str(value["interface_hash"]), str(value["bundle_hash"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise IntegrityError("World bundle is malformed") from exc
        if bundle.bundle_id != bundle_id or (
            bundle.bundle_hash, bundle.interface_hash, bundle.input_generation_id,
            bundle.main_generation_id, bundle.surface_generation_id,
        ) != row[:5]:
            raise IntegrityError("World bundle row differs from its canonical bytes")
        worlds = {role: self.load_world(bundle.generation_for(role)) for role in WorldRole}
        verify_bundle(bundle, worlds)
        return bundle

    def active_bundle(self) -> WorldBundle | None:
        self.init()
        with self._connect() as connection:
            self._assert_schema(connection)
            row = connection.execute(
                "SELECT bundle_id FROM active_bundle WHERE singleton=1"
            ).fetchone()
        return None if row is None or row[0] is None else self.load_bundle(str(row[0]))

    def bundle_worlds(self, bundle: WorldBundle) -> dict[WorldRole, CompiledWorld]:
        worlds = {role: self.load_world(bundle.generation_for(role)) for role in WorldRole}
        verify_bundle(bundle, worlds)
        return worlds

    @staticmethod
    def _not_ready(prompt: str, modality: str) -> dict[str, Any]:
        input_hash = digest("moth-world-input/5.0", {
            "bundle_id": None, "modality": modality, "prompt": normalize_text(prompt),
        })
        result: dict[str, Any] = {
            "schema": "moth-world-result/5.0", "runtime": "5.0",
            "status": "REFUSAL", "stage": "RUNTIME", "bundle_id": None,
            "episode_id": digest("moth-world-episode/5.0", {"input_hash": input_hash}),
            "grounding": None, "stages": [], "handoffs": [],
            "refusal": {
                "code": RefusalCode.WORLD_NOT_READY.value,
                "message": "Runtime 5.0 has no active three-world bundle.",
                "grounded_context": {},
            },
            "execution": {"performed": False, "dispatch_count": 0},
            "replay": {"input_hash": input_hash, "bundle_hash": None},
        }
        payload = {key: value for key, value in result.items() if key != "replay"}
        payload["replay"] = dict(result["replay"])
        result["replay"]["result_hash"] = sha256_bytes(canonical_bytes(payload))
        return result

    @staticmethod
    def _integrity_refusal(prompt: str, modality: str) -> dict[str, Any]:
        input_hash = digest("moth-world-input/5.0", {
            "bundle_id": None, "modality": modality, "prompt": normalize_text(prompt),
        })
        result: dict[str, Any] = {
            "schema": "moth-world-result/5.0", "runtime": "5.0",
            "status": "REFUSAL", "stage": "RUNTIME", "bundle_id": None,
            "episode_id": digest("moth-world-episode/5.0", {"input_hash": input_hash}),
            "grounding": None, "stages": [], "handoffs": [],
            "refusal": {
                "code": RefusalCode.INTEGRITY_FAILURE.value,
                "message": "Runtime 5.0 store or active bundle failed verification.",
                "grounded_context": {},
            },
            "execution": {"performed": False, "dispatch_count": 0},
            "replay": {"input_hash": input_hash, "bundle_hash": None},
        }
        payload = {key: value for key, value in result.items() if key != "replay"}
        payload["replay"] = dict(result["replay"])
        result["replay"]["result_hash"] = sha256_bytes(canonical_bytes(payload))
        return result

    def query(self, prompt: str, *, encoder=None, thresholds=None,
              modality: str = "text") -> dict[str, Any]:
        try:
            bundle = self.active_bundle()
        except IntegrityError:
            return self._integrity_refusal(prompt, modality)
        if bundle is None:
            return self._not_ready(prompt, modality)
        try:
            worlds = self.bundle_worlds(bundle)
            result, receipts, handoffs = query_worlds(
                worlds, bundle, prompt, encoder=encoder, thresholds=thresholds,
                modality=modality,
            )
            self._record_episode(prompt, modality, result, receipts, handoffs)
        except IntegrityError:
            return self._integrity_refusal(prompt, modality)
        return result

    def _record_episode(
        self, prompt: str, modality: str, result: dict[str, Any],
        receipts: tuple[WorldStageReceipt, ...], handoffs: tuple[WorldHandoff, ...],
    ) -> None:
        verify_result_receipt(result)
        bundle = self.load_bundle(str(result["bundle_id"]))
        worlds = self.bundle_worlds(bundle)
        rebuilt_receipts, rebuilt_handoffs = verify_archived_result(result, worlds, bundle)
        if receipts != rebuilt_receipts or handoffs != rebuilt_handoffs:
            raise IntegrityError("query evidence differs from archived reconstruction")
        raw = result_bytes(result)
        episode_id = str(result["episode_id"])
        expected_episode = (
            bundle.bundle_id, normalize_text(prompt), modality,
            result["replay"]["input_hash"], sha256_bytes(raw), raw,
        )
        expected_receipts = [
            (index, receipt.role.value, canonical_bytes(receipt.canonical()))
            for index, receipt in enumerate(receipts, 1)
        ]
        expected_handoffs = [
            (
                index, handoff.source_role.value, handoff.target_role.value,
                canonical_bytes(handoff.canonical()),
            )
            for index, handoff in enumerate(handoffs, 1)
        ]
        with self._connect() as connection:
            self._assert_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT bundle_id, prompt, modality, input_hash, result_sha256, result_json "
                "FROM episodes WHERE episode_id=?", (episode_id,),
            ).fetchone()
            if existing is not None:
                try:
                    existing_episode = (*existing[:5], bytes(existing[5]))
                    existing_receipts = [
                        (row[0], row[1], bytes(row[2]))
                        for row in connection.execute(
                            "SELECT stage_order, role, receipt_json FROM settlement_receipts "
                            "WHERE episode_id=? ORDER BY stage_order", (episode_id,),
                        )
                    ]
                    existing_handoffs = [
                        (row[0], row[1], row[2], bytes(row[3]))
                        for row in connection.execute(
                            "SELECT handoff_order, source_role, target_role, receipt_json "
                            "FROM handoff_receipts WHERE episode_id=? ORDER BY handoff_order",
                            (episode_id,),
                        )
                    ]
                except (TypeError, ValueError) as exc:
                    connection.rollback()
                    raise IntegrityError("immutable episode contains malformed bytes") from exc
                if (
                    existing_episode != expected_episode
                    or existing_receipts != expected_receipts
                    or existing_handoffs != expected_handoffs
                ):
                    connection.rollback()
                    raise IntegrityError(
                        "immutable episode identifier collides with different bytes or receipts"
                    )
                connection.commit()
                return
            connection.execute(
                "INSERT INTO episodes VALUES (?, ?, ?, ?, ?, ?, ?)",
                (episode_id, *expected_episode),
            )
            for index, role, receipt_raw in expected_receipts:
                connection.execute(
                    "INSERT INTO settlement_receipts VALUES (?, ?, ?, ?)",
                    (episode_id, index, role, receipt_raw),
                )
            for index, source_role, target_role, handoff_raw in expected_handoffs:
                connection.execute(
                    "INSERT INTO handoff_receipts VALUES (?, ?, ?, ?, ?)",
                    (episode_id, index, source_role, target_role, handoff_raw),
                )
            connection.commit()

    def replay(self, episode_id: str, *, encoder_free: bool) -> bytes:
        if not encoder_free:
            raise ValueError("Runtime 5.0 replay requires --encoder-free")
        self.init()
        with self._connect() as connection:
            self._assert_schema(connection)
            row = connection.execute(
                "SELECT bundle_id, prompt, modality, input_hash, result_sha256, result_json "
                "FROM episodes WHERE episode_id=?", (episode_id,),
            ).fetchone()
            stored_receipts = connection.execute(
                "SELECT stage_order, role, receipt_json FROM settlement_receipts "
                "WHERE episode_id=? ORDER BY stage_order", (episode_id,),
            ).fetchall()
            stored_handoffs = connection.execute(
                "SELECT handoff_order, source_role, target_role, receipt_json "
                "FROM handoff_receipts WHERE episode_id=? ORDER BY handoff_order",
                (episode_id,),
            ).fetchall()
        if row is None:
            raise KeyError(episode_id)
        bundle_id, prompt, modality, input_hash, result_sha, raw = row
        try:
            raw = bytes(raw)
        except (TypeError, ValueError) as exc:
            raise IntegrityError("episode result bytes are malformed") from exc
        if sha256_bytes(raw) != result_sha:
            raise IntegrityError("episode result bytes changed")
        try:
            result = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise IntegrityError("episode result is not valid UTF-8 JSON") from exc
        try:
            canonical = canonical_bytes(result)
        except (TypeError, ValueError) as exc:
            raise IntegrityError("episode result has invalid canonical values") from exc
        if canonical != raw:
            raise IntegrityError("episode result JSON is not canonical")
        bundle = self.load_bundle(str(bundle_id))
        worlds = self.bundle_worlds(bundle)
        try:
            receipts, handoffs = verify_archived_result(result, worlds, bundle)
        except IntegrityError:
            raise
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise IntegrityError("episode evidence is malformed") from exc
        expected_receipts = [
            (index, receipt.role.value, canonical_bytes(receipt.canonical()))
            for index, receipt in enumerate(receipts, 1)
        ]
        expected_handoffs = [
            (
                index, handoff.source_role.value, handoff.target_role.value,
                canonical_bytes(handoff.canonical()),
            )
            for index, handoff in enumerate(handoffs, 1)
        ]
        try:
            actual_receipts = [
                (row[0], row[1], bytes(row[2])) for row in stored_receipts
            ]
            actual_handoffs = [
                (row[0], row[1], row[2], bytes(row[3])) for row in stored_handoffs
            ]
        except (TypeError, ValueError) as exc:
            raise IntegrityError("episode receipt bytes are malformed") from exc
        if actual_receipts != expected_receipts:
            raise IntegrityError("settlement receipt table differs from reconstructed evidence")
        if actual_handoffs != expected_handoffs:
            raise IntegrityError("handoff receipt table differs from reconstructed evidence")
        expected_input = digest("moth-world-input/5.0", {
            "bundle_id": bundle.bundle_id, "modality": modality,
            "prompt": normalize_text(prompt),
        })
        if input_hash != expected_input or result["replay"]["input_hash"] != expected_input:
            raise IntegrityError("episode input receipt changed")
        return raw

    def history(self, role: WorldRole | str | None = None) -> list[dict[str, Any]]:
        self.init()
        query = (
            "SELECT generation_id, role, parent_generation_id, world_hash "
            "FROM world_generations"
        )
        arguments: tuple[Any, ...] = ()
        if role is not None:
            selected = WorldRole(str(role).upper())
            query += " WHERE role=?"
            arguments = (selected.value,)
        query += " ORDER BY rowid"
        with self._connect() as connection:
            self._assert_schema(connection)
            rows = connection.execute(query, arguments).fetchall()
        return [
            {
                "generation_id": row[0], "role": row[1],
                "parent_generation_id": row[2], "world_hash": row[3],
            }
            for row in rows
        ]

    def status(self) -> dict[str, Any]:
        self.init()
        with self._connect() as connection:
            self._assert_schema(connection)
            generations = connection.execute("SELECT COUNT(*) FROM world_generations").fetchone()[0]
            bundles = connection.execute("SELECT COUNT(*) FROM bundles").fetchone()[0]
            episodes = connection.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
            active = connection.execute(
                "SELECT bundle_id FROM active_bundle WHERE singleton=1"
            ).fetchone()[0]
        return {
            "schema": STORE_SCHEMA, "runtime": "5.0",
            "heads": {role.value: self.head_id(role) for role in WorldRole},
            "active_bundle": active, "generations": generations,
            "bundles": bundles, "episodes": episodes,
        }

    def verify(self) -> dict[str, Any]:
        self.init()
        with self._connect() as connection:
            self._assert_schema(connection)
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            foreign_key_failures = connection.execute("PRAGMA foreign_key_check").fetchall()
            generations = [row[0] for row in connection.execute(
                "SELECT generation_id FROM world_generations ORDER BY generation_id"
            )]
            bundles = [row[0] for row in connection.execute(
                "SELECT bundle_id FROM bundles ORDER BY bundle_id"
            )]
            episodes = [row[0] for row in connection.execute(
                "SELECT episode_id FROM episodes ORDER BY episode_id"
            )]
            heads = connection.execute(
                "SELECT role, generation_id FROM world_heads ORDER BY role"
            ).fetchall()
            active_row = connection.execute(
                "SELECT bundle_id FROM active_bundle WHERE singleton=1"
            ).fetchone()
        if integrity != "ok":
            raise IntegrityError(f"SQLite integrity check failed: {integrity}")
        if foreign_key_failures:
            raise IntegrityError("SQLite foreign-key integrity check failed")
        for generation_id in generations:
            self.load_world(generation_id)
        for role, generation_id in heads:
            if generation_id is not None and self.load_world(generation_id).world_role != WorldRole(role):
                raise IntegrityError("World head refers to a generation with the wrong role")
        for bundle_id in bundles:
            self.load_bundle(bundle_id)
        if active_row is None:
            raise IntegrityError("active World bundle head is absent")
        if active_row[0] is not None:
            self.load_bundle(str(active_row[0]))
        for episode_id in episodes:
            self.replay(episode_id, encoder_free=True)
        return {**self.status(), "integrity": "ok"}

    def export(self, destination: str | Path) -> dict[str, Any]:
        self.verify()
        target = Path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise FileExistsError(target)
        with self._connect() as source, sqlite3.connect(target) as output:
            source.backup(output)
        receipt = {
            "schema": "moth-world-export/5.0", "path": str(target.resolve()),
            "sha256": sha256_bytes(target.read_bytes()),
            "active_bundle": self.status()["active_bundle"],
        }
        receipt_id = digest("moth-world-export-receipt/5.0", receipt)
        with self._connect() as connection:
            self._assert_schema(connection)
            connection.execute(
                "INSERT INTO export_receipts VALUES (?, ?)",
                (receipt_id, canonical_bytes(receipt)),
            )
        return {**receipt, "receipt_id": receipt_id}
