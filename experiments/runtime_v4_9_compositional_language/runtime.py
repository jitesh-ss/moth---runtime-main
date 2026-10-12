"""End-to-end semantic Input -> Runtime 4.9 Main -> Surface cascade."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from moth_runtime_v4_9.canonical import canonical_bytes, digest

from .compiler import load_contract
from .input_world import make_handoff, settle_input, verify_handoff, verify_input
from .main_world import compile_main_world, settle_main
from .model import LanguageContract, LanguageRefusal, LanguageRefusalCode


RESULT_SCHEMA = "moth-compositional-language-result/1.0"


@dataclass
class CompositionalRuntime:
    contract: LanguageContract

    def __post_init__(self) -> None:
        self.main_world, self.main_encoder = compile_main_world()

    def query(self, prompt: str) -> dict[str, Any]:
        input_settlement = settle_input(self.contract, prompt)
        verify_input(self.contract, prompt, input_settlement)
        handoff = make_handoff(input_settlement)
        verify_handoff(input_settlement, handoff)
        main = settle_main(self.main_world, self.main_encoder, handoff)
        if main.factor_evidence is None:
            raise LanguageRefusal(LanguageRefusalCode.INTEGRITY_FAILURE, "Main omitted factor evidence", {})
        surface_value = main.output
        main_record = {
            "generation_id": self.main_world.generation_id,
            "world_hash": self.main_world.world_hash,
            "output": surface_value,
            "violation_count": main.violation_count,
            "proof_count": main.proof_count,
            "factor_trace_hash": main.factor_evidence["trace_hash"],
            "factor_energy": main.factor_evidence["energy"],
            "semantic_hash": digest("moth-compositional-main-semantic/1.0", surface_value),
        }
        surface = {
            "kind": "DECISION_RESULT",
            "value": surface_value,
            "semantic_hash": main_record["semantic_hash"],
        }
        result = {
            "schema": RESULT_SCHEMA,
            "status": "ANSWER",
            "contract_hash": self.contract.contract_hash,
            "input": input_settlement.canonical(),
            "handoff": handoff.canonical(),
            "main": main_record,
            "surface": surface,
            "execution": {"performed": False, "dispatch_count": 0},
        }
        result["result_hash"] = digest("moth-compositional-language-result/1.0", result)
        return result

    def verify_result(self, prompt: str, candidate: dict[str, Any]) -> None:
        claimed = dict(candidate)
        result_hash = claimed.pop("result_hash", None)
        if result_hash != digest("moth-compositional-language-result/1.0", claimed):
            raise LanguageRefusal(LanguageRefusalCode.INTEGRITY_FAILURE, "cascade result hash changed", {})
        expected = self.query(prompt)
        if canonical_bytes(expected) != canonical_bytes(candidate):
            raise LanguageRefusal(LanguageRefusalCode.INTEGRITY_FAILURE, "cascade result differs from reconstruction", {})


def build_runtime() -> CompositionalRuntime:
    return CompositionalRuntime(load_contract())


def query(prompt: str) -> dict[str, Any]:
    return build_runtime().query(prompt)
