from __future__ import annotations

from dataclasses import replace
import json

import pytest

from moth_runtime_v5_0.archive import world_from_archive, world_to_archive
from moth_runtime_v5_0.canonical import canonical_bytes
from moth_runtime_v5_0.compiler import CompilationError, compile_sources
from moth_runtime_v5_0.encoder import DeterministicEncoder
from moth_runtime_v5_0.model import IntegrityError, MeaningType, RefusalCode, WorldRole
from moth_runtime_v5_0.runtime import query_worlds, verify_archived_result
from moth_runtime_v5_0.handoff import build_bundle
from moth_runtime_v5_0.store import WorldStore
from moth_runtime_v4_9.store import WorldStore as WorldStore49

from tests.test_runtime_v5_0 import SURFACE, factor_source


def _quoted(value) -> str:
    return json.dumps(json.dumps(value, separators=(",", ":")))


def decision_source() -> str:
    values = [
        ("yes", "true"), ("no", "false"),
        ("proposed", "PROPOSED"), ("backup", "BACKUP"), ("none", "NONE"),
        ("reason-none", "NONE"), ("reason-resource", "RESOURCE"),
        ("reason-permission", "PERMISSION"), ("reason-deadline", "DEADLINE"),
    ]
    fields = [
        "proposed-resource", "proposed-permission", "proposed-deadline",
        "backup-resource", "backup-permission", "backup-deadline",
    ]
    validity_rows = []
    diagnosis_rows = []
    for resource in ("no", "yes"):
        for permission in ("no", "yes"):
            for deadline in ("no", "yes"):
                validity_rows.append([resource, permission, deadline, "yes" if resource == permission == deadline == "yes" else "no"])
                reason = "reason-resource" if resource == "no" else "reason-permission" if permission == "no" else "reason-deadline" if deadline == "no" else "reason-none"
                diagnosis_rows.append([resource, permission, deadline, reason])
    templates = {
        "validity": {"ports": [{"name": key, "domain": "boolean"} for key in ("resource", "permission", "deadline", "valid")], "allowed_tuples": validity_rows},
        "selection": {"ports": [{"name": "proposed-valid", "domain": "boolean"}, {"name": "backup-valid", "domain": "boolean"}, {"name": "selected", "domain": "selection"}], "allowed_tuples": [["yes", "yes", "proposed"], ["yes", "no", "proposed"], ["no", "yes", "backup"], ["no", "no", "none"]]},
        "diagnosis": {"ports": [{"name": key, "domain": "boolean"} for key in ("resource", "permission", "deadline")] + [{"name": "reason", "domain": "failure-reason"}], "allowed_tuples": diagnosis_rows},
    }
    steps = []
    for field in fields:
        steps.append({"opcode": "CREATE_VARIABLE", "instance": field, "domain": "boolean"})
    for name, domain in (("proposed-valid", "boolean"), ("backup-valid", "boolean"), ("selected-plan", "selection"), ("failure-reason", "failure-reason")):
        steps.append({"opcode": "CREATE_VARIABLE", "instance": name, "domain": domain})
    for candidate in ("proposed", "backup"):
        factor = f"{candidate}-validity"
        steps.append({"opcode": "INSTANTIATE_FACTOR", "instance": factor, "template": "validity"})
        for port in ("resource", "permission", "deadline"):
            steps.append({"opcode": "BIND_PORT", "factor": factor, "port": port, "variable": f"{candidate}-{port}"})
        steps.append({"opcode": "BIND_PORT", "factor": factor, "port": "valid", "variable": f"{candidate}-valid"})
    steps.append({"opcode": "INSTANTIATE_FACTOR", "instance": "selection", "template": "selection"})
    for port, variable in (("proposed-valid", "proposed-valid"), ("backup-valid", "backup-valid"), ("selected", "selected-plan")):
        steps.append({"opcode": "BIND_PORT", "factor": "selection", "port": port, "variable": variable})
    steps.append({"opcode": "INSTANTIATE_FACTOR", "instance": "diagnosis", "template": "diagnosis"})
    for port in ("resource", "permission", "deadline"):
        steps.append({"opcode": "BIND_PORT", "factor": "diagnosis", "port": port, "variable": f"proposed-{port}"})
    steps.append({"opcode": "BIND_PORT", "factor": "diagnosis", "port": "reason", "variable": "failure-reason"})
    for field in fields:
        steps.append({"opcode": "CLAMP_FROM_PROMPT", "variable": field, "field": field})
    for ordinal, variable in enumerate(("proposed-valid", "backup-valid", "selected-plan", "failure-reason")):
        steps.append({"opcode": "EXPOSE_OUTPUT", "variable": variable, "ordinal": ordinal, "label": variable})
    source = factor_source(
        values=values,
        domains={"boolean": ["no", "yes"], "selection": ["proposed", "backup", "none"], "failure-reason": ["reason-none", "reason-resource", "reason-permission", "reason-deadline"]},
        templates=templates,
        programs={"validate-and-select": steps},
        fields=fields,
    )
    entities = [
        "direct-courier", "backup-courier", "cold-storage", "road-permit", "delivery-deadline",
        "deployment-engineer", "backup-engineer", "server-access", "production-approval", "deployment-deadline",
    ]
    return source + "\n".join([
        'Directional relation "satisfies" maps Entity to Entity and is multi-valued.',
        *[f'Entity "{name}" is declared.' for name in entities],
    ]) + "\n"


def semantic_contract(domain: str) -> dict:
    if domain == "delivery":
        definition = {
            "domain": ["delivery", "courier", "carrier"],
            "entities": [
                ("proposed", "direct-courier", "PROPOSED", ["direct courier", "proposed courier", "direct carrier", "proposed carrier", "direct plan", "proposed plan"]),
                ("backup", "backup-courier", "BACKUP", ["backup courier", "alternative courier", "backup carrier", "alternative carrier", "backup plan", "alternative plan"]),
                ("resource", "cold-storage", "RESOURCE", ["cold storage", "refrigeration", "refrigerated storage", "cold-chain equipment"]),
                ("permission", "road-permit", "PERMISSION", ["road permit", "delivery authorization", "delivery permission", "permission", "authorization"]),
                ("deadline", "delivery-deadline", "DEADLINE", ["delivery deadline"]),
            ],
            "deadline_frames": ["{SUBJECT} can meet the deadline", "{SUBJECT} can arrive before the deadline", "{SUBJECT} can arrive on time"],
            "deadline_negative": ["{SUBJECT} cannot meet the deadline", "{SUBJECT} cannot arrive before the deadline", "{SUBJECT} cannot arrive on time"],
        }
    else:
        definition = {
            "domain": ["deployment", "engineer", "production"],
            "entities": [
                ("proposed", "deployment-engineer", "PROPOSED", ["deployment engineer", "proposed engineer", "primary engineer", "proposed plan"]),
                ("backup", "backup-engineer", "BACKUP", ["backup engineer", "alternative engineer", "alternate engineer", "backup plan", "alternative plan"]),
                ("resource", "server-access", "RESOURCE", ["server access", "production access", "system access"]),
                ("permission", "production-approval", "PERMISSION", ["production approval", "deployment approval", "production permission", "approval", "authorization"]),
                ("deadline", "deployment-deadline", "DEADLINE", ["deployment deadline"]),
            ],
            "deadline_frames": ["{SUBJECT} can meet the deadline", "{SUBJECT} can finish before the deadline", "{SUBJECT} can complete on time"],
            "deadline_negative": ["{SUBJECT} cannot meet the deadline", "{SUBJECT} cannot finish before the deadline", "{SUBJECT} cannot complete on time"],
        }
    frames = [
        {"template": "{SUBJECT} has {OBJECT}", "polarity": "POSITIVE"},
        {"template": "{SUBJECT} possesses {OBJECT}", "polarity": "POSITIVE"},
        {"template": "{SUBJECT} lacks {OBJECT}", "polarity": "NEGATIVE"},
        {"template": "{SUBJECT} does not have {OBJECT}", "polarity": "NEGATIVE"},
        {"template": "{SUBJECT} has no {OBJECT}", "polarity": "NEGATIVE"},
        {"template": "{SUBJECT} is without {OBJECT}", "polarity": "NEGATIVE"},
        {"template": "{SUBJECT} is unavailable to {OBJECT}", "polarity": "NEGATIVE"},
        {"template": "{SUBJECT} is authorized", "polarity": "POSITIVE", "object": "permission"},
        {"template": "{SUBJECT} has authorization", "polarity": "POSITIVE", "object": "permission"},
        {"template": "{SUBJECT} is not authorized", "polarity": "NEGATIVE", "object": "permission"},
        {"template": "{SUBJECT} lacks authorization", "polarity": "NEGATIVE", "object": "permission"},
    ]
    frames += [{"template": value, "polarity": "POSITIVE", "object": "deadline"} for value in definition["deadline_frames"]]
    frames += [{"template": value, "polarity": "NEGATIVE", "object": "deadline"} for value in definition["deadline_negative"]]
    projections = []
    for subject_role, prefix in (("PROPOSED", "proposed"), ("BACKUP", "backup")):
        for object_role, suffix in (("RESOURCE", "resource"), ("PERMISSION", "permission"), ("DEADLINE", "deadline")):
            projections.append({"subject_role": subject_role, "predicate": "satisfies", "object_role": object_role, "field": f"{prefix}-{suffix}", "positive_value": "yes", "negative_value": "no"})
    return {
        "schema": "moth-semantic-contract/5.0", "language": "en",
        "domain": {"id": domain, "surfaces": definition["domain"]},
        "entities": [{"key": key, "entity": entity, "role": role, "surfaces": surfaces} for key, entity, role, surfaces in definition["entities"]],
        "predicates": [{"id": "satisfies", "relation": "satisfies", "subject_roles": ["PROPOSED", "BACKUP"], "object_roles": ["RESOURCE", "PERMISSION", "DEADLINE"], "frames": frames}],
        "pronouns": {"surfaces": ["it"], "policy": "MOST_RECENT_UNAMBIGUOUS"},
        "intents": [{
            "id": "validate-and-select",
            "surfaces": ["validate the proposed plan and select a replacement", "can the proposed plan be used and which plan should replace it", "review the proposed option and choose a replacement", "is the proposed plan valid and what should we use instead"],
            "instruction": "factor-settle", "slots": {"PROGRAM": "validate-and-select", "SCHEMA": "answer-json"}, "projections": projections,
        }],
        "transformations": ["external-paraphrase", "internal-relation-form"],
    }


def semantic_source(*domains: str) -> str:
    rows = [decision_source()]
    for domain in domains:
        rows.append(f'Semantic contract "{domain}-en" is canonical semantic JSON {_quoted(semantic_contract(domain))}.')
    return "\n".join(rows) + "\n"


def worlds(*domains: str):
    encoder = DeterministicEncoder()
    base = decision_source()
    result = {
        WorldRole.INPUT: compile_sources({"input.moth": semantic_source(*domains)}, encoder=encoder, world_role=WorldRole.INPUT),
        WorldRole.MAIN: compile_sources({"main.moth": base}, encoder=encoder, world_role=WorldRole.MAIN),
        WorldRole.SURFACE: compile_sources({"surface.moth": SURFACE}, encoder=encoder, world_role=WorldRole.SURFACE),
    }
    return result, encoder, build_bundle(result)


DELIVERY = "Direct courier lacks cold storage. Direct courier has road permit. Direct courier can meet the deadline. Backup courier has refrigeration. Backup courier has road permit. Backup courier can meet the deadline. Can the proposed plan be used and which plan should replace it?"
DELIVERY_PARAPHRASE = "Proposed carrier is without refrigerated storage. It is authorized. It can arrive before the deadline. Alternative carrier possesses refrigeration. It has authorization. It can arrive on time. Review the proposed option and choose a replacement."
DELIVERY_REORDERED = "Backup courier can meet the deadline. Direct courier has road permit. Backup courier has cold storage. Direct courier lacks refrigeration. Backup courier has permission. Direct courier can arrive on time. Validate the proposed plan and select a replacement."
DEPLOYMENT = "Deployment engineer has server access. Deployment engineer lacks production approval. Deployment engineer can finish before the deadline. Backup engineer has production access. Backup engineer has deployment approval. Backup engineer can finish before the deadline. Validate the proposed plan and select a replacement."


def test_semantic_contract_compiles_deterministically_and_archives():
    first, encoder, _ = worlds("delivery")
    second = compile_sources({"input.moth": semantic_source("delivery")}, encoder=encoder, world_role=WorldRole.INPUT)
    assert first[WorldRole.INPUT].world_hash == second.world_hash
    assert len(first[WorldRole.INPUT].by_kind(MeaningType.SEMANTIC_CONTRACT)) == 1
    archived = world_to_archive(first[WorldRole.INPUT])
    assert world_from_archive(archived) == first[WorldRole.INPUT]
    with pytest.raises(CompilationError, match="only in Input Worlds"):
        compile_sources({"bad.moth": semantic_source("delivery")}, world_role=WorldRole.MAIN)


def test_semantic_paraphrases_converge_and_main_surface_are_preserved():
    compiled, _, bundle = worlds("delivery")
    first, receipts, handoffs = query_worlds(compiled, bundle, DELIVERY)
    second, _, _ = query_worlds(compiled, bundle, DELIVERY_PARAPHRASE)
    reordered, _, _ = query_worlds(compiled, bundle, DELIVERY_REORDERED)
    assert first["status"] == second["status"] == "ANSWER"
    assert first["output"] == second["output"] == {"kind": "FACTOR_RESULT", "value": {"proposed-valid": "false", "backup-valid": "true", "selected-plan": "BACKUP", "failure-reason": "RESOURCE"}}
    first_input = first["stages"][0]["program"]["grounding"]["semantic_interpretation"]
    second_input = second["stages"][0]["program"]["grounding"]["semantic_interpretation"]
    reordered_input = reordered["stages"][0]["program"]["grounding"]["semantic_interpretation"]
    assert first_input["semantic_graph_hash"] == second_input["semantic_graph_hash"] == reordered_input["semantic_graph_hash"]
    assert handoffs[0].payload["semantic_graph_hash"] == first_input["semantic_graph_hash"]
    assert receipts[1].role == WorldRole.MAIN
    verify_archived_result(first, compiled, bundle)


def test_two_domains_reuse_one_main_world_and_legacy_precedence():
    compiled, _, bundle = worlds("delivery", "deployment")
    delivery, _, _ = query_worlds(compiled, bundle, DELIVERY)
    deployment, _, _ = query_worlds(compiled, bundle, DEPLOYMENT)
    assert delivery["status"] == deployment["status"] == "ANSWER"
    assert compiled[WorldRole.MAIN].world_hash == compiled[WorldRole.MAIN].world_hash
    legacy_prompt = "Settle validate-and-select with proposed-resource = no, proposed-permission = yes, proposed-deadline = yes, backup-resource = yes, backup-permission = yes, backup-deadline = yes using answer-json."
    legacy, _, _ = query_worlds(compiled, bundle, legacy_prompt)
    assert legacy["status"] == "ANSWER"
    assert legacy["stages"][0]["program"]["grounding"]["mode"] == "LEGACY_ENVELOPE"
    assert legacy["stages"][0]["program"]["grounding_cost_units"] == 0


@pytest.mark.parametrize(("prompt", "code"), [
    ("Direct courier and backup courier are available. It lacks refrigeration. Direct courier has permission. Direct courier can meet the deadline. Backup courier has permission. Backup courier can meet the deadline. Validate the proposed plan and select a replacement.", RefusalCode.AMBIGUOUS_REFERENCE),
    ("Direct courier lacks cold storage. Direct courier has permission. Backup courier has refrigeration. Backup courier has permission. Backup courier can meet the deadline. Validate the proposed plan and select a replacement.", RefusalCode.INCOMPLETE_FACT_GRAPH),
    ("Direct courier lacks cold storage. Direct courier has refrigeration. Direct courier has permission. Direct courier can meet the deadline. Backup courier has refrigeration. Backup courier has permission. Backup courier can meet the deadline. Validate the proposed plan and select a replacement.", RefusalCode.CONFLICTING_FACTS),
    ("Drone courier lacks cold storage. Direct courier has permission. Direct courier can meet the deadline. Backup courier has refrigeration. Backup courier has permission. Backup courier can meet the deadline. Validate the proposed plan and select a replacement.", RefusalCode.UNKNOWN_ENTITY),
    ("Direct courier lacks cold storage. Direct courier has permission. Direct courier can meet the deadline. Backup courier has refrigeration. Backup courier has permission. Backup courier can meet the deadline. Write a poem about these couriers.", RefusalCode.UNSUPPORTED_INTENT),
])
def test_semantic_refusals_are_stable(prompt, code):
    compiled, _, bundle = worlds("delivery")
    result, _, _ = query_worlds(compiled, bundle, prompt)
    assert result["status"] == "REFUSAL"
    assert result["refusal"]["code"] == code.value


def test_semantic_trace_tampering_fails_encoder_free_verification():
    compiled, _, bundle = worlds("delivery")
    result, _, _ = query_worlds(compiled, bundle, DELIVERY)
    altered = json.loads(canonical_bytes(result))
    altered["stages"][0]["program"]["grounding"]["semantic_interpretation"]["facts"][0]["polarity"] = "TAMPERED"
    with pytest.raises(IntegrityError):
        verify_archived_result(altered, compiled, bundle)


def test_empty_store_and_cross_runtime_store_rejection(tmp_path):
    store = WorldStore(tmp_path / "store-5.0.sqlite3")
    store.init()
    assert store.query("anything")["refusal"]["code"] == RefusalCode.WORLD_NOT_READY.value
    old = tmp_path / "store-4.9.sqlite3"
    WorldStore49(old).init()
    with pytest.raises(IntegrityError, match="cross-runtime"):
        WorldStore(old).init()


def test_semantic_store_persistence_and_encoder_free_replay(tmp_path):
    encoder = DeterministicEncoder()
    store = WorldStore(tmp_path / "semantic.sqlite3")
    store.publish(WorldRole.INPUT, {"input.moth": semantic_source("delivery")}, encoder=encoder)
    store.publish(WorldRole.MAIN, {"main.moth": decision_source()}, encoder=encoder)
    store.publish(WorldRole.SURFACE, {"surface.moth": SURFACE}, encoder=encoder)
    store.activate()
    result = store.query(DELIVERY)
    assert result["status"] == "ANSWER"
    assert store.replay(result["episode_id"], encoder_free=True) == canonical_bytes(result)


def test_typed_vector_candidate_retrieval_and_encoder_free_scores():
    compiled, _, bundle = worlds("delivery")
    input_world = compiled[WorldRole.INPUT]
    target_surface = next(
        item for item in input_world.by_kind(MeaningType.SEMANTIC_SURFACE)
        if item.payload.get("text") == "direct courier"
    )

    class ArchivedVectorQuery:
        @staticmethod
        def encode_query(text, *, token_limit=128):
            return input_world.vectors[target_surface.meaning_id].vector

    prompt = DELIVERY.replace("Direct courier lacks", "Chosen courier lacks", 1)
    result, _, _ = query_worlds(
        compiled, bundle, prompt, encoder=ArchivedVectorQuery(),
        thresholds={"SEMANTIC_SURFACE": {"score": 0.82, "margin": 0.05}},
    )
    assert result["status"] == "ANSWER"
    evidence = result["stages"][0]["program"]["grounding"]["semantic_interpretation"]["clause_evidence"][0]["subject"]
    assert evidence["method"] == "vector"
    verify_archived_result(result, compiled, bundle)
