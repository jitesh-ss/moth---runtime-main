"""Lazy typed-energy exports for Runtime 5.3."""

from __future__ import annotations

from importlib import import_module
from typing import Any


_EXPORTS = {
    "EnergyFoundation": (".loader", "EnergyFoundation"),
    "HcfTensorField": (".loader", "HcfTensorField"),
    "load_energy_foundation": (".loader", "load_energy_foundation"),
    "load_hcf_field": (".loader", "load_hcf_field"),
    "SettlementResult": (".settlement", "SettlementResult"),
    "settle": (".settlement", "settle"),
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
