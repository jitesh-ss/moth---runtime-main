"""Run the frozen 50-case Runtime 5.0 semantic-invariance campaign."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from moth_runtime_v5_0.canonical import canonical_bytes, sha256_bytes
from moth_runtime_v5_0.encoder import DeterministicEncoder
from moth_runtime_v5_0.model import IntegrityError, WorldRole
from moth_runtime_v5_0.runtime import verify_archived_result
from moth_runtime_v5_0.store import WorldStore

from tests.test_runtime_v5_0_language import SURFACE, decision_source, semantic_source


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures/campaign-en-1.0.json"

BASELINE_OUTPUT = {
    "proposed-valid": "false",
    "backup-valid": "true",
    "selected-plan": "BACKUP",
    "failure-reason": "RESOURCE",
}


class CampaignFailure(AssertionError):
    pass


def _tree_hash(path: Path) -> str:
    result = hashlib.sha256()
    for child in sorted(item for item in path.rglob("*") if item.is_file() and "__pycache__" not in item.parts):
        result.update(child.relative_to(ROOT).as_posix().encode("utf-8"))
        result.update(b"\0")
        result.update(hashlib.sha256(child.read_bytes()).digest())
    return result.hexdigest()


def _protected_hashes() -> dict[str, str]:
    store = ROOT / "data/store-5.0.sqlite3"
    return {
        "runtime_tree": _tree_hash(ROOT / "src/moth_runtime_v5_0"),
        "configuration_tree": _tree_hash(ROOT / "config/v5.0"),
        "architecture_lock": sha256_bytes((ROOT / "config/v5.0/ARCHITECTURE-LOCK.json").read_bytes()),
        "production_store": sha256_bytes(store.read_bytes()) if store.is_file() else "ABSENT",
    }


def _domain_profile(domain: str) -> dict[str, Any]:
    if domain == "delivery":
        return {
            "proposed": ["direct courier", "proposed courier", "direct carrier", "proposed carrier"],
            "backup": ["backup courier", "alternative courier", "backup carrier", "alternative carrier"],
            "resource": ["cold storage", "refrigeration", "refrigerated storage", "cold-chain equipment"],
            "permission": ["road permit", "delivery authorization", "delivery permission", "permission"],
            "deadlines": ["can meet the deadline", "can arrive before the deadline", "can arrive on time"],
        }
    return {
        "proposed": ["deployment engineer", "proposed engineer", "primary engineer"],
        "backup": ["backup engineer", "alternative engineer", "alternate engineer"],
        "resource": ["server access", "production access", "system access"],
        "permission": ["production approval", "deployment approval", "production permission", "approval"],
        "deadlines": ["can meet the deadline", "can finish before the deadline", "can complete on time"],
    }


def _permission_clause(subject: str, obj: str, index: int) -> str:
    forms = (
        f"{subject} has {obj}",
        f"{subject} possesses {obj}",
        f"{subject} is authorized",
        f"{subject} has authorization",
    )
    return forms[index % len(forms)]


def _negative_resource(subject: str, obj: str, index: int) -> str:
    forms = (
        f"{subject} lacks {obj}",
        f"{subject} does not have {obj}",
        f"{subject} has no {obj}",
        f"{subject} is without {obj}",
        f"{subject} is unavailable to {obj}",
    )
    return forms[index % len(forms)]


def _positive_resource(subject: str, obj: str, index: int) -> str:
    return f"{subject} {'has' if index % 2 == 0 else 'possesses'} {obj}"


def _prompt(clauses: list[str], intent: str) -> str:
    return ". ".join(value[0].upper() + value[1:] for value in [*clauses, intent]) + "."


def equivalence_cases(domain: str, count: int) -> list[dict[str, Any]]:
    profile = _domain_profile(domain)
    intents = (
        "validate the proposed plan and select a replacement",
        "can the proposed plan be used and which plan should replace it",
        "review the proposed option and choose a replacement",
        "is the proposed plan valid and what should we use instead",
    )
    cases = []
    for index in range(count):
        proposed = profile["proposed"][index % len(profile["proposed"])]
        backup = profile["backup"][(index * 3 + 1) % len(profile["backup"])]
        resource = profile["resource"][(index * 2 + 1) % len(profile["resource"])]
        backup_resource = profile["resource"][(index * 3) % len(profile["resource"])]
        permission = profile["permission"][(index + 1) % len(profile["permission"])]
        backup_permission = profile["permission"][(index * 3 + 2) % len(profile["permission"])]
        if index % 2 == 0:
            clauses = [
                _negative_resource(proposed, resource, index),
                _permission_clause(proposed, permission, index),
                f"{proposed} {profile['deadlines'][index % 3]}",
                _positive_resource(backup, backup_resource, index),
                _permission_clause(backup, backup_permission, index + 1),
                f"{backup} {profile['deadlines'][(index + 1) % 3]}",
            ]
            rotation = index % len(clauses)
            clauses = clauses[rotation:] + clauses[:rotation]
        else:
            proposed_block = [
                _negative_resource(proposed, resource, index),
                _permission_clause("it", permission, index),
                f"it {profile['deadlines'][index % 3]}",
            ]
            backup_block = [
                _positive_resource(backup, backup_resource, index),
                _permission_clause("it", backup_permission, index + 1),
                f"it {profile['deadlines'][(index + 1) % 3]}",
            ]
            clauses = proposed_block + backup_block if index % 4 == 1 else backup_block + proposed_block
        cases.append({
            "id": f"{domain[:3]}-equivalent-{index + 1:02d}",
            "domain": domain,
            "kind": "EQUIVALENT",
            "prompt": _prompt(clauses, intents[index % len(intents)]),
            "expected": BASELINE_OUTPUT,
        })
    prompts = [case["prompt"] for case in cases]
    if len(set(prompts)) != count:
        raise CampaignFailure(f"{domain}: generated equivalence prompts are not unique")
    return cases


def _graph(result: dict[str, Any]) -> str:
    return str(result["stages"][0]["program"]["grounding"]["semantic_interpretation"]["semantic_graph_hash"])


def run_campaign() -> dict[str, Any]:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if fixture.get("schema") != "moth-v5-adversarial-semantic-campaign/1.0" or not fixture.get("frozen_before_execution"):
        raise CampaignFailure("campaign fixture is not frozen")
    before = _protected_hashes()
    count = int(fixture["equivalence_cases_per_domain"])
    cases = [
        *equivalence_cases("delivery", count),
        *equivalence_cases("deployment", count),
        *fixture["contrasts"],
    ]
    if len(cases) != 50 or len({case["id"] for case in cases}) != 50:
        raise CampaignFailure("campaign must contain exactly 50 unique cases")

    results: list[dict[str, Any]] = []
    graph_sets = {"delivery": set(), "deployment": set()}
    replay_count = 0
    accepted = 0
    refused = 0
    valid_contrasts = 0
    expected_refusals = 0
    with TemporaryDirectory(prefix="moth-v5-adversarial-") as temporary:
        encoder = DeterministicEncoder()
        store = WorldStore(Path(temporary) / "store-5.0.sqlite3")
        store.publish(WorldRole.INPUT, {"input.moth": semantic_source("delivery", "deployment")}, encoder=encoder)
        store.publish(WorldRole.MAIN, {"main.moth": decision_source()}, encoder=encoder)
        store.publish(WorldRole.SURFACE, {"surface.moth": SURFACE}, encoder=encoder)
        bundle = store.activate()
        worlds = store.bundle_worlds(bundle)
        main_world_hash = worlds[WorldRole.MAIN].world_hash
        main_program_ids: set[str] = set()

        for case in cases:
            result = store.query(str(case["prompt"]))
            replay = store.replay(str(result["episode_id"]), encoder_free=True)
            if replay != canonical_bytes(result):
                raise CampaignFailure(f"{case['id']}: replay differs from result bytes")
            replay_count += 1
            kind = str(case["kind"])
            if kind == "EQUIVALENT":
                if result.get("status") != "ANSWER" or result.get("output", {}).get("value") != case["expected"]:
                    raise CampaignFailure(f"{case['id']}: equivalent prompt did not produce the baseline answer")
                graph_sets[str(case["domain"])].add(_graph(result))
                main_program_ids.add(str(result["stages"][1]["program"]["slots"]["PROGRAM"]))
                accepted += 1
            elif kind == "ANSWER_DIFFERENT":
                if result.get("status") != "ANSWER" or result.get("output", {}).get("value") != case["expected"]:
                    raise CampaignFailure(f"{case['id']}: valid contrast produced the wrong answer")
                if _graph(result) in graph_sets[str(case["domain"])]:
                    raise CampaignFailure(f"{case['id']}: semantic contrast collapsed into the baseline graph")
                main_program_ids.add(str(result["stages"][1]["program"]["slots"]["PROGRAM"]))
                accepted += 1
                valid_contrasts += 1
            else:
                actual = result.get("refusal", {}).get("code")
                if result.get("status") != "REFUSAL" or actual != case["expected_refusal"]:
                    raise CampaignFailure(f"{case['id']}: expected {case['expected_refusal']}, got {actual}")
                refused += 1
                expected_refusals += 1
            if result.get("execution") != {"performed": False, "dispatch_count": 0}:
                raise CampaignFailure(f"{case['id']}: execution contract changed")
            results.append({
                "id": case["id"], "status": result["status"],
                "result_hash": result["replay"]["result_hash"],
                "semantic_graph_hash": _graph(result) if result["status"] == "ANSWER" else None,
                "refusal": result.get("refusal", {}).get("code"),
            })

        if any(len(values) != 1 for values in graph_sets.values()):
            raise CampaignFailure("equivalent prompts did not converge to one graph per domain")
        if len(main_program_ids) != 1:
            raise CampaignFailure("accepted prompts did not share one Main program")

        accepted_result = store.query(equivalence_cases("delivery", 1)[0]["prompt"])
        tampered = deepcopy(accepted_result)
        tampered["stages"][0]["program"]["grounding"]["semantic_interpretation"]["facts"][0]["polarity"] = "TAMPERED"
        try:
            verify_archived_result(tampered, worlds, bundle)
        except IntegrityError:
            tamper_detected = True
        else:
            tamper_detected = False
        if not tamper_detected:
            raise CampaignFailure("altered semantic trace passed verification")

    after = _protected_hashes()
    if before != after:
        raise CampaignFailure("protected Runtime 5.0 or production-store bytes changed")
    result_manifest_hash = sha256_bytes(canonical_bytes(results))
    return {
        "schema": "moth-v5-adversarial-semantic-result/1.0",
        "verdict": "ADVERSARIAL_SEMANTIC_INVARIANCE_CONFIRMED",
        "cases": len(cases),
        "accepted": accepted,
        "equivalent_accepted": accepted - valid_contrasts,
        "valid_contrasts": valid_contrasts,
        "expected_refusals": expected_refusals,
        "refused": refused,
        "unsafe_acceptances": 0,
        "equivalence_graph_counts": {key: len(value) for key, value in graph_sets.items()},
        "shared_main_program_count": len(main_program_ids),
        "main_world_hash": main_world_hash,
        "encoder_free_replays": replay_count,
        "semantic_tamper_detected": tamper_detected,
        "execution_performed": False,
        "dispatch_count": 0,
        "protected_hashes_unchanged": True,
        "protected_hashes": before,
        "fixture_sha256": sha256_bytes(FIXTURE.read_bytes()),
        "result_manifest_sha256": result_manifest_hash,
    }


def main() -> None:
    print(json.dumps(run_campaign(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
