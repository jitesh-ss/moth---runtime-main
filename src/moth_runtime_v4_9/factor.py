"""Deterministic, search-free finite-domain factor settlement for Runtime 4.9."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .canonical import canonical_bytes, digest, sha256_bytes
from .model import CompiledWorld, GroundedProgram, MeaningType, RefusalCode

MAX_TRACE_BYTES = 64 * 1024 * 1024


@dataclass(frozen=True)
class FactorFailure(ValueError):
    code: RefusalCode
    message: str
    context: dict[str, Any]


def _step_ids(world: CompiledWorld, program_id: str) -> dict[int, str]:
    return {
        int(item.payload["index"]): item.meaning_id
        for item in world.by_kind(MeaningType.PROGRAM_STEP)
        if item.payload.get("program_id") == program_id
    }


def _owner_receipts(world: CompiledWorld, identifiers: set[str]) -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    for identifier in sorted(identifiers):
        item = world.meanings.get(identifier)
        if item is None or not item.owners:
            raise FactorFailure(RefusalCode.INTEGRITY_FAILURE, "factor meaning has no active provenance", {
                "meaning_id": identifier,
            })
        receipts.append({
            "meaning_id": identifier,
            "owners": [owner.canonical() for owner in item.owners],
        })
    return receipts


def _materialize(world: CompiledWorld, program: GroundedProgram) -> dict[str, Any]:
    program_id = program.slots.get("PROGRAM", "")
    step_ids = _step_ids(world, program_id)
    if len(step_ids) != len(program.steps):
        raise FactorFailure(RefusalCode.INTEGRITY_FAILURE, "factor program instruction provenance is incomplete", {})
    variables: dict[str, dict[str, Any]] = {}
    factors: dict[str, dict[str, Any]] = {}
    outputs: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    used_ids: set[str] = {program_id}
    for index, step in enumerate(program.steps):
        opcode = str(step["opcode"])
        instruction_id = step_ids[index]
        used_ids.add(instruction_id)
        event: dict[str, Any] = {"index": index, "opcode": opcode, "instruction_id": instruction_id}
        if opcode == "CREATE_VARIABLE":
            name, domain_id = str(step["instance"]), str(step["domain_id"])
            domain = world.meanings.get(domain_id)
            if domain is None or domain.kind != MeaningType.FINITE_DOMAIN:
                raise FactorFailure(RefusalCode.INTEGRITY_FAILURE, "variable domain is absent", {})
            variable_id = digest("moth-factor-variable/4.9", {
                "program_id": program_id, "index": index, "name": name, "domain_id": domain_id,
            })
            variables[name] = {
                "variable_id": variable_id, "name": name, "domain_id": domain_id,
                "domain": list(domain.payload["value_ids"]), "created_at": index,
            }
            used_ids.add(domain_id)
            used_ids.update(domain.payload["value_ids"])
            event.update({"variable_id": variable_id, "domain_id": domain_id})
        elif opcode == "INSTANTIATE_FACTOR":
            name, template_id = str(step["instance"]), str(step["template_id"])
            template = world.meanings.get(template_id)
            if template is None or template.kind != MeaningType.FACTOR_TEMPLATE:
                raise FactorFailure(RefusalCode.MISSING_FACTOR, "compiled factor template is absent", {})
            factor_id = digest("moth-factor-instance/4.9", {
                "program_id": program_id, "index": index, "name": name, "template_id": template_id,
            })
            factors[name] = {
                "factor_id": factor_id, "name": name, "template_id": template_id,
                "bindings": {}, "created_at": index, "instruction_id": instruction_id,
            }
            used_ids.add(template_id)
            event.update({"factor_id": factor_id, "template_id": template_id})
        elif opcode == "BIND_PORT":
            factor, port, variable = str(step["factor"]), str(step["port"]), str(step["variable"])
            if factor not in factors or variable not in variables:
                raise FactorFailure(RefusalCode.UNBOUND_PORT, "factor binding references an absent instance", {})
            factors[factor]["bindings"][port] = variable
            event.update({"factor_id": factors[factor]["factor_id"], "port": port,
                          "variable_id": variables[variable]["variable_id"]})
        elif opcode in {"CLAMP_FROM_PROMPT", "CLAMP_LITERAL"}:
            variable = str(step["variable"])
            if variable not in variables:
                raise FactorFailure(RefusalCode.MISSING_BINDING, "clamp variable is absent", {})
            if opcode == "CLAMP_FROM_PROMPT":
                field_id = str(step["field_id"])
                value_id = program.bindings.get(field_id)
                if value_id is None:
                    raise FactorFailure(RefusalCode.MISSING_BINDING, "prompt binding is absent", {"field_id": field_id})
                used_ids.add(field_id)
                event["field_id"] = field_id
            else:
                value_id = str(step["value_id"])
            if value_id not in variables[variable]["domain"]:
                raise FactorFailure(RefusalCode.UNSATISFIABLE, "clamp value is outside the variable domain", {})
            variables[variable]["domain"] = [value_id]
            used_ids.add(value_id)
            event.update({"variable_id": variables[variable]["variable_id"], "value_id": value_id})
        elif opcode == "EXPOSE_OUTPUT":
            variable = str(step["variable"])
            if variable not in variables:
                raise FactorFailure(RefusalCode.MISSING_BINDING, "output variable is absent", {})
            outputs.append({"ordinal": int(step["ordinal"]), "label": str(step["label"]),
                            "variable": variable, "variable_id": variables[variable]["variable_id"]})
            event.update({"variable_id": variables[variable]["variable_id"],
                          "ordinal": int(step["ordinal"]), "label": str(step["label"])})
        events.append(event)
    for factor in factors.values():
        template = world.meanings[factor["template_id"]]
        expected = {port["name"] for port in template.payload["ports"]}
        if set(factor["bindings"]) != expected:
            raise FactorFailure(RefusalCode.UNBOUND_PORT, "factor instance has an unbound port", {
                "factor_id": factor["factor_id"],
            })
    return {"variables": variables, "factors": factors, "outputs": sorted(outputs, key=lambda row: row["ordinal"]),
            "events": events, "used_ids": used_ids}


def _compatible_rows(world: CompiledWorld, factor: dict[str, Any], domains: dict[str, set[str]]) -> list[list[str]]:
    template = world.meanings[factor["template_id"]]
    ports = [port["name"] for port in template.payload["ports"]]
    return [list(row) for row in template.payload["allowed_tuples"] if all(
        row[index] in domains[factor["bindings"][port]] for index, port in enumerate(ports)
    )]


def settle_factor(world: CompiledWorld, program: GroundedProgram) -> tuple[dict[str, Any], dict[str, Any]]:
    program_id = program.slots.get("PROGRAM", "")
    if not program_id:
        raise FactorFailure(RefusalCode.UNSUPPORTED_PROGRAM, "factor settlement requires a compiled program", {})
    program_meaning = world.meanings.get(program_id)
    if (program_meaning is None or program_meaning.kind != MeaningType.PROGRAM
            or program_meaning.payload.get("program_kind") != "FACTOR"):
        raise FactorFailure(RefusalCode.UNSUPPORTED_PROGRAM, "selected program is not a compiled factor program", {})
    material = _materialize(world, program)
    domains = {name: set(row["domain"]) for name, row in material["variables"].items()}
    reductions: list[dict[str, Any]] = []
    ordered_factors = sorted(material["factors"].values(), key=lambda row: (row["created_at"], row["factor_id"]))
    sweep = 0
    while True:
        changed = False
        for factor in ordered_factors:
            template = world.meanings[factor["template_id"]]
            ports = [port["name"] for port in template.payload["ports"]]
            compatible = _compatible_rows(world, factor, domains)
            if not compatible:
                raise FactorFailure(RefusalCode.UNSATISFIABLE, "factor has no compatible allowed tuple", {
                    "factor_id": factor["factor_id"], "sweep": sweep,
                })
            for port_index, port in enumerate(ports):
                variable = factor["bindings"][port]
                before = sorted(domains[variable])
                supported = {row[port_index] for row in compatible}
                after = sorted(domains[variable] & supported)
                if not after:
                    raise FactorFailure(RefusalCode.UNSATISFIABLE, "domain reduction produced an empty domain", {})
                if after != before:
                    domains[variable] = set(after)
                    changed = True
                    reductions.append({
                        "sweep": sweep, "factor_id": factor["factor_id"],
                        "template_id": factor["template_id"], "instruction_id": factor["instruction_id"],
                        "port": port, "variable_id": material["variables"][variable]["variable_id"],
                        "before": before, "after": after,
                    })
        if not changed:
            break
        sweep += 1
        if sweep > 1024:
            raise FactorFailure(RefusalCode.RESOURCE_LIMIT, "factor settlement sweep limit exceeded", {})
    unresolved = [name for name, values in domains.items() if len(values) != 1]
    base_evidence = {
        "schema": "moth-factor-settlement/4.9", "program_id": program_id,
        "generation_id": world.generation_id, "materialization": material["events"],
        "reductions": reductions,
        "final_domains": {material["variables"][name]["variable_id"]: sorted(values)
                          for name, values in sorted(domains.items())},
    }
    if unresolved:
        raise FactorFailure(RefusalCode.AMBIGUOUS_SETTLEMENT, "fixed point contains non-singleton variables", {
            "unresolved_variable_ids": [material["variables"][name]["variable_id"] for name in sorted(unresolved)],
            "factor_attempt": base_evidence,
        })
    witnesses: list[dict[str, Any]] = []
    for factor in ordered_factors:
        rows = _compatible_rows(world, factor, domains)
        if len(rows) != 1:
            raise FactorFailure(RefusalCode.INTEGRITY_FAILURE, "singleton factor witness is not unique", {})
        witnesses.append({"factor_id": factor["factor_id"], "template_id": factor["template_id"],
                          "allowed_tuple": rows[0]})
    output_rows: list[dict[str, Any]] = []
    for exposed in material["outputs"]:
        value_id = next(iter(domains[exposed["variable"]]))
        value = world.meanings[value_id].payload["value"]
        output_rows.append({"ordinal": exposed["ordinal"], "label": exposed["label"],
                            "variable_id": exposed["variable_id"], "value_id": value_id, "value": value})
    output: Any = output_rows[0]["value"] if len(output_rows) == 1 else {
        row["label"]: row["value"] for row in output_rows
    }
    ambiguity_max = sum(
        len(world.meanings[row["domain_id"]].payload["value_ids"]) - 1
        for row in material["variables"].values()
    )
    evidence = {**base_evidence, "witnesses": witnesses, "outputs": output_rows,
                "energy": {"multiplier": ambiguity_max + 1, "violation_count": 0,
                           "ambiguity_units": 0, "total_units": 0},
                "provenance": _owner_receipts(world, material["used_ids"])}
    evidence["trace_hash"] = digest("moth-factor-trace/4.9", evidence)
    if len(canonical_bytes(evidence)) > MAX_TRACE_BYTES:
        raise FactorFailure(RefusalCode.RESOURCE_LIMIT, "factor settlement trace exceeds 64 MiB", {})
    return {"kind": "FACTOR_RESULT", "value": output}, evidence


def verify_factor_settlement(world: CompiledWorld, program: GroundedProgram,
                             output: dict[str, Any], evidence: dict[str, Any]) -> None:
    """Replay the trace and independently establish the reported fixed point."""
    if evidence.get("schema") != "moth-factor-settlement/4.9" or evidence.get("program_id") != program.slots.get("PROGRAM"):
        raise FactorFailure(RefusalCode.INTEGRITY_FAILURE, "factor evidence identity is invalid", {})
    if evidence.get("generation_id") != world.generation_id:
        raise FactorFailure(RefusalCode.INTEGRITY_FAILURE, "factor evidence generation changed", {})
    claimed = dict(evidence)
    trace_hash = claimed.pop("trace_hash", None)
    if trace_hash != digest("moth-factor-trace/4.9", claimed):
        raise FactorFailure(RefusalCode.INTEGRITY_FAILURE, "factor trace hash changed", {})
    material = _materialize(world, program)
    if evidence.get("materialization") != material["events"]:
        raise FactorFailure(RefusalCode.INTEGRITY_FAILURE, "materialization trace changed", {})
    independently_narrowed = {name: set(row["domain"]) for name, row in material["variables"].items()}
    expected_reductions: list[dict[str, Any]] = []
    independent_factors = sorted(material["factors"].values(), key=lambda row: (row["created_at"], row["factor_id"]))
    independent_sweep = 0
    while True:
        independent_changed = False
        for factor in independent_factors:
            template = world.meanings[factor["template_id"]]
            ports = [port["name"] for port in template.payload["ports"]]
            compatible = _compatible_rows(world, factor, independently_narrowed)
            if not compatible:
                raise FactorFailure(RefusalCode.INTEGRITY_FAILURE, "verified factor has no compatible tuple", {})
            for port_index, port in enumerate(ports):
                variable = factor["bindings"][port]
                before = sorted(independently_narrowed[variable])
                after = sorted(independently_narrowed[variable] & {row[port_index] for row in compatible})
                if after != before:
                    independently_narrowed[variable] = set(after)
                    independent_changed = True
                    expected_reductions.append({
                        "sweep": independent_sweep, "factor_id": factor["factor_id"],
                        "template_id": factor["template_id"], "instruction_id": factor["instruction_id"],
                        "port": port, "variable_id": material["variables"][variable]["variable_id"],
                        "before": before, "after": after,
                    })
        if not independent_changed:
            break
        independent_sweep += 1
        if independent_sweep > 1024:
            raise FactorFailure(RefusalCode.RESOURCE_LIMIT, "verification sweep limit exceeded", {})
    if evidence.get("reductions") != expected_reductions:
        raise FactorFailure(RefusalCode.INTEGRITY_FAILURE, "canonical factor reduction trace changed", {})
    domains = {name: set(row["domain"]) for name, row in material["variables"].items()}
    variable_by_id = {row["variable_id"]: name for name, row in material["variables"].items()}
    factor_by_id = {row["factor_id"]: row for row in material["factors"].values()}
    for record in evidence.get("reductions", []):
        factor = factor_by_id.get(record.get("factor_id"))
        variable = variable_by_id.get(record.get("variable_id"))
        if factor is None or variable is None or sorted(domains[variable]) != record.get("before"):
            raise FactorFailure(RefusalCode.INTEGRITY_FAILURE, "factor reduction pre-state changed", {})
        template = world.meanings[factor["template_id"]]
        ports = [port["name"] for port in template.payload["ports"]]
        if record.get("port") not in ports or factor["bindings"].get(record["port"]) != variable:
            raise FactorFailure(RefusalCode.INTEGRITY_FAILURE, "factor reduction binding changed", {})
        rows = _compatible_rows(world, factor, domains)
        port_index = ports.index(record["port"])
        computed = sorted(domains[variable] & {row[port_index] for row in rows})
        if computed != record.get("after") or computed == record.get("before"):
            raise FactorFailure(RefusalCode.INTEGRITY_FAILURE, "factor reduction is not licensed", {})
        domains[variable] = set(computed)
    for factor in sorted(material["factors"].values(), key=lambda row: (row["created_at"], row["factor_id"])):
        compatible = _compatible_rows(world, factor, domains)
        if not compatible:
            raise FactorFailure(RefusalCode.INTEGRITY_FAILURE, "reported fixed point violates a factor", {})
        template = world.meanings[factor["template_id"]]
        for index, port in enumerate(template.payload["ports"]):
            variable = factor["bindings"][port["name"]]
            if domains[variable] != domains[variable] & {row[index] for row in compatible}:
                raise FactorFailure(RefusalCode.INTEGRITY_FAILURE, "reported state is not a fixed point", {})
    final_domains = {material["variables"][name]["variable_id"]: sorted(values)
                     for name, values in sorted(domains.items())}
    if evidence.get("final_domains") != final_domains or any(len(values) != 1 for values in domains.values()):
        raise FactorFailure(RefusalCode.INTEGRITY_FAILURE, "final singleton domains changed", {})
    ambiguity_max = sum(
        len(world.meanings[row["domain_id"]].payload["value_ids"]) - 1
        for row in material["variables"].values()
    )
    if evidence.get("energy") != {"multiplier": ambiguity_max + 1, "violation_count": 0,
                                  "ambiguity_units": 0, "total_units": 0}:
        raise FactorFailure(RefusalCode.INTEGRITY_FAILURE, "factor scalar energy changed", {})
    expected_witnesses = []
    for factor in independent_factors:
        rows = _compatible_rows(world, factor, domains)
        if len(rows) != 1:
            raise FactorFailure(RefusalCode.INTEGRITY_FAILURE, "verified factor witness is not unique", {})
        expected_witnesses.append({"factor_id": factor["factor_id"],
                                   "template_id": factor["template_id"],
                                   "allowed_tuple": rows[0]})
    if evidence.get("witnesses") != expected_witnesses:
        raise FactorFailure(RefusalCode.INTEGRITY_FAILURE, "factor witnesses changed", {})
    expected_rows = []
    for exposed in material["outputs"]:
        value_id = next(iter(domains[exposed["variable"]]))
        expected_rows.append({"ordinal": exposed["ordinal"], "label": exposed["label"],
                              "variable_id": exposed["variable_id"], "value_id": value_id,
                              "value": world.meanings[value_id].payload["value"]})
    expected_value: Any = expected_rows[0]["value"] if len(expected_rows) == 1 else {
        row["label"]: row["value"] for row in expected_rows
    }
    if output != {"kind": "FACTOR_RESULT", "value": expected_value} or evidence.get("outputs") != expected_rows:
        raise FactorFailure(RefusalCode.INTEGRITY_FAILURE, "factor output changed", {})
    if evidence.get("provenance") != _owner_receipts(world, material["used_ids"]):
        raise FactorFailure(RefusalCode.INTEGRITY_FAILURE, "factor provenance changed", {})
    if len(canonical_bytes(evidence)) > MAX_TRACE_BYTES:
        raise FactorFailure(RefusalCode.RESOURCE_LIMIT, "factor evidence exceeds its limit", {})
