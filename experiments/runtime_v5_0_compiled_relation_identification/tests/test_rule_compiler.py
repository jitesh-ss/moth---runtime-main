from copy import deepcopy
import json
from pathlib import Path

import pytest

from moth_runtime_v5_0.model import CompilationError
from tests.test_runtime_v5_0_language import semantic_contract

from experiments.runtime_v5_0_compiled_relation_identification.rule_compiler import (
    compile_relation_identification,
)


HERE = Path(__file__).resolve().parents[1]
RULES = json.loads((HERE / "fixtures/relation-identification-en-1.0.json").read_text())


def test_rules_compile_deterministically_to_six_frames():
    first, first_manifest = compile_relation_identification(semantic_contract("delivery"), RULES)
    second, second_manifest = compile_relation_identification(semantic_contract("delivery"), RULES)
    assert first == second
    assert first_manifest == second_manifest
    original = semantic_contract("delivery")["predicates"][0]["frames"]
    assert len(first["predicates"][0]["frames"]) == len(original) + 6


@pytest.mark.parametrize("mutation", ["roles", "coordinates", "template"])
def test_unsafe_rules_fail_atomically(mutation):
    candidate = deepcopy(RULES)
    if mutation == "roles":
        candidate["subject_roles"] = ["RESOURCE"]
    elif mutation == "coordinates":
        candidate["coordinates"]["modality"] = "POSSIBLE"
    else:
        candidate["rules"][0]["construction"] = "{OBJECT} is missing {SUBJECT}"
    with pytest.raises(CompilationError):
        compile_relation_identification(semantic_contract("delivery"), candidate)
