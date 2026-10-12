"""Candidate activation over immutable foundation masks."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from .loader import EnergyFoundation, HcfTensorField


def activation_mask(
    foundation: EnergyFoundation, fields: Sequence[HcfTensorField]
) -> np.ndarray:
    mask = foundation.tensors["candidate_enabled_default"].astype(
        bool, copy=True
    )
    for field in sorted(
        fields,
        key=lambda item: int(item.level) if item.level is not None else -1,
    ):
        for identity, state in zip(
            field.tensors["activation_candidate"],
            field.tensors["activation_state"],
        ):
            mask[foundation.candidate_index(identity.tobytes())] = bool(state)
    return mask
