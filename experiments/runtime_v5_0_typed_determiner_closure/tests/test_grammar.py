from copy import deepcopy
import json
from pathlib import Path

import pytest

from moth_runtime_v5_0.model import CompilationError
from experiments.runtime_v5_0_blind_compositional_closure.field import compile_field
from experiments.runtime_v5_0_typed_determiner_closure.grammar import compile_determiner_extension


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "experiments/runtime_v5_0_blind_compositional_closure/fixtures/field-en-1.0.json"
BASE_SHA = "2275ac182e275c021c0587a33b04fc65b2d42a01872d373d4cb13acdbc89a11c"
BASE = compile_field(json.loads(BASE_PATH.read_text()))
EXTENSION = json.loads((HERE / "fixtures/determiner-extension-en-1.0.json").read_text())


def test_extension_compiles_deterministically():
    first = compile_determiner_extension(BASE, EXTENSION, base_field_sha256=BASE_SHA)
    second = compile_determiner_extension(BASE, EXTENSION, base_field_sha256=BASE_SHA)
    assert first == second
    assert first.field_hash != BASE.field_hash
    assert first.payload["noun_phrase_operator"]["maximum_prefixes"] == 1


@pytest.mark.parametrize("mutation", ["base", "prefixes", "roles", "contribution"])
def test_unsafe_extension_mutations_fail(mutation):
    candidate = deepcopy(EXTENSION)
    if mutation == "base":
        candidate["base_field_sha256"] = "0" * 64
    elif mutation == "prefixes":
        candidate["operator"]["maximum_prefixes"] = 2
    elif mutation == "roles":
        candidate["operator"]["roles"] = ["UNKNOWN"]
    else:
        candidate["operator"]["semantic_contribution"] = "DROP_WORDS"
    with pytest.raises(CompilationError):
        compile_determiner_extension(BASE, candidate, base_field_sha256=BASE_SHA)
