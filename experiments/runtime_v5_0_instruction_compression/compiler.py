"""Compile bounded ordinary agent skills into granular instruction policies."""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any

from .model import (
    COMPILATION_SCHEMA,
    POLICY_SCHEMA,
    Clause,
    CompilationFailure,
    FieldValidationError,
    canonical_bytes,
    digest,
    normalize_text,
    policy_hash,
    sha256_bytes,
)


EXPECTED_LAYERS = {"L1", "L2", "L3"}
EXPECTED_PROFILES = {"SAFE_TEXT_PATCH", "EVIDENCE_LEDGER"}


def _duplicates(values: list[str]) -> set[str]:
    seen: set[str] = set()
    return {value for value in values if value in seen or seen.add(value)}


def validate_field(field: dict[str, Any]) -> dict[str, Any]:
    if field.get("schema") != "moth-instruction-base-field/1.0":
        raise FieldValidationError("FIELD", "unsupported field schema")
    if set(field.get("layers", {})) != EXPECTED_LAYERS:
        raise FieldValidationError("FIELD", "hierarchy layers are incomplete")

    actions = field["layers"]["L1"].get("actions", [])
    states = field["layers"]["L1"].get("states", [])
    if not actions or not states or _duplicates(actions) or _duplicates(states):
        raise FieldValidationError("L1", "atomic actions/states are empty or duplicated")

    operators = set(field["layers"]["L2"].get("operators", []))
    conditions = set(field["layers"]["L2"].get("conditions", []))
    required_operators = {
        "SEQUENCE", "REQUIRES", "MUST", "MUST_NOT", "ASK_FIRST",
        "REFUSE_IF", "COMPLETE_IF", "INSERT_BEFORE",
    }
    if not required_operators <= operators or not conditions:
        raise FieldValidationError("L2", "control/policy substrate is incomplete")

    macros = field["layers"]["L3"].get("workflow_macros", {})
    for name, expansion in macros.items():
        if not name or not expansion or any(action not in actions for action in expansion):
            raise FieldValidationError("L3", f"invalid workflow macro: {name}")

    rules = field.get("interpretation_rules", [])
    rule_ids = [str(rule.get("id", "")) for rule in rules]
    if not rules or "" in rule_ids or _duplicates(rule_ids):
        raise FieldValidationError("L4", "interpretation rules are empty or duplicated")
    for rule in rules:
        if not rule.get("sections") or not rule.get("groups"):
            raise FieldValidationError("L4", f"interpretation rule is incomplete: {rule['id']}")
        if any(not group or any(not normalize_text(str(item)) for item in group) for group in rule["groups"]):
            raise FieldValidationError("L4", f"interpretation group is empty: {rule['id']}")

    profiles = field.get("skill_profiles", {})
    if set(profiles) != EXPECTED_PROFILES:
        raise FieldValidationError("L5", "skill profiles are incomplete")
    for profile_id, profile in profiles.items():
        if set(profile.get("required_rules", [])) - set(rule_ids):
            raise FieldValidationError("L5", f"profile has undeclared rules: {profile_id}")
        if any(macro not in macros for macro in profile.get("workflow", [])):
            raise FieldValidationError("L5", f"profile has undeclared workflow: {profile_id}")
        for policy in profile.get("policies", []):
            if policy.get("mode") not in operators:
                raise FieldValidationError("L2", f"undeclared policy operator: {policy.get('mode')}")
            if policy.get("condition") not in conditions:
                raise FieldValidationError("L2", f"undeclared policy condition: {policy.get('condition')}")

    composition = field.get("composition_rules", [])
    if len(composition) != 1:
        raise FieldValidationError("L6", "exactly one bounded composition rule is required")
    rule = composition[0]
    if rule.get("base") not in profiles or rule.get("extension") not in profiles:
        raise FieldValidationError("L6", "composition references an undeclared profile")
    if rule.get("operator") not in operators or rule.get("insert_action") not in actions:
        raise FieldValidationError("L6", "composition operator/action is undeclared")

    return {
        "L1": {"actions": len(actions), "states": len(states)},
        "L2": {"operators": len(operators), "conditions": len(conditions)},
        "L3": {"workflow_macros": len(macros)},
        "L4": {"interpretation_rules": len(rules)},
        "L5": {"skill_profiles": len(profiles)},
        "L6": {"composition_rules": len(composition)},
    }


def parse_skill(document: str) -> tuple[dict[str, str], list[Clause]]:
    if len(document.encode("utf-8")) > 65_536:
        raise CompilationFailure("RESOURCE_LIMIT", "skill exceeds frozen byte limit")
    lines = document.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    metadata: dict[str, str] = {}
    clauses: list[Clause] = []
    section = ""
    in_frontmatter = bool(lines and lines[0].strip() == "---")
    frontmatter_closed = not in_frontmatter

    for index, raw in enumerate(lines, 1):
        stripped = raw.strip()
        if in_frontmatter:
            if index > 1 and stripped == "---":
                in_frontmatter = False
                frontmatter_closed = True
                continue
            if index == 1:
                continue
            if ":" not in stripped:
                raise CompilationFailure("MALFORMED_SKILL", "invalid frontmatter", {"line": index})
            key, value = stripped.split(":", 1)
            metadata[normalize_text(key).casefold()] = normalize_text(value)
            continue
        if stripped.startswith("## "):
            section = normalize_text(stripped[3:]).casefold()
            continue
        if not stripped or stripped.startswith("# "):
            continue
        text = stripped[2:] if stripped.startswith("- ") else stripped
        if section in {"procedure", "safety", "completion"}:
            normalized = normalize_text(text)
            clauses.append(Clause(section, normalized, index, sha256_bytes(normalized.encode("utf-8"))))

    if not frontmatter_closed or not metadata.get("name") or not metadata.get("description"):
        raise CompilationFailure("MALFORMED_SKILL", "name and description frontmatter are required")
    description = normalize_text(metadata["description"])
    clauses.insert(0, Clause("description", description, 3, sha256_bytes(description.encode("utf-8"))))
    if len(clauses) > 64:
        raise CompilationFailure("RESOURCE_LIMIT", "too many normative clauses")
    return metadata, clauses


def _matches(clause: Clause, rule: dict[str, Any]) -> bool:
    if clause.section not in rule["sections"]:
        return False
    text = clause.text.casefold()
    return all(any(normalize_text(str(phrase)).casefold() in text for phrase in group) for group in rule["groups"])


def _edges(workflow: list[str]) -> list[list[str]]:
    return [[left, right] for left, right in zip(workflow, workflow[1:])]


def validate_policy(policy: dict[str, Any], field: dict[str, Any]) -> None:
    if policy.get("schema") != POLICY_SCHEMA:
        raise CompilationFailure("INVALID_POLICY", "policy schema is invalid")
    actions = set(field["layers"]["L1"]["actions"])
    operators = set(field["layers"]["L2"]["operators"])
    conditions = set(field["layers"]["L2"]["conditions"])
    workflow = policy.get("workflow", [])
    if not workflow or len(workflow) != len(set(workflow)) or set(workflow) - actions:
        raise CompilationFailure("INVALID_POLICY", "workflow actions are missing, duplicated, or undeclared")
    if policy.get("edges") != _edges(workflow):
        raise CompilationFailure("INVALID_POLICY", "workflow dependency graph is not a total sequence")
    for item in policy.get("policies", []):
        if item.get("mode") not in operators or item.get("condition") not in conditions:
            raise CompilationFailure("INVALID_POLICY", "policy uses an undeclared operator or condition")
    units = 1 + len(workflow) + len(policy["edges"]) + len(policy.get("policies", [])) + len(policy.get("completion", []))
    if units > int(field["limits"]["maximum_graph_units"]):
        raise CompilationFailure("RESOURCE_LIMIT", "compiled graph exceeds frozen unit limit")


def compile_skill(
    document: str,
    field: dict[str, Any],
    *,
    ignored_rule_ids: set[str] | None = None,
) -> dict[str, Any]:
    validate_field(field)
    metadata, clauses = parse_skill(document)
    ignored = ignored_rule_ids or set()
    evidence: list[dict[str, Any]] = []
    recognized: set[str] = set()
    rules = list(field["interpretation_rules"])

    for clause in clauses:
        matched = [rule for rule in rules if _matches(clause, rule)]
        if not matched:
            raise CompilationFailure(
                "UNSUPPORTED_INSTRUCTION",
                "normative clause has no compiled interpretation",
                {"line": clause.line, "section": clause.section, "clause": clause.text},
            )
        if len(matched) != 1:
            raise CompilationFailure(
                "AMBIGUOUS_INSTRUCTION",
                "normative clause selects multiple interpretations",
                {"line": clause.line, "rules": sorted(rule["id"] for rule in matched)},
            )
        rule_id = matched[0]["id"]
        if rule_id in ignored:
            continue
        recognized.add(rule_id)
        evidence.append({"rule_id": rule_id, "clause": clause.as_dict()})

    candidates = []
    for profile_id, profile in field["skill_profiles"].items():
        required = set(profile["required_rules"])
        if recognized == required:
            candidates.append((profile_id, profile))
    if len(candidates) != 1:
        missing_by_profile = {
            profile_id: sorted(set(profile["required_rules"]) - recognized)
            for profile_id, profile in field["skill_profiles"].items()
        }
        raise CompilationFailure(
            "INCOMPLETE_SKILL",
            "skill does not uniquely satisfy a compiled profile",
            {"recognized": sorted(recognized), "missing": missing_by_profile},
        )

    profile_id, profile = candidates[0]
    macros = field["layers"]["L3"]["workflow_macros"]
    workflow = [action for macro in profile["workflow"] for action in macros[macro]]
    policy = {
        "schema": POLICY_SCHEMA,
        "policy_id": profile_id,
        "trigger": profile["trigger"],
        "workflow": workflow,
        "edges": _edges(workflow),
        "policies": sorted(deepcopy(profile["policies"]), key=lambda item: item["id"]),
        "completion": sorted(profile["completion"]),
    }
    validate_policy(policy, field)
    trace = {
        "source_name": metadata["name"],
        "source_hash": sha256_bytes(document.encode("utf-8")),
        "profile_id": profile_id,
        "recognized_rules": sorted(recognized),
        "clause_evidence": evidence,
        "normative_clause_count": len(clauses),
        "graph_unit_count": 1 + len(policy["workflow"]) + len(policy["edges"]) + len(policy["policies"]) + len(policy["completion"]),
    }
    return {
        "schema": COMPILATION_SCHEMA,
        "field_id": field["field_id"],
        "field_hash": digest("moth-instruction-base-field/1.0", field),
        "policy": policy,
        "policy_hash": policy_hash(policy),
        "trace": trace,
        "trace_hash": digest("moth-skill-compilation-trace/1.0", trace),
    }


def compose_skills(base: dict[str, Any], extension: dict[str, Any], field: dict[str, Any]) -> dict[str, Any]:
    validate_field(field)
    base_policy = base["policy"]
    extension_policy = extension["policy"]
    matches = [
        rule for rule in field["composition_rules"]
        if rule["base"] == base_policy["policy_id"] and rule["extension"] == extension_policy["policy_id"]
    ]
    if len(matches) != 1:
        raise CompilationFailure("UNSUPPORTED_COMPOSITION", "no unique composition rule")
    rule = matches[0]
    workflow = list(base_policy["workflow"])
    anchor = rule["anchor_action"]
    if workflow.count(anchor) != 1 or rule["insert_action"] in workflow:
        raise CompilationFailure("UNSUPPORTED_COMPOSITION", "composition anchor is missing or ambiguous")
    workflow.insert(workflow.index(anchor), rule["insert_action"])
    policies = {item["id"]: deepcopy(item) for item in base_policy["policies"]}
    for item in extension_policy["policies"]:
        prior = policies.get(item["id"])
        if prior is not None and prior != item:
            raise CompilationFailure("CONFLICTING_INSTRUCTIONS", "composed policy conflicts")
        policies[item["id"]] = deepcopy(item)
    policy = {
        "schema": POLICY_SCHEMA,
        "policy_id": f"{base_policy['policy_id']}+{extension_policy['policy_id']}",
        "trigger": base_policy["trigger"],
        "workflow": workflow,
        "edges": _edges(workflow),
        "policies": sorted(policies.values(), key=lambda item: item["id"]),
        "completion": sorted(set(base_policy["completion"]) | set(extension_policy["completion"])),
    }
    validate_policy(policy, field)
    trace = {
        "composition_rule": rule["id"],
        "base_policy_hash": base["policy_hash"],
        "extension_policy_hash": extension["policy_hash"],
        "operator": rule["operator"],
        "insert_action": rule["insert_action"],
        "anchor_action": rule["anchor_action"],
    }
    return {
        "schema": COMPILATION_SCHEMA,
        "field_id": field["field_id"],
        "field_hash": digest("moth-instruction-base-field/1.0", field),
        "policy": policy,
        "policy_hash": policy_hash(policy),
        "trace": trace,
        "trace_hash": digest("moth-skill-composition-trace/1.0", trace),
    }


def semantic_policy_bytes(compilation: dict[str, Any]) -> bytes:
    return canonical_bytes(compilation["policy"])
