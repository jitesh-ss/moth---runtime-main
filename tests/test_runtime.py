from __future__ import annotations

import json
import hashlib
from pathlib import Path
import sqlite3

import pytest

from moth_runtime.canonical import canonical_bytes, normalize_text
from moth_runtime.compiler import compile_sources
from moth_runtime.encoder import DeterministicEncoder
from moth_runtime.model import MeaningType
from moth_runtime.runtime import query, result_bytes
from moth_runtime.store import CapabilityStore, STORE_SCHEMA


ROOT = Path(__file__).resolve().parents[1]
WORLD = ROOT / "tests/fixtures/world.moth"
PYTHON = ROOT / "tests/fixtures/python"


@pytest.fixture(scope="module")
def compiled():
    encoder = DeterministicEncoder()
    field = compile_sources(
        {"world.moth": WORLD.read_text(encoding="utf-8")},
        encoder=encoder,
        capability_level="L8",
        code_root=PYTHON,
    )
    return field, encoder


def test_standalone_identity_and_source_order():
    encoder = DeterministicEncoder()
    source = WORLD.read_text(encoding="utf-8")
    first = compile_sources({"world.moth": source, "empty.moth": "# empty\n"}, encoder=encoder)
    second = compile_sources({"empty.moth": "# empty\n", "world.moth": source}, encoder=encoder)
    assert normalize_text(" cafe\u0301 ") == "café"
    assert first.field_hash == second.field_hash
    package = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "src/moth_runtime").glob("*.py"))
    assert "/Users/jitesh-ss/work/ltm/moth" not in package
    assert "live.experiments" not in package
    lock = json.loads((ROOT / "config/ARCHITECTURE-LOCK.json").read_text(encoding="utf-8"))
    assert lock["architecture"]["sha256"] == hashlib.sha256((ROOT / "ARCHITECTURE.md").read_bytes()).hexdigest()
    assert lock["product"]["sha256"] == hashlib.sha256((ROOT / "PRODUCT.md").read_bytes()).hexdigest()


def test_directional_depth_and_closed_world_refusal(compiled):
    field, encoder = compiled
    result = query(field, "Starting from Node-00, follow route for 8 steps using answer-json.", encoder=encoder)
    assert result["status"] == "ANSWER"
    assert result["output"]["value"]["canonical_name"] == "Node-08"
    assert len(result["proof"]["semantic_edge_ids"]) == 8
    assert result["energy"]["violation_count"] == 0
    refused = query(field, "Return Never-Compiled using answer-json.", encoder=encoder)
    assert refused["status"] == "REFUSAL"
    assert refused["refusal"]["code"] == "UNKNOWN_ENTITY"


def test_compiled_json_and_inert_tool_plan(compiled):
    field, encoder = compiled
    rendered = query(
        field,
        "Render basic-payload with message = message-alpha, count = count-one using compiled-json.",
        encoder=encoder,
    )
    assert rendered["output"]["value"] == {"count": 1, "message": "alpha"}
    tool = query(
        field,
        "Plan tool reporter with message = message-alpha, count = count-one using compiled-json.",
        encoder=encoder,
    )
    assert tool["status"] == "ANSWER"
    assert tool["execution"] == {"performed": False, "dispatch_count": 0}
    assert "execute" not in json.dumps(tool["output"])


def test_patch_plan_is_hash_bound_and_non_mutating(compiled):
    field, encoder = compiled
    source = PYTHON / "sample_app.py"
    before = source.read_bytes()
    span = next(
        item
        for item in field.by_kind(MeaningType.CODE_SPAN)
        if field.meanings[str(item.payload["symbol_id"])].name == "sample_app.format_name"
    )
    result = query(
        field,
        f"Build replace-symbol for {span.name} with replacement-function using patch-json.",
        encoder=encoder,
    )
    assert result["status"] == "ANSWER"
    assert result["output"]["kind"] == "PATCH_PLAN"
    assert result["execution"] == {"performed": False, "dispatch_count": 0}
    assert source.read_bytes() == before


def test_store_replay_is_byte_exact(tmp_path):
    encoder = DeterministicEncoder()
    store = CapabilityStore(tmp_path / "disposable.sqlite3")
    store.publish(
        {"world.moth": WORLD.read_text(encoding="utf-8")},
        encoder=encoder,
        capability_level="L8",
        code_root=PYTHON,
    )
    result = store.query("Return Node-00 using answer-json.", encoder=encoder)
    assert store.replay(result["episode_id"], encoder_free=True) == result_bytes(result)
    assert store.verify()["schema"] == STORE_SCHEMA


def test_new_production_field_initializes_empty(tmp_path):
    path = tmp_path / "fresh.sqlite3"
    CapabilityStore(path).init()
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT schema_id FROM descriptor WHERE singleton=1").fetchone()[0] == STORE_SCHEMA
        assert connection.execute("SELECT generation_id FROM head WHERE singleton=1").fetchone()[0] is None
        assert connection.execute("SELECT COUNT(*) FROM generations").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM episodes").fetchone()[0] == 0
