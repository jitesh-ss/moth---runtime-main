"""Bounded prompt parser and inert JSON transformation operations."""

from __future__ import annotations

from copy import deepcopy
import json
import re
from typing import Any, Iterable

from moth_runtime_v5_0.canonical import normalize_text


SOURCE_MARKERS = ("source data:", "input json:", "given this json:")


class JsonSkillFailure(ValueError):
    def __init__(self, code: str, message: str, context: dict[str, Any] | None = None):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.context = context or {}


def depth(value: Any) -> int:
    if isinstance(value, dict):
        return 1 + max((depth(item) for item in value.values()), default=0)
    if isinstance(value, list):
        return 1 + max((depth(item) for item in value), default=0)
    return 0


def record_count(value: Any) -> int:
    if isinstance(value, dict):
        return 1 + sum(record_count(item) for item in value.values())
    if isinstance(value, list):
        return sum(record_count(item) for item in value)
    return 0


def extract_source(prompt: str) -> tuple[Any, str]:
    folded = prompt.casefold()
    positions = [(folded.find(marker), marker) for marker in SOURCE_MARKERS if marker in folded]
    if len(positions) != 1:
        raise JsonSkillFailure("MALFORMED_SOURCE", "request must contain exactly one delimited strict JSON source")
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
    selected = {}
    for field in fields:
        if field not in record:
            raise JsonSkillFailure("MISSING_FIELD", "requested field is absent", {"field": field})
        selected[field] = deepcopy(record[field])
    return selected


def route(instruction: str) -> dict[str, Any]:
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

    nested = re.search(r"(?:under|beneath) (?:the )?(?:path )?([a-z][a-z0-9_.-]*(?:\.[a-z][a-z0-9_.-]*)+)", text)
    scalar_array = re.search(r"(?:array|list) of (?:the )?([a-z][a-z0-9_-]*) (?:values|field values)", text)
    record_fields = re.search(r"records? (?:containing|with|using) (?:only )?fields? ([a-z0-9_, -]+?)(?: as strict json| in json|$)", text)
    select_fields = re.search(r"(?:select|keep|return) (?:only )?fields? ([a-z0-9_, -]+?)(?: as| in| and rename|$)", text)
    if "paginated" in text or "pagination envelope" in text:
        return {"family": "paginated_envelope"}
    if "success/error" in text or "success or error" in text or "discriminated union" in text:
        return {"family": "success_error_union"}
    if "group" in text and " by " in text:
        match = re.search(r"group (?:the )?(?:records )?by ([a-z][a-z0-9_-]*)", text)
        if not match:
            raise JsonSkillFailure("AMBIGUOUS_FIELD", "grouping field is ambiguous")
        return {"family": "grouped_records", "field": match.group(1)}
    if "keyed" in text or "key the records" in text:
        match = re.search(r"(?:keyed by|key the records by|object keyed by) ([a-z][a-z0-9_-]*)", text)
        if not match:
            raise JsonSkillFailure("AMBIGUOUS_FIELD", "key field is ambiguous")
        return {"family": "keyed_map", "field": match.group(1)}
    if "envelope" in text:
        return {"family": "result_envelope"}
    if nested:
        return {"family": "nested_object", "path": nested.group(1).split(".")}
    if scalar_array:
        return {"family": "scalar_array", "field": scalar_array.group(1)}
    if "mixed events" in text or "heterogeneous records" in text:
        return {"family": "heterogeneous_array"}
    if record_fields:
        return {"family": "homogeneous_records", "fields": _csv_fields(record_fields.group(1))}
    if "include absent fields as null" in text or "fill missing fields with null" in text:
        return {"family": "nullable_sparse", "null_policy": "include"}
    if "omit null fields" in text or "remove fields whose value is null" in text:
        return {"family": "nullable_sparse", "null_policy": "omit"}
    if "rename" in text:
        pairs = re.findall(r"([a-z][a-z0-9_-]*) to ([a-z][a-z0-9_-]*)", text)
        if not pairs:
            raise JsonSkillFailure("AMBIGUOUS_FIELD", "rename mapping is ambiguous")
        if len({target for _, target in pairs}) != len(pairs):
            raise JsonSkillFailure("DUPLICATE_OUTPUT_KEY", "renames produce duplicate keys")
        return {"family": "projection_rename", "renames": pairs}
    if "canonical" in text and ("key" in text or "order" in text):
        return {"family": "canonical_order"}
    if "source order" in text:
        return {"family": "source_order"}
    if "compact" in text or "minified" in text or "single-line" in text:
        return {"family": "compact_json"}
    if "pretty" in text or "indented" in text:
        match = re.search(r"(?:with|using) (two|four|2|4)[ -]space", text)
        if not match:
            raise JsonSkillFailure("AMBIGUOUS_FORMAT", "pretty layout needs two or four spaces")
        return {"family": "pretty_json", "indent": 2 if match.group(1) in {"two", "2"} else 4}
    if select_fields:
        return {"family": "flat_selection", "fields": _csv_fields(select_fields.group(1))}
    raise JsonSkillFailure("UNSUPPORTED_TRANSFORMATION", "JSON shape request is unsupported")


def realize(source: Any, operation: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
    family = operation["family"]
    layout = {"indent": None, "sort_keys": False, "compact": True}
    if family == "flat_selection":
        if not isinstance(source, dict):
            raise JsonSkillFailure("SOURCE_SHAPE_MISMATCH", "flat selection requires an object")
        value = _select(source, operation["fields"])
    elif family == "nested_object":
        value = deepcopy(source)
        for key in reversed(operation["path"]):
            value = {key: value}
    elif family == "scalar_array":
        if not isinstance(source, list) or not all(isinstance(item, dict) for item in source):
            raise JsonSkillFailure("SOURCE_SHAPE_MISMATCH", "scalar array requires records")
        field = operation["field"]
        if any(field not in item for item in source):
            raise JsonSkillFailure("MISSING_FIELD", "requested field is absent", {"field": field})
        value = [deepcopy(item[field]) for item in source]
    elif family == "heterogeneous_array":
        if not isinstance(source, list):
            raise JsonSkillFailure("SOURCE_SHAPE_MISMATCH", "heterogeneous array requires an array")
        value = deepcopy(source)
    elif family == "homogeneous_records":
        if not isinstance(source, list) or not all(isinstance(item, dict) for item in source):
            raise JsonSkillFailure("SOURCE_SHAPE_MISMATCH", "record projection requires records")
        value = [_select(item, operation["fields"]) for item in source]
    elif family == "keyed_map":
        if not isinstance(source, list) or not all(isinstance(item, dict) for item in source):
            raise JsonSkillFailure("SOURCE_SHAPE_MISMATCH", "keyed map requires records")
        field, value = operation["field"], {}
        for item in source:
            if field not in item:
                raise JsonSkillFailure("MISSING_FIELD", "key field is absent", {"field": field})
            key = str(item[field])
            if key in value:
                raise JsonSkillFailure("DUPLICATE_OUTPUT_KEY", "key field is not unique", {"key": key})
            value[key] = deepcopy(item)
    elif family == "result_envelope":
        value = {"status": "ok", "data": deepcopy(source), "meta": {"count": len(source) if isinstance(source, (list, dict)) else 1}}
    elif family == "paginated_envelope":
        if not isinstance(source, list):
            raise JsonSkillFailure("SOURCE_SHAPE_MISMATCH", "pagination requires an array")
        value = {"data": deepcopy(source), "pagination": {"page": 1, "per_page": len(source), "total": len(source)}}
    elif family == "success_error_union":
        if not isinstance(source, dict) or not isinstance(source.get("ok"), bool):
            raise JsonSkillFailure("SOURCE_SHAPE_MISMATCH", "union requires an ok boolean")
        branch = "data" if source["ok"] else "error"
        if branch not in source:
            raise JsonSkillFailure("MISSING_FIELD", f"union requires {branch}", {"field": branch})
        value = {"type": "success" if source["ok"] else "error", branch: deepcopy(source[branch])}
    elif family == "nullable_sparse":
        if not isinstance(source, list) or not all(isinstance(item, dict) for item in source):
            raise JsonSkillFailure("SOURCE_SHAPE_MISMATCH", "sparse handling requires records")
        if operation["null_policy"] == "include":
            keys = sorted({key for item in source for key in item})
            value = [{key: deepcopy(item.get(key)) for key in keys} for item in source]
        else:
            value = [{key: deepcopy(item) for key, item in row.items() if item is not None} for row in source]
    elif family == "projection_rename":
        if not isinstance(source, dict):
            raise JsonSkillFailure("SOURCE_SHAPE_MISMATCH", "renaming requires an object")
        mapping = dict(operation["renames"])
        if len(mapping) != len(operation["renames"]):
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
        field, value = operation["field"], {}
        for item in source:
            if field not in item:
                raise JsonSkillFailure("MISSING_FIELD", "group field is absent", {"field": field})
            value.setdefault(str(item[field]), []).append(deepcopy(item))
    elif family in {"canonical_order", "source_order", "compact_json", "pretty_json"}:
        value = deepcopy(source)
        if family == "canonical_order":
            layout["sort_keys"] = True
        if family == "pretty_json":
            layout.update({"indent": operation["indent"], "compact": False})
    else:
        raise JsonSkillFailure("UNSUPPORTED_TRANSFORMATION", "route has no realizer")
    return value, layout


def render(value: Any, layout: dict[str, Any]) -> str:
    if layout["indent"] is not None:
        return json.dumps(value, ensure_ascii=False, indent=layout["indent"], sort_keys=layout["sort_keys"])
    return json.dumps(value, ensure_ascii=False, sort_keys=layout["sort_keys"], separators=(",", ":"))
