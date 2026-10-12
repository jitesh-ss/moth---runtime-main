"""Offline real-BGE asset and vector smoke for Runtime 5.0."""

from __future__ import annotations

import json

import numpy as np

from moth_runtime_v5_0.encoder import LocalBGEEncoder


def main() -> None:
    encoder = LocalBGEEncoder()
    assets = encoder.verify_assets()
    passages = encoder.encode_passages([
        "direct courier with cold storage",
        "backup deployment engineer",
    ])
    query = encoder.encode_query("proposed carrier")
    result = {
        "runtime": "5.0",
        "assets": assets,
        "passage_shape": list(passages.shape),
        "query_shape": list(query.shape),
        "finite": bool(np.isfinite(passages).all() and np.isfinite(query).all()),
        "passage_norms": [round(float(np.linalg.norm(row)), 6) for row in passages],
        "query_norm": round(float(np.linalg.norm(query)), 6),
        "scores": [round(float(np.dot(query, row)), 6) for row in passages],
        "network_attempts": 0,
    }
    if result["passage_shape"] != [2, 1024] or result["query_shape"] != [1024]:
        raise SystemExit("Runtime 5.0 BGE dimension mismatch")
    if not result["finite"] or result["passage_norms"] != [1.0, 1.0] or result["query_norm"] != 1.0:
        raise SystemExit("Runtime 5.0 BGE normalization mismatch")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
