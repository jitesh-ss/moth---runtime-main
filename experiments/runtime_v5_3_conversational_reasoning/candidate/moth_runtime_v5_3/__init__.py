"""Moth Runtime 5.3 public interface with lazy module loading."""

from __future__ import annotations

from importlib import import_module
from typing import Any


__all__ = [
    "ConversationalRuntime",
    "ConversationStore",
    "EnergyFoundation",
    "FieldKind",
    "HcfTensorField",
    "Level",
    "ModelArtifact53",
    "Runtime53",
    "Runtime53Failure",
    "RuntimeFoundation",
    "load_foundation",
]


_EXPORTS = {
    "Kernel53": (".kernel", "Kernel53"),
    "ReasoningRequest": (".reasoning", "ReasoningRequest"),
    "ReasoningResult": (".reasoning", "ReasoningResult"),
    "ConversationalRuntime": (".runtime", "ConversationalRuntime"),
    "ConversationStore": (".persistence.store", "ConversationStore"),
    "EnergyFoundation": (".energy.loader", "EnergyFoundation"),
    "FieldKind": (".compiled_fields", "FieldKind"),
    "HcfTensorField": (".energy.loader", "HcfTensorField"),
    "Level": (".energy.schema", "Level"),
    "ModelArtifact53": (".artifact", "ModelArtifact53"),
    "Runtime53": (".runtime", "Runtime53"),
    "Runtime53Failure": (".energy.schema", "Runtime53Failure"),
    "RuntimeFoundation": (".assets", "RuntimeFoundation"),
    "load_foundation": (".assets", "load_foundation"),
}


def __getattr__(name: str) -> Any:
    try:
        module_name, attribute = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(name) from exc
    value = getattr(import_module(module_name, __name__), attribute)
    globals()[name] = value
    return value
