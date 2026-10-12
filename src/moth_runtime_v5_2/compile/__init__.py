"""Lazy public exports for Runtime 5.2 source compilers."""

from __future__ import annotations

from importlib import import_module
from typing import Any


_EXPORTS = {
    "compile_energy_foundation": (".fields", "compile_energy_foundation"),
    "compile_context_message": (".hcf", "compile_context_message"),
    "compile_hcf_source": (".hcf", "compile_hcf_source"),
    "compile_system_prompt": (".hcf", "compile_system_prompt"),
    "compile_field_object": (".skills", "compile_field_object"),
    "compile_skill_object": (".skills", "compile_skill_object"),
    "load_field_object": (".skills", "load_field_object"),
    "load_skill_object": (".skills", "load_skill_object"),
    "plan_inert_skill": (".skills", "plan_inert_skill"),
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
