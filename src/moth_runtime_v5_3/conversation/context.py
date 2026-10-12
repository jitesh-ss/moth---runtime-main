"""Deterministic active-context projection without compiled JSON entries."""

from __future__ import annotations

import re
from typing import Any

from moth_runtime_v5_3.legacy.canonical import digest, normalize_text, sha256_bytes


CONTEXT_SCHEMA = "moth-active-context/5.3"
_TURN_REFERENCE = re.compile(r"@turn:(\d+)", re.IGNORECASE)
_REPEAT = {
    "repeat that",
    "repeat that.",
    "repeat the previous request",
    "repeat the previous request.",
    "do that again",
    "do that again.",
}


class ContextFailure(ValueError):
    def __init__(
        self,
        code: str,
        message: str,
        context: dict[str, Any] | None = None,
    ):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.context = context or {}


def token_count(value: str) -> int:
    return len(normalize_text(value).split())


def project_context(
    prior_messages: list[dict[str, Any]],
    *,
    current_message: dict[str, Any],
    budget_tokens: int,
) -> tuple[dict[str, Any], str]:
    current_tokens = token_count(str(current_message["content"]))
    if current_tokens > budget_tokens:
        raise ContextFailure(
            "CONTEXT_LIMIT",
            "current message exceeds active-context budget",
        )
    by_turn: dict[int, list[dict[str, Any]]] = {}
    for message in prior_messages:
        if message["role"] != "SYSTEM":
            by_turn.setdefault(
                int(message["turn_sequence"]), []
            ).append(message)
    referenced: list[dict[str, Any]] = []
    reference_turns = [
        int(value)
        for value in _TURN_REFERENCE.findall(
            str(current_message["content"])
        )
    ]
    for turn_number in reference_turns:
        rows = by_turn.get(turn_number)
        if not rows:
            raise ContextFailure(
                "UNKNOWN_REFERENCE",
                "referenced conversation turn does not exist",
                {"turn": turn_number},
            )
        referenced.extend(
            sorted(rows, key=lambda item: item["ordinal"])
        )
    effective_prompt = str(current_message["content"])
    if normalize_text(effective_prompt).casefold() in _REPEAT:
        earlier_users = [
            item for item in prior_messages if item["role"] == "USER"
        ]
        if not earlier_users:
            raise ContextFailure(
                "UNKNOWN_REFERENCE", "there is no previous user request"
            )
        source = max(
            earlier_users,
            key=lambda item: (
                item["turn_sequence"],
                item["ordinal"],
            ),
        )
        referenced.append(source)
        effective_prompt = str(source["content"])
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    used = current_tokens
    for message in referenced:
        identifier = str(message["message_id"])
        if identifier in seen:
            continue
        cost = int(message["token_count"])
        if used + cost > budget_tokens:
            raise ContextFailure(
                "CONTEXT_LIMIT",
                "mandatory referenced context exceeds active-context budget",
                {"message_id": identifier},
            )
        selected.append(message)
        seen.add(identifier)
        used += cost
    eligible = sorted(
        (
            item
            for item in prior_messages
            if item["role"] != "SYSTEM"
        ),
        key=lambda item: (
            int(item["turn_sequence"]),
            int(item["ordinal"]),
        ),
        reverse=True,
    )
    for message in eligible:
        identifier = str(message["message_id"])
        if identifier in seen:
            continue
        cost = int(message["token_count"])
        if used + cost <= budget_tokens:
            selected.append(message)
            seen.add(identifier)
            used += cost
    selected = sorted(
        selected,
        key=lambda item: (
            int(item["turn_sequence"]),
            int(item["ordinal"]),
        ),
    )
    body = {
        "schema": CONTEXT_SCHEMA,
        "budget_tokens": budget_tokens,
        "active_tokens": used,
        "stored_message_count": len(prior_messages) + 1,
        "selected_message_ids": [
            item["message_id"] for item in selected
        ],
        "current_message_id": current_message["message_id"],
        "current_message_hash": sha256_bytes(
            normalize_text(
                str(current_message["content"])
            ).encode("utf-8")
        ),
        "reference_turns": reference_turns,
        "effective_prompt_hash": sha256_bytes(
            normalize_text(effective_prompt).encode("utf-8")
        ),
        "transient_context_object_hashes": [
            current_message["hcf_object_hash"]
        ],
    }
    return (
        {
            **body,
            "context_hash": digest("moth-active-context/5.3", body),
        },
        effective_prompt,
    )
