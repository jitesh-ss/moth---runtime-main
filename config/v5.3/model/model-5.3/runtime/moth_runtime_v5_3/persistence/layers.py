"""Validation and mutation of revisioned SYSTEM and CONTEXT attachments."""

from __future__ import annotations

from typing import Iterable

import numpy as np

from ..energy.loader import (
    EnergyFoundation,
    HcfTensorField,
    load_hcf_field,
)
from ..energy.schema import Effect, Level, Runtime53Failure
from .store import ConversationStore


class LayerManager:
    def __init__(self, store: ConversationStore, foundation: EnergyFoundation):
        self.store = store
        self.foundation = foundation

    def _field(self, object_hash: str) -> HcfTensorField:
        return load_hcf_field(
            self.store.objects.open(object_hash), self.foundation
        )

    def fields_for_revision(
        self,
        conversation_id: str,
        level: Level,
        revision_id: str | None = None,
    ) -> tuple[HcfTensorField, ...]:
        snapshot = self.store.layer_snapshot(
            conversation_id, level, revision_id
        )
        return tuple(
            self._field(member["object_hash"])
            for member in snapshot["members"]
        )

    @staticmethod
    def _aggregate_validate(
        fields: Iterable[HcfTensorField], level: Level
    ) -> None:
        entry_ids: set[bytes] = set()
        constraints: dict[tuple[int, int], set[bytes]] = {}
        activations: dict[bytes, int] = {}
        for field in fields:
            if field.level is not level:
                raise Runtime53Failure(
                    "INVALID_HCF_FIELD",
                    "field level differs from attachment level",
                )
            tensors = field.tensors
            for row in range(len(tensors["entry_id"])):
                entry_id = tensors["entry_id"][row].tobytes()
                if entry_id in entry_ids:
                    raise Runtime53Failure(
                        "INVALID_HCF_FIELD", "duplicate HCF entry"
                    )
                entry_ids.add(entry_id)
                effect = int(tensors["effect"][row])
                if effect not in (
                    int(Effect.REQUIRE),
                    int(Effect.FORBID),
                ):
                    continue
                key = (int(tensors["scope_index"][row]), effect)
                constraints.setdefault(key, set()).add(
                    tensors["value_hash"][row].tobytes()
                )
            for identity, state in zip(
                tensors["activation_candidate"],
                tensors["activation_state"],
            ):
                key = identity.tobytes()
                if key in activations and activations[key] != int(state):
                    raise Runtime53Failure(
                        "AMBIGUOUS_HCF",
                        "same-level activation conflict",
                    )
                activations[key] = int(state)
        for (scope, effect), values in constraints.items():
            if effect == int(Effect.REQUIRE) and len(values) > 1:
                raise Runtime53Failure(
                    "AMBIGUOUS_HCF",
                    "same-level REQUIRE values conflict",
                    {"scope_index": scope},
                )
            opposite = constraints.get(
                (
                    scope,
                    int(Effect.FORBID)
                    if effect == int(Effect.REQUIRE)
                    else int(Effect.REQUIRE),
                ),
                set(),
            )
            if values & opposite:
                raise Runtime53Failure(
                    "AMBIGUOUS_HCF",
                    "same-level REQUIRE/FORBID conflict",
                    {"scope_index": scope},
                )

    def _members(
        self, conversation_id: str, level: Level
    ) -> dict[str, str]:
        snapshot = self.store.layer_snapshot(conversation_id, level)
        return {
            member["key"]: member["object_hash"]
            for member in snapshot["members"]
        }

    @staticmethod
    def _constraint_rows(fields: Iterable[HcfTensorField]) -> list[tuple[int, int, bytes]]:
        rows: list[tuple[int, int, bytes]] = []
        for field in fields:
            tensors = field.tensors
            for row in range(len(tensors["entry_id"])):
                effect = int(tensors["effect"][row])
                if effect in (int(Effect.REQUIRE), int(Effect.FORBID)):
                    rows.append(
                        (
                            int(tensors["scope_index"][row]),
                            effect,
                            tensors["value_hash"][row].tobytes(),
                        )
                    )
        return rows

    def _base_constraints(self) -> list[tuple[int, int, bytes]]:
        tensors = self.foundation.tensors
        rows: list[tuple[int, int, bytes]] = []
        for row in range(len(tensors["base_entry_id"])):
            effect = int(tensors["base_effect"][row])
            if effect in (int(Effect.REQUIRE), int(Effect.FORBID)):
                rows.append(
                    (
                        int(tensors["base_scope_index"][row]),
                        effect,
                        tensors["base_value_hash"][row].tobytes(),
                    )
                )
        return rows

    @staticmethod
    def _constraints_conflict(
        lower: tuple[int, int, bytes], higher: tuple[int, int, bytes]
    ) -> bool:
        lower_scope, lower_effect, lower_value = lower
        higher_scope, higher_effect, higher_value = higher
        if lower_scope != higher_scope:
            return False
        if lower_effect == int(Effect.REQUIRE) and higher_effect == int(Effect.REQUIRE):
            return lower_value != higher_value
        return (
            lower_effect != higher_effect and lower_value == higher_value
        )

    def _base_delegates(self, scope: int, target: Level) -> bool:
        tensors = self.foundation.tensors
        return bool(
            np.any(
                (tensors["base_effect"] == int(Effect.DELEGATE))
                & (tensors["base_scope_index"] == scope)
                & (tensors["base_target_level"] == int(target))
            )
        )

    def _base_redelegates_to_system(self, scope: int) -> bool:
        tensors = self.foundation.tensors
        return bool(
            np.any(
                (tensors["base_effect"] == int(Effect.DELEGATE))
                & (tensors["base_scope_index"] == scope)
                & (tensors["base_target_level"] == int(Level.SYSTEM))
                & (tensors["base_redelegable"] == 1)
            )
        )

    @staticmethod
    def _system_delegates(
        system_fields: Iterable[HcfTensorField], scope: int
    ) -> bool:
        for field in system_fields:
            tensors = field.tensors
            if np.any(
                (tensors["effect"] == int(Effect.DELEGATE))
                & (tensors["scope_index"] == scope)
                & (tensors["target_level"] == int(Level.CONTEXT))
            ):
                return True
        return False

    def _delegated(
        self,
        scope: int,
        target: Level,
        system_fields: Iterable[HcfTensorField],
    ) -> bool:
        if self._base_delegates(scope, target):
            return True
        return bool(
            target is Level.CONTEXT
            and self._base_redelegates_to_system(scope)
            and self._system_delegates(system_fields, scope)
        )

    def _validate_authorization(
        self,
        fields: Iterable[HcfTensorField],
        level: Level,
        system_fields: Iterable[HcfTensorField] = (),
    ) -> None:
        fields = tuple(fields)
        system_fields = tuple(system_fields)
        for field in fields:
            scopes = field.tensors["activation_scope_index"]
            for scope in scopes:
                scope_index = int(scope)
                if not self._delegated(scope_index, level, system_fields):
                    raise Runtime53Failure(
                        "UNAUTHORIZED_LAYER_OVERRIDE",
                        "candidate activation is not delegated to this layer",
                        {"level": level.name, "scope_index": scope_index},
                    )

        higher = self._base_constraints()
        if level is Level.CONTEXT:
            higher.extend(self._constraint_rows(system_fields))
        for lower in self._constraint_rows(fields):
            if not any(self._constraints_conflict(lower, item) for item in higher):
                continue
            scope_index = lower[0]
            if level is Level.SYSTEM:
                authorized = self._base_delegates(scope_index, Level.SYSTEM)
            else:
                conflicts_with_system = any(
                    self._constraints_conflict(lower, item)
                    for item in self._constraint_rows(system_fields)
                )
                authorized = (
                    self._system_delegates(system_fields, scope_index)
                    if conflicts_with_system
                    else self._delegated(scope_index, Level.CONTEXT, system_fields)
                )
            if not authorized:
                raise Runtime53Failure(
                    "UNAUTHORIZED_LAYER_OVERRIDE",
                    "constraint override is not delegated to this layer",
                    {"level": level.name, "scope_index": scope_index},
                )

    def upsert(
        self,
        conversation_id: str,
        level: Level,
        attachment_key: str,
        object_hash: str,
        expected_revision: int,
    ) -> dict:
        if level is Level.BASE:
            raise Runtime53Failure(
                "INVALID_HCF_FIELD", "BASE is immutable"
            )
        if not attachment_key or any(
            character not in "abcdefghijklmnopqrstuvwxyz0123456789._-"
            for character in attachment_key
        ):
            raise Runtime53Failure(
                "INVALID_HCF_FIELD", "attachment key is invalid"
            )
        field = self._field(object_hash)
        if field.level is not level:
            raise Runtime53Failure(
                "INVALID_HCF_FIELD",
                "field level differs from attachment level",
            )
        members = self._members(conversation_id, level)
        members[attachment_key] = object_hash
        fields = tuple(self._field(value) for value in members.values())
        self._aggregate_validate(fields, level)
        if level is Level.SYSTEM:
            self._validate_authorization(fields, level)
            context_fields = self.fields_for_revision(
                conversation_id, Level.CONTEXT
            )
            self._validate_authorization(
                context_fields, Level.CONTEXT, fields
            )
        else:
            system_fields = self.fields_for_revision(
                conversation_id, Level.SYSTEM
            )
            self._validate_authorization(fields, level, system_fields)
        return self.store.commit_layer(
            conversation_id,
            level,
            expected_revision,
            members.items(),
            {
                "operation": "UPSERT",
                "key": attachment_key,
                "object_hash": object_hash,
            },
        )

    def remove(
        self,
        conversation_id: str,
        level: Level,
        attachment_key: str,
        expected_revision: int,
    ) -> dict:
        if level is Level.BASE:
            raise Runtime53Failure(
                "INVALID_HCF_FIELD", "BASE is immutable"
            )
        members = self._members(conversation_id, level)
        if attachment_key not in members:
            raise Runtime53Failure(
                "NO_LAYER_CHANGE", "attachment does not exist"
            )
        removed = members.pop(attachment_key)
        fields = tuple(self._field(value) for value in members.values())
        self._aggregate_validate(fields, level)
        if level is Level.SYSTEM:
            self._validate_authorization(fields, level)
            context_fields = self.fields_for_revision(
                conversation_id, Level.CONTEXT
            )
            self._validate_authorization(
                context_fields, Level.CONTEXT, fields
            )
        else:
            system_fields = self.fields_for_revision(
                conversation_id, Level.SYSTEM
            )
            self._validate_authorization(fields, level, system_fields)
        return self.store.commit_layer(
            conversation_id,
            level,
            expected_revision,
            members.items(),
            {
                "operation": "REMOVE",
                "key": attachment_key,
                "object_hash": removed,
            },
        )
