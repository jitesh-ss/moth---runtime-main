"""Experiment-local autonomous JSON router over a compiled Runtime 5.1 skill.

The candidate receives only a natural prompt.  It does not accept a per-turn
skill id, presentation mode, schema id, or task snapshot.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
import sqlite3
from typing import Any, Iterable

from moth_runtime_v5_0.canonical import canonical_bytes, digest, normalize_text, sha256_bytes
from moth_runtime_v5_0.model import IntegrityError
from moth_runtime_v5_1.compiled_fields import CompiledField, verify_skill_compilation
from moth_runtime_v5_1.hcf import (
    HcfEffect,
    HcfFailure,
    HierarchyLevel,
    make_entry,
    settle_candidates,
)


SCHEMA = "moth-autonomous-json-result/5.1-experiment"
SUPPORTED_TRIGGER = "NATURAL_JSON_FORMAT_REQUEST"
REQUIRED_WORKFLOW_ACTIONS = {
    "DETECT_JSON_INTENT",
    "PARSE_SOURCE_DATA",
    "BIND_OUTPUT_SHAPE",
    "PARSE_EMITTED_JSON",
    "VERIFY_EXACT_DATA",
    "VERIFY_REQUESTED_SHAPE",
    "BIND_HASHES",
    "EMIT_JSON",
}
SOURCE_MARKERS = ("source data:", "input json:", "given this json:")


class JsonSkillFailure(ValueError):
    def __init__(self, code: str, message: str, context: dict[str, Any] | None = None):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.context = context or {}


def _refusal(code: str, message: str, *, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    body = {
        "schema": SCHEMA,
        "status": "REFUSAL",
        "code": code,
        "message": message,
        "response": None,
        "value": None,
        "route": None,
        "hcf": None,
        "skill": None,
        "execution": {"network": 0, "tool_dispatches": 0, "code_executions": 0, "writes": 0},
        "evidence": evidence or {},
    }
    return {**body, "result_hash": digest(SCHEMA, body)}


def _depth(value: Any) -> int:
    if isinstance(value, dict):
        return 1 + max((_depth(item) for item in value.values()), default=0)
    if isinstance(value, list):
        return 1 + max((_depth(item) for item in value), default=0)
    return 0


def _record_count(value: Any) -> int:
    if isinstance(value, dict):
        return 1 + sum(_record_count(item) for item in value.values())
    if isinstance(value, list):
        return sum(_record_count(item) for item in value)
    return 0


def _extract_source(prompt: str) -> tuple[Any, str]:
    folded = prompt.casefold()
    positions = [(folded.find(marker), marker) for marker in SOURCE_MARKERS if marker in folded]
    if len(positions) != 1:
        raise JsonSkillFailure(
            "MALFORMED_SOURCE",
            "request must contain exactly one delimited strict JSON source",
        )
    start, marker = positions[0]
    raw = prompt[start + len(marker):].lstrip()
    try:
        value, end = json.JSONDecoder().raw_decode(raw)
    except json.JSONDecodeError as exc:
        raise JsonSkillFailure("MALFORMED_SOURCE", "source is not strict JSON", {"offset": exc.pos}) from exc
    trailing = raw[end:].strip()
    if trailing and not trailing.startswith("."):
        raise JsonSkillFailure("MALFORMED_SOURCE", "unexpected content follows source JSON")
    return value, prompt[:start].strip()


def _csv_fields(text: str) -> list[str]:
    cleaned = text.replace(" and ", ",")
    fields = [item.strip().strip("`\"'") for item in cleaned.split(",") if item.strip()]
    if not fields or len(set(fields)) != len(fields):
        raise JsonSkillFailure("AMBIGUOUS_FIELD", "field list is empty or ambiguous")
    return fields


def _select(record: dict[str, Any], fields: Iterable[str]) -> dict[str, Any]:
    selected: dict[str, Any] = {}
    for field in fields:
        if field not in record:
            raise JsonSkillFailure("MISSING_FIELD", "requested field is absent", {"field": field})
        selected[field] = deepcopy(record[field])
    return selected


def _route(instruction: str, source: Any) -> dict[str, Any]:
    text = normalize_text(instruction).casefold()
    if "json" not in text:
        raise JsonSkillFailure("UNRELATED_REQUEST", "request does not ask for JSON")
    if any(term in text for term in ("ignore the compiled skill", "use the network", "invoke a tool", "write the file", "execute code")):
        raise JsonSkillFailure("AUTHORITY_VIOLATION", "request asks for prohibited authority")
    if any(term in text for term in ("json5", "json lines", "jsonl", "yaml", "xml", "python literal")):
        raise JsonSkillFailure("UNSUPPORTED_FORMAT", "requested format is not strict JSON")
    if any(term in text for term in ("sum ", "average ", "calculate ", "compute total", "join with external")):
        raise JsonSkillFailure("UNSUPPORTED_TRANSFORMATION", "requested computation is outside the skill")
    if "compact" in text and ("pretty" in text or "indented" in text):
        raise JsonSkillFailure("AMBIGUOUS_FORMAT", "compact and pretty layouts conflict")
    if "canonical" in text and "source order" in text:
        raise JsonSkillFailure("HCF_CONFLICT", "canonical and source key order conflict")
    if "ambiguous field" in text:
        raise JsonSkillFailure("AMBIGUOUS_FIELD", "field reference is ambiguous")
    if "silently discard" in text or "without saying which fields" in text:
        raise JsonSkillFailure("LOSSY_TRANSFORMATION", "loss-inducing transformation is not explicit")

    route: dict[str, Any]
    nested = re.search(r"(?:under|beneath) (?:the )?(?:path )?([a-z][a-z0-9_.-]*(?:\.[a-z][a-z0-9_.-]*)+)", text)
    scalar_array = re.search(r"(?:array|list) of (?:the )?([a-z][a-z0-9_-]*) (?:values|field values)", text)
    record_fields = re.search(r"records? (?:containing|with|using) (?:only )?fields? ([a-z0-9_, -]+?)(?: as strict json| in json|$)", text)
    select_fields = re.search(r"(?:select|keep|return) (?:only )?fields? ([a-z0-9_, -]+?)(?: as| in| and rename|$)", text)

    if "paginated" in text or "pagination envelope" in text:
        route = {"family": "paginated_envelope"}
    elif "success/error" in text or "success or error" in text or "discriminated union" in text:
        route = {"family": "success_error_union"}
    elif "group" in text and " by " in text:
        match = re.search(r"group (?:the )?(?:records )?by ([a-z][a-z0-9_-]*)", text)
        if not match:
            raise JsonSkillFailure("AMBIGUOUS_FIELD", "grouping field is ambiguous")
        route = {"family": "grouped_records", "field": match.group(1)}
    elif "keyed" in text or "key the records" in text:
        match = re.search(r"(?:keyed by|key the records by|object keyed by) ([a-z][a-z0-9_-]*)", text)
        if not match:
            raise JsonSkillFailure("AMBIGUOUS_FIELD", "key field is ambiguous")
        route = {"family": "keyed_map", "field": match.group(1)}
    elif "envelope" in text:
        route = {"family": "result_envelope"}
    elif nested:
        route = {"family": "nested_object", "path": nested.group(1).split(".")}
    elif scalar_array:
        route = {"family": "scalar_array", "field": scalar_array.group(1)}
    elif "mixed events" in text or "heterogeneous records" in text:
        route = {"family": "heterogeneous_array"}
    elif record_fields:
        route = {"family": "homogeneous_records", "fields": _csv_fields(record_fields.group(1))}
    elif "include absent fields as null" in text or "fill missing fields with null" in text:
        route = {"family": "nullable_sparse", "null_policy": "include"}
    elif "omit null fields" in text or "remove fields whose value is null" in text:
        route = {"family": "nullable_sparse", "null_policy": "omit"}
    elif "rename" in text:
        pairs = re.findall(r"([a-z][a-z0-9_-]*) to ([a-z][a-z0-9_-]*)", text)
        if not pairs:
            raise JsonSkillFailure("AMBIGUOUS_FIELD", "rename mapping is ambiguous")
        targets = [target for _, target in pairs]
        if len(set(targets)) != len(targets):
            raise JsonSkillFailure("DUPLICATE_OUTPUT_KEY", "renames produce duplicate keys")
        route = {"family": "projection_rename", "renames": pairs}
    elif "canonical" in text and ("key" in text or "order" in text):
        route = {"family": "canonical_order"}
    elif "source order" in text:
        route = {"family": "source_order"}
    elif "compact" in text or "minified" in text or "single-line" in text:
        route = {"family": "compact_json"}
    elif "pretty" in text or "indented" in text:
        indent_match = re.search(r"(?:with|using) (two|four|2|4)[ -]space", text)
        if not indent_match:
            raise JsonSkillFailure("AMBIGUOUS_FORMAT", "pretty layout needs two or four spaces")
        route = {"family": "pretty_json", "indent": 2 if indent_match.group(1) in {"two", "2"} else 4}
    elif select_fields:
        route = {"family": "flat_selection", "fields": _csv_fields(select_fields.group(1))}
    else:
        raise JsonSkillFailure("UNSUPPORTED_TRANSFORMATION", "JSON shape request is unsupported")
    return route


def _realize(source: Any, route: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
    family = route["family"]
    layout = {"indent": None, "sort_keys": False, "compact": True}
    if family == "flat_selection":
        if not isinstance(source, dict):
            raise JsonSkillFailure("SOURCE_SHAPE_MISMATCH", "flat selection requires an object")
        value = _select(source, route["fields"])
    elif family == "nested_object":
        value = deepcopy(source)
        for key in reversed(route["path"]):
            value = {key: value}
    elif family == "scalar_array":
        if not isinstance(source, list) or not all(isinstance(item, dict) for item in source):
            raise JsonSkillFailure("SOURCE_SHAPE_MISMATCH", "scalar array requires records")
        field = route["field"]
        value = []
        for item in source:
            if field not in item:
                raise JsonSkillFailure("MISSING_FIELD", "requested field is absent", {"field": field})
            value.append(deepcopy(item[field]))
    elif family == "heterogeneous_array":
        if not isinstance(source, list):
            raise JsonSkillFailure("SOURCE_SHAPE_MISMATCH", "heterogeneous array requires an array")
        value = deepcopy(source)
    elif family == "homogeneous_records":
        if not isinstance(source, list) or not all(isinstance(item, dict) for item in source):
            raise JsonSkillFailure("SOURCE_SHAPE_MISMATCH", "record projection requires records")
        value = [_select(item, route["fields"]) for item in source]
    elif family == "keyed_map":
        if not isinstance(source, list) or not all(isinstance(item, dict) for item in source):
            raise JsonSkillFailure("SOURCE_SHAPE_MISMATCH", "keyed map requires records")
        field = route["field"]
        value = {}
        for item in source:
            if field not in item:
                raise JsonSkillFailure("MISSING_FIELD", "key field is absent", {"field": field})
            key = str(item[field])
            if key in value:
                raise JsonSkillFailure("DUPLICATE_OUTPUT_KEY", "key field is not unique", {"key": key})
            value[key] = deepcopy(item)
    elif family == "result_envelope":
        count = len(source) if isinstance(source, (list, dict)) else 1
        value = {"status": "ok", "data": deepcopy(source), "meta": {"count": count}}
    elif family == "paginated_envelope":
        if not isinstance(source, list):
            raise JsonSkillFailure("SOURCE_SHAPE_MISMATCH", "pagination requires an array")
        value = {"data": deepcopy(source), "pagination": {"page": 1, "per_page": len(source), "total": len(source)}}
    elif family == "success_error_union":
        if not isinstance(source, dict) or not isinstance(source.get("ok"), bool):
            raise JsonSkillFailure("SOURCE_SHAPE_MISMATCH", "union requires an ok boolean")
        if source["ok"]:
            if "data" not in source:
                raise JsonSkillFailure("MISSING_FIELD", "success union requires data", {"field": "data"})
            value = {"type": "success", "data": deepcopy(source["data"])}
        else:
            if "error" not in source:
                raise JsonSkillFailure("MISSING_FIELD", "error union requires error", {"field": "error"})
            value = {"type": "error", "error": deepcopy(source["error"])}
    elif family == "nullable_sparse":
        if not isinstance(source, list) or not all(isinstance(item, dict) for item in source):
            raise JsonSkillFailure("SOURCE_SHAPE_MISMATCH", "sparse handling requires records")
        if route["null_policy"] == "include":
            keys = sorted({key for item in source for key in item})
            value = [{key: deepcopy(item.get(key)) for key in keys} for item in source]
        else:
            value = [{key: deepcopy(item) for key, item in row.items() if item is not None} for row in source]
    elif family == "projection_rename":
        if not isinstance(source, dict):
            raise JsonSkillFailure("SOURCE_SHAPE_MISMATCH", "renaming requires an object")
        mapping = dict(route["renames"])
        if len(mapping) != len(route["renames"]):
            raise JsonSkillFailure("AMBIGUOUS_FIELD", "source field is renamed more than once")
        for key in mapping:
            if key not in source:
                raise JsonSkillFailure("MISSING_FIELD", "rename source is absent", {"field": key})
        value = {mapping.get(key, key): deepcopy(item) for key, item in source.items()}
        if len(value) != len(source):
            raise JsonSkillFailure("DUPLICATE_OUTPUT_KEY", "rename collides with an existing key")
    elif family == "grouped_records":
        if not isinstance(source, list) or not all(isinstance(item, dict) for item in source):
            raise JsonSkillFailure("SOURCE_SHAPE_MISMATCH", "grouping requires records")
        field = route["field"]
        value = {}
        for item in source:
            if field not in item:
                raise JsonSkillFailure("MISSING_FIELD", "group field is absent", {"field": field})
            value.setdefault(str(item[field]), []).append(deepcopy(item))
    elif family == "canonical_order":
        value = deepcopy(source)
        layout.update({"sort_keys": True})
    elif family == "source_order":
        value = deepcopy(source)
    elif family == "compact_json":
        value = deepcopy(source)
    elif family == "pretty_json":
        value = deepcopy(source)
        layout.update({"indent": route["indent"], "compact": False})
    else:
        raise JsonSkillFailure("UNSUPPORTED_TRANSFORMATION", "route has no realizer")
    return value, layout


def _render(value: Any, layout: dict[str, Any]) -> str:
    if layout["indent"] is not None:
        return json.dumps(value, ensure_ascii=False, indent=layout["indent"], sort_keys=layout["sort_keys"])
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=layout["sort_keys"],
        separators=(",", ":"),
    )


def _hcf_settle(skill: dict[str, Any], prompt_hash: str) -> tuple[dict[str, Any], dict[str, Any]]:
    entries = [
        make_entry(meaning_id="base.no-network", level=HierarchyLevel.BASE, effect=HcfEffect.REQUIRE, scope="runtime.network", value=False, source_hash=prompt_hash),
        make_entry(meaning_id="base.no-tools", level=HierarchyLevel.BASE, effect=HcfEffect.REQUIRE, scope="runtime.tool_execution", value=False, source_hash=prompt_hash),
        make_entry(meaning_id="base.no-writes", level=HierarchyLevel.BASE, effect=HcfEffect.REQUIRE, scope="runtime.world_management", value=False, source_hash=prompt_hash),
        make_entry(meaning_id="context.json-trigger", level=HierarchyLevel.CONTEXT, effect=HcfEffect.REQUIRE, scope="skill.trigger", value=SUPPORTED_TRIGGER, source_hash=prompt_hash),
    ]
    candidates = [
        {
            "candidate_id": "skill.autonomous-json-formatting",
            "semantic": {"compilation_id": skill["compilation_id"], "trigger": skill["policy"]["trigger"]},
            "properties": {
                "skill.trigger": skill["policy"]["trigger"],
                "runtime.network": False,
                "runtime.tool_execution": False,
                "runtime.world_management": False,
            },
            "grounding_cost_units": 0,
        },
        {
            "candidate_id": "skill.none",
            "semantic": {"compilation_id": None, "trigger": None},
            "properties": {
                "skill.trigger": None,
                "runtime.network": False,
                "runtime.tool_execution": False,
                "runtime.world_management": False,
            },
            "grounding_cost_units": 1,
        },
    ]
    return settle_candidates(candidates, entries)


def settle_json_request(
    prompt: str,
    field: CompiledField,
    skill: dict[str, Any] | None,
    *,
    router_enabled: bool = True,
    unrelated_skill: bool = False,
) -> dict[str, Any]:
    raw_prompt = prompt.replace("\r\n", "\n").replace("\r", "\n").strip()
    prompt_hash = sha256_bytes(raw_prompt.encode("utf-8"))
    if not router_enabled:
        return _refusal("ROUTER_DISABLED", "autonomous routing is disabled")
    if skill is None:
        return _refusal("SKILL_UNAVAILABLE", "JSON skill is not available")
    if unrelated_skill:
        return _refusal("SKILL_NOT_APPLICABLE", "available skill does not match JSON requests")
    try:
        verify_skill_compilation(skill, field)
        if skill["policy"].get("trigger") != SUPPORTED_TRIGGER:
            raise JsonSkillFailure("SKILL_NOT_APPLICABLE", "compiled trigger does not match JSON requests")
        workflow = set(skill["policy"].get("workflow", []))
        if not REQUIRED_WORKFLOW_ACTIONS.issubset(workflow):
            raise JsonSkillFailure("POLICY_INVALID", "compiled workflow lacks required verification actions")
        if len(raw_prompt.encode("utf-8")) > 32768:
            raise JsonSkillFailure("RESOURCE_LIMIT", "prompt exceeds byte limit")
        source, instruction = _extract_source(raw_prompt)
        if _depth(source) > 8 or _record_count(source) > 256:
            raise JsonSkillFailure("RESOURCE_LIMIT", "source exceeds depth or record limit")
        route = _route(instruction, source)
        candidate, hcf = _hcf_settle(skill, prompt_hash)
        value, layout = _realize(source, route)
        response = _render(value, layout)
        recovered = json.loads(response)
        if canonical_bytes(recovered) != canonical_bytes(value):
            raise JsonSkillFailure("VALUE_MISMATCH", "emitted JSON changed the planned value")
        route_body = {**route, "source_hash": digest("moth-json-source/5.1-experiment", source), "layout": layout}
        route_receipt = {**route_body, "route_hash": digest("moth-json-route/5.1-experiment", route_body)}
        body = {
            "schema": SCHEMA,
            "status": "ANSWER",
            "code": None,
            "message": None,
            "response": response,
            "value": recovered,
            "route": route_receipt,
            "hcf": hcf,
            "skill": {
                "field_hash": field.field_hash,
                "compilation_id": skill["compilation_id"],
                "policy_hash": skill["policy_hash"],
                "candidate_id": candidate["candidate_id"],
            },
            "execution": {"network": 0, "tool_dispatches": 0, "code_executions": 0, "writes": 0},
            "evidence": {"prompt_hash": prompt_hash, "response_hash": sha256_bytes(response.encode("utf-8"))},
        }
        return {**body, "result_hash": digest(SCHEMA, body)}
    except IntegrityError as exc:
        return _refusal("INTEGRITY_FAILURE", str(exc), evidence={"prompt_hash": prompt_hash})
    except HcfFailure as exc:
        return _refusal(exc.code, exc.message, evidence={"prompt_hash": prompt_hash, "hcf": exc.context})
    except JsonSkillFailure as exc:
        return _refusal(exc.code, exc.message, evidence={"prompt_hash": prompt_hash, **exc.context})


class AutonomousJsonRuntime:
    """A fresh persistent experiment instance with one artifact-bound skill."""

    def __init__(self, store_path: str | Path, field: CompiledField, skill: dict[str, Any]):
        self.path = Path(store_path)
        self.field = field
        self.skill = deepcopy(skill)
        verify_skill_compilation(self.skill, self.field)
        self.artifact_hash = digest(
            "moth-autonomous-json-artifact/5.1-experiment",
            {"field_hash": field.field_hash, "compilation_id": skill["compilation_id"], "policy_hash": skill["policy_hash"]},
        )
        self._init_store()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_store(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS conversations(id TEXT PRIMARY KEY, head INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS turns(
                    conversation_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    prompt TEXT NOT NULL,
                    result BLOB NOT NULL,
                    PRIMARY KEY(conversation_id, sequence)
                );
                """
            )
            row = connection.execute("SELECT value FROM metadata WHERE key='artifact_hash'").fetchone()
            if row is None:
                connection.execute("INSERT INTO metadata(key,value) VALUES('artifact_hash',?)", (self.artifact_hash,))
            elif row["value"] != self.artifact_hash:
                raise IntegrityError("experiment store artifact binding changed")

    def create_conversation(self) -> str:
        with self._connect() as connection:
            ordinal = connection.execute("SELECT COUNT(*) AS n FROM conversations").fetchone()["n"]
            identifier = digest("moth-json-conversation/5.1-experiment", {"artifact_hash": self.artifact_hash, "ordinal": ordinal})
            connection.execute("INSERT INTO conversations(id,head) VALUES(?,0)", (identifier,))
        return identifier

    def turn(self, conversation_id: str, prompt: str) -> dict[str, Any]:
        result = settle_json_request(prompt, self.field, self.skill)
        with self._connect() as connection:
            row = connection.execute("SELECT head FROM conversations WHERE id=?", (conversation_id,)).fetchone()
            if row is None:
                raise KeyError(conversation_id)
            sequence = int(row["head"]) + 1
            result = {**result, "conversation_id": conversation_id, "sequence": sequence, "artifact_hash": self.artifact_hash}
            result_body = {key: value for key, value in result.items() if key != "result_hash"}
            result["result_hash"] = digest(SCHEMA, result_body)
            connection.execute(
                "INSERT INTO turns(conversation_id,sequence,prompt,result) VALUES(?,?,?,?)",
                (conversation_id, sequence, prompt, canonical_bytes(result)),
            )
            connection.execute("UPDATE conversations SET head=? WHERE id=?", (sequence, conversation_id))
        return result

    def replay(self, conversation_id: str, sequence: int) -> bytes:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT result FROM turns WHERE conversation_id=? AND sequence=?",
                (conversation_id, sequence),
            ).fetchone()
            if row is None:
                raise KeyError((conversation_id, sequence))
            return bytes(row["result"])
