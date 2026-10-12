"""Compiled L1-L6 fields, inert skill compilation, and plan-only evaluation."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath
import re
from typing import Any

from moth_runtime_v5_0.canonical import canonical_bytes, digest, normalize_text, sha256_bytes
from moth_runtime_v5_0.model import IntegrityError


FIELD_ARCHIVE_SCHEMA = "moth-layered-compiled-field/5.2"
SKILL_COMPILATION_SCHEMA = "moth-skill-compilation/5.2"
SKILL_POLICY_SCHEMA = "moth-compiled-skill-policy/5.2"
PLAN_SCHEMA = "moth-inert-skill-plan/5.2"


class FieldKind(StrEnum):
    INSTRUCTION = "INSTRUCTION"
    SURFACE_NATURAL = "SURFACE_NATURAL"
    SURFACE_RICH = "SURFACE_RICH"
    SURFACE_STRUCTURED = "SURFACE_STRUCTURED"
    SURFACE_PYTHON = "SURFACE_PYTHON"


class FieldFailure(ValueError):
    def __init__(self, code: str, message: str, context: dict[str, Any] | None = None):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.context = context or {}


@dataclass(frozen=True)
class CompiledField:
    field_id: str
    kind: FieldKind
    archive: dict[str, Any]

    @property
    def field_hash(self) -> str:
        return str(self.archive["field_hash"])

    @property
    def source(self) -> dict[str, Any]:
        return deepcopy(self.archive["source"])

    @property
    def capabilities(self) -> tuple[str, ...]:
        return tuple(self.archive["capabilities"])


def _duplicates(values: list[str]) -> set[str]:
    seen: set[str] = set()
    return {value for value in values if value in seen or seen.add(value)}


def _field_inventory(field: dict[str, Any]) -> dict[str, Any]:
    field_id = field.get("field_id")
    layers = field.get("layers")
    if not isinstance(field_id, str) or not field_id or not isinstance(layers, dict):
        raise FieldFailure("INVALID_FIELD", "field identity or layers are invalid")
    if set(layers) != {"L1", "L2", "L3"}:
        raise FieldFailure("INVALID_FIELD", "compiled field requires L1, L2, and L3")
    l1, l2, l3 = layers["L1"], layers["L2"], layers["L3"]
    if not all(isinstance(value, dict) for value in (l1, l2, l3)):
        raise FieldFailure("INVALID_FIELD", "compiled layer must be an object")
    actions = [str(value) for value in l1.get("actions", [])]
    states = [str(value) for value in l1.get("states", [])]
    operators = [str(value) for value in l2.get("operators", [])]
    conditions = [str(value) for value in l2.get("conditions", [])]
    macros = l3.get("workflow_macros", {})
    if (
        not actions or not states or not operators or not conditions
        or not isinstance(macros, dict) or not macros
        or any(_duplicates(values) for values in (actions, states, operators, conditions))
    ):
        raise FieldFailure("INVALID_FIELD", "L1-L3 field substrate is incomplete or duplicated")
    for name, expansion in macros.items():
        if not name or not isinstance(expansion, list) or not expansion or set(expansion) - set(actions):
            raise FieldFailure("INVALID_FIELD", f"workflow macro is invalid: {name}")
    rules = field.get("interpretation_rules")
    profiles = field.get("skill_profiles")
    if not isinstance(rules, list) or not rules or not isinstance(profiles, dict) or not profiles:
        raise FieldFailure("INVALID_FIELD", "L4 rules or L5 profiles are absent")
    rule_ids = [str(rule.get("id", "")) for rule in rules if isinstance(rule, dict)]
    if len(rule_ids) != len(rules) or "" in rule_ids or _duplicates(rule_ids):
        raise FieldFailure("INVALID_FIELD", "L4 interpretation-rule identities are invalid")
    for rule in rules:
        groups = rule.get("groups")
        sections = rule.get("sections")
        if not isinstance(groups, list) or not groups or not isinstance(sections, list) or not sections:
            raise FieldFailure("INVALID_FIELD", f"L4 rule is incomplete: {rule['id']}")
        if any(not isinstance(group, list) or not group for group in groups):
            raise FieldFailure("INVALID_FIELD", f"L4 rule group is invalid: {rule['id']}")
    for profile_id, profile in profiles.items():
        if not isinstance(profile, dict) or set(profile.get("required_rules", [])) - set(rule_ids):
            raise FieldFailure("INVALID_FIELD", f"L5 profile has undeclared rules: {profile_id}")
        if set(profile.get("workflow", [])) - set(macros):
            raise FieldFailure("INVALID_FIELD", f"L5 profile has undeclared macros: {profile_id}")
    composition = field.get("composition_rules", [])
    if not isinstance(composition, list):
        raise FieldFailure("INVALID_FIELD", "L6 composition rules are invalid")
    return {
        "L1": {"actions": len(actions), "states": len(states)},
        "L2": {"operators": len(operators), "conditions": len(conditions)},
        "L3": {"workflow_macros": len(macros)},
        "L4": {"interpretation_rules": len(rules)},
        "L5": {"skill_profiles": len(profiles)},
        "L6": {"composition_rules": len(composition)},
    }


def compile_field_archive(
    field: dict[str, Any], kind: FieldKind | str, capabilities: list[str] | tuple[str, ...],
) -> dict[str, Any]:
    kind = FieldKind(str(kind))
    inventory = _field_inventory(field)
    capability_ids = sorted({str(value) for value in capabilities})
    if not capability_ids or any(not value for value in capability_ids):
        raise FieldFailure("INVALID_FIELD", "field capabilities are empty")
    source = deepcopy(field)
    source_bytes = canonical_bytes(source)
    body = {
        "schema": FIELD_ARCHIVE_SCHEMA,
        "field_id": str(field["field_id"]),
        "kind": kind.value,
        "source_schema": str(field.get("schema", "")),
        "source_hash": sha256_bytes(source_bytes),
        "inventory": inventory,
        "interpretation_rule_hashes": {
            str(rule["id"]): digest("moth-field-rule/5.2", rule)
            for rule in sorted(field["interpretation_rules"], key=lambda item: str(item["id"]))
        },
        "skill_profile_hashes": {
            str(profile_id): digest("moth-field-profile/5.2", profile)
            for profile_id, profile in sorted(field["skill_profiles"].items())
        },
        "capabilities": capability_ids,
        "compiler": "moth-layered-skill-compiler/5.2",
        "verifier": "moth-layered-field-verifier/5.2",
        "limits": deepcopy(field.get("limits", {})),
        "source": source,
    }
    return {**body, "field_hash": digest("moth-layered-compiled-field/5.2", body)}


def load_field_archive(value: dict[str, Any]) -> CompiledField:
    if not isinstance(value, dict) or value.get("schema") != FIELD_ARCHIVE_SCHEMA:
        raise IntegrityError("compiled field archive schema is invalid")
    body = {key: item for key, item in value.items() if key != "field_hash"}
    if set(value) != {
        "schema", "field_id", "kind", "source_schema", "source_hash", "inventory",
        "interpretation_rule_hashes", "skill_profile_hashes", "capabilities", "compiler",
        "verifier", "limits", "source", "field_hash",
    }:
        raise IntegrityError("compiled field archive shape is invalid")
    try:
        kind = FieldKind(str(value["kind"]))
        rebuilt = compile_field_archive(value["source"], kind, value["capabilities"])
    except (FieldFailure, TypeError, ValueError) as exc:
        raise IntegrityError("compiled field archive content is invalid") from exc
    if canonical_bytes(rebuilt) != canonical_bytes(value):
        raise IntegrityError("compiled field archive differs from reconstruction")
    if value["field_hash"] != digest("moth-layered-compiled-field/5.2", body):
        raise IntegrityError("compiled field hash changed")
    return CompiledField(str(value["field_id"]), kind, deepcopy(value))


def _parse_skill(document: str, field: dict[str, Any]) -> tuple[dict[str, str], list[dict[str, Any]]]:
    limits = field.get("limits", {})
    maximum_bytes = int(limits.get("maximum_skill_bytes", 65_536))
    maximum_clauses = int(limits.get("maximum_normative_clauses", limits.get("maximum_clauses", 64)))
    if len(document.encode("utf-8")) > maximum_bytes:
        raise FieldFailure("RESOURCE_LIMIT", "skill exceeds compiled field byte limit")
    # Preserve the clause boundaries of the qualified compilers.  A field may
    # mention ``purpose`` as an alternative match location, but the frozen
    # compilers intentionally treat prose in that section as non-normative.
    if field.get("schema") == "moth-instruction-base-field/1.0":
        admitted_sections = {"procedure", "safety", "completion"}
    else:
        admitted_sections = {"workflow", "fidelity", "size", "completion"}
    lines = document.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    metadata: dict[str, str] = {}
    clauses: list[dict[str, Any]] = []
    section = ""
    in_frontmatter = bool(lines and lines[0].strip() == "---")
    frontmatter_closed = not in_frontmatter
    for line_number, raw in enumerate(lines, 1):
        stripped = raw.strip()
        if in_frontmatter:
            if line_number > 1 and stripped == "---":
                in_frontmatter = False
                frontmatter_closed = True
                continue
            if line_number == 1:
                continue
            if ":" not in stripped:
                raise FieldFailure("MALFORMED_SKILL", "invalid skill frontmatter")
            key, raw_value = stripped.split(":", 1)
            metadata[normalize_text(key).casefold()] = normalize_text(raw_value)
            continue
        if stripped.startswith("## "):
            section = normalize_text(stripped[3:]).casefold()
            continue
        if not stripped or stripped.startswith("# ") or section not in admitted_sections:
            continue
        text = normalize_text(stripped[2:] if stripped.startswith("- ") else stripped)
        clauses.append({
            "section": section, "text": text, "line": line_number,
            "clause_hash": sha256_bytes(text.encode("utf-8")),
        })
    if not frontmatter_closed or not metadata.get("name") or not metadata.get("description"):
        raise FieldFailure("MALFORMED_SKILL", "name and description frontmatter are required")
    text = normalize_text(metadata["description"])
    clauses.insert(0, {
        "section": "description", "text": text, "line": 3,
        "clause_hash": sha256_bytes(text.encode("utf-8")),
    })
    if len(clauses) > maximum_clauses:
        raise FieldFailure("RESOURCE_LIMIT", "skill exceeds compiled clause limit")
    return metadata, clauses


def _matches(clause: dict[str, Any], rule: dict[str, Any]) -> bool:
    if clause["section"] not in {str(value).casefold() for value in rule["sections"]}:
        return False
    text = str(clause["text"]).casefold()
    return all(
        any(normalize_text(str(phrase)).casefold() in text for phrase in group)
        for group in rule["groups"]
    )


def _policy_hash(policy: dict[str, Any]) -> str:
    return digest("moth-compiled-skill-policy/5.2", policy)


def compile_skill_document(field: CompiledField, document: str) -> dict[str, Any]:
    source = field.source
    metadata, clauses = _parse_skill(document, source)
    evidence: list[dict[str, Any]] = []
    recognized: set[str] = set()
    for clause in clauses:
        matches = [rule for rule in source["interpretation_rules"] if _matches(clause, rule)]
        if not matches:
            raise FieldFailure(
                "UNSUPPORTED_INSTRUCTION", "normative clause has no compiled interpretation",
                {"line": clause["line"], "section": clause["section"]},
            )
        if len(matches) != 1:
            raise FieldFailure(
                "AMBIGUOUS_INSTRUCTION", "normative clause selects multiple interpretations",
                {"line": clause["line"], "rules": sorted(str(item["id"]) for item in matches)},
            )
        rule_id = str(matches[0]["id"])
        recognized.add(rule_id)
        evidence.append({"rule_id": rule_id, "clause": clause})
    profiles = [
        (str(profile_id), profile)
        for profile_id, profile in source["skill_profiles"].items()
        if recognized == set(profile.get("required_rules", []))
    ]
    if len(profiles) != 1:
        raise FieldFailure(
            "INCOMPLETE_SKILL", "skill does not uniquely satisfy a compiled profile",
            {"recognized": sorted(recognized)},
        )
    profile_id, profile = profiles[0]
    macros = source["layers"]["L3"]["workflow_macros"]
    workflow = [action for macro in profile.get("workflow", []) for action in macros[macro]]
    policy = {
        "schema": SKILL_POLICY_SCHEMA,
        "policy_id": profile_id,
        "trigger": profile.get("trigger"),
        "workflow": workflow,
        "edges": [[left, right] for left, right in zip(workflow, workflow[1:])],
        "policies": sorted(deepcopy(profile.get("policies", [])), key=lambda item: str(item.get("id", ""))),
        "completion": sorted(str(value) for value in profile.get("completion", [])),
    }
    source_hash = sha256_bytes(normalize_text(document).encode("utf-8"))
    trace = {
        "field_id": field.field_id, "field_hash": field.field_hash,
        "profile_id": profile_id, "source_hash": source_hash,
        "normative_clause_count": len(clauses),
        "graph_unit_count": 1 + len(policy["workflow"]) + len(policy["edges"])
        + len(policy["policies"]) + len(policy["completion"]),
        "evidence": evidence,
    }
    trace_hash = digest("moth-skill-compilation-trace/5.2", trace)
    body = {
        "schema": SKILL_COMPILATION_SCHEMA,
        "field_id": field.field_id, "field_hash": field.field_hash,
        "field_kind": field.kind.value, "skill_name": metadata["name"],
        "profile_id": profile_id, "source_hash": source_hash,
        "policy": policy, "policy_hash": _policy_hash(policy),
        "trace": trace, "trace_hash": trace_hash,
    }
    return {**body, "compilation_id": digest("moth-skill-compilation-id/5.2", body)}


def verify_skill_compilation(compilation: dict[str, Any], field: CompiledField) -> None:
    if compilation.get("schema") != SKILL_COMPILATION_SCHEMA:
        raise IntegrityError("skill compilation schema is invalid")
    if compilation.get("field_id") != field.field_id or compilation.get("field_hash") != field.field_hash:
        raise IntegrityError("skill compilation field binding changed")
    if compilation.get("field_kind") != field.kind.value:
        raise IntegrityError("skill compilation field kind changed")
    policy = compilation.get("policy")
    trace = compilation.get("trace")
    if not isinstance(policy, dict) or policy.get("schema") != SKILL_POLICY_SCHEMA:
        raise IntegrityError("compiled skill policy is invalid")
    if compilation.get("policy_hash") != _policy_hash(policy):
        raise IntegrityError("compiled skill policy hash changed")
    if not isinstance(trace, dict) or compilation.get("trace_hash") != digest("moth-skill-compilation-trace/5.2", trace):
        raise IntegrityError("skill compilation trace hash changed")
    body = {key: value for key, value in compilation.items() if key != "compilation_id"}
    if compilation.get("compilation_id") != digest("moth-skill-compilation-id/5.2", body):
        raise IntegrityError("skill compilation identity changed")


def compose_skill_compilations(
    base: dict[str, Any], extension: dict[str, Any], field: CompiledField,
) -> dict[str, Any]:
    """Apply one declared L6 composition rule without interpreting new text."""
    verify_skill_compilation(base, field)
    verify_skill_compilation(extension, field)
    base_policy, extension_policy = base["policy"], extension["policy"]
    matches = [
        rule for rule in field.source.get("composition_rules", [])
        if rule.get("base") == base_policy.get("policy_id")
        and rule.get("extension") == extension_policy.get("policy_id")
    ]
    if len(matches) != 1:
        raise FieldFailure("UNSUPPORTED_COMPOSITION", "no unique L6 composition rule")
    rule = matches[0]
    workflow = list(base_policy["workflow"])
    anchor, inserted = str(rule["anchor_action"]), str(rule["insert_action"])
    if workflow.count(anchor) != 1 or inserted in workflow:
        raise FieldFailure("UNSUPPORTED_COMPOSITION", "composition anchor is missing or ambiguous")
    workflow.insert(workflow.index(anchor), inserted)
    policies = {str(item["id"]): deepcopy(item) for item in base_policy.get("policies", [])}
    for item in extension_policy.get("policies", []):
        item_id = str(item["id"])
        if item_id in policies and policies[item_id] != item:
            raise FieldFailure("CONFLICTING_INSTRUCTIONS", "composed policies conflict")
        policies[item_id] = deepcopy(item)
    policy = {
        "schema": SKILL_POLICY_SCHEMA,
        "policy_id": f"{base_policy['policy_id']}+{extension_policy['policy_id']}",
        "trigger": base_policy.get("trigger"),
        "workflow": workflow,
        "edges": [[left, right] for left, right in zip(workflow, workflow[1:])],
        "policies": sorted(policies.values(), key=lambda item: str(item["id"])),
        "completion": sorted(set(base_policy.get("completion", [])) | set(extension_policy.get("completion", []))),
    }
    source_hash = digest(
        "moth-composed-skill-sources/5.2",
        {"base": base["source_hash"], "extension": extension["source_hash"]},
    )
    trace = {
        "field_id": field.field_id,
        "field_hash": field.field_hash,
        "profile_id": policy["policy_id"],
        "source_hash": source_hash,
        "composition_rule": str(rule["id"]),
        "base_compilation_id": base["compilation_id"],
        "extension_compilation_id": extension["compilation_id"],
        "base_policy_hash": base["policy_hash"],
        "extension_policy_hash": extension["policy_hash"],
        "operator": str(rule["operator"]),
        "insert_action": inserted,
        "anchor_action": anchor,
    }
    body = {
        "schema": SKILL_COMPILATION_SCHEMA,
        "field_id": field.field_id,
        "field_hash": field.field_hash,
        "field_kind": field.kind.value,
        "skill_name": "safe-text-patch-with-evidence",
        "profile_id": policy["policy_id"],
        "source_hash": source_hash,
        "policy": policy,
        "policy_hash": _policy_hash(policy),
        "trace": trace,
        "trace_hash": digest("moth-skill-compilation-trace/5.2", trace),
    }
    result = {**body, "compilation_id": digest("moth-skill-compilation-id/5.2", body)}
    verify_skill_compilation(result, field)
    return result


def plan_inert_skill(
    compilation: dict[str, Any], task: dict[str, Any], *, artifact_hash: str | None = None,
) -> dict[str, Any]:
    """Evaluate a file-edit skill against embedded text without touching a filesystem."""
    policy = compilation["policy"]
    target = task.get("target")
    files = task.get("files", {})
    status, code = "ACTION_PLAN", None
    patch: dict[str, Any] | None = None
    if not isinstance(files, dict) or not isinstance(target, str) or not target:
        status, code = "REFUSAL", "TARGET_NOT_UNIQUE"
    else:
        path = PurePosixPath(target)
        if path.is_absolute() or ".." in path.parts:
            status, code = "REFUSAL", "SCOPE_VIOLATION"
        elif target in task.get("binary_files", []):
            status, code = "REFUSAL", "UNSUPPORTED_TARGET"
        elif target not in files:
            status, code = "REFUSAL", "TARGET_NOT_UNIQUE"
        elif path.suffix.casefold() not in {".txt", ".md", ".json", ".toml", ".yaml", ".yml"}:
            status, code = "REFUSAL", "UNSUPPORTED_TARGET"
        elif task.get("extra_change"):
            status, code = "REFUSAL", "SCOPE_VIOLATION"
        elif task.get("protected") and not task.get("authorized"):
            status, code = "AUTHORITY_REQUIRED", "PROTECTED_TARGET"
        else:
            current, old, new = files[target], task.get("old"), task.get("new")
            if not all(isinstance(value, str) for value in (current, old, new)):
                status, code = "REFUSAL", "PRECONDITION_FAILED"
            elif not old or old == new or current.count(old) != 1:
                status, code = "REFUSAL", "PRECONDITION_FAILED"
            else:
                proposed = current.replace(old, new, 1)
                patch = {
                    "path": target, "old": old, "new": new,
                    "before_sha256": sha256_bytes(current.encode("utf-8")),
                    "after_sha256": sha256_bytes(proposed.encode("utf-8")),
                    "proposed_text": proposed,
                }
    body = {
        "schema": PLAN_SCHEMA, "status": status, "code": code,
        "task_hash": digest("moth-inert-skill-task/5.2", task),
        "compilation_id": compilation["compilation_id"],
        "policy_hash": compilation["policy_hash"],
        "model_artifact_hash": artifact_hash,
        "workflow": list(policy["workflow"]), "patch": patch,
        "verification_steps": list(policy.get("completion", [])) if patch else [],
        "execution": {"performed": False, "dispatch_count": 0, "writes": 0},
    }
    return {**body, "plan_hash": digest("moth-inert-skill-plan/5.2", body)}
