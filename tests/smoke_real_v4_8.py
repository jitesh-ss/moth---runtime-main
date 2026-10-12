"""Narrow offline real-encoder smoke for the Runtime 4.8 cascade."""

from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import tempfile

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from moth_runtime_v4_8.encoder import LocalBGEEncoder
from moth_runtime_v4_8.model import WorldRole
from moth_runtime_v4_8.runtime import result_bytes
from moth_runtime_v4_8.store import WorldStore
from moth_runtime_v4_8.canonical import sha256_bytes

ROOT = Path(__file__).resolve().parents[1]
PRIME_47 = ROOT / "data/store-4.7.sqlite3"

SOURCE = """\
Entity "Node-00" is declared.
Entity "Node-01" is declared.
Directional relation "route" maps Entity to Entity and is functional.
Operation "lookup" selects kernel primitive "LOOKUP".
Operation "chain_advance" selects kernel primitive "CHAIN_ADVANCE".
Numeral "1" denotes 1 steps.
Output schema "answer-json" selects kernel schema "ANSWER_WITH_PROOF".
Relation form "route-form" for relation "route" accepts "The route from {SOURCE} leads to {DESTINATION}.".
Instruction "lookup-entity" selects operation "lookup" accepts "Return {ENTITY} using {SCHEMA}.".
Instruction "advance-relation" selects operation "chain_advance" accepts "Starting from {ENTITY}, follow {RELATION} for {NUMERAL} steps using {SCHEMA}.".
Instruction prototype "advance-alt" for instruction "advance-relation" is "Move from {ENTITY} through {RELATION} for {NUMERAL} links using {SCHEMA}.".
The route from "Node-00" leads to "Node-01".
"""

INPUT_SOURCE = SOURCE.replace(
    'The route from "Node-00" leads to "Node-01".\n', "",
)

SURFACE_SOURCE = """\
Operation "realize-semantic-result" selects kernel primitive "REALIZE_SEMANTIC_RESULT".
Instruction "realize-semantic-result" selects operation "realize-semantic-result" accepts "Realize the verified semantic result.".
"""


def main() -> int:
    before_prime = sha256_bytes(PRIME_47.read_bytes())
    encoder = LocalBGEEncoder()
    encoder_receipt = encoder.verify_assets()
    network_attempts = 0
    original_connect = socket.socket.connect

    def blocked_connect(self, address):
        nonlocal network_attempts
        network_attempts += 1
        raise RuntimeError(f"network disabled during Runtime 4.8 smoke: {address}")

    socket.socket.connect = blocked_connect
    try:
        with tempfile.TemporaryDirectory(prefix="moth-4.8-smoke-") as directory:
            store = WorldStore(Path(directory) / "store.sqlite3")
            store.publish(
                WorldRole.INPUT, {"input.moth": INPUT_SOURCE}, encoder=encoder,
            )
            store.publish(
                WorldRole.MAIN, {"main.moth": SOURCE}, encoder=encoder,
            )
            store.publish(
                WorldRole.SURFACE, {"surface.moth": SURFACE_SOURCE}, encoder=encoder,
            )
            bundle = store.activate()
            thresholds = {
                "default": {"score": 0.82, "margin": 0.05},
                "INSTRUCTION": {"score": 0.82, "margin": 0.08},
            }
            exact = store.query(
                "Starting from Node-00, follow route for 1 steps using answer-json.",
                encoder=encoder, thresholds=thresholds,
            )
            paraphrase = store.query(
                "Move from Node-00 through route for 1 links using answer-json.",
                encoder=encoder, thresholds=thresholds,
            )
            for result in (exact, paraphrase):
                assert result["status"] == "ANSWER"
                assert result["output"]["value"]["canonical_name"] == "Node-01"
                assert [row["role"] for row in result["stages"]] == [
                    "INPUT", "MAIN", "SURFACE",
                ]
                assert len(result["handoffs"]) == 2
                assert all(row["settlement"]["violation_count"] == 0 for row in result["stages"])
                assert result["execution"] == {"performed": False, "dispatch_count": 0}
            assert store.replay(exact["episode_id"], encoder_free=True) == result_bytes(exact)
            assert store.verify()["integrity"] == "ok"
            summary = {
                "runtime": "4.8",
                "bundle_id": bundle.bundle_id,
                "encoder": encoder_receipt,
                "exact": exact["output"],
                "paraphrase": paraphrase["output"],
                "settlements": 6,
                "handoffs": 4,
                "network_attempts": network_attempts,
                "execution_performed": False,
                "dispatch_count": 0,
            }
    finally:
        socket.socket.connect = original_connect
    assert network_attempts == 0
    assert sha256_bytes(PRIME_47.read_bytes()) == before_prime
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
