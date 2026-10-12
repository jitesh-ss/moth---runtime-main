from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from moth_runtime_v4_9.canonical import canonical_bytes
from moth_runtime_v4_9.encoder import LocalBGEEncoder

from experiments.runtime_v4_9_semantic_equivalence.compiler import (
    FIXTURE,
    compile_semantic_world,
    load_semantic_world,
)
from experiments.runtime_v4_9_semantic_equivalence.downstream import (
    compile_downstream_world,
    settle_downstream,
)
from experiments.runtime_v4_9_semantic_equivalence.model import (
    SemanticRefusal,
    SemanticRefusalCode,
)
from experiments.runtime_v4_9_semantic_equivalence.reference import verify_against_compiled_world
from experiments.runtime_v4_9_semantic_equivalence.settlement import (
    forged_trace,
    settle_internal,
    settle_text,
    verify_settlement,
)

ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = Path(__file__).resolve().parents[1]
CASES = EXPERIMENT / "fixtures/cases-en-1.0.json"
PROTECTED_HASH = "3ddad5a0f486179c3a9d56665bdbd1aeb1f770a660bcaf7828a490c7746beccb"


@pytest.fixture(scope="session")
def world():
    return load_semantic_world()


@pytest.fixture(scope="session")
def cases():
    return json.loads(CASES.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def encoder():
    value = LocalBGEEncoder()
    assert value.verify_assets()["verified"] is True
    return value


def meaning_ids(world):
    return {item.key: item.meaning_id for item in world.meanings}


def protected_tree_hash() -> str:
    completed = subprocess.run(
        [
            "git", "ls-files", "src/moth_runtime", "src/moth_runtime_v4_8",
            "src/moth_runtime_v4_9", "config/v4.8", "config/v4.9", "docs/v4.8", "docs/v4.9",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = bytearray()
    for relative in sorted(completed.stdout.splitlines()):
        file_hash = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        payload.extend(f"{file_hash}  {relative}\n".encode("utf-8"))
    return hashlib.sha256(payload).hexdigest()


def test_compilation_is_deterministic_and_runtime_is_preserved(world):
    source = json.loads(FIXTURE.read_text(encoding="utf-8"))
    rebuilt = compile_semantic_world(source)
    assert canonical_bytes(rebuilt.canonical()) == canonical_bytes(world.canonical())
    assert rebuilt.world_hash == world.world_hash
    assert protected_tree_hash() == PROTECTED_HASH


def test_all_frozen_text_cases(world, cases, encoder):
    ids = meaning_ids(world)
    for case in cases["text_cases"]:
        if "expected_meaning" in case:
            result = settle_text(world, case["text"], encoder=encoder)
            assert result.meaning_id == ids[case["expected_meaning"]], case["id"]
            verify_settlement(world, result, text=case["text"], encoder=encoder)
            verify_against_compiled_world(world, result)
        else:
            with pytest.raises(SemanticRefusal) as captured:
                settle_text(world, case["text"], encoder=encoder)
            assert captured.value.code.value == case["expected_refusal"], case["id"]


def test_all_frozen_internal_cases_use_same_canonical_meanings(world, cases):
    ids = meaning_ids(world)
    for case in cases["internal_cases"]:
        if "expected_meaning" in case:
            result = settle_internal(world, case["observation"])
            assert result.meaning_id == ids[case["expected_meaning"]], case["id"]
            verify_settlement(world, result, observation=case["observation"])
            verify_against_compiled_world(world, result)
        else:
            with pytest.raises(SemanticRefusal) as captured:
                settle_internal(world, case["observation"])
            assert captured.value.code.value == case["expected_refusal"], case["id"]


def test_text_and_internal_equivalence_converge(world, encoder):
    texts = [
        "Direct courier lacks cold storage.",
        "The proposed courier does not have refrigerated storage.",
        "Refrigeration is unavailable to the direct carrier.",
        "The primary delivery operator lacks cold-chain equipment.",
    ]
    observations = [
        {"relation": "LACKS", "arguments": {"holder": "direct-courier", "capability": "cold-storage"}},
        {"relation": "CAPABILITY_UNAVAILABLE_TO", "arguments": {"capability": "cold-storage", "recipient": "direct-courier"}},
        {"relation": "HAS_CAPABILITY_NEGATIVE", "arguments": {"subject": "direct-courier", "object": "cold-storage"}},
    ]
    text_ids = {settle_text(world, text, encoder=encoder).meaning_id for text in texts}
    internal_ids = {settle_internal(world, item).meaning_id for item in observations}
    assert len(text_ids) == 1
    assert text_ids == internal_ids


def test_encoder_is_candidate_prior_not_semantic_authority(world, encoder):
    target = settle_text(world, "The primary delivery operator lacks cold-chain equipment.", encoder=encoder)
    assert target.trace["observations"][0]["subject"]["candidates"][0]["method"] == "vector"
    assert target.trace["observations"][0]["object"]["candidates"][0]["method"] == "vector"
    opposite = settle_text(world, "The direct courier has cold storage.", encoder=encoder)
    assert target.meaning_id != opposite.meaning_id
    assert target.coordinate.polarity == "NEGATIVE"
    assert opposite.coordinate.polarity == "POSITIVE"


def test_semantic_prior_ablation_breaks_unseen_surface_only(world):
    with pytest.raises(SemanticRefusal) as captured:
        settle_text(world, "The primary delivery operator lacks cold-chain equipment.", encoder=None)
    assert captured.value.code == SemanticRefusalCode.UNKNOWN_ENTITY
    exact = settle_text(world, "The proposed courier lacks refrigeration.", encoder=None)
    assert exact.coordinate.subject == "direct-courier"


def test_polarity_role_and_internal_transform_are_causal(world):
    lacks_frame = next(item for item in world.frames if item.key == "subject-lacks-object")
    altered_frames = tuple(
        replace(item, polarity="POSITIVE") if item.frame_id == lacks_frame.frame_id else item
        for item in world.frames
    )
    altered_world = replace(world, frames=altered_frames)
    altered = settle_text(altered_world, "Direct courier lacks cold storage.")
    assert altered.coordinate.polarity == "POSITIVE"

    with pytest.raises(SemanticRefusal) as reversed_roles:
        settle_text(world, "Cold storage lacks the direct courier.")
    assert reversed_roles.value.code == SemanticRefusalCode.TYPE_MISMATCH

    without_transforms = replace(world, transforms=())
    with pytest.raises(SemanticRefusal) as missing_transform:
        settle_internal(without_transforms, {
            "relation": "LACKS",
            "arguments": {"holder": "direct-courier", "capability": "cold-storage"},
        })
    assert missing_transform.value.code == SemanticRefusalCode.UNSUPPORTED_MEANING


def test_trace_tampering_is_rejected(world):
    result = settle_text(world, "Direct courier lacks cold storage.")
    trace = json.loads(json.dumps(result.trace))
    trace["selection"]["total_energy_units"] += 1
    forged = forged_trace(result, trace)
    with pytest.raises(SemanticRefusal) as captured:
        verify_settlement(world, forged, text="Direct courier lacks cold storage.")
    assert captured.value.code == SemanticRefusalCode.INTEGRITY_FAILURE


def test_repeated_settlement_is_byte_identical(world, encoder):
    text = "The primary delivery operator lacks cold-chain equipment."
    first = settle_text(world, text, encoder=encoder)
    second = settle_text(world, text, encoder=encoder)
    assert canonical_bytes(first.canonical()) == canonical_bytes(second.canonical())


def test_equivalent_text_and_internal_meanings_drive_same_unmodified_v4_9_factor(world, encoder):
    downstream, deterministic = compile_downstream_world()
    text_forms = [
        "Direct courier lacks cold storage.",
        "The proposed courier does not have refrigerated storage.",
        "Refrigeration is unavailable to the direct carrier.",
        "The primary delivery operator lacks cold-chain equipment.",
    ]
    internal_forms = [
        {"relation": "LACKS", "arguments": {"holder": "direct-courier", "capability": "cold-storage"}},
        {"relation": "CAPABILITY_UNAVAILABLE_TO", "arguments": {"capability": "cold-storage", "recipient": "direct-courier"}},
    ]
    keys = {item.meaning_id: item.key for item in world.meanings}
    semantic_results = [settle_text(world, text, encoder=encoder) for text in text_forms]
    semantic_results += [settle_internal(world, item) for item in internal_forms]
    downstream_results = [
        settle_downstream(downstream, deterministic, keys[result.meaning_id])
        for result in semantic_results
    ]
    assert {result.output for result in downstream_results} == {"PLAN_INVALID"}
    assert all(result.factor_evidence["energy"]["total_units"] == 0 for result in downstream_results)

    opposite = settle_text(world, "The direct courier has cold storage.", encoder=encoder)
    opposite_result = settle_downstream(downstream, deterministic, keys[opposite.meaning_id])
    assert opposite_result.output == "PLAN_VALID"
