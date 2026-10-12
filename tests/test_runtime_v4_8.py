from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3

import pytest

import moth_runtime_v4_8.runtime as runtime_v4_8
from moth_runtime_v4_8.canonical import canonical_bytes, digest, sha256_bytes
from moth_runtime_v4_8.compiler import compile_sources
from moth_runtime_v4_8.encoder import DeterministicEncoder
from moth_runtime_v4_8.handoff import handoff_from_dict, verify_handoff
from moth_runtime_v4_8.model import IntegrityError, MeaningType, WorldRole
from moth_runtime_v4_8.runtime import (
    _receipt, _result_receipt, verify_archived_result,
)
from moth_runtime_v4_8.store import STORE_SCHEMA, WorldStore

ROOT = Path(__file__).resolve().parents[1]
WORLD = (ROOT / "tests/fixtures/world.moth").read_text(encoding="utf-8")
THRESHOLDS = {
    "default": {"score": 0.82, "margin": 0.05},
    "INSTRUCTION": {"score": 0.82, "margin": 0.08},
}

MINIMAL = """\
Entity "Node-00" is declared.
Operation "lookup" selects kernel primitive "LOOKUP".
Output schema "answer-json" selects kernel schema "ANSWER_WITH_PROOF".
Instruction "lookup-entity" selects operation "lookup" accepts "Return {ENTITY} using {SCHEMA}.".
"""

SURFACE_REALIZER = """\
Operation "realize-semantic-result" selects kernel primitive "REALIZE_SEMANTIC_RESULT".
Instruction "realize-semantic-result" selects operation "realize-semantic-result" accepts "Realize the verified semantic result.".
"""


def without_relation_premises(source: str) -> str:
    return "\n".join(
        line for line in source.splitlines()
        if not line.startswith("The route from ")
    ) + "\n"


def publish_bundle(store: WorldStore, source: str = WORLD):
    encoder = DeterministicEncoder()
    store.publish(
        WorldRole.INPUT,
        {"input.moth": without_relation_premises(source)},
        encoder=encoder,
    )
    store.publish(WorldRole.MAIN, {"main.moth": source}, encoder=encoder)
    store.publish(
        WorldRole.SURFACE,
        {"surface.moth": SURFACE_REALIZER},
        encoder=encoder,
    )
    return encoder, store.activate()


def tree_hash(files: list[Path]) -> str:
    result = hashlib.sha256()
    for path in sorted(files):
        result.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        result.update(b"\0")
        result.update(hashlib.sha256(path.read_bytes()).digest())
    return result.hexdigest()


def test_runtime_4_7_protected_assets_are_byte_identical():
    assert tree_hash(list((ROOT / "src/moth_runtime").glob("*.py"))) == (
        "a83b04b1730813e0edcfd85daa0d70399c7757426bb4dd4f00acb320fbda756b"
    )
    assert tree_hash([
        path for path in (ROOT / "config").glob("*.json")
        if path.parent == ROOT / "config"
    ]) == "1cbcea8472505631db43ee17cd6a28c14c8bcfe6e2576c2ad1d740a0aa601a06"
    assert tree_hash([
        ROOT / "ARCHITECTURE.md", ROOT / "PRODUCT.md", ROOT / "ARCHITECTURE-DETAILED.md",
    ]) == "1b37b8ab3f4d56e8051f7b26a490ad893dc41718d06ae5ee211f24e3330bc21f"
    prime = ROOT / "data/store-4.7.sqlite3"
    assert sha256_bytes(prime.read_bytes()) == (
        "4bda69217d0e64b398508e206a670dd99f3e64976dc9e7a0aadb5f22e55cd3da"
    )
    copied = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "src/moth_runtime_v4_8").glob("*.py")
    )
    assert "from moth_runtime" not in copied
    assert "import moth_runtime" not in copied


def test_runtime_4_8_architecture_lock_matches_frozen_assets():
    lock = json.loads(
        (ROOT / "config/v4.8/ARCHITECTURE-LOCK.json").read_text(encoding="utf-8")
    )
    for group in ("documents", "configuration"):
        for record in lock[group].values():
            assert sha256_bytes((ROOT / record["path"]).read_bytes()) == record["sha256"]
    for group in ("implementation", "launcher"):
        record = lock[group]
        assert tree_hash(list((ROOT / record["path"]).glob("*.py"))) == record["tree_sha256"]
    production = lock["production_store"]
    assert sha256_bytes((ROOT / production["path"]).read_bytes()) == production["sha256"]
    assert lock["runtime_4_7_preservation"]["preserved_after_implementation"] is True
    assert lock["launcher"]["explicit_runtime_required"] is True
    assert lock["qualification"]["verdict"] == "NOT_RUN"


def test_empty_store_and_world_not_ready(tmp_path):
    store = WorldStore(tmp_path / "empty.sqlite3")
    store.init()
    assert store.status() == {
        "schema": STORE_SCHEMA,
        "runtime": "4.8",
        "heads": {"INPUT": None, "MAIN": None, "SURFACE": None},
        "active_bundle": None,
        "generations": 0,
        "bundles": 0,
        "episodes": 0,
    }
    result = store.query("anything")
    assert result["status"] == "REFUSAL"
    assert result["refusal"]["code"] == "WORLD_NOT_READY"
    assert result["stages"] == [] and result["handoffs"] == []
    assert store.status()["episodes"] == 0


def test_cross_runtime_store_is_refused_without_mutation(tmp_path):
    target = tmp_path / "copied-4.7.sqlite3"
    shutil.copy2(ROOT / "data/store-4.7.sqlite3", target)
    before = sha256_bytes(target.read_bytes())
    with pytest.raises(IntegrityError, match="cross-runtime"):
        WorldStore(target).init()
    assert sha256_bytes(target.read_bytes()) == before


def test_world_role_and_source_order_are_content_addressed():
    encoder = DeterministicEncoder()
    first = compile_sources(
        {"world.moth": MINIMAL, "empty.moth": "# empty\n"},
        encoder=encoder, world_role=WorldRole.INPUT,
    )
    second = compile_sources(
        {"empty.moth": "# empty\n", "world.moth": MINIMAL},
        encoder=encoder, world_role=WorldRole.INPUT,
    )
    main = compile_sources(
        {"world.moth": MINIMAL, "empty.moth": "# empty\n"},
        encoder=encoder, world_role=WorldRole.MAIN,
    )
    assert first.world_hash == second.world_hash
    assert first.generation_id == second.generation_id
    assert first.world_hash != main.world_hash
    assert first.world_role == WorldRole.INPUT


def test_atomic_bundle_cascade_and_encoder_free_replay(tmp_path):
    store = WorldStore(tmp_path / "cascade.sqlite3")
    encoder, bundle = publish_bundle(store)
    result = store.query(
        "Return Node-00 using answer-json.", encoder=encoder, thresholds=THRESHOLDS,
    )
    assert result["status"] == "ANSWER"
    assert result["output"]["value"]["canonical_name"] == "Node-00"
    assert [stage["role"] for stage in result["stages"]] == ["INPUT", "MAIN", "SURFACE"]
    assert [stage["settlement"]["output_kind"] for stage in result["stages"]] == [
        "MAIN_REQUEST", "SEMANTIC_RESULT", "SURFACE_RESPONSE",
    ]
    assert len(result["stages"]) == 3 and len(result["handoffs"]) == 2
    assert [item["payload_kind"] for item in result["handoffs"]] == [
        "MAIN_REQUEST", "SEMANTIC_RESULT",
    ]
    assert all(stage["settlement"]["violation_count"] == 0 for stage in result["stages"])
    assert all(stage["settlement"]["proof_count"] == 1 for stage in result["stages"])
    assert "Return Node-00" not in json.dumps(result["handoffs"])
    assert store.replay(result["episode_id"], encoder_free=True) == canonical_bytes(result)
    assert store.verify()["integrity"] == "ok"

    old_bundle = store.active_bundle()
    store.add(WorldRole.MAIN, "extra.moth", "# disconnected\n", encoder=encoder)
    assert store.active_bundle() == old_bundle == bundle


def test_surface_contract_realizes_compiled_structured_output(tmp_path):
    store = WorldStore(tmp_path / "structured.sqlite3")
    encoder, _ = publish_bundle(store)
    result = store.query(
        "Render basic-payload with message = message-alpha, count = count-one "
        "using compiled-json.",
        encoder=encoder,
        thresholds=THRESHOLDS,
    )
    assert result["status"] == "ANSWER"
    assert result["output"] == {
        "kind": "COMPILED_JSON",
        "value": {"count": 1, "message": "alpha"},
    }
    assert [stage["settlement"]["output_kind"] for stage in result["stages"]] == [
        "MAIN_REQUEST", "SEMANTIC_RESULT", "SURFACE_RESPONSE",
    ]
    assert store.replay(result["episode_id"], encoder_free=True) == canonical_bytes(result)


def test_world_roles_are_separated_and_handoffs_are_id_only(tmp_path, monkeypatch):
    store = WorldStore(tmp_path / "separated.sqlite3")
    encoder, bundle = publish_bundle(store)
    worlds = store.bundle_worlds(bundle)
    assert worlds[WorldRole.INPUT].edges == ()
    assert not worlds[WorldRole.SURFACE].by_kind(MeaningType.ENTITY)
    assert not worlds[WorldRole.SURFACE].by_kind(MeaningType.RELATION)
    assert not worlds[WorldRole.SURFACE].edges

    grounding_calls: list[str] = []
    original_ground_prompt = runtime_v4_8.ground_prompt

    def counted_ground_prompt(world, prompt, **options):
        grounding_calls.append(world.world_role.value)
        return original_ground_prompt(world, prompt, **options)

    monkeypatch.setattr(runtime_v4_8, "ground_prompt", counted_ground_prompt)

    result = store.query(
        "Starting from Node-00, follow route for 8 steps using answer-json.",
        encoder=encoder,
        thresholds=THRESHOLDS,
    )
    assert result["status"] == "ANSWER"
    assert grounding_calls == ["INPUT"]
    assert result["output"]["value"]["canonical_name"] == "Node-08"
    assert [stage["settlement"]["output_kind"] for stage in result["stages"]] == [
        "MAIN_REQUEST", "SEMANTIC_RESULT", "SURFACE_RESPONSE",
    ]
    assert result["handoffs"][0]["payload"] == result["stages"][0]["settlement"]["output"]
    assert result["handoffs"][1]["payload"] == result["stages"][1]["settlement"]["output"]
    main_request = result["handoffs"][0]["payload"]
    encoded_request = json.dumps(main_request, sort_keys=True)
    assert set(main_request) == {
        "schema", "interface_id", "instruction_id", "operation_id",
        "primitive", "slots", "bindings",
    }
    assert all(token not in encoded_request for token in (
        "canonical_name", "prompt", "grounding", "steps", "Node-00", "route",
    ))
    assert store.replay(result["episode_id"], encoder_free=True) == canonical_bytes(result)


def test_incomplete_and_incompatible_activation_do_not_publish_bundle(tmp_path):
    encoder = DeterministicEncoder()
    incomplete = WorldStore(tmp_path / "incomplete.sqlite3")
    incomplete.publish(WorldRole.INPUT, {"world.moth": MINIMAL}, encoder=encoder)
    with pytest.raises(IntegrityError, match="requires Input, Main, and Surface"):
        incomplete.activate()
    assert incomplete.status()["active_bundle"] is None

    incompatible = WorldStore(tmp_path / "incompatible.sqlite3")
    incompatible.publish(WorldRole.INPUT, {"world.moth": MINIMAL}, encoder=encoder)
    incompatible.publish(WorldRole.MAIN, {"world.moth": MINIMAL}, encoder=encoder)
    other = MINIMAL.replace("Node-00", "Other-00")
    incompatible.publish(WorldRole.SURFACE, {"world.moth": other}, encoder=encoder)
    with pytest.raises(IntegrityError, match="semantic realizer|incompatible"):
        incompatible.activate()
    assert incompatible.status()["active_bundle"] is None


def test_main_refusal_short_circuits_surface(tmp_path):
    encoder = DeterministicEncoder()
    store = WorldStore(tmp_path / "short-circuit.sqlite3")
    store.publish(
        WorldRole.INPUT,
        {"world.moth": without_relation_premises(WORLD)},
        encoder=encoder,
    )
    missing_middle = WORLD.replace(
        'The route from "Node-03" leads to "Node-04".\n', "",
    )
    store.publish(WorldRole.MAIN, {"world.moth": missing_middle}, encoder=encoder)
    store.publish(
        WorldRole.SURFACE, {"world.moth": SURFACE_REALIZER}, encoder=encoder,
    )
    store.activate()
    result = store.query(
        "Starting from Node-00, follow route for 8 steps using answer-json.",
        encoder=encoder, thresholds=THRESHOLDS,
    )
    assert result["status"] == "REFUSAL"
    assert result["stage"] == "MAIN"
    assert result["refusal"]["code"] == "MISSING_PREMISE"
    assert [stage["role"] for stage in result["stages"]] == ["INPUT"]
    assert len(result["handoffs"]) == 1


def test_forged_stage_and_handoff_are_rejected(tmp_path):
    store = WorldStore(tmp_path / "tamper.sqlite3")
    encoder, bundle = publish_bundle(store)
    result = store.query(
        "Return Node-00 using answer-json.", encoder=encoder, thresholds=THRESHOLDS,
    )
    worlds = store.bundle_worlds(bundle)
    receipt = _receipt(result["stages"][0]["receipt"])
    handoff = handoff_from_dict(result["handoffs"][0])
    forged = replace(handoff, target_generation_id="forged-generation")
    with pytest.raises(IntegrityError, match="target generation"):
        verify_handoff(
            forged, bundle, worlds[WorldRole.INPUT], worlds[WorldRole.MAIN], receipt,
        )

    altered = json.loads(json.dumps(result))
    altered["stages"][1]["settlement"]["output"]["canonical_name"] = "Forged"
    altered["replay"]["result_hash"] = _result_receipt(altered)
    with pytest.raises(Exception):
        verify_archived_result(altered, worlds, bundle)


@pytest.mark.parametrize(
    "target",
    ["source", "provenance", "meaning", "edge", "vector", "compiler", "world", "generation"],
)
def test_store_recomputes_every_archived_world_identity(tmp_path, target):
    store = WorldStore(tmp_path / f"archive-{target}.sqlite3")
    encoder = DeterministicEncoder()
    world = store.publish(WorldRole.INPUT, {"world.moth": WORLD}, encoder=encoder)
    with sqlite3.connect(store.path) as connection:
        raw = bytes(connection.execute(
            "SELECT archive_json FROM world_generations WHERE generation_id=?",
            (world.generation_id,),
        ).fetchone()[0])
        value = json.loads(raw.decode("utf-8"))
        entity_id = next(
            key for key, item in value["meanings"].items() if item["kind"] == "ENTITY"
        )
        if target == "source":
            value["sources"]["world.moth"]["sha256"] = "0" * 64
        elif target == "provenance":
            value["meanings"][entity_id]["owners"][0]["statement_sha256"] = "0" * 64
        elif target == "meaning":
            value["meanings"][entity_id]["payload"]["name"] = "forged"
        elif target == "edge":
            value["edges"][0]["edge_id"] = "0" * 64
        elif target == "vector":
            value["vectors"][entity_id]["vector_hash"] = "0" * 64
        elif target == "compiler":
            value["compiler_hash"] = "0" * 64
        elif target == "world":
            value["world_hash"] = "0" * 64
        else:
            value["generation_id"] = "0" * 64
        value["archive_hash"] = digest(
            "moth-world-archive/4.8",
            {key: item for key, item in value.items() if key != "archive_hash"},
        )
        forged = canonical_bytes(value)
        connection.execute(
            "UPDATE world_generations SET archive_sha256=?, archive_json=? "
            "WHERE generation_id=?",
            (sha256_bytes(forged), forged, world.generation_id),
        )
    with pytest.raises(IntegrityError):
        store.load_world(world.generation_id)
    with pytest.raises(IntegrityError):
        store.verify()


@pytest.mark.parametrize("mode", ["noncanonical", "malformed"])
def test_store_requires_valid_canonical_world_archive_bytes(tmp_path, mode):
    store = WorldStore(tmp_path / f"{mode}-world.sqlite3")
    world = store.publish(
        WorldRole.INPUT, {"world.moth": MINIMAL}, encoder=DeterministicEncoder(),
    )
    with sqlite3.connect(store.path) as connection:
        value = json.loads(bytes(connection.execute(
            "SELECT archive_json FROM world_generations WHERE generation_id=?",
            (world.generation_id,),
        ).fetchone()[0]).decode("utf-8"))
        corrupted = (
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
            if mode == "noncanonical" else b"{"
        )
        connection.execute(
            "UPDATE world_generations SET archive_sha256=?, archive_json=? "
            "WHERE generation_id=?",
            (sha256_bytes(corrupted), corrupted, world.generation_id),
        )
    with pytest.raises(IntegrityError):
        store.load_world(world.generation_id)


@pytest.mark.parametrize("payload", [b"{", b'{"schema":"moth-world-bundle/4.8"}'])
def test_corrupted_bundle_load_fails_as_integrity_error(tmp_path, payload):
    store = WorldStore(tmp_path / "corrupt-bundle.sqlite3")
    _, bundle = publish_bundle(store)
    with sqlite3.connect(store.path) as connection:
        connection.execute(
            "UPDATE bundles SET bundle_json=? WHERE bundle_id=?",
            (payload, bundle.bundle_id),
        )
    with pytest.raises(IntegrityError):
        store.load_bundle(bundle.bundle_id)
    with pytest.raises(IntegrityError):
        store.active_bundle()
    refusal = store.query("Return Node-00 using answer-json.")
    assert refusal["status"] == "REFUSAL"
    assert refusal["refusal"]["code"] == "INTEGRITY_FAILURE"
    assert refusal["stages"] == [] and refusal["handoffs"] == []


@pytest.mark.parametrize(
    ("table", "column", "message"),
    [
        ("settlement_receipts", "stage_order", "settlement receipt table"),
        ("handoff_receipts", "handoff_order", "handoff receipt table"),
    ],
)
def test_replay_and_verify_compare_independent_receipt_tables(
    tmp_path, table, column, message,
):
    store = WorldStore(tmp_path / f"receipt-{table}.sqlite3")
    encoder, _ = publish_bundle(store)
    result = store.query(
        "Return Node-00 using answer-json.", encoder=encoder, thresholds=THRESHOLDS,
    )
    with sqlite3.connect(store.path) as connection:
        connection.execute(
            f"UPDATE {table} SET receipt_json=? WHERE episode_id=? AND {column}=1",
            (canonical_bytes({}), result["episode_id"]),
        )
    with pytest.raises(IntegrityError, match=message):
        store.replay(result["episode_id"], encoder_free=True)
    with pytest.raises(IntegrityError, match=message):
        store.verify()


def test_deterministic_episode_rows_are_immutable(tmp_path):
    store = WorldStore(tmp_path / "immutable-episode.sqlite3")
    encoder, _ = publish_bundle(store)
    prompt = "Return Node-00 using answer-json."
    first = store.query(prompt, encoder=encoder, thresholds=THRESHOLDS)

    def rows():
        with sqlite3.connect(store.path) as connection:
            return (
                connection.execute(
                    "SELECT rowid, * FROM episodes ORDER BY episode_id"
                ).fetchall(),
                connection.execute(
                    "SELECT rowid, * FROM settlement_receipts ORDER BY episode_id, stage_order"
                ).fetchall(),
                connection.execute(
                    "SELECT rowid, * FROM handoff_receipts ORDER BY episode_id, handoff_order"
                ).fetchall(),
            )

    before = rows()
    second = store.query(prompt, encoder=encoder, thresholds=THRESHOLDS)
    assert second == first
    assert rows() == before

    corrupted = canonical_bytes({"corrupted": True})
    with sqlite3.connect(store.path) as connection:
        connection.execute(
            "UPDATE settlement_receipts SET receipt_json=? "
            "WHERE episode_id=? AND stage_order=1",
            (corrupted, first["episode_id"]),
        )
    refusal = store.query(prompt, encoder=encoder, thresholds=THRESHOLDS)
    assert refusal["status"] == "REFUSAL"
    assert refusal["refusal"]["code"] == "INTEGRITY_FAILURE"
    with sqlite3.connect(store.path) as connection:
        assert bytes(connection.execute(
            "SELECT receipt_json FROM settlement_receipts "
            "WHERE episode_id=? AND stage_order=1",
            (first["episode_id"],),
        ).fetchone()[0]) == corrupted


def test_production_4_8_store_is_empty_when_present():
    path = ROOT / "data/store-4.8.sqlite3"
    if not path.exists():
        pytest.skip("production Runtime 4.8 store is initialized at release freeze")
    with sqlite3.connect(f"file:{path}?mode=ro&immutable=1", uri=True) as connection:
        assert connection.execute(
            "SELECT schema_id FROM descriptor WHERE singleton=1"
        ).fetchone()[0] == STORE_SCHEMA
        assert dict(connection.execute(
            "SELECT role, generation_id FROM world_heads ORDER BY role"
        )) == {"INPUT": None, "MAIN": None, "SURFACE": None}
        assert connection.execute(
            "SELECT bundle_id FROM active_bundle WHERE singleton=1"
        ).fetchone()[0] is None
        assert connection.execute("SELECT COUNT(*) FROM world_generations").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM bundles").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM episodes").fetchone()[0] == 0
