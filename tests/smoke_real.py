"""One bounded real-BGE end-to-end smoke workflow."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import socket
import sqlite3
import tempfile

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from moth_runtime.encoder import LocalBGEEncoder
from moth_runtime.model import MeaningType
from moth_runtime.runtime import result_bytes
from moth_runtime.store import CapabilityStore, STORE_SCHEMA


ROOT = Path(__file__).resolve().parents[1]
WORLD = ROOT / "tests/fixtures/world.moth"
PYTHON = ROOT / "tests/fixtures/python"


def main() -> int:
    def blocked(*_args, **_kwargs):
        raise RuntimeError("network access is forbidden during Runtime 4.7 smoke verification")

    socket.create_connection = blocked
    socket.socket.connect = blocked
    encoder = LocalBGEEncoder()
    assets = encoder.verify_assets()
    python_before = hashlib.sha256((PYTHON / "sample_app.py").read_bytes()).hexdigest()

    with tempfile.TemporaryDirectory(prefix="moth-4.7-smoke-") as directory:
        store = CapabilityStore(Path(directory) / "smoke.sqlite3")
        field = store.publish(
            {"world.moth": WORLD.read_text(encoding="utf-8")},
            encoder=encoder,
            capability_level="L8",
            code_root=PYTHON,
        )
        exact = store.query(
            "Starting from Node-00, follow route for 8 steps using answer-json.",
            encoder=encoder,
        )
        paraphrase = store.query(
            "Move from Node-00 through route for 8 links using answer-json.",
            encoder=encoder,
        )
        structured = store.query(
            "Render basic-payload with message = message-alpha, count = count-one using compiled-json.",
            encoder=encoder,
        )
        tool = store.query(
            "Plan tool reporter with message = message-alpha, count = count-one using compiled-json.",
            encoder=encoder,
        )
        span = next(
            item
            for item in field.by_kind(MeaningType.CODE_SPAN)
            if field.meanings[str(item.payload["symbol_id"])].name == "sample_app.format_name"
        )
        patch = store.query(
            f"Build replace-symbol for {span.name} with replacement-function using patch-json.",
            encoder=encoder,
        )
        replay = store.replay(exact["episode_id"], encoder_free=True)

        assert exact["output"]["value"]["canonical_name"] == "Node-08"
        assert paraphrase["grounded_program"]["slots"] == exact["grounded_program"]["slots"]
        assert structured["output"]["value"] == {"count": 1, "message": "alpha"}
        assert exact["energy"]["violation_count"] == 0
        assert exact["proof"]["proof_count"] == 1
        assert len(exact["proof"]["provenance"]) == 8
        assert replay == result_bytes(exact)
        assert tool["execution"] == patch["execution"] == {"performed": False, "dispatch_count": 0}
        assert hashlib.sha256((PYTHON / "sample_app.py").read_bytes()).hexdigest() == python_before
        assert store.verify()["schema"] == STORE_SCHEMA

    with tempfile.TemporaryDirectory(prefix="moth-4.7-fresh-") as directory:
        fresh = Path(directory) / "production.sqlite3"
        CapabilityStore(fresh).init()
        with sqlite3.connect(fresh) as connection:
            assert connection.execute("SELECT generation_id FROM head WHERE singleton=1").fetchone()[0] is None
            assert connection.execute("SELECT COUNT(*) FROM generations").fetchone()[0] == 0
            assert connection.execute("SELECT COUNT(*) FROM episodes").fetchone()[0] == 0

    report = {
        "schema": "moth-standalone-smoke/4.7",
        "status": "PASS",
        "encoder": assets,
        "endpoint": "Node-08",
        "proof_edges": 8,
        "canonical_json": structured["output"]["value"],
        "encoder_free_replay": True,
        "execution_performed": False,
        "dispatch_count": 0,
        "network_allowed": False,
        "production_field_empty": True,
    }
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
