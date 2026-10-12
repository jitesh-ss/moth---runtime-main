from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from moth_runtime_v4_9.canonical import canonical_bytes

from experiments.runtime_v4_9_compositional_language.compiler import (
    FIXTURE,
    compile_contract,
    load_contract,
)
from experiments.runtime_v4_9_compositional_language.input_world import (
    make_handoff,
    settle_input,
    verify_handoff,
)
from experiments.runtime_v4_9_compositional_language.model import (
    LanguageRefusal,
    LanguageRefusalCode,
)
from experiments.runtime_v4_9_compositional_language.runtime import build_runtime

ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = Path(__file__).resolve().parents[1]
CASES_PATH = EXPERIMENT / "fixtures/cases-en-1.0.json"
RUNTIME_HASH = "3ddad5a0f486179c3a9d56665bdbd1aeb1f770a660bcaf7828a490c7746beccb"
ATTEMPT_001_HASH = "e1b92641fc6dddc642977e32b4278f19d3da986083647ee6ec911ba3930404a3"


@pytest.fixture(scope="session")
def contract():
    return load_contract()


@pytest.fixture(scope="session")
def runtime():
    return build_runtime()


@pytest.fixture(scope="session")
def cases():
    return json.loads(CASES_PATH.read_text(encoding="utf-8"))


def runtime_hash() -> str:
    completed = subprocess.run(
        [
            "git", "ls-files", "src/moth_runtime", "src/moth_runtime_v4_8",
            "src/moth_runtime_v4_9", "config/v4.8", "config/v4.9", "docs/v4.8", "docs/v4.9",
        ], cwd=ROOT, check=True, capture_output=True, text=True,
    )
    payload = bytearray()
    for relative in sorted(completed.stdout.splitlines()):
        digest = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        payload.extend(f"{digest}  {relative}\n".encode())
    return hashlib.sha256(payload).hexdigest()


def attempt_001_hash() -> str:
    folder = ROOT / "experiments/runtime_v4_9_semantic_equivalence"
    paths = [
        path for path in folder.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and "runs" not in path.parts
    ]
    payload = bytearray()
    for path in sorted(paths):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        payload.extend(f"{digest}  {path.relative_to(ROOT).as_posix()}\n".encode())
    return hashlib.sha256(payload).hexdigest()


def test_contract_is_deterministic_and_protected_inputs_are_unchanged(contract):
    rebuilt = compile_contract(json.loads(FIXTURE.read_text(encoding="utf-8")))
    assert canonical_bytes(rebuilt.canonical()) == canonical_bytes(contract.canonical())
    assert rebuilt.contract_hash == contract.contract_hash
    assert runtime_hash() == RUNTIME_HASH
    assert attempt_001_hash() == ATTEMPT_001_HASH


def test_all_frozen_accepted_prompts(runtime, cases):
    for case in cases["accepted"]:
        result = runtime.query(case["prompt"])
        assert result["input"]["domain"] == case["domain"], case["id"]
        assert result["surface"]["value"] == case["expected"], case["id"]
        assert result["main"]["factor_energy"]["total_units"] == 0, case["id"]
        assert result["main"]["violation_count"] == 0, case["id"]
        runtime.verify_result(case["prompt"], result)


def test_all_frozen_refusals(runtime, cases):
    for case in cases["refusals"]:
        with pytest.raises(LanguageRefusal) as captured:
            runtime.query(case["prompt"])
        assert captured.value.code.value == case["expected_refusal"], case["id"]


def test_equivalent_prompts_settle_same_fact_graph_and_main_value(runtime, cases):
    grouped: dict[str, list[dict]] = {}
    for case in cases["accepted"]:
        if group := case.get("equivalence_group"):
            grouped.setdefault(group, []).append(runtime.query(case["prompt"]))
    assert grouped
    for results in grouped.values():
        fact_graphs = {canonical_bytes(item["input"]["facts"]) for item in results}
        outputs = {canonical_bytes(item["surface"]["value"]) for item in results}
        assert len(fact_graphs) == 1
        assert len(outputs) == 1


def test_one_generic_main_world_serves_both_domains(runtime, cases):
    generation_ids = {
        runtime.query(case["prompt"])["main"]["generation_id"]
        for case in cases["accepted"]
    }
    world_hashes = {
        runtime.query(case["prompt"])["main"]["world_hash"]
        for case in cases["accepted"]
    }
    assert len(generation_ids) == 1
    assert len(world_hashes) == 1


def test_anaphora_intent_and_complete_fact_graph_are_causal(contract, cases):
    pronoun_case = next(case for case in cases["accepted"] if case["id"] == "d02-resource-repair-pronouns")
    with pytest.raises(LanguageRefusal) as anaphora:
        settle_input(contract, pronoun_case["prompt"], enable_anaphora=False)
    assert anaphora.value.code == LanguageRefusalCode.AMBIGUOUS_REFERENCE

    without_intents = replace(contract, intent_surfaces=())
    with pytest.raises(LanguageRefusal) as intent:
        settle_input(without_intents, cases["accepted"][0]["prompt"])
    assert intent.value.code == LanguageRefusalCode.UNSUPPORTED_INTENT

    missing_case = next(case for case in cases["refusals"] if case["id"] == "r02-missing-fact")
    with pytest.raises(LanguageRefusal) as missing:
        settle_input(contract, missing_case["prompt"])
    assert missing.value.code == LanguageRefusalCode.INCOMPLETE_FACT_GRAPH


def test_handoff_and_result_tampering_are_rejected(contract, runtime, cases):
    case = cases["accepted"][0]
    input_settlement = settle_input(contract, case["prompt"])
    handoff = make_handoff(input_settlement)
    altered_bindings = dict(handoff.bindings)
    altered_bindings["proposed-resource"] = "yes"
    forged_handoff = replace(handoff, bindings=altered_bindings)
    with pytest.raises(LanguageRefusal) as handoff_error:
        verify_handoff(input_settlement, forged_handoff)
    assert handoff_error.value.code == LanguageRefusalCode.INTEGRITY_FAILURE

    result = runtime.query(case["prompt"])
    forged_result = json.loads(json.dumps(result))
    forged_result["surface"]["value"]["selected-plan"] = "PROPOSED"
    with pytest.raises(LanguageRefusal) as result_error:
        runtime.verify_result(case["prompt"], forged_result)
    assert result_error.value.code == LanguageRefusalCode.INTEGRITY_FAILURE


def test_repeated_results_are_byte_identical(runtime, cases):
    for case in cases["accepted"]:
        first = runtime.query(case["prompt"])
        second = runtime.query(case["prompt"])
        assert canonical_bytes(first) == canonical_bytes(second), case["id"]
