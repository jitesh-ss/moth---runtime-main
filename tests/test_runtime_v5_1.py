from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from moth_runtime_v5_0.archive import world_to_archive
from moth_runtime_v5_0.canonical import canonical_bytes, sha256_bytes
from moth_runtime_v5_0.model import IntegrityError, WorldRole
from moth_runtime_v5_0.runtime import query_worlds
from moth_runtime_v5_1.assets import load_foundation
from moth_runtime_v5_1.cli import main as cli_main
from moth_runtime_v5_1.hcf import (
    HcfEffect, HcfFailure, HierarchyLevel,
    compile_system_prompt, entry_from_dict, make_entry, settle_candidates, validate_entries,
    verify_trace,
)
from moth_runtime_v5_1.runtime import Runtime51
from moth_runtime_v5_1.kernel import query_worlds_timed
from moth_runtime_v5_1.store import ConcurrentTurnError

from tests.test_runtime_v5_0_language import DELIVERY, worlds


ROOT = Path(__file__).resolve().parents[1]


def _tree_hash(folder: Path) -> str:
    result = hashlib.sha256()
    for path in sorted(folder.glob("*.py")):
        result.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        result.update(b"\0")
        result.update(hashlib.sha256(path.read_bytes()).digest())
    return result.hexdigest()


def _write_json(path: Path, value) -> bytes:
    raw = canonical_bytes(value)
    path.write_bytes(raw)
    return raw


def development_foundation(tmp_path: Path) -> Path:
    root = tmp_path / "foundation"
    root.mkdir()
    compiled, encoder, _ = worlds("delivery")
    descriptors = {}
    for role in WorldRole:
        filename = f"{role.value.casefold()}.json"
        raw = _write_json(root / filename, world_to_archive(compiled[role]))
        descriptors[role.value] = {
            "path": filename, "sha256": sha256_bytes(raw),
            "generation_id": compiled[role].generation_id,
            "world_hash": compiled[role].world_hash,
        }
    base = json.loads((ROOT / "config/v5.1/base-hcf-en-1.0.json").read_text())
    base_raw = _write_json(root / "base.json", base)
    manifest = {
        "schema": "moth-runtime-foundation/5.1", "runtime": "5.1",
        "hcf_schema": "moth-hcf-field/5.1",
        "base_fields": [{
            "field_id": base["field_id"], "path": "base.json",
            "sha256": sha256_bytes(base_raw),
        }],
        "compiled_worlds": descriptors,
        "encoder": {
            "kind": "DETERMINISTIC", "fingerprint": encoder.fingerprint,
            "thresholds": {},
        },
        "context": {"max_message_tokens": 128, "active_context_tokens": 4096},
        "surface": {"modes": ["concise", "detailed", "structured"]},
    }
    _write_json(root / "runtime-foundation.json", manifest)
    return root


# Compatibility helper name used by the conversation tests below.
development_assets = development_foundation


def test_runtime_5_1_architecture_lock():
    lock = json.loads((ROOT / "config/v5.1/ARCHITECTURE-LOCK.json").read_text())
    for group in ("documents", "configuration"):
        for record in lock[group].values():
            assert hashlib.sha256((ROOT / record["path"]).read_bytes()).hexdigest() == record["sha256"]
    assert _tree_hash(ROOT / lock["implementation"]["path"]) == lock["implementation"]["tree_sha256"]
    assert _tree_hash(ROOT / lock["launcher"]["path"]) == lock["launcher"]["tree_sha256"]
    report = lock["qualification"]
    assert hashlib.sha256((ROOT / report["path"]).read_bytes()).hexdigest() == report["sha256"]
    assert report["verdict"] == "BOUNDED_CONVERSATIONAL_HCF_RUNTIME_CONFIRMED"


def _candidate(name: str, cost: int = 0):
    return {
        "candidate_id": name, "semantic": {"mode": name},
        "properties": {"response.mode": name}, "grounding_cost_units": cost,
    }


def _entry(level, effect, value=None, target=None, redelegable=False):
    return make_entry(
        meaning_id=f"{level.value.lower()}.{effect.value.lower()}.{value or target.value}",
        level=level, effect=effect, scope="response.mode", value=value,
        target_level=target, redelegable=redelegable, source_hash="a" * 64,
    )


def test_hcf_lexicographic_precedence_and_no_numeric_inversion():
    entries = (
        _entry(HierarchyLevel.BASE, HcfEffect.REQUIRE, "concise"),
        _entry(HierarchyLevel.CONTEXT, HcfEffect.REQUIRE, "detailed"),
    )
    with pytest.raises(HcfFailure) as failure:
        settle_candidates([_candidate("concise", 999999), _candidate("detailed", 0)], entries)
    assert failure.value.code == "HCF_CONFLICT"
    trace = failure.value.context["trace"]
    assert trace["winner_id"] == "concise"
    assert trace["winning_energy"]["base_violations"] == 0


def test_explicit_delegation_allows_lower_level_and_trace_verifies():
    entries = (
        _entry(HierarchyLevel.BASE, HcfEffect.REQUIRE, "concise"),
        _entry(HierarchyLevel.BASE, HcfEffect.DELEGATE,
               target=HierarchyLevel.CONTEXT),
        _entry(HierarchyLevel.CONTEXT, HcfEffect.REQUIRE, "detailed"),
    )
    candidates = [_candidate("concise", 1), _candidate("detailed", 0)]
    winner, trace = settle_candidates(candidates, entries)
    assert winner["candidate_id"] == "detailed"
    assert trace["winning_energy"] == {
        "base_violations": 0, "system_violations": 0,
        "context_violations": 0, "grounding_cost_units": 0,
    }
    assert verify_trace(candidates, entries, trace) == winner
    altered = json.loads(canonical_bytes(trace))
    altered["winner_id"] = "concise"
    with pytest.raises(HcfFailure, match="differs from reconstruction"):
        verify_trace(candidates, entries, altered)


def test_same_level_conflict_and_distinct_minimum_refuse():
    with pytest.raises(HcfFailure, match="same-level"):
        validate_entries((
            _entry(HierarchyLevel.SYSTEM, HcfEffect.REQUIRE, "concise"),
            _entry(HierarchyLevel.SYSTEM, HcfEffect.REQUIRE, "detailed"),
        ))
    with pytest.raises(HcfFailure) as failure:
        settle_candidates([_candidate("concise"), _candidate("detailed")], ())
    assert failure.value.code == "AMBIGUOUS_HCF"


def test_bounded_system_prompt_compilation():
    entries = compile_system_prompt(
        "Respond concisely.\nDelegate response.mode to context."
    )
    assert {entry.effect for entry in entries} == {HcfEffect.REQUIRE, HcfEffect.DELEGATE}
    with pytest.raises(HcfFailure) as failure:
        compile_system_prompt("Be magical and infer everything.")
    assert failure.value.code == "UNSUPPORTED_SYSTEM_PROMPT"


def test_foundation_validates_hashes_and_does_not_expose_world_management(tmp_path):
    root = development_foundation(tmp_path)
    foundation = load_foundation(root)
    assert foundation.bundle.generation_for(WorldRole.INPUT) == foundation.worlds[WorldRole.INPUT].generation_id
    assert foundation.foundation_id.startswith("foundation-")
    manifest_path = root / "runtime-foundation.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["context"]["active_context_tokens"] = 2048
    _write_json(manifest_path, manifest)
    # The manifest itself is the root receipt; changing it is valid until a store binds it.
    changed = load_foundation(root)
    assert changed.manifest_hash != foundation.manifest_hash
    # Operational configuration is outside the attached foundation content.
    assert changed.foundation_hash == foundation.foundation_hash


def test_asset_member_tampering_is_rejected(tmp_path):
    root = development_foundation(tmp_path)
    base_path = root / "base.json"
    base_path.write_bytes(base_path.read_bytes() + b" ")
    with pytest.raises(IntegrityError, match="foundation hash mismatch"):
        load_foundation(root)


def test_multiple_base_fields_attach_as_one_foundation_and_weights_are_rejected(tmp_path):
    root = development_foundation(tmp_path)
    extra = {
        "schema": "moth-hcf-base-field/5.1",
        "field_id": "moth-base-hcf-extra/1.0",
        "entries": [{
            "meaning_id": "base.concise-default", "effect": "REQUIRE",
            "scope": "response.mode", "value": "concise",
        }],
    }
    extra_raw = _write_json(root / "base-extra.json", extra)
    manifest_path = root / "runtime-foundation.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["base_fields"].append({
        "field_id": extra["field_id"], "path": "base-extra.json",
        "sha256": sha256_bytes(extra_raw),
    })
    _write_json(manifest_path, manifest)
    foundation = load_foundation(root)
    assert [field.field_id for field in foundation.base_fields] == [
        "moth-base-hcf-en/1.0", "moth-base-hcf-extra/1.0",
    ]
    assert len(foundation.base_entries) == 5

    manifest["weights"] = []
    _write_json(manifest_path, manifest)
    with pytest.raises(IntegrityError, match="manifest schema"):
        load_foundation(root)

    manifest.pop("weights")
    conflicting = {
        "schema": "moth-hcf-base-field/5.1",
        "field_id": "moth-base-hcf-conflict/1.0",
        "entries": [{
            "meaning_id": "base.detailed-default", "effect": "REQUIRE",
            "scope": "response.mode", "value": "detailed",
        }],
    }
    conflict_raw = _write_json(root / "base-conflict.json", conflicting)
    manifest["base_fields"].append({
        "field_id": conflicting["field_id"], "path": "base-conflict.json",
        "sha256": sha256_bytes(conflict_raw),
    })
    _write_json(manifest_path, manifest)
    with pytest.raises(HcfFailure, match="same-level"):
        load_foundation(root)


def test_timed_kernel_is_byte_identical_to_runtime_5_0():
    compiled, encoder, bundle = worlds("delivery")
    expected, expected_receipts, expected_handoffs = query_worlds(
        compiled, bundle, DELIVERY, encoder=encoder,
    )
    observed, receipts, handoffs, timings = query_worlds_timed(
        compiled, bundle, DELIVERY, encoder=encoder,
    )
    assert canonical_bytes(observed) == canonical_bytes(expected)
    assert receipts == expected_receipts
    assert handoffs == expected_handoffs
    assert set(timings) == {
        "bundle_verification_ns", "input_grounding_ns", "input_settlement_ns",
        "input_main_handoff_ns", "main_settlement_ns", "main_surface_handoff_ns",
        "surface_settlement_ns",
    }


def test_conversation_continuity_context_replay_and_verification(tmp_path):
    assets = development_assets(tmp_path)
    runtime = Runtime51.initialize(tmp_path / "store-5.1.sqlite3", assets)
    conversation_id = runtime.create_conversation("Respond in detail.")
    first = runtime.turn(conversation_id, DELIVERY)
    assert first["status"] == "ANSWER"
    assert first["response_mode"] == "detailed"
    assert "verified FACTOR_RESULT" in first["response"]

    second = runtime.turn(conversation_id, "repeat that.")
    assert second["status"] == "ANSWER"
    assert second["kernel"]["output"] == first["kernel"]["output"]
    assert second["context"]["selected_message_ids"]
    assert second["replay"]["previous_result_hash"] == first["replay"]["result_hash"]
    assert runtime.replay_turn(conversation_id, second["turn_id"]) == canonical_bytes(second)
    context_view = runtime.inspect_context(conversation_id, second["turn_id"])
    assert any(item["content"] == "repeat that." for item in context_view["messages"])
    hcf_view = runtime.inspect_hcf(conversation_id, second["turn_id"])
    assert {item["level"] for item in hcf_view["entries"]} == {"BASE", "SYSTEM", "CONTEXT"}
    assert "input_settlement_ns" in runtime.store.metrics(second["turn_id"])["timings_ns"]
    verified = runtime.verify_conversation(conversation_id)
    assert verified["verified"] is True
    assert verified["turn_count"] == 2
    assert len(runtime.store.messages(conversation_id)) == 5


def test_context_conflict_refuses_before_kernel_and_sessions_do_not_leak(tmp_path):
    runtime = Runtime51.initialize(tmp_path / "store.sqlite3", development_assets(tmp_path))
    first_session = runtime.create_conversation("Respond concisely.")
    refused = runtime.turn(first_session, "Please respond in detail about this request.")
    assert refused["status"] == "REFUSAL"
    assert refused["refusal"]["code"] == "HCF_CONFLICT"
    assert refused["kernel"] is None
    assert runtime.verify_conversation(first_session)["verified"] is True

    second_session = runtime.create_conversation("")
    accepted = runtime.turn(second_session, DELIVERY)
    assert accepted["status"] == "ANSWER"
    assert accepted["deterministic"]["stored_message_count_before_turn"] == 1


def test_store_rejects_changed_assets_and_older_store(tmp_path):
    root = development_assets(tmp_path)
    store_path = tmp_path / "store.sqlite3"
    Runtime51.initialize(store_path, root)
    manifest = json.loads((root / "runtime-foundation.json").read_text())
    manifest["context"]["active_context_tokens"] = 2048
    _write_json(root / "runtime-foundation.json", manifest)
    with pytest.raises(IntegrityError, match="foundation mismatch"):
        Runtime51.open(store_path)


def test_mandatory_reference_overflow_refuses_but_preserves_messages(tmp_path):
    root = development_assets(tmp_path)
    manifest_path = root / "runtime-foundation.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["context"] = {"max_message_tokens": 5, "active_context_tokens": 5}
    _write_json(manifest_path, manifest)
    runtime = Runtime51.initialize(tmp_path / "limited.sqlite3", root)
    conversation_id = runtime.create_conversation("")
    runtime.turn(conversation_id, "one two three four five")
    refused = runtime.turn(conversation_id, "@turn:1")
    assert refused["status"] == "REFUSAL"
    assert refused["refusal"]["code"] == "CONTEXT_LIMIT"
    assert len(runtime.store.messages(conversation_id)) == 5


def test_stale_conversation_head_and_system_tampering_fail_closed(tmp_path):
    runtime = Runtime51.initialize(tmp_path / "store.sqlite3", development_assets(tmp_path))
    conversation_id = runtime.create_conversation("Respond concisely.")
    result = runtime.turn(conversation_id, DELIVERY)
    messages = runtime.store.messages(conversation_id)
    user = next(item for item in messages if item["role"] == "USER")
    assistant = next(item for item in messages if item["role"] == "ASSISTANT")
    with pytest.raises(ConcurrentTurnError):
        runtime.store.append_turn(
            conversation_id=conversation_id, expected_head=0,
            user_message=user, assistant_content=assistant["content"],
            assistant_entries=tuple(entry_from_dict(item) for item in assistant["hcf_entries"]),
            result=result, context_receipt=result["context"], hcf_trace=result["hcf"],
            kernel_result=result["kernel"], metrics=runtime.store.metrics(result["turn_id"]),
        )

    import sqlite3
    with sqlite3.connect(runtime.store.path) as connection:
        connection.execute(
            "UPDATE conversations SET system_prompt='Respond in detail.' WHERE conversation_id=?",
            (conversation_id,),
        )
    with pytest.raises(IntegrityError, match="system layer hash"):
        runtime.verify_conversation(conversation_id)


def test_console_lifecycle(tmp_path, capsys):
    assets = development_assets(tmp_path)
    store = tmp_path / "console.sqlite3"
    system = tmp_path / "system.txt"
    system.write_text("Respond concisely.\n", encoding="utf-8")
    assert cli_main(["--store", str(store), "init", "--foundation", str(assets)]) == 0
    assert cli_main(["--store", str(store), "session", "create", "--system", str(system)]) == 0
    output = capsys.readouterr().out.strip().splitlines()
    created = json.loads(output[-1])
    assert cli_main(["--store", str(store), "turn", created["conversation_id"], DELIVERY]) == 0
    assert "BACKUP" in capsys.readouterr().out
    assert cli_main(["--store", str(store), "inspect", "foundation"]) == 0
    inspected = json.loads(capsys.readouterr().out)
    assert inspected["foundation_id"].startswith("foundation-")
