from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import sqlite3

import numpy as np
import pytest

from experiments.runtime_v5_2_energy_native_fields.build_artifact import build_artifact
from moth_runtime_v5_0.canonical import canonical_bytes
from moth_runtime_v5_2.artifact import ModelArtifact52
from moth_runtime_v5_2.energy.schema import Level, Runtime52Failure
from moth_runtime_v5_2.persistence.objects import ObjectStore
from moth_runtime_v5_2.runtime import Runtime52
from tests.test_runtime_v5_0_language import DELIVERY


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def artifact(tmp_path_factory: pytest.TempPathFactory) -> Path:
    target = tmp_path_factory.mktemp("runtime-5.2") / "model-5.2"
    receipt = build_artifact(target)
    assert receipt["verified"] is True
    return target


def _runtime(tmp_path: Path, artifact: Path) -> Runtime52:
    return Runtime52.initialize(tmp_path / "store-5.2", artifact)


def _tree_hash(folder: Path) -> str:
    result = hashlib.sha256()
    for path in sorted(folder.rglob("*.py")):
        result.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        result.update(b"\0")
        result.update(hashlib.sha256(path.read_bytes()).digest())
    return result.hexdigest()


def _field(
    runtime: Runtime52,
    *,
    level: Level,
    entries: list[dict] | None = None,
    activations: list[dict] | None = None,
) -> str:
    receipt = runtime.compile_hcf_field(
        {
            "schema": "moth-hcf-source/5.2",
            "entries": entries or [],
            "activations": activations or [],
        },
        level,
    )
    return receipt["object_hash"]


def test_artifact_is_tensor_native_self_contained_and_independent(artifact: Path):
    model = ModelArtifact52.open(artifact)
    receipt = model.verify()
    assert receipt["verified"] is True
    assert receipt["candidate_count"] == 16
    assert receipt["field_count"] == 5
    assert receipt["skill_count"] == 10
    assert set(model.manifest["runtime"]["packages"]) == {
        "moth_runtime_v5_0",
        "moth_runtime_v5_2",
    }
    assert model.manifest["runtime"]["entrypoint"] == "moth_runtime_v5_2.cli:main"
    assert all(
        path.suffix == ".safetensors"
        for path in (artifact / "objects" / "sha256").rglob("*")
        if path.is_file()
    )
    manifest = model.manifest
    assert all("entries" not in item and "properties" not in item for item in manifest["fields"])
    for source in (artifact / "runtime" / "moth_runtime_v5_2").rglob("*.py"):
        tree = ast.parse(source.read_text(encoding="utf-8"))
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
        assert not any(name.startswith("moth_runtime_v5_1") for name in imported)


def test_promoted_architecture_lock_and_artifact_verify():
    lock = json.loads(
        (ROOT / "config/v5.2/ARCHITECTURE-LOCK.json").read_text(encoding="utf-8")
    )
    for group in ("documents", "configuration"):
        for record in lock[group].values():
            assert hashlib.sha256((ROOT / record["path"]).read_bytes()).hexdigest() == record["sha256"]
    assert _tree_hash(ROOT / lock["implementation"]["path"]) == lock["implementation"]["tree_sha256"]
    assert _tree_hash(ROOT / lock["launcher"]["path"]) == lock["launcher"]["tree_sha256"]
    report = lock["qualification"]
    assert hashlib.sha256((ROOT / report["path"]).read_bytes()).hexdigest() == report["sha256"]
    assert report["verdict"] == "ENERGY_NATIVE_MUTABLE_RUNTIME_5_2_CONFIRMED"
    promoted = ModelArtifact52.open(ROOT / "config/v5.2/model/model-5.2")
    assert promoted.verify()["artifact_hash"] == "8652fbbc6842fd3e6781be465055eca8666e4d32a611e97c5513dbfa680ebcf5"


def test_three_clean_builds_are_byte_deterministic(tmp_path: Path):
    hashes = []
    for index in range(3):
        target = tmp_path / f"build-{index}"
        build_artifact(target)
        hashes.append(
            {
                path.relative_to(target).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in target.rglob("*")
                if path.is_file()
            }
        )
    assert hashes[0] == hashes[1] == hashes[2]


def test_tensor_objects_are_read_only_and_fail_closed_on_tamper(tmp_path: Path, artifact: Path):
    runtime = _runtime(tmp_path, artifact)
    array = runtime.energy.tensors["candidate_id"]
    assert array.flags.writeable is False
    with pytest.raises(ValueError):
        array[0, 0] ^= np.uint8(1)

    object_hash = runtime.energy.file_hash
    object_path = runtime.store.objects.path_for(object_hash)
    raw = bytearray(object_path.read_bytes())
    raw[-1] ^= 1
    object_path.write_bytes(raw)
    with pytest.raises(Runtime52Failure) as failure:
        ObjectStore(runtime.store.root).open(object_hash)
    assert failure.value.code == "OBJECT_HASH_MISMATCH"


def test_conversation_parity_replay_and_self_contained_store(tmp_path: Path, artifact: Path):
    copied_artifact = tmp_path / "source-artifact"
    import shutil
    shutil.copytree(artifact, copied_artifact)
    runtime = _runtime(tmp_path, copied_artifact)
    conversation = runtime.create_conversation("Respond in detail.")
    first = runtime.turn(conversation, DELIVERY)
    assert first["status"] == "ANSWER"
    assert first["response_mode"] == "detailed"
    assert first["output"]["value"]["selected-plan"] == "BACKUP"
    assert first["deterministic"]["candidate_dictionary_reconstructions"] == 0
    assert first["replay"]["system_revision_id"]
    second = runtime.turn(conversation, "repeat that.")
    assert second["kernel"]["output"] == first["kernel"]["output"]
    assert second["replay"]["previous_result_hash"] == first["replay"]["result_hash"]
    assert runtime.replay_turn(conversation, first["turn_id"]) == canonical_bytes(first)
    assert runtime.verify_conversation(conversation)["verified"] is True

    shutil.rmtree(copied_artifact)
    reopened = Runtime52.open(runtime.store.root)
    assert reopened.verify_conversation(conversation)["turn_count"] == 2


def test_revisioned_system_and_context_mutation_preserves_old_turns(tmp_path: Path, artifact: Path):
    runtime = _runtime(tmp_path, artifact)
    conversation = runtime.create_conversation("Delegate response.mode to context.")
    first = runtime.turn(conversation, DELIVERY)
    context_object = _field(
        runtime,
        level=Level.CONTEXT,
        entries=[{
            "meaning_id": "context.detailed",
            "effect": "REQUIRE",
            "scope": "response.mode",
            "value": "detailed",
        }],
    )
    revision = runtime.upsert_layer_field(
        conversation, Level.CONTEXT, "detail", context_object, 0
    )
    assert revision["revision_number"] == 1
    second = runtime.turn(conversation, DELIVERY)
    assert second["response_mode"] == "detailed"
    assert first["replay"]["context_revision_id"] != second["replay"]["context_revision_id"]
    assert runtime.replay_turn(conversation, first["turn_id"]) == canonical_bytes(first)
    assert runtime.verify_conversation(conversation)["verified"] is True

    removed = runtime.remove_layer_field(
        conversation, Level.CONTEXT, "detail", 1
    )
    assert removed["revision_number"] == 2
    assert len(runtime.layer_history(conversation, Level.CONTEXT)) == 3
    with pytest.raises(Runtime52Failure) as stale:
        runtime.upsert_layer_field(
            conversation, Level.CONTEXT, "detail", context_object, 1
        )
    assert stale.value.code == "STALE_LAYER_REVISION"


def test_unauthorized_overrides_and_noop_mutations_are_rejected(tmp_path: Path, artifact: Path):
    runtime = _runtime(tmp_path, artifact)
    conversation = runtime.create_conversation("Respond in detail.")
    conflicting = _field(
        runtime,
        level=Level.CONTEXT,
        entries=[{
            "meaning_id": "context.concise",
            "effect": "REQUIRE",
            "scope": "response.mode",
            "value": "concise",
        }],
    )
    with pytest.raises(Runtime52Failure) as unauthorized:
        runtime.upsert_layer_field(
            conversation, Level.CONTEXT, "mode", conflicting, 0
        )
    assert unauthorized.value.code == "UNAUTHORIZED_LAYER_OVERRIDE"
    assert runtime.inspect_layer(conversation, Level.CONTEXT)["revision_number"] == 0

    activation = _field(
        runtime,
        level=Level.CONTEXT,
        activations=[{
            "candidate_id": "surface.detailed",
            "state": "DISABLE",
        }],
    )
    with pytest.raises(Runtime52Failure) as unauthorized_activation:
        runtime.upsert_layer_field(
            conversation, Level.CONTEXT, "activation", activation, 0
        )
    assert unauthorized_activation.value.code == "UNAUTHORIZED_LAYER_OVERRIDE"

    same = runtime.inspect_layer(conversation, Level.SYSTEM)["members"][0]
    with pytest.raises(Runtime52Failure) as noop:
        runtime.upsert_layer_field(
            conversation,
            Level.SYSTEM,
            same["key"],
            same["object_hash"],
            1,
        )
    assert noop.value.code == "NO_LAYER_CHANGE"


def test_redelegable_activation_and_empty_candidate_refusal(tmp_path: Path, artifact: Path):
    runtime = _runtime(tmp_path, artifact)
    conversation = runtime.create_conversation(
        "Delegate candidate.activation to context."
    )
    candidates = [
        runtime.energy.labels[int(index)]
        for index in runtime.energy.tensors["candidate_label_index"]
    ]
    activation = _field(
        runtime,
        level=Level.CONTEXT,
        activations=[
            {"candidate_id": candidate, "state": "DISABLE"}
            for candidate in candidates
        ],
    )
    runtime.upsert_layer_field(
        conversation, Level.CONTEXT, "disable-all", activation, 0
    )
    refused = runtime.turn(conversation, DELIVERY)
    assert refused["status"] == "REFUSAL"
    assert refused["refusal"]["code"] == "NO_CANDIDATE"
    assert refused["kernel"] is None


def test_store_schema_has_no_compiled_json_columns(tmp_path: Path, artifact: Path):
    runtime = _runtime(tmp_path, artifact)
    with sqlite3.connect(runtime.store.catalog) as connection:
        tables = [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )]
        columns = {
            f"{table}.{row[1]}"
            for table in tables
            for row in connection.execute(f"PRAGMA table_info({table})")
        }
    forbidden = ("compiled_json", "policy_json", "candidate_json", "hcf_entries_json")
    assert not any(any(name.endswith(item) for item in forbidden) for name in columns)


def test_runtime_5_1_store_is_rejected(tmp_path: Path):
    old_store = tmp_path / "old.sqlite3"
    old_store.write_bytes(b"SQLite format 3\x00")
    with pytest.raises(Runtime52Failure) as failure:
        Runtime52.open(old_store)
    assert failure.value.code == "STORE_VERSION_MISMATCH"
