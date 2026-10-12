"""Canonical Runtime 4.7 closed-world proof-carrying energy field."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .canonical import read_json
from .encoder import LocalBGEEncoder
from .store import CapabilityStore


class CapabilityRuntime:
    """Bound runtime over one immutable Runtime 4.7 store generation."""

    def __init__(self, store: CapabilityStore, *, encoder: Any = None, generation_id: str | None = None):
        self.store = store
        self.encoder = encoder or LocalBGEEncoder()
        self.generation_id = generation_id
        config = Path(__file__).resolve().parents[2] / "config/grounding-en-1.0.json"
        self.thresholds = read_json(config)["thresholds"]

    @classmethod
    def open(cls, path: str | Path, *, encoder: Any = None, generation_id: str | None = None):
        store = CapabilityStore(path)
        store.load(generation_id)
        return cls(store, encoder=encoder, generation_id=generation_id)

    @classmethod
    def initialize(cls, path: str | Path) -> CapabilityStore:
        store = CapabilityStore(path)
        store.init()
        return store

    def query(self, prompt: str, *, modality: str = "text") -> dict[str, Any]:
        return self.store.query(
            prompt,
            encoder=self.encoder,
            thresholds=self.thresholds,
            generation_id=self.generation_id,
            modality=modality,
        )


__all__ = ["CapabilityRuntime", "CapabilityStore"]
