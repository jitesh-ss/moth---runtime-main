from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest

from moth_runtime_v4_9.canonical import canonical_bytes
from moth_runtime_v4_9.compiler import CompilationError, compile_sources
from moth_runtime_v4_9.encoder import DeterministicEncoder
from moth_runtime_v4_9.energy import SettlementFailure, settle, verify_settlement
from moth_runtime_v4_9.grounding import ground_prompt
from moth_runtime_v4_9.model import RefusalCode, WorldRole
from moth_runtime_v4_9.store import WorldStore

ROOT = Path(__file__).resolve().parents[1]


SURFACE = """\
Operation "realize-semantic-result" selects kernel primitive "REALIZE_SEMANTIC_RESULT".
Instruction "realize-semantic-result" selects operation "realize-semantic-result" accepts "Realize the verified semantic result.".
"""


def _tree_hash(folder):
    result = hashlib.sha256()
    for path in sorted(folder.glob("*.py")):
        result.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        result.update(b"\0")
        result.update(hashlib.sha256(path.read_bytes()).digest())
    return result.hexdigest()


def test_runtime_4_9_architecture_lock():
    lock = json.loads((ROOT / "config/v4.9/ARCHITECTURE-LOCK.json").read_text())
    for group in ("documents", "configuration"):
        for record in lock[group].values():
            assert hashlib.sha256((ROOT / record["path"]).read_bytes()).hexdigest() == record["sha256"]
    assert _tree_hash(ROOT / lock["implementation"]["path"]) == lock["implementation"]["tree_sha256"]
    assert _tree_hash(ROOT / lock["launcher"]["path"]) == lock["launcher"]["tree_sha256"]
    assert lock["qualification"]["verdict"] == "FACTOR_SETTLEMENT_CONFIRMED"


def quoted_json(value) -> str:
    return json.dumps(json.dumps(value, separators=(",", ":")))


def factor_source(*, values: list[tuple[str, str]], domains: dict[str, list[str]],
                  templates: dict[str, dict], programs: dict[str, list[dict]],
                  fields: list[str]) -> str:
    schema = {
        "type": "object", "properties": {name: {"type": "string"} for name in fields},
        "required": fields, "additionalProperties": False,
    }
    lines = ['Scalar type "symbol" selects kernel type "STRING".']
    lines += [f'Value "{name}" has type "symbol" and canonical JSON {quoted_json(value)}.'
              for name, value in values]
    lines.append(f'Structured schema "inputs" is canonical JSON Schema {quoted_json(schema)}.')
    lines += [f'Schema field "{name}" in schema "inputs" has type "symbol" and is required.'
              for name in fields]
    lines += [f'Finite domain "{name}" is canonical value JSON {quoted_json(items)}.'
              for name, items in domains.items()]
    lines += [f'Factor template "{name}" is canonical table JSON {quoted_json(table)}.'
              for name, table in templates.items()]
    lines += [f'Factor program "{name}" is canonical instruction JSON {quoted_json(steps)}.'
              for name, steps in programs.items()]
    lines += [
        'Operation "factor-settle" selects kernel primitive "FACTOR_SETTLEMENT".',
        'Output schema "answer-json" selects kernel schema "ANSWER_WITH_PROOF".',
        'Instruction "factor-settle" selects operation "factor-settle" accepts "Settle {PROGRAM} with {BINDINGS} using {SCHEMA}.".',
    ]
    return "\n".join(lines) + "\n"


def addition_source(width: int, *, carry_prompt: bool = False) -> str:
    values = [("zero", "0"), ("one", "1")]
    ports = [{"name": name, "domain": "bit"} for name in ("a", "b", "cin", "sum", "cout")]
    rows = []
    for a in range(2):
        for b in range(2):
            for carry in range(2):
                total = a + b + carry
                rows.append([["zero", "one"][v] for v in (a, b, carry, total & 1, total >> 1)])
    steps: list[dict] = []
    for index in range(width):
        for prefix in ("a", "b", "s"):
            steps.append({"opcode": "CREATE_VARIABLE", "instance": f"{prefix}{index}", "domain": "bit"})
    for index in range(width + 1):
        steps.append({"opcode": "CREATE_VARIABLE", "instance": f"c{index}", "domain": "bit"})
    for index in range(width):
        steps.append({"opcode": "INSTANTIATE_FACTOR", "instance": f"f{index}", "template": "full-adder"})
        for port, variable in (("a", f"a{index}"), ("b", f"b{index}"), ("cin", f"c{index}"),
                               ("sum", f"s{index}"), ("cout", f"c{index + 1}")):
            steps.append({"opcode": "BIND_PORT", "factor": f"f{index}", "port": port,
                          "variable": variable})
    fields = []
    if carry_prompt:
        fields.append("carry-in")
        steps.append({"opcode": "CLAMP_FROM_PROMPT", "variable": "c0", "field": "carry-in"})
    else:
        steps.append({"opcode": "CLAMP_LITERAL", "variable": "c0", "value": "zero"})
    for prefix in ("a", "b"):
        for index in range(width):
            field = f"{prefix}{index}"
            fields.append(field)
            steps.append({"opcode": "CLAMP_FROM_PROMPT", "variable": field, "field": field})
    for index in range(width):
        steps.append({"opcode": "EXPOSE_OUTPUT", "variable": f"s{index}", "ordinal": index,
                      "label": f"s{index}"})
    steps.append({"opcode": "EXPOSE_OUTPUT", "variable": f"c{width}", "ordinal": width,
                  "label": "carry"})
    return factor_source(values=values, domains={"bit": ["zero", "one"]},
                         templates={"full-adder": {"ports": ports, "allowed_tuples": rows}},
                         programs={f"add-{width}": steps}, fields=fields)


def addition_prompt(width: int, left: int, right: int, *, carry: int | None = None) -> str:
    bindings = []
    if carry is not None:
        bindings.append("carry-in = " + ("one" if carry else "zero"))
    for prefix, number in (("a", left), ("b", right)):
        for index in range(width):
            bindings.append(f"{prefix}{index} = " + ("one" if number >> index & 1 else "zero"))
    return f"Settle add-{width} with " + ", ".join(bindings) + " using answer-json."


def decode_addition(output: dict[str, str], width: int) -> int:
    return sum((output[f"s{index}"] == "1") << index for index in range(width)) + (
        (output["carry"] == "1") << width
    )


@pytest.mark.parametrize("width,left,right", [
    (4, 7, 6), (4, 9, 5), (8, 137, 59), (8, 255, 1),
    (8, 173, 54), (16, 43690, 21845), (16, 65535, 1),
])
def test_unseen_compiled_full_adder_carry_chains(width, left, right):
    encoder = DeterministicEncoder()
    world = compile_sources({"addition.moth": addition_source(width)}, encoder=encoder,
                            world_role=WorldRole.MAIN)
    program = ground_prompt(world, addition_prompt(width, left, right), encoder=encoder)
    result = settle(world, program)
    verify_settlement(world, program, result)
    assert decode_addition(result.output, width) == left + right
    assert result.violation_count == 0
    assert result.factor_evidence["energy"] == {
        "multiplier": 4 * width + 2, "violation_count": 0,
        "ambiguity_units": 0, "total_units": 0,
    }
    assert len(result.factor_evidence["witnesses"]) == width


@pytest.mark.parametrize("a,b,carry", [
    (a, b, carry) for a in range(2) for b in range(2) for carry in range(2)
])
def test_all_full_adder_truth_table_rows(a, b, carry):
    encoder = DeterministicEncoder()
    source = addition_source(1, carry_prompt=True)
    world = compile_sources({"adder.moth": source}, encoder=encoder, world_role=WorldRole.MAIN)
    program = ground_prompt(world, addition_prompt(1, a, b, carry=carry), encoder=encoder)
    result = settle(world, program)
    verify_settlement(world, program, result)
    assert decode_addition(result.output, 1) == a + b + carry


def test_same_kernel_solves_graph_coloring_and_scheduling():
    values = [("red", "red"), ("blue", "blue")]
    inequality = {
        "ports": [{"name": "left", "domain": "color"}, {"name": "right", "domain": "color"}],
        "allowed_tuples": [["red", "blue"], ["blue", "red"]],
    }
    graph_steps = [{"opcode": "CREATE_VARIABLE", "instance": name, "domain": "color"}
                   for name in ("n0", "n1", "n2", "n3")]
    for index in range(3):
        graph_steps += [
            {"opcode": "INSTANTIATE_FACTOR", "instance": f"edge{index}", "template": "different"},
            {"opcode": "BIND_PORT", "factor": f"edge{index}", "port": "left", "variable": f"n{index}"},
            {"opcode": "BIND_PORT", "factor": f"edge{index}", "port": "right", "variable": f"n{index + 1}"},
        ]
    graph_steps += [
        {"opcode": "CLAMP_FROM_PROMPT", "variable": "n0", "field": "start"},
        {"opcode": "EXPOSE_OUTPUT", "variable": "n3", "ordinal": 0, "label": "color"},
    ]
    graph = factor_source(values=values, domains={"color": ["red", "blue"]},
                          templates={"different": inequality}, programs={"color-chain": graph_steps},
                          fields=["start"])
    encoder = DeterministicEncoder()
    world = compile_sources({"graph.moth": graph}, encoder=encoder, world_role=WorldRole.MAIN)
    program = ground_prompt(world, "Settle color-chain with start = red using answer-json.", encoder=encoder)
    result = settle(world, program)
    verify_settlement(world, program, result)
    assert result.output == "blue"

    schedule_values = [("early", "early"), ("middle", "middle"), ("late", "late")]
    before = {
        "ports": [{"name": "first", "domain": "slot"}, {"name": "second", "domain": "slot"}],
        "allowed_tuples": [["early", "middle"], ["early", "late"], ["middle", "late"]],
    }
    schedule_steps = [
        {"opcode": "CREATE_VARIABLE", "instance": "design", "domain": "slot"},
        {"opcode": "CREATE_VARIABLE", "instance": "build", "domain": "slot"},
        {"opcode": "CREATE_VARIABLE", "instance": "ship", "domain": "slot"},
        {"opcode": "INSTANTIATE_FACTOR", "instance": "p0", "template": "before"},
        {"opcode": "BIND_PORT", "factor": "p0", "port": "first", "variable": "design"},
        {"opcode": "BIND_PORT", "factor": "p0", "port": "second", "variable": "build"},
        {"opcode": "INSTANTIATE_FACTOR", "instance": "p1", "template": "before"},
        {"opcode": "BIND_PORT", "factor": "p1", "port": "first", "variable": "build"},
        {"opcode": "BIND_PORT", "factor": "p1", "port": "second", "variable": "ship"},
        {"opcode": "CLAMP_FROM_PROMPT", "variable": "design", "field": "anchor"},
        {"opcode": "EXPOSE_OUTPUT", "variable": "build", "ordinal": 0, "label": "slot"},
    ]
    schedule = factor_source(values=schedule_values, domains={"slot": [v[0] for v in schedule_values]},
                             templates={"before": before}, programs={"schedule": schedule_steps}, fields=["anchor"])
    world = compile_sources({"schedule.moth": schedule}, encoder=encoder, world_role=WorldRole.MAIN)
    program = ground_prompt(world, "Settle schedule with anchor = early using answer-json.", encoder=encoder)
    result = settle(world, program)
    verify_settlement(world, program, result)
    assert result.output == "middle"


def test_ambiguous_unsatisfiable_and_compile_time_controls():
    encoder = DeterministicEncoder()
    source = addition_source(4)
    world = compile_sources({"addition.moth": source}, encoder=encoder, world_role=WorldRole.MAIN)
    incomplete = ground_prompt(world, addition_prompt(4, 0, 0), encoder=encoder)
    broken_steps = tuple(step for step in incomplete.steps if not (
        step["opcode"] == "CLAMP_FROM_PROMPT" and step.get("variable") == "b3"
    ))
    with pytest.raises(SettlementFailure) as ambiguous:
        settle(world, replace(incomplete, steps=broken_steps))
    assert ambiguous.value.code == RefusalCode.INTEGRITY_FAILURE

    bad = "\n".join(line for line in source.splitlines()
                    if not line.startswith('Factor template "full-adder"')) + "\n"
    with pytest.raises(CompilationError):
        compile_sources({"bad.moth": bad}, encoder=encoder, world_role=WorldRole.MAIN)


def test_factor_verifier_rejects_forged_trace():
    encoder = DeterministicEncoder()
    world = compile_sources({"addition.moth": addition_source(4)}, encoder=encoder,
                            world_role=WorldRole.MAIN)
    program = ground_prompt(world, addition_prompt(4, 3, 8), encoder=encoder)
    result = settle(world, program)
    evidence = json.loads(json.dumps(result.factor_evidence))
    evidence["reductions"][0]["after"] = evidence["reductions"][0]["before"]
    forged = replace(result, factor_evidence=evidence)
    with pytest.raises(SettlementFailure, match="settlement differs|factor evidence hash"):
        verify_settlement(world, program, forged)


def test_factor_fixed_point_refuses_ambiguity_and_contradiction():
    encoder = DeterministicEncoder()
    values = [("zero", "0"), ("one", "1")]
    equality = {
        "ports": [{"name": "left", "domain": "bit"}, {"name": "right", "domain": "bit"}],
        "allowed_tuples": [["zero", "zero"], ["one", "one"]],
    }
    ambiguous_steps = [
        {"opcode": "CREATE_VARIABLE", "instance": "x", "domain": "bit"},
        {"opcode": "CREATE_VARIABLE", "instance": "y", "domain": "bit"},
        {"opcode": "CREATE_VARIABLE", "instance": "anchor", "domain": "bit"},
        {"opcode": "INSTANTIATE_FACTOR", "instance": "eq", "template": "equal"},
        {"opcode": "BIND_PORT", "factor": "eq", "port": "left", "variable": "x"},
        {"opcode": "BIND_PORT", "factor": "eq", "port": "right", "variable": "y"},
        {"opcode": "CLAMP_FROM_PROMPT", "variable": "anchor", "field": "given"},
        {"opcode": "EXPOSE_OUTPUT", "variable": "x", "ordinal": 0, "label": "value"},
    ]
    source = factor_source(values=values, domains={"bit": ["zero", "one"]},
                           templates={"equal": equality}, programs={"ambiguous": ambiguous_steps},
                           fields=["given"])
    world = compile_sources({"ambiguous.moth": source}, encoder=encoder, world_role=WorldRole.MAIN)
    program = ground_prompt(world, "Settle ambiguous with given = zero using answer-json.", encoder=encoder)
    with pytest.raises(SettlementFailure) as ambiguous:
        settle(world, program)
    assert ambiguous.value.code == RefusalCode.AMBIGUOUS_SETTLEMENT

    unsat_steps = ambiguous_steps[:-2] + [
        {"opcode": "CLAMP_FROM_PROMPT", "variable": "x", "field": "left"},
        {"opcode": "CLAMP_FROM_PROMPT", "variable": "y", "field": "right"},
        {"opcode": "EXPOSE_OUTPUT", "variable": "x", "ordinal": 0, "label": "value"},
    ]
    source = factor_source(values=values, domains={"bit": ["zero", "one"]},
                           templates={"equal": equality}, programs={"unsat": unsat_steps},
                           fields=["left", "right"])
    world = compile_sources({"unsat.moth": source}, encoder=encoder, world_role=WorldRole.MAIN)
    program = ground_prompt(world, "Settle unsat with left = zero, right = one using answer-json.", encoder=encoder)
    with pytest.raises(SettlementFailure) as unsat:
        settle(world, program)
    assert unsat.value.code == RefusalCode.UNSATISFIABLE


def test_three_world_factor_settlement_and_encoder_free_replay(tmp_path):
    encoder = DeterministicEncoder()
    source = addition_source(8)
    store = WorldStore(tmp_path / "factor.sqlite3")
    store.publish(WorldRole.INPUT, {"input.moth": source}, encoder=encoder)
    store.publish(WorldRole.MAIN, {"main.moth": source}, encoder=encoder)
    store.publish(WorldRole.SURFACE, {"surface.moth": SURFACE}, encoder=encoder)
    store.activate()
    result = store.query(addition_prompt(8, 173, 54), encoder=encoder,
                         thresholds={"default": {"score": 0.82, "margin": 0.05}})
    assert result["status"] == "ANSWER"
    assert decode_addition(result["output"]["value"], 8) == 227
    assert result["stages"][1]["settlement"]["factor_evidence"]["witnesses"]
    assert result["execution"] == {"performed": False, "dispatch_count": 0}
    assert store.replay(result["episode_id"], encoder_free=True) == canonical_bytes(result)
