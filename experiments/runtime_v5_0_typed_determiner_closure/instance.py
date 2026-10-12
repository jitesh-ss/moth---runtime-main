"""Determiner-aware isolated compositional Runtime 5.0 instance."""

from __future__ import annotations

from typing import Any

from experiments.runtime_v5_0_blind_compositional_closure.instance import (
    CompositionalInstance, CompositionFailure,
)


class TypedDeterminerInstance(CompositionalInstance):
    def _relation(self, fragment: str, entity: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        matches = []
        capabilities = {row["role"]: row for row in self.field.payload["capabilities"]}
        operator = self.field.payload["noun_phrase_operator"]
        determiners = operator["determiners"]
        for rule in self.field.payload["relation_rules"]:
            role = rule["object_role"]
            if role is None:
                if fragment == rule["fragment"]:
                    matches.append((rule, None, None, None))
                continue
            capability = capabilities.get(role)
            if capability is None:
                continue
            placeholder = "{" + role.casefold() + "}"
            for surface in capability["surfaces"]:
                candidates = [(surface, None)]
                already_determined = any(surface.startswith(value + " ") for value in determiners)
                if role in operator["roles"] and not already_determined:
                    candidates.extend((value + " " + surface, value) for value in determiners)
                for candidate, determiner in candidates:
                    if fragment == rule["fragment"].replace(placeholder, candidate):
                        matches.append((rule, capability, surface, determiner))
        if len(matches) != 1:
            raise CompositionFailure(
                "UNKNOWN_CAPABILITY" if not matches else "UNSUPPORTED_LANGUAGE",
                "fragment does not select exactly one typed noun-phrase relation",
                {"fragment": fragment, "match_count": len(matches)},
            )
        rule, capability, surface, determiner = matches[0]
        output = rule["emit"].replace("{subject}", entity["canonical"])
        if capability is not None:
            output = output.replace("{" + capability["role"].casefold() + "}", capability["canonical"])
        return output, {
            "rule_id": rule["id"], "input": fragment, "output": output,
            "subject_id": entity["id"], "object_id": capability["id"] if capability else "compiled-static",
            "object_surface": surface, "determiner": determiner,
            "noun_phrase_rule": operator["id"] if determiner else None,
        }

