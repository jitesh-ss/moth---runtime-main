"""Runtime 5.2 canonical receipts."""

from __future__ import annotations

from typing import Any

from moth_runtime_v5_0.canonical import canonical_bytes, sha256_bytes


def result_receipt(result: dict[str, Any]) -> str:
    payload = {key: value for key, value in result.items() if key != "replay"}
    replay = dict(result.get("replay", {}))
    replay.pop("result_hash", None)
    payload["replay"] = replay
    return sha256_bytes(canonical_bytes(payload))


def finish_result(result: dict[str, Any]) -> dict[str, Any]:
    result.setdefault("replay", {})["result_hash"] = result_receipt(result)
    return result


def verify_result_receipt(result: dict[str, Any]) -> None:
    if result.get("schema") != "moth-conversation-turn/5.2" or result.get("runtime") != "5.2":
        raise ValueError("cross-runtime Runtime 5.2 result refused")
    if result.get("replay", {}).get("result_hash") != result_receipt(result):
        raise ValueError("Runtime 5.2 result receipt hash mismatch")

