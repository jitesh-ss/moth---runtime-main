from copy import deepcopy
import json
from pathlib import Path

import pytest

from moth_runtime_v5_0.model import CompilationError
from experiments.runtime_v5_0_blind_compositional_closure.field import compile_field


HERE = Path(__file__).resolve().parents[1]
SOURCE = json.loads((HERE / "fixtures/field-en-1.0.json").read_text())


def test_field_compiles_deterministically():
    assert compile_field(SOURCE) == compile_field(SOURCE)
    assert len(compile_field(SOURCE).payload["relation_rules"]) == 14


@pytest.mark.parametrize("mutation", ["schema", "role", "slot", "limit"])
def test_unsafe_field_mutations_fail(mutation):
    candidate = deepcopy(SOURCE)
    if mutation == "schema":
        candidate["schema"] = "unknown"
    elif mutation == "role":
        candidate["capabilities"][1]["role"] = "RESOURCE"
    elif mutation == "slot":
        candidate["relation_rules"][0]["fragment"] = "is short of {UNKNOWN}"
    else:
        candidate["limits"]["tokens"] = 1000
    with pytest.raises(CompilationError):
        compile_field(candidate)
