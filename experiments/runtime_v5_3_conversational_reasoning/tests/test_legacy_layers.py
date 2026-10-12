import sqlite3
import pytest
from pathlib import Path
from moth_runtime_v5_3.runtime import Runtime53
from moth_runtime_v5_3.energy.schema import Level,Runtime53Failure
from moth_runtime_v5_3.legacy.canonical import canonical_bytes
from tests.test_runtime_v5_0_language import DELIVERY


def _runtime(tmp_path: Path, artifact: Path) -> Runtime53:
    return Runtime53.initialize(tmp_path / "store-5.3", artifact)

def _field(
    runtime: Runtime53,
    *,
    level: Level,
    entries: list[dict] | None = None,
    activations: list[dict] | None = None,
) -> str:
    receipt = runtime.compile_hcf_field(
        {
            "schema": "moth-hcf-source/5.3",
            "entries": entries or [],
            "activations": activations or [],
        },
        level,
    )
    return receipt["object_hash"]

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
    with pytest.raises(Runtime53Failure) as stale:
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
    with pytest.raises(Runtime53Failure) as unauthorized:
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
    with pytest.raises(Runtime53Failure) as unauthorized_activation:
        runtime.upsert_layer_field(
            conversation, Level.CONTEXT, "activation", activation, 0
        )
    assert unauthorized_activation.value.code == "UNAUTHORIZED_LAYER_OVERRIDE"

    same = runtime.inspect_layer(conversation, Level.SYSTEM)["members"][0]
    with pytest.raises(Runtime53Failure) as noop:
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
