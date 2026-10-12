"""Disposable compositional Input settlement wrapped around Runtime 5.0."""

from __future__ import annotations

import json
import re
from typing import Any

from moth_runtime_v5_0.canonical import canonical_bytes, digest, normalize_text, sha256_bytes

from .field import CompiledField


RECORD_SCHEMA = "moth-v5-compositional-settlement/1.0"


class CompositionFailure(ValueError):
    def __init__(self, code: str, message: str, context: dict[str, Any] | None = None):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.context = context or {}


class CompositionIntegrityError(ValueError):
    pass


class CompositionalInstance:
    def __init__(self, store: Any, encoder: Any, thresholds: dict[str, Any], field: CompiledField):
        self.store = store
        self.encoder = encoder
        self.thresholds = thresholds
        self.field = field
        self._archive: dict[str, bytes] = {}

    def _subject(self, sentence: str, last_entity: dict[str, Any] | None) -> tuple[dict[str, Any], str, dict[str, Any]]:
        candidates = [
            (surface, entity)
            for entity in self.field.payload["entities"]
            for surface in entity["surfaces"]
            if sentence == surface or sentence.startswith(surface + " ")
        ]
        candidates.sort(key=lambda row: (-len(row[0]), row[1]["id"]))
        if candidates:
            surface, entity = candidates[0]
            return entity, sentence[len(surface):].strip(), {"method": "compiled_entity", "surface": surface, "entity_id": entity["id"]}
        for pronoun in self.field.payload["pronouns"]["surfaces"]:
            if sentence == pronoun or sentence.startswith(pronoun + " "):
                if last_entity is None:
                    raise CompositionFailure("AMBIGUOUS_REFERENCE", "pronoun has no unique antecedent")
                return last_entity, sentence[len(pronoun):].strip(), {"method": "pronoun", "surface": pronoun, "entity_id": last_entity["id"]}
        raise CompositionFailure("UNKNOWN_ENTITY", "sentence has no compiled subject", {"sentence": sentence})

    def _relation(self, fragment: str, entity: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        matches = []
        capabilities = {row["role"]: row for row in self.field.payload["capabilities"]}
        for rule in self.field.payload["relation_rules"]:
            role = rule["object_role"]
            if role is None:
                if fragment == rule["fragment"]:
                    matches.append((rule, None, None))
                continue
            capability = capabilities.get(role)
            if capability is None:
                continue
            placeholder = "{" + role.casefold() + "}"
            for surface in capability["surfaces"]:
                if fragment == rule["fragment"].replace(placeholder, surface):
                    matches.append((rule, capability, surface))
        if len(matches) != 1:
            raise CompositionFailure(
                "UNKNOWN_CAPABILITY" if not matches else "UNSUPPORTED_LANGUAGE",
                "fragment does not select exactly one compiled relation rule",
                {"fragment": fragment, "match_count": len(matches)},
            )
        rule, capability, surface = matches[0]
        output = rule["emit"].replace("{subject}", entity["canonical"])
        if capability is not None:
            output = output.replace("{" + capability["role"].casefold() + "}", capability["canonical"])
        return output, {
            "rule_id": rule["id"], "input": fragment, "output": output,
            "subject_id": entity["id"], "object_id": capability["id"] if capability else "compiled-static",
            "object_surface": surface,
        }

    def compose(self, raw_prompt: str) -> dict[str, Any]:
        text = normalize_text(raw_prompt).casefold()
        limits = self.field.payload["limits"]
        if len(text.split()) > limits["tokens"]:
            raise CompositionFailure("RESOURCE_LIMIT", "prompt exceeds compiled token limit")
        for coordinate, markers in self.field.payload["forbidden_markers"].items():
            for marker in markers:
                if re.search(rf"(?<!\w){re.escape(marker)}(?!\w)", text):
                    raise CompositionFailure("UNSUPPORTED_LANGUAGE", f"unsupported {coordinate} marker", {"marker": marker})
        sentences = [part.strip(" ,") for part in re.split(r"[.!?;]+", text) if part.strip()]
        if not 1 <= len(sentences) <= limits["sentences"]:
            raise CompositionFailure("RESOURCE_LIMIT", "sentence count exceeds compiled limit")
        intent = self.field.payload["intent"]
        intent_rows = [
            (index, sentence, validation, selection)
            for index, sentence in enumerate(sentences)
            for validation in intent["validation_markers"]
            for selection in intent["selection_markers"]
            if validation in sentence and selection in sentence
        ]
        if len(intent_rows) != 1:
            raise CompositionFailure("UNSUPPORTED_INTENT", "prompt does not compose exactly one compiled intent")
        intent_index, intent_sentence, validation_marker, selection_marker = intent_rows[0]

        operators = self.field.payload["coordination"]["operators"]
        split_expression = None if not operators else re.compile(r"\s+(?:" + "|".join(re.escape(value) for value in operators) + r")\s+")
        canonical_clauses = []
        trace = []
        last_entity = None
        for index, sentence in enumerate(sentences):
            if index == intent_index:
                continue
            entity, residue, subject_evidence = self._subject(sentence, last_entity)
            last_entity = entity
            fragments = [residue] if split_expression is None else split_expression.split(residue)
            if not 1 <= len(fragments) <= self.field.payload["coordination"]["maximum_facts_per_sentence"]:
                raise CompositionFailure("UNSUPPORTED_LANGUAGE", "coordination exceeds compiled sentence boundary")
            for fragment in fragments:
                clause, evidence = self._relation(fragment.strip(), entity)
                canonical_clauses.append(clause)
                trace.append({"sentence_index": index, "subject": subject_evidence, **evidence})
        if not 1 <= len(canonical_clauses) <= limits["facts"]:
            raise CompositionFailure("RESOURCE_LIMIT", "fact count exceeds compiled limit")
        canonical_prompt = ". ".join(value[0].upper() + value[1:] for value in canonical_clauses)
        canonical_prompt += ". Validate the proposed plan and select a replacement."
        return {
            "field_hash": self.field.field_hash,
            "canonical_prompt": canonical_prompt,
            "facts": canonical_clauses,
            "trace": trace,
            "intent_evidence": {
                "sentence_index": intent_index, "input": intent_sentence,
                "validation_marker": validation_marker, "selection_marker": selection_marker,
                "intent_id": intent["id"],
            },
        }

    def query(self, raw_prompt: str) -> dict[str, Any]:
        try:
            composition = self.compose(raw_prompt)
        except CompositionFailure as failure:
            base_result = None
            status = "REFUSAL"
            refusal = {"code": failure.code, "message": failure.message, "context": failure.context}
            output = None
        else:
            base_result = self.store.query(
                composition["canonical_prompt"], encoder=self.encoder, thresholds=self.thresholds,
            )
            status = base_result["status"]
            refusal = base_result.get("refusal")
            output = base_result.get("output")
        body = {
            "schema": RECORD_SCHEMA, "field_hash": self.field.field_hash,
            "raw_prompt": raw_prompt, "raw_prompt_hash": sha256_bytes(raw_prompt.encode("utf-8")),
            "status": status, "refusal": refusal, "output": output,
            "composition": composition if base_result is not None else None,
            "base_result": base_result,
            "execution": {"performed": False, "dispatch_count": 0},
        }
        episode_id = digest("moth-v5-compositional-episode/1.0", body)
        record = {**body, "episode_id": episode_id}
        record["outer_hash"] = digest(RECORD_SCHEMA, record)
        self._archive[episode_id] = canonical_bytes(record)
        return record

    def verify(self, record: dict[str, Any]) -> None:
        outer_hash = record.get("outer_hash")
        unhashed = {key: value for key, value in record.items() if key != "outer_hash"}
        if outer_hash != digest(RECORD_SCHEMA, unhashed):
            raise CompositionIntegrityError("compositional outer hash changed")
        if record.get("field_hash") != self.field.field_hash:
            raise CompositionIntegrityError("compositional field hash changed")
        raw = record.get("raw_prompt")
        if not isinstance(raw, str) or record.get("raw_prompt_hash") != sha256_bytes(raw.encode("utf-8")):
            raise CompositionIntegrityError("raw prompt commitment changed")

    def replay(self, episode_id: str, *, encoder_free: bool = True) -> bytes:
        archived = self._archive[episode_id]
        record = json.loads(archived)
        self.verify(record)
        raw = record["raw_prompt"]
        try:
            recomposed = self.compose(raw)
        except CompositionFailure as failure:
            if record["base_result"] is not None or record["refusal"]["code"] != failure.code:
                raise CompositionIntegrityError("composition refusal replay changed")
        else:
            if recomposed != record["composition"] or record["base_result"] is None:
                raise CompositionIntegrityError("composition trace replay changed")
            base = record["base_result"]
            replayed = self.store.replay(str(base["episode_id"]), encoder_free=encoder_free)
            if replayed != canonical_bytes(base):
                raise CompositionIntegrityError("nested Runtime 5.0 replay changed")
        return archived
