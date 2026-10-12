"""Independent pinned BGE adapter and deterministic unit-test encoder."""

from __future__ import annotations

import json
from pathlib import Path
import threading
from typing import Sequence

import numpy as np

from .canonical import digest, sha256_bytes, sha256_file
from .model import IntegrityError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENCODER_MANIFEST = PROJECT_ROOT / "config/v5.0/encoder-text-en-1.0.json"


class LocalBGEEncoder:
    def __init__(self, model_path: str | Path | None = None):
        self.manifest = json.loads(ENCODER_MANIFEST.read_text(encoding="utf-8"))
        self.path = Path(model_path).resolve() if model_path else (
            PROJECT_ROOT / self.manifest["model_path"]
        ).resolve()
        self.dimension = int(self.manifest["dimension"])
        self.batch_size = int(self.manifest["batch_size"])
        self.query_prefix = str(self.manifest["query_prefix"])
        self.fingerprint = digest("moth-world-encoder/5.0", {
            key: value for key, value in self.manifest.items() if key != "model_path"
        })
        self._model = None
        self._lock = threading.RLock()
        self._query_cache: dict[str, np.ndarray] = {}

    def verify_assets(self) -> dict[str, object]:
        if not self.path.is_dir():
            raise IntegrityError(f"pinned encoder directory is missing: {self.path}")
        for name, expected in self.manifest["model_files"].items():
            path = self.path / name
            if not path.is_file() or sha256_file(path) != expected:
                raise IntegrityError(f"pinned encoder asset mismatch: {name}")
        return {"verified": True, "dimension": self.dimension, "fingerprint": self.fingerprint}

    def _load(self):
        if self._model is not None:
            return self._model
        with self._lock:
            if self._model is not None:
                return self._model
            self.verify_assets()
            try:
                import torch
                from sentence_transformers import SentenceTransformer

                torch.set_num_threads(1)
                torch.use_deterministic_algorithms(True)
                model = SentenceTransformer(str(self.path), local_files_only=True, device="cpu")
                model.eval()
                for parameter in model.parameters():
                    parameter.requires_grad_(False)
            except Exception as exc:
                raise IntegrityError("unable to load pinned local BGE encoder") from exc
            dimension_getter = getattr(model, "get_embedding_dimension", None)
            if dimension_getter is None:
                dimension_getter = model.get_sentence_embedding_dimension
            dimension = dimension_getter()
            if int(dimension) != self.dimension:
                raise IntegrityError("encoder dimension differs from manifest")
            self._model = model
            return model

    def token_count(self, text: str) -> int:
        encoded = self._load().tokenizer(text, add_special_tokens=False, truncation=False)
        return len(encoded["input_ids"])

    def _encode(self, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, self.dimension), dtype="<f4")
        with self._lock:
            values = self._load().encode(
                list(texts), batch_size=self.batch_size, normalize_embeddings=True,
                show_progress_bar=False, convert_to_numpy=True,
            )
        vectors = np.asarray(values, dtype="<f4")
        if vectors.shape != (len(texts), self.dimension) or not np.isfinite(vectors).all():
            raise IntegrityError("encoder returned invalid vectors")
        return vectors

    def encode_passages(self, texts: list[str]) -> np.ndarray:
        return self._encode(texts)

    def encode_query(self, text: str, *, token_limit: int = 128) -> np.ndarray:
        if self.token_count(text) > token_limit:
            raise ValueError("RESOURCE_LIMIT: prompt exceeds token limit")
        if text not in self._query_cache:
            self._query_cache[text] = self._encode([self.query_prefix + text])[0]
        return self._query_cache[text].copy()

    def vector_hash(self, vector: np.ndarray) -> str:
        raw = np.asarray(vector, dtype="<f4").tobytes(order="C")
        return sha256_bytes(b"moth-world-vector/5.0\0" + self.fingerprint.encode() + raw)


class DeterministicEncoder:
    """Small, deterministic encoder for focused mechanics tests only."""

    dimension = 64
    fingerprint = "DETERMINISTIC-TEST-ENCODER-64"

    @staticmethod
    def _one(text: str) -> np.ndarray:
        vector = np.zeros(64, dtype="<f4")
        normalized = " ".join(text.casefold().split())
        tokens = normalized.replace("_", " ").replace("-", " ").split()
        for token in tokens or [normalized]:
            raw = bytes.fromhex(sha256_bytes(token.encode("utf-8")))
            for index, byte in enumerate(raw):
                vector[index % 64] += (byte - 127.5) / 127.5
        norm = float(np.linalg.norm(vector))
        if norm == 0:
            vector[0] = 1.0
        else:
            vector /= norm
        return vector

    def encode_passages(self, texts: list[str]) -> np.ndarray:
        return np.asarray([self._one(text) for text in texts], dtype="<f4")

    def encode_query(self, text: str, *, token_limit: int = 128) -> np.ndarray:
        if len(text.split()) > token_limit:
            raise ValueError("RESOURCE_LIMIT: prompt exceeds token limit")
        return self._one(text)

    def vector_hash(self, vector: np.ndarray) -> str:
        return sha256_bytes(np.asarray(vector, dtype="<f4").tobytes())

    def verify_assets(self) -> dict[str, object]:
        return {"verified": True, "dimension": 64, "fingerprint": self.fingerprint}
