"""Frozen structured-value schema subset and canonical materialization."""

from __future__ import annotations

import math
from typing import Any

from .canonical import canonical_bytes
from .model import CompilationError

ALLOWED_TYPES = {"object", "array", "string", "integer", "number", "boolean", "null"}


def validate_schema(schema: Any, *, depth: int = 0) -> None:
    if depth > 8 or not isinstance(schema, dict):
        raise CompilationError("INVALID_SCHEMA: schema nesting or node type")
    kind = schema.get("type")
    if kind not in ALLOWED_TYPES:
        raise CompilationError(f"INVALID_SCHEMA: unsupported type {kind!r}")
    allowed_keys = {
        "type", "properties", "required", "additionalProperties", "items", "enum",
        "x-moth-field", "const",
    }
    if set(schema) - allowed_keys:
        raise CompilationError("INVALID_SCHEMA: unsupported schema keyword")
    if "x-moth-field" in schema and not isinstance(schema["x-moth-field"], str):
        raise CompilationError("INVALID_SCHEMA: field binding must be a string")
    if kind == "object":
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        if not isinstance(properties, dict) or len(properties) > 64:
            raise CompilationError("INVALID_SCHEMA: object field limit")
        if schema.get("additionalProperties") is not False:
            raise CompilationError("INVALID_SCHEMA: additionalProperties must be false")
        if not isinstance(required, list) or len(required) != len(set(required)):
            raise CompilationError("INVALID_SCHEMA: invalid required fields")
        if any(name not in properties for name in required):
            raise CompilationError("INVALID_SCHEMA: required field is undeclared")
        for name, child in properties.items():
            if not isinstance(name, str):
                raise CompilationError("INVALID_SCHEMA: object key must be a string")
            validate_schema(child, depth=depth + 1)
    elif kind == "array":
        if "items" not in schema:
            raise CompilationError("INVALID_SCHEMA: array items missing")
        validate_schema(schema["items"], depth=depth + 1)
    if "enum" in schema:
        values = schema["enum"]
        if not isinstance(values, list) or not values:
            raise CompilationError("INVALID_SCHEMA: enum must be non-empty")
        for value in values:
            if not value_matches_type(value, kind):
                raise CompilationError("INVALID_SCHEMA: enum value type mismatch")
    if "const" in schema and not value_matches_type(schema["const"], kind):
        raise CompilationError("INVALID_SCHEMA: const type mismatch")


def value_matches_type(value: Any, kind: str) -> bool:
    if kind == "null":
        return value is None
    if kind == "boolean":
        return isinstance(value, bool)
    if kind == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if kind == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))
    if kind == "string":
        return isinstance(value, str)
    if kind == "array":
        return isinstance(value, list)
    if kind == "object":
        return isinstance(value, dict)
    return False


def validate_value(schema: dict[str, Any], value: Any, *, depth: int = 0) -> bool:
    if depth > 8 or not value_matches_type(value, str(schema["type"])):
        return False
    if "enum" in schema and value not in schema["enum"]:
        return False
    if "const" in schema and value != schema["const"]:
        return False
    if schema["type"] == "object":
        properties = schema.get("properties", {})
        if set(value) - set(properties):
            return False
        if any(name not in value for name in schema.get("required", [])):
            return False
        return all(validate_value(properties[name], child, depth=depth + 1) for name, child in value.items())
    if schema["type"] == "array":
        return len(value) <= 256 and all(validate_value(schema["items"], child, depth=depth + 1) for child in value)
    return True


def materialize(schema: dict[str, Any], bindings: dict[str, Any]) -> Any:
    """Construct a value using only declared field bindings and schema constants."""
    used: set[str] = set()

    def build(node: dict[str, Any], *, required: bool) -> tuple[bool, Any]:
        if "x-moth-field" in node:
            field = str(node["x-moth-field"])
            if field not in bindings:
                if required:
                    raise ValueError(f"MISSING_FIELD:{field}")
                return False, None
            used.add(field)
            value = bindings[field]
            if not validate_value(node, value):
                raise TypeError(f"TYPE_MISMATCH:{field}")
            return True, value
        if "const" in node:
            return True, node["const"]
        if node["type"] == "object":
            output: dict[str, Any] = {}
            required_names = set(node.get("required", []))
            for name, child in node.get("properties", {}).items():
                present, value = build(child, required=name in required_names)
                if present:
                    if name in output:
                        raise ValueError("DUPLICATE_FIELD")
                    output[name] = value
            return True, output
        if node["type"] == "array":
            raise ValueError("INVALID_SCHEMA: arrays require x-moth-field or const")
        if required:
            raise ValueError("MISSING_FIELD")
        return False, None

    present, result = build(schema, required=True)
    if not present:
        raise ValueError("MISSING_ROOT")
    if set(bindings) != used:
        raise ValueError("EXTRA_FIELD:" + ",".join(sorted(set(bindings) - used)))
    if not validate_value(schema, result):
        raise TypeError("TYPE_MISMATCH:result")
    if len(canonical_bytes(result)) > 65_536:
        raise ValueError("RESOURCE_LIMIT: rendered JSON exceeds 64 KiB")
    return result

