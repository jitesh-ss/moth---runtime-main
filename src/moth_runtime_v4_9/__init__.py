"""Independent opt-in Runtime 4.9 three-World runtime."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .canonical import read_json
from .encoder import LocalBGEEncoder
from .store import WorldStore


class ThreeWorldRuntime:
    """Bound Runtime 4.9 orchestrator over one active immutable World bundle."""

    def __init__(self, store: WorldStore, *, encoder: Any = None):
        self.store = store
        self.encoder = encoder or LocalBGEEncoder()
        config = Path(__file__).resolve().parents[2] / "config/v4.9/grounding-en-1.0.json"
        self.thresholds = read_json(config)["thresholds"]

    @classmethod
    def open(cls, path: str | Path, *, encoder: Any = None) -> "ThreeWorldRuntime":
        store = WorldStore(path)
        if store.active_bundle() is None:
            raise ValueError("Runtime 4.9 has no active three-world bundle")
        return cls(store, encoder=encoder)

    @classmethod
    def initialize(cls, path: str | Path) -> WorldStore:
        store = WorldStore(path)
        store.init()
        return store

    def query(self, prompt: str, *, modality: str = "text") -> dict[str, Any]:
        return self.store.query(
            prompt, encoder=self.encoder, thresholds=self.thresholds, modality=modality,
        )


__all__ = ["ThreeWorldRuntime", "WorldStore"]
