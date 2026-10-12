"""Direct lexicographic minimization over Runtime 5.3 tensors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from moth_runtime_v5_3.legacy.canonical import digest

from .activation import activation_mask
from .loader import EnergyFoundation, HcfTensorField
from .schema import Effect, Level, Runtime53Failure


@dataclass(frozen=True)
class SettlementResult:
    candidate_index: int
    candidate_id: str
    mode: str
    energy: tuple[int, int, int, int]
    trace: dict


def _entry_arrays(
    foundation: EnergyFoundation, fields: Sequence[HcfTensorField]
) -> dict[str, np.ndarray]:
    base = foundation.tensors
    parts = [
        {
            "entry_id": base["base_entry_id"],
            "entry_hash": base["base_entry_hash"],
            "level": np.full(
                len(base["base_entry_id"]),
                int(Level.BASE),
                dtype=np.uint8,
            ),
            "effect": base["base_effect"],
            "scope_index": base["base_scope_index"],
            "value_hash": base["base_value_hash"],
            "target_level": base["base_target_level"],
            "redelegable": base["base_redelegable"],
        }
    ]
    parts.extend(
        {name: field.tensors[name] for name in parts[0]} for field in fields
    )
    return {
        name: np.concatenate([part[name] for part in parts], axis=0)
        for name in parts[0]
    }


def _delegation(
    entries: dict[str, np.ndarray], owner: int, target: int, scope: int
) -> list[int]:
    effect = entries["effect"]
    levels = entries["level"]
    scopes = entries["scope_index"]
    targets = entries["target_level"]
    direct = np.flatnonzero(
        (effect == int(Effect.DELEGATE))
        & (levels == owner)
        & (scopes == scope)
        & (targets == target)
    )
    if len(direct):
        return [int(value) for value in direct]
    if owner == int(Level.BASE) and target == int(Level.CONTEXT):
        first = np.flatnonzero(
            (effect == int(Effect.DELEGATE))
            & (levels == int(Level.BASE))
            & (scopes == scope)
            & (targets == int(Level.SYSTEM))
            & (entries["redelegable"] == 1)
        )
        second = np.flatnonzero(
            (effect == int(Effect.DELEGATE))
            & (levels == int(Level.SYSTEM))
            & (scopes == scope)
            & (targets == int(Level.CONTEXT))
        )
        if len(first) and len(second):
            return [int(first[0]), int(second[0])]
    return []


def settle(
    foundation: EnergyFoundation, fields: Sequence[HcfTensorField]
) -> SettlementResult:
    mask = activation_mask(foundation, fields)
    active = np.flatnonzero(mask)
    if len(active) == 0:
        raise Runtime53Failure(
            "NO_CANDIDATE", "HCF settlement has no active candidates"
        )
    entries = _entry_arrays(foundation, fields)
    candidate_count = foundation.candidate_count
    energies = np.zeros((candidate_count, 4), dtype=np.int64)
    energies[:, 3] = foundation.tensors["grounding_cost_units"]
    constraints = np.flatnonzero(
        (entries["effect"] == int(Effect.REQUIRE))
        | (entries["effect"] == int(Effect.FORBID))
    )
    satisfied = np.ones(
        (len(entries["effect"]), candidate_count), dtype=bool
    )
    for row in constraints:
        scope = int(entries["scope_index"][row])
        present = foundation.tensors["candidate_property_present"][
            :, scope
        ].astype(bool)
        equal = np.all(
            foundation.tensors["candidate_property_value_hash"][:, scope]
            == entries["value_hash"][row],
            axis=1,
        )
        if entries["effect"][row] == int(Effect.REQUIRE):
            satisfied[row] = present & equal
        else:
            satisfied[row] = ~(present & equal)

    # Index delegation once per scope/level pair. Keep numeric decisions until
    # selection; detailed JSON is built only for the active trace rows below.
    delegated_rows = {}
    delegation_index = {}
    lower_index = {}
    for row in constraints:
        owner = int(entries['level'][row])
        scope = int(entries['scope_index'][row])
        key = (owner, scope)
        if key not in lower_index:
            lower_index[key] = [int(r) for r in constraints
                if int(entries['level'][r]) > owner and int(entries['scope_index'][r]) == scope]
        for lower in lower_index[key]:
            target = int(entries['level'][lower])
            dkey = (owner, target, scope)
            if dkey not in delegation_index:
                delegation_index[dkey] = _delegation(entries, owner, target, scope)
        for candidate in active:
            if satisfied[row, candidate]:
                continue
            grants = []
            for lower in lower_index[key]:
                if satisfied[lower, candidate]:
                    grants = delegation_index[owner, int(entries['level'][lower]), scope]
                    if grants:
                        break
            if grants:
                delegated_rows[int(row), int(candidate)] = grants
            else:
                energies[candidate, owner] += 1

    minimum = min(
        tuple(int(value) for value in energies[index]) for index in active
    )
    winners = [
        int(index)
        for index in active
        if tuple(int(value) for value in energies[index]) == minimum
    ]
    semantic_rows = {
        foundation.tensors["semantic_id"][index].tobytes()
        for index in winners
    }
    candidate_names = [
        foundation.labels[
            int(foundation.tensors["candidate_label_index"][index])
        ]
        for index in winners
    ]
    if len(semantic_rows) > 1:
        raise Runtime53Failure(
            "AMBIGUOUS_HCF",
            "distinct candidates share minimum HCF energy",
            {
                "energy": list(minimum),
                "candidate_ids": sorted(candidate_names),
            },
        )
    winner = min(
        winners,
        key=lambda index: foundation.tensors["candidate_id"][
            index
        ].tobytes(),
    )
    rows = []
    entry_ids = [row.tobytes().hex() for row in entries['entry_id']]
    for index in active:
        name = foundation.labels[int(foundation.tensors['candidate_label_index'][index])]
        vector = tuple(int(value) for value in energies[index])
        evaluations = []
        used = set()
        for row in constraints:
            grants = delegated_rows.get((int(row), int(index)), [])
            identifiers = [entry_ids[g] for g in grants]
            used.update(identifiers)
            evaluations.append({
                'entry_id': entry_ids[row], 'level': Level(int(entries['level'][row])).name,
                'scope_index': int(entries['scope_index'][row]),
                'satisfied': bool(satisfied[row,index]), 'delegated': bool(grants),
                'delegation_entry_ids': identifiers,
            })
        rows.append({
            'candidate_id':name,
            'energy':dict(zip(('base_violations','system_violations','context_violations','grounding_cost_units'),vector)),
            'evaluations':evaluations, 'delegation_entry_ids':sorted(used),
        })
    body = {
        "schema": "moth-hcf-settlement/5.3",
        "foundation_hash": foundation.logical_hash,
        "entry_hashes": [
            row.tobytes().hex() for row in entries["entry_hash"]
        ],
        "active_candidate_count": len(active),
        "candidates": sorted(rows, key=lambda row: row["candidate_id"]),
        "winner_id": foundation.labels[
            int(foundation.tensors["candidate_label_index"][winner])
        ],
        "winning_energy": {
            "base_violations": minimum[0],
            "system_violations": minimum[1],
            "context_violations": minimum[2],
            "grounding_cost_units": minimum[3],
        },
    }
    trace = {
        **body,
        "trace_hash": digest("moth-hcf-trace/5.3", body),
    }
    if any(minimum[:3]):
        raise Runtime53Failure(
            "HCF_CONFLICT",
            "minimum candidate retains a hierarchy violation",
            {"trace": trace},
        )
    return SettlementResult(
        winner,
        body["winner_id"],
        foundation.labels[
            int(foundation.tensors["candidate_mode_index"][winner])
        ],
        minimum,
        trace,
    )
