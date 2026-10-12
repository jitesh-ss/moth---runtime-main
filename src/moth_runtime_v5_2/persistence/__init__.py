"""Lazy persistence exports for Runtime 5.2."""

from __future__ import annotations

from importlib import import_module
from typing import Any


_EXPORTS = {
    "ObjectStore": (".objects", "ObjectStore"),
    "TensorEnvelope": (".objects", "TensorEnvelope"),
    "ConversationStore": (".store", "ConversationStore"),
    "ConcurrentTurnError": (".store", "ConcurrentTurnError"),
}
__all__ = list(_EXPORTS)


def __getattr__(name: str) -> Any:
    try:
        module_name, attribute = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(name) from exc
    value = getattr(import_module(module_name, __name__), attribute)
    globals()[name] = value
    return value
