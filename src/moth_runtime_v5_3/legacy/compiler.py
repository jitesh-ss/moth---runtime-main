"""Independent deterministic compiler for the Runtime 5.0 language."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Protocol

from .canonical import digest, meaning_id, normalize_text, sha256_bytes
from .model import (
    CompiledWorld, CompilationError, FACTOR_OPCODES, Meaning, MeaningType, OPERATIONS,
    Provenance, SemanticEdge, Source, VectorRecord, WorldRole,
)
from .structure import validate_schema, value_matches_type

COMPILER_VERSION = "5.0.0"
QUOTED = r'"(?:[^"\\]|\\.)*"'

PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("entity", re.compile(rf'^Entity (?P<name>{QUOTED}) is declared\.$')),
    ("relation", re.compile(rf'^Directional relation (?P<name>{QUOTED}) maps (?:Entity|Meaning) to (?:Entity|Meaning) and is (?P<cardinality>functional|multi-valued)\.$')),
    ("numeral", re.compile(rf'^Numeral (?P<name>{QUOTED}) denotes (?P<value>[0-9]+) steps\.$')),
    ("operation", re.compile(rf'^Operation (?P<name>{QUOTED}) selects kernel primitive (?P<primitive>{QUOTED})\.$')),
    ("relation_form", re.compile(rf'^Relation form (?P<name>{QUOTED}) for relation (?P<relation>{QUOTED}) accepts (?P<template>{QUOTED})\.$')),
    ("instruction", re.compile(rf'^Instruction (?P<name>{QUOTED}) selects operation (?P<operation>{QUOTED}) accepts (?P<template>{QUOTED})\.$')),
    ("prototype", re.compile(rf'^Instruction prototype (?P<name>{QUOTED}) for instruction (?P<instruction>{QUOTED}) is (?P<template>{QUOTED})\.$')),
    ("output_schema", re.compile(rf'^Output schema (?P<name>{QUOTED}) selects kernel schema (?P<kernel>{QUOTED})\.$')),
    ("scalar_type", re.compile(rf'^Scalar type (?P<name>{QUOTED}) selects kernel type (?P<kernel>{QUOTED})\.$')),
    ("value", re.compile(rf'^Value (?P<name>{QUOTED}) has type (?P<type>{QUOTED}) and canonical JSON (?P<json>{QUOTED})\.$')),
    ("enum", re.compile(rf'^Enum member (?P<name>{QUOTED}) has type (?P<type>{QUOTED}) and canonical JSON (?P<json>{QUOTED})\.$')),
    ("list", re.compile(rf'^List value (?P<name>{QUOTED}) has element type (?P<type>{QUOTED}) and canonical JSON (?P<json>{QUOTED})\.$')),
    ("structured_schema", re.compile(rf'^Structured schema (?P<name>{QUOTED}) is canonical JSON Schema (?P<json>{QUOTED})\.$')),
    ("finite_domain", re.compile(rf'^Finite domain (?P<name>{QUOTED}) is canonical value JSON (?P<values>{QUOTED})\.$')),
    ("factor_template", re.compile(rf'^Factor template (?P<name>{QUOTED}) is canonical table JSON (?P<table>{QUOTED})\.$')),
    ("factor_program", re.compile(rf'^Factor program (?P<name>{QUOTED}) is canonical instruction JSON (?P<steps>{QUOTED})\.$')),
    ("schema_field", re.compile(rf'^Schema field (?P<name>{QUOTED}) in schema (?P<schema>{QUOTED}) has type (?P<type>{QUOTED}) and is (?P<required>required|optional)\.$')),
    ("sequence", re.compile(rf'^Relation sequence (?P<name>{QUOTED}) is (?P<relations>{QUOTED})\.$')),
    ("program", re.compile(rf'^Program (?P<name>{QUOTED}) is canonical step JSON (?P<steps>{QUOTED})\.$')),
    ("tool", re.compile(rf'^Tool (?P<name>{QUOTED}) uses schema (?P<schema>{QUOTED})\.$')),
    ("tool_argument", re.compile(rf'^Tool argument (?P<name>{QUOTED}) for tool (?P<tool>{QUOTED}) selects field (?P<field>{QUOTED})\.$')),
    ("fragment", re.compile(rf'^Text fragment (?P<name>{QUOTED}) is (?P<text>{QUOTED})\.$')),
    ("patch", re.compile(rf'^Patch template (?P<name>{QUOTED}) selects operation (?P<operation>{QUOTED})\.$')),
    ("semantic_contract", re.compile(rf'^Semantic contract (?P<name>{QUOTED}) is canonical semantic JSON (?P<json>{QUOTED})\.$')),
    ("alias", re.compile(rf'^Alias (?P<alias>{QUOTED}) denotes (?P<kind>[A-Za-z ]+) (?P<name>{QUOTED})\.$')),
)

KIND_SURFACES = {
    "Entity": MeaningType.ENTITY,
    "Relation": MeaningType.RELATION,
    "Numeral": MeaningType.NUMERAL,
    "Operation": MeaningType.OPERATION,
    "Instruction": MeaningType.INSTRUCTION,
    "Output schema": MeaningType.OUTPUT_SCHEMA,
    "Scalar type": MeaningType.SCALAR_TYPE,
    "Value": MeaningType.VALUE,
    "Enum member": MeaningType.ENUM_MEMBER,
    "List value": MeaningType.LIST_VALUE,
    "Structured schema": MeaningType.STRUCTURED_SCHEMA,
    "Schema field": MeaningType.SCHEMA_FIELD,
    "Relation sequence": MeaningType.RELATION_SEQUENCE,
    "Program": MeaningType.PROGRAM,
    "Tool": MeaningType.TOOL,
    "Tool argument": MeaningType.TOOL_ARGUMENT,
    "Code file": MeaningType.CODE_FILE,
    "Code symbol": MeaningType.CODE_SYMBOL,
    "Code span": MeaningType.CODE_SPAN,
    "Text fragment": MeaningType.TEXT_FRAGMENT,
    "Patch template": MeaningType.PATCH_TEMPLATE,
    "Finite domain": MeaningType.FINITE_DOMAIN,
    "Factor template": MeaningType.FACTOR_TEMPLATE,
}

TYPE_KERNELS = {
    "STRING": "string", "INTEGER": "integer", "NUMBER": "number",
    "BOOLEAN": "boolean", "NULL": "null", "OBJECT": "object", "ARRAY": "array",
}


class PassageEncoder(Protocol):
    fingerprint: str

    def encode_passages(self, texts: list[str]): ...
    def vector_hash(self, vector) -> str: ...


@dataclass(frozen=True)
class Statement:
    source: Source
    text: str
    provenance: Provenance


def _unquote(value: str) -> str:
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError as exc:
        raise CompilationError(f"invalid quoted string: {value}") from exc
    if not isinstance(decoded, str):
        raise CompilationError("quoted source value is not a string")
    return normalize_text(decoded) if "\n" not in decoded else decoded.replace("\r\n", "\n").replace("\r", "\n")


def _json_string(value: str) -> Any:
    try:
        return json.loads(_unquote(value))
    except json.JSONDecodeError as exc:
        raise CompilationError("declaration contains invalid canonical JSON") from exc


def _statements(source_id: str, document: str) -> list[Statement]:
    normalized = document.replace("\r\n", "\n").replace("\r", "\n")
    source = Source(source_id, normalized, sha256_bytes(normalized.encode("utf-8")))
    result: list[Statement] = []
    offset = 0
    for line_number, raw in enumerate(normalized.splitlines(keepends=True), 1):
        line = raw.rstrip("\n")
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            offset += len(raw)
            continue
        if not stripped.endswith("."):
            raise CompilationError(f"{source_id}:{line_number}: unterminated statement")
        start_in_line = len(line) - len(line.lstrip())
        char_start = offset + start_in_line
        char_end = char_start + len(stripped)
        byte_start = len(normalized[:char_start].encode("utf-8"))
        byte_end = len(normalized[:char_end].encode("utf-8"))
        text = normalize_text(stripped)
        result.append(Statement(source, text, Provenance(
            source_id, source.sha256, sha256_bytes(text.encode("utf-8")),
            char_start, char_end, byte_start, byte_end, line_number,
            start_in_line + 1, COMPILER_VERSION,
        )))
        offset += len(raw)
    return result


def _template_pattern(template: str) -> re.Pattern[str]:
    expression = re.escape(template)
    for slot in re.findall(r"\{([A-Z_]+)\}", template):
        expression = expression.replace(re.escape("{" + slot + "}"), rf"(?P<{slot.lower()}>.+?)")
    return re.compile("^" + expression + "$")


def compile_sources(
    source_texts: dict[str, str], *, encoder: PassageEncoder | None = None,
    generation_parent: str | None = None, capability_level: str = "L9",
    code_root: str | Path | None = None, world_role: WorldRole | str = WorldRole.MAIN,
) -> CompiledWorld:
    world_role = WorldRole(world_role)
    if not source_texts:
        raise CompilationError("at least one source is required")
    if capability_level not in {f"L{index}" for index in range(10)}:
        raise CompilationError("invalid capability level")
    statements: list[Statement] = []
    sources: dict[str, Source] = {}
    total_bytes = 0
    for source_id, text in sorted(source_texts.items()):
        size = len(text.encode("utf-8"))
        if not source_id or size > 16 * 1024 * 1024:
            raise CompilationError("RESOURCE_LIMIT: source file limit")
        total_bytes += size
        parsed = _statements(source_id, text)
        sources[source_id] = parsed[0].source if parsed else Source(source_id, text, sha256_bytes(text.encode()))
        statements.extend(parsed)
    if total_bytes > 1024 * 1024 * 1024 or len(sources) > 10_000:
        raise CompilationError("RESOURCE_LIMIT: source collection limit")

    parsed_rows: list[tuple[str, re.Match[str], Statement]] = []
    unmatched: list[Statement] = []
    for statement in statements:
        matched = False
        for tag, pattern in PATTERNS:
            if match := pattern.fullmatch(statement.text):
                parsed_rows.append((tag, match, statement))
                matched = True
                break
        if not matched:
            unmatched.append(statement)

    meanings: dict[str, Meaning] = {}
    by_name: dict[tuple[MeaningType, str], str] = {}

    def declare(kind: MeaningType, name: str, payload: dict[str, Any], owner: Provenance) -> str:
        canonical_payload = {"name": name, **payload}
        identifier = meaning_id(kind.value, canonical_payload)
        key = (kind, name.casefold())
        prior = by_name.get(key)
        if prior is not None and prior != identifier:
            raise CompilationError(f"conflicting {kind.value} declaration: {name}")
        if identifier in meanings:
            owners = tuple(sorted(set(meanings[identifier].owners + (owner,))))
            meanings[identifier] = Meaning(identifier, kind, name, canonical_payload, owners)
        else:
            meanings[identifier] = Meaning(identifier, kind, name, canonical_payload, (owner,))
        by_name[key] = identifier
        return identifier

    def target(kind: MeaningType, name: str) -> str:
        identifier = by_name.get((kind, name.casefold()))
        if identifier is None:
            raise CompilationError(f"undeclared {kind.value}: {name}")
        return identifier

    deferred: list[tuple[str, re.Match[str], Statement]] = []
    aliases_raw: list[tuple[re.Match[str], Statement]] = []
    for tag, match, statement in parsed_rows:
        owner = statement.provenance
        if tag == "entity":
            declare(MeaningType.ENTITY, _unquote(match["name"]), {}, owner)
        elif tag == "relation":
            declare(MeaningType.RELATION, _unquote(match["name"]), {
                "directional": True, "cardinality": match["cardinality"],
            }, owner)
        elif tag == "numeral":
            value = int(match["value"])
            if value > 50:
                raise CompilationError("numeral exceeds depth 50")
            declare(MeaningType.NUMERAL, _unquote(match["name"]), {"steps": value}, owner)
        elif tag == "operation":
            primitive = _unquote(match["primitive"])
            if primitive not in OPERATIONS:
                raise CompilationError(f"unsupported kernel primitive: {primitive}")
            declare(MeaningType.OPERATION, _unquote(match["name"]), {"primitive": primitive}, owner)
        elif tag == "output_schema":
            kernel = _unquote(match["kernel"])
            if kernel not in {"ANSWER_WITH_PROOF", "TYPED_REFUSAL", "COMPILED_JSON", "PATCH_PLAN"}:
                raise CompilationError(f"unsupported output schema: {kernel}")
            declare(MeaningType.OUTPUT_SCHEMA, _unquote(match["name"]), {"kernel": kernel}, owner)
        elif tag == "scalar_type":
            kernel = _unquote(match["kernel"])
            if kernel not in TYPE_KERNELS:
                raise CompilationError(f"unsupported scalar type: {kernel}")
            declare(MeaningType.SCALAR_TYPE, _unquote(match["name"]), {
                "kernel": kernel, "json_type": TYPE_KERNELS[kernel],
            }, owner)
        elif tag == "structured_schema":
            schema = _json_string(match["json"])
            validate_schema(schema)
            declare(MeaningType.STRUCTURED_SCHEMA, _unquote(match["name"]), {"schema": schema}, owner)
        elif tag == "fragment":
            text = _unquote(match["text"])
            declare(MeaningType.TEXT_FRAGMENT, _unquote(match["name"]), {
                "text": text, "text_sha256": sha256_bytes(text.encode("utf-8")),
            }, owner)
        elif tag == "patch":
            operation = _unquote(match["operation"])
            if operation not in {"REPLACE_SPAN", "INSERT_BEFORE", "INSERT_AFTER", "DELETE_SPAN"}:
                raise CompilationError("unsupported patch operation")
            declare(MeaningType.PATCH_TEMPLATE, _unquote(match["name"]), {"operation": operation}, owner)
        elif tag == "alias":
            aliases_raw.append((match, statement))
        else:
            deferred.append((tag, match, statement))

    # Values depend on declared scalar types.
    remaining: list[tuple[str, re.Match[str], Statement]] = []
    for tag, match, statement in deferred:
        owner = statement.provenance
        if tag in {"value", "enum", "list"}:
            type_id = target(MeaningType.SCALAR_TYPE, _unquote(match["type"]))
            type_item = meanings[type_id]
            value = _json_string(match["json"])
            if tag == "list":
                if not isinstance(value, list) or len(value) > 256:
                    raise CompilationError("LIST_VALUE requires an array within limit")
                if any(not value_matches_type(child, str(type_item.payload["json_type"])) for child in value):
                    raise CompilationError("LIST_VALUE element type mismatch")
                declare(MeaningType.LIST_VALUE, _unquote(match["name"]), {
                    "element_type_id": type_id, "value": value,
                }, owner)
            else:
                if not value_matches_type(value, str(type_item.payload["json_type"])):
                    raise CompilationError("VALUE type mismatch")
                kind = MeaningType.ENUM_MEMBER if tag == "enum" else MeaningType.VALUE
                declare(kind, _unquote(match["name"]), {"type_id": type_id, "value": value}, owner)
        else:
            remaining.append((tag, match, statement))

    def value_target(name: str) -> str:
        found = [
            by_name[(kind, name.casefold())]
            for kind in (MeaningType.VALUE, MeaningType.ENUM_MEMBER)
            if (kind, name.casefold()) in by_name
        ]
        if len(found) != 1:
            raise CompilationError(f"undeclared or ambiguous factor value: {name}")
        return found[0]

    # Finite domains depend on compiled VALUE or ENUM_MEMBER meanings.
    unresolved: list[tuple[str, re.Match[str], Statement]] = []
    for tag, match, statement in remaining:
        if tag != "finite_domain":
            unresolved.append((tag, match, statement))
            continue
        values = _json_string(match["values"])
        if not isinstance(values, list) or not 1 <= len(values) <= 256:
            raise CompilationError("finite domain size outside 1..256")
        if any(not isinstance(value, str) for value in values):
            raise CompilationError("finite domain values must be compiled names")
        value_ids = [value_target(normalize_text(value)) for value in values]
        if len(set(value_ids)) != len(value_ids):
            raise CompilationError("finite domain contains duplicate values")
        type_ids = {str(meanings[value_id].payload["type_id"]) for value_id in value_ids}
        if len(type_ids) != 1:
            raise CompilationError("finite domain values must share one scalar type")
        declare(MeaningType.FINITE_DOMAIN, _unquote(match["name"]), {
            "value_ids": value_ids, "type_id": next(iter(type_ids)),
        }, statement.provenance)
    remaining = unresolved

    # Factor templates depend on domains and their compiled values.
    unresolved = []
    for tag, match, statement in remaining:
        if tag != "factor_template":
            unresolved.append((tag, match, statement))
            continue
        table = _json_string(match["table"])
        if not isinstance(table, dict) or set(table) != {"ports", "allowed_tuples"}:
            raise CompilationError("factor table shape is invalid")
        raw_ports = table["ports"]
        raw_tuples = table["allowed_tuples"]
        if not isinstance(raw_ports, list) or not 1 <= len(raw_ports) <= 16:
            raise CompilationError("factor port count outside 1..16")
        ports: list[dict[str, str]] = []
        port_names: set[str] = set()
        domain_values: list[set[str]] = []
        for port in raw_ports:
            if not isinstance(port, dict) or set(port) != {"name", "domain"}:
                raise CompilationError("factor port shape is invalid")
            name = normalize_text(str(port["name"]))
            if not name or name in port_names:
                raise CompilationError("factor port name is empty or duplicate")
            domain_id = target(MeaningType.FINITE_DOMAIN, normalize_text(str(port["domain"])))
            ports.append({"name": name, "domain_id": domain_id})
            port_names.add(name)
            domain_values.append(set(meanings[domain_id].payload["value_ids"]))
        if not isinstance(raw_tuples, list) or not 1 <= len(raw_tuples) <= 4096:
            raise CompilationError("factor tuple count outside 1..4096")
        tuples: list[list[str]] = []
        for row in raw_tuples:
            if not isinstance(row, list) or len(row) != len(ports) or any(
                not isinstance(value, str) for value in row
            ):
                raise CompilationError("factor tuple arity or value shape is invalid")
            resolved = [value_target(normalize_text(value)) for value in row]
            if any(value not in domain_values[index] for index, value in enumerate(resolved)):
                raise CompilationError("factor tuple value is outside its port domain")
            tuples.append(resolved)
        canonical_tuples = sorted({tuple(row) for row in tuples})
        if len(canonical_tuples) != len(tuples):
            raise CompilationError("factor table contains duplicate tuples")
        declare(MeaningType.FACTOR_TEMPLATE, _unquote(match["name"]), {
            "ports": ports, "allowed_tuples": [list(row) for row in canonical_tuples],
        }, statement.provenance)
    remaining = unresolved

    # Relations, programs, instructions, tools, and schemas resolve by identifier.
    # Factor programs are materialized last so declaration order cannot affect
    # reference resolution for schema fields or other compiled meanings.
    remaining = sorted(
        remaining,
        key=lambda row: {"factor_program": 1, "semantic_contract": 2}.get(row[0], 0),
    )
    for tag, match, statement in remaining:
        owner = statement.provenance
        if tag == "relation_form":
            template = _unquote(match["template"])
            if template.count("{SOURCE}") != 1 or template.count("{DESTINATION}") != 1:
                raise CompilationError("relation form requires SOURCE and DESTINATION")
            declare(MeaningType.RELATION_FORM, _unquote(match["name"]), {
                "relation_id": target(MeaningType.RELATION, _unquote(match["relation"])),
                "template": template,
            }, owner)
        elif tag == "instruction":
            template = _unquote(match["template"])
            _template_pattern(template)
            declare(MeaningType.INSTRUCTION, _unquote(match["name"]), {
                "operation_id": target(MeaningType.OPERATION, _unquote(match["operation"])),
                "template": template,
            }, owner)
        elif tag == "prototype":
            template = _unquote(match["template"])
            _template_pattern(template)
            declare(MeaningType.INSTRUCTION_PROTOTYPE, _unquote(match["name"]), {
                "instruction_id": target(MeaningType.INSTRUCTION, _unquote(match["instruction"])),
                "template": template,
            }, owner)
        elif tag == "schema_field":
            declare(MeaningType.SCHEMA_FIELD, _unquote(match["name"]), {
                "schema_id": target(MeaningType.STRUCTURED_SCHEMA, _unquote(match["schema"])),
                "type_id": target(MeaningType.SCALAR_TYPE, _unquote(match["type"])),
                "required": match["required"] == "required",
            }, owner)
        elif tag == "sequence":
            names = [normalize_text(value) for value in _unquote(match["relations"]).split(",") if value.strip()]
            if not names or len(names) > 50:
                raise CompilationError("relation sequence length outside 1..50")
            declare(MeaningType.RELATION_SEQUENCE, _unquote(match["name"]), {
                "relation_ids": [target(MeaningType.RELATION, name) for name in names],
            }, owner)
        elif tag == "program":
            steps = _json_string(match["steps"])
            if not isinstance(steps, list) or not 1 <= len(steps) <= 16:
                raise CompilationError("program step count outside 1..16")
            for step in steps:
                if not isinstance(step, dict) or step.get("operation") not in OPERATIONS:
                    raise CompilationError("invalid program step")
                if set(step) & {"branch", "loop", "goto"}:
                    raise CompilationError("program branching and loops are unsupported")
            program_id = declare(MeaningType.PROGRAM, _unquote(match["name"]), {"steps": steps}, owner)
            for index, step in enumerate(steps):
                declare(MeaningType.PROGRAM_STEP, f"{_unquote(match['name'])}:{index}", {
                    "program_id": program_id, "index": index, "step": step,
                }, owner)
        elif tag == "factor_program":
            raw_steps = _json_string(match["steps"])
            if not isinstance(raw_steps, list) or not 1 <= len(raw_steps) <= 16_384:
                raise CompilationError("factor instruction count outside 1..16384")
            variables: dict[str, str] = {}
            factors: dict[str, str] = {}
            bound_ports: set[tuple[str, str]] = set()
            outputs: dict[int, str] = {}
            steps: list[dict[str, Any]] = []
            aggregate_cells = 0
            for index, raw_step in enumerate(raw_steps):
                if not isinstance(raw_step, dict) or raw_step.get("opcode") not in FACTOR_OPCODES:
                    raise CompilationError("invalid factor instruction opcode")
                opcode = str(raw_step["opcode"])
                step = dict(raw_step)
                if opcode == "CREATE_VARIABLE":
                    if set(step) != {"opcode", "instance", "domain"}:
                        raise CompilationError("CREATE_VARIABLE shape is invalid")
                    instance = normalize_text(str(step["instance"]))
                    if not instance or instance in variables:
                        raise CompilationError("variable instance is empty or duplicate")
                    domain_id = target(MeaningType.FINITE_DOMAIN, normalize_text(str(step["domain"])))
                    variables[instance] = domain_id
                    step["domain_id"] = domain_id
                    del step["domain"]
                elif opcode == "INSTANTIATE_FACTOR":
                    if set(step) != {"opcode", "instance", "template"}:
                        raise CompilationError("INSTANTIATE_FACTOR shape is invalid")
                    instance = normalize_text(str(step["instance"]))
                    if not instance or instance in factors:
                        raise CompilationError("factor instance is empty or duplicate")
                    template_id = target(MeaningType.FACTOR_TEMPLATE, normalize_text(str(step["template"])))
                    factors[instance] = template_id
                    template = meanings[template_id]
                    aggregate_cells += len(template.payload["ports"]) * len(template.payload["allowed_tuples"])
                    if aggregate_cells > 16_777_216:
                        raise CompilationError("RESOURCE_LIMIT: aggregate factor tuple cells")
                    step["template_id"] = template_id
                    del step["template"]
                elif opcode == "BIND_PORT":
                    if set(step) != {"opcode", "factor", "port", "variable"}:
                        raise CompilationError("BIND_PORT shape is invalid")
                    factor = normalize_text(str(step["factor"]))
                    variable = normalize_text(str(step["variable"]))
                    port = normalize_text(str(step["port"]))
                    if factor not in factors:
                        raise CompilationError("factor must be declared before BIND_PORT")
                    if variable not in variables:
                        raise CompilationError("variable must be declared before BIND_PORT")
                    ports = {item["name"]: item["domain_id"] for item in meanings[factors[factor]].payload["ports"]}
                    if port not in ports or ports[port] != variables[variable]:
                        raise CompilationError("factor port is absent or domain-mismatched")
                    if (factor, port) in bound_ports:
                        raise CompilationError("factor port is bound more than once")
                    bound_ports.add((factor, port))
                elif opcode == "CLAMP_FROM_PROMPT":
                    if set(step) != {"opcode", "variable", "field"}:
                        raise CompilationError("CLAMP_FROM_PROMPT shape is invalid")
                    variable = normalize_text(str(step["variable"]))
                    if variable not in variables:
                        raise CompilationError("variable must be declared before clamp")
                    field_id = target(MeaningType.SCHEMA_FIELD, normalize_text(str(step["field"])))
                    if meanings[field_id].payload["type_id"] != meanings[variables[variable]].payload["type_id"]:
                        raise CompilationError("prompt clamp field and variable domain are type-mismatched")
                    step["field_id"] = field_id
                    del step["field"]
                elif opcode == "CLAMP_LITERAL":
                    if set(step) != {"opcode", "variable", "value"}:
                        raise CompilationError("CLAMP_LITERAL shape is invalid")
                    variable = normalize_text(str(step["variable"]))
                    if variable not in variables:
                        raise CompilationError("variable must be declared before clamp")
                    value_id = value_target(normalize_text(str(step["value"])))
                    if value_id not in meanings[variables[variable]].payload["value_ids"]:
                        raise CompilationError("literal clamp is outside variable domain")
                    step["value_id"] = value_id
                    del step["value"]
                else:
                    if set(step) != {"opcode", "variable", "ordinal", "label"}:
                        raise CompilationError("EXPOSE_OUTPUT shape is invalid")
                    variable = normalize_text(str(step["variable"]))
                    ordinal = step["ordinal"]
                    if variable not in variables or not isinstance(ordinal, int) or isinstance(ordinal, bool):
                        raise CompilationError("output variable or ordinal is invalid")
                    if ordinal < 0 or ordinal in outputs:
                        raise CompilationError("output ordinal is negative or duplicate")
                    outputs[ordinal] = variable
                step["instruction_index"] = index
                steps.append(step)
            if len(variables) > 1024 or len(factors) > 4096:
                raise CompilationError("RESOURCE_LIMIT: factor program instances")
            for factor, template_id in factors.items():
                expected = {port["name"] for port in meanings[template_id].payload["ports"]}
                actual = {port for candidate, port in bound_ports if candidate == factor}
                if actual != expected:
                    raise CompilationError("factor program has an unbound port")
            if not outputs or sorted(outputs) != list(range(len(outputs))):
                raise CompilationError("factor outputs must have contiguous ordinals")
            program_id = declare(MeaningType.PROGRAM, _unquote(match["name"]), {
                "program_kind": "FACTOR", "steps": steps,
            }, owner)
            for index, step in enumerate(steps):
                declare(MeaningType.PROGRAM_STEP, f"{_unquote(match['name'])}:{index}", {
                    "program_id": program_id, "index": index, "step": step,
                }, owner)
        elif tag == "tool":
            declare(MeaningType.TOOL, _unquote(match["name"]), {
                "schema_id": target(MeaningType.STRUCTURED_SCHEMA, _unquote(match["schema"])),
            }, owner)
        elif tag == "tool_argument":
            declare(MeaningType.TOOL_ARGUMENT, _unquote(match["name"]), {
                "tool_id": target(MeaningType.TOOL, _unquote(match["tool"])),
                "field_id": target(MeaningType.SCHEMA_FIELD, _unquote(match["field"])),
            }, owner)
        elif tag == "semantic_contract":
            if world_role != WorldRole.INPUT:
                raise CompilationError("semantic contracts are valid only in Input Worlds")
            if sum(item.kind == MeaningType.SEMANTIC_CONTRACT for item in meanings.values()) >= 64:
                raise CompilationError("RESOURCE_LIMIT: semantic contracts per Input World")
            from .semantic import compile_semantic_contract

            compile_semantic_contract(
                name=_unquote(match["name"]),
                source=_json_string(match["json"]),
                owner=owner,
                meanings=meanings,
                target=target,
                declare=declare,
            )
        else:
            raise CompilationError(f"unsupported deferred declaration: {tag}")

    aliases: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for match, statement in aliases_raw:
        surface_kind = match["kind"]
        if surface_kind not in KIND_SURFACES:
            raise CompilationError(f"unsupported alias kind: {surface_kind}")
        kind = KIND_SURFACES[surface_kind]
        target_id = target(kind, _unquote(match["name"]))
        alias = _unquote(match["alias"])
        aliases[kind.value][alias.casefold()].append(target_id)
        declare(MeaningType.ALIAS, alias + "->" + target_id[:12], {
            "surface": alias, "kind": kind.value, "target_id": target_id,
        }, statement.provenance)

    # Compile relation premises after every relation form and endpoint meaning exists.
    forms = []
    for item in meanings.values():
        if item.kind == MeaningType.RELATION_FORM:
            template = str(item.payload["template"])
            expression = re.escape(template)
            expression = expression.replace(re.escape("{SOURCE}"), rf"(?P<source>{QUOTED})")
            expression = expression.replace(re.escape("{DESTINATION}"), rf"(?P<destination>{QUOTED})")
            forms.append((item, re.compile("^" + expression + "$")))
    edge_owners: dict[tuple[str, str, str], list[Provenance]] = defaultdict(list)
    for statement in unmatched:
        matches = [(item, pattern.fullmatch(statement.text)) for item, pattern in forms]
        matches = [(item, match) for item, match in matches if match is not None]
        if len(matches) != 1:
            raise CompilationError(f"unaccepted or ambiguous source language: {statement.text}")
        form, match = matches[0]
        source_name = _unquote(match["source"])
        destination_name = _unquote(match["destination"])
        source_id = None
        destination_id = None
        for endpoint_kind in (MeaningType.ENTITY, MeaningType.CODE_SYMBOL, MeaningType.CODE_FILE):
            source_id = source_id or by_name.get((endpoint_kind, source_name.casefold()))
            destination_id = destination_id or by_name.get((endpoint_kind, destination_name.casefold()))
        if source_id is None or destination_id is None:
            raise CompilationError("relation premise references undeclared meaning")
        edge_owners[(str(form.payload["relation_id"]), source_id, destination_id)].append(statement.provenance)

    if code_root is not None:
        from .python_adapter import compile_python_tree

        code_meanings, code_edges, code_sources = compile_python_tree(Path(code_root), meanings, by_name)
        for item in code_meanings:
            prior = by_name.get((item.kind, item.name.casefold()))
            if prior is not None and prior != item.meaning_id:
                raise CompilationError(f"conflicting compiled code meaning: {item.name}")
            meanings[item.meaning_id] = item
            by_name[(item.kind, item.name.casefold())] = item.meaning_id
        for edge in code_edges:
            edge_owners[(edge.relation_id, edge.source_id, edge.destination_id)].extend(edge.owners)
        sources.update(code_sources)

    # Program references remain source-level names in the immutable payload so
    # their content address is stable; compilation nevertheless proves closure.
    for program in (item for item in meanings.values() if item.kind == MeaningType.PROGRAM):
        for step in program.payload["steps"]:
            if "schema" in step:
                target(MeaningType.STRUCTURED_SCHEMA, str(step["schema"]))
            if "field" in step:
                target(MeaningType.SCHEMA_FIELD, str(step["field"]))

    edges = tuple(
        SemanticEdge(
            digest("moth-world-edge/5.0", {
                "relation_id": relation_id, "source_id": source_id,
                "destination_id": destination_id,
            }), relation_id, source_id, destination_id,
            tuple(sorted(set(edge_owners[(relation_id, source_id, destination_id)]))),
        )
        for relation_id, source_id, destination_id in sorted(edge_owners)
    )
    if len(meanings) > 50_000 or len(edges) > 250_000:
        raise CompilationError("RESOURCE_LIMIT: World size")

    # Functional relations are checked globally, including code edges.
    for relation in (item for item in meanings.values() if item.kind == MeaningType.RELATION):
        if relation.payload["cardinality"] != "functional":
            continue
        destinations: dict[str, set[str]] = defaultdict(set)
        for edge in edges:
            if edge.relation_id == relation.meaning_id:
                destinations[edge.source_id].add(edge.destination_id)
        if any(len(values) > 1 for values in destinations.values()):
            raise CompilationError(f"functional relation has multiple destinations: {relation.name}")

    names: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for identifier, item in sorted(meanings.items()):
        if item.kind != MeaningType.ALIAS:
            names[item.kind.value][item.name.casefold()].append(identifier)

    vectors: dict[str, VectorRecord] = {}
    encoder_hash = "NO_ENCODER"
    if encoder is not None:
        groundable = [item for _, item in sorted(meanings.items()) if item.kind not in {
            MeaningType.ALIAS, MeaningType.RELATION_FORM, MeaningType.PROGRAM_STEP,
            MeaningType.CODE_SPAN,
        }]
        texts = [str(item.payload.get("text", item.payload.get("template", item.name))) for item in groundable]
        encoded = encoder.encode_passages(texts)
        for item, text, vector in zip(groundable, texts, encoded):
            vectors[item.meaning_id] = VectorRecord(
                item.meaning_id, text, encoder.vector_hash(vector),
                tuple(float(value) for value in vector),
            )
        encoder_hash = encoder.fingerprint

    semantic = {
        "capability_level": capability_level,
        "meanings": {key: value.canonical(include_owners=False) for key, value in sorted(meanings.items())},
        "aliases": {
            kind: {surface: sorted(set(ids)) for surface, ids in sorted(values.items())}
            for kind, values in sorted(aliases.items())
        },
        "edges": [{
            "edge_id": edge.edge_id, "relation_id": edge.relation_id,
            "source_id": edge.source_id, "destination_id": edge.destination_id,
        } for edge in edges],
    }
    compiler_hash = digest("moth-world-compiler/5.0", semantic)
    world_payload = {
        "world_role": world_role.value,
        "compiler_hash": compiler_hash, "encoder_hash": encoder_hash,
        "vector_hashes": {key: value.vector_hash for key, value in sorted(vectors.items())},
        "parent": generation_parent, "sources": {key: value.sha256 for key, value in sorted(sources.items())},
    }
    world_hash = digest("moth-compiled-world/5.0", world_payload)
    generation_id = digest("moth-world-generation/5.0", world_payload)
    return CompiledWorld(
        sources, meanings,
        {kind: {surface: tuple(sorted(set(ids))) for surface, ids in values.items()} for kind, values in names.items()},
        {kind: {surface: tuple(sorted(set(ids))) for surface, ids in values.items()} for kind, values in aliases.items()},
        edges, vectors, world_hash, compiler_hash, encoder_hash, generation_id,
        capability_level, world_role,
    )
