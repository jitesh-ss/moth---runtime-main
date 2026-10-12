"""Small direct reference checks independent of settlement ranking."""

from __future__ import annotations

from moth_runtime_v4_9.canonical import canonical_bytes

from .model import SemanticSettlement, SemanticWorld


def verify_against_compiled_world(world: SemanticWorld, settlement: SemanticSettlement) -> None:
    matches = [item for item in world.meanings if item.meaning_id == settlement.meaning_id]
    if len(matches) != 1:
        raise AssertionError("settlement does not select exactly one compiled meaning")
    meaning = matches[0]
    if canonical_bytes(meaning.coordinate.canonical()) != canonical_bytes(settlement.coordinate.canonical()):
        raise AssertionError("settlement coordinate differs from compiled meaning")
    selection = settlement.trace.get("selection", {})
    if selection.get("meaning_id") != settlement.meaning_id:
        raise AssertionError("trace selection differs from result")
    if selection.get("total_energy_units") != settlement.total_energy_units:
        raise AssertionError("trace energy differs from result")
