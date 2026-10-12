from pathlib import Path
from typing import Any
from copy import deepcopy
import json
ROOT=Path(__file__).resolve().parents[2]
class QualificationFailure(AssertionError): pass
def _json(relative):return json.loads((ROOT/relative).read_text())

def _surface_panel(runtime: Any) -> dict[str, Any]:
    from moth_runtime_v5_3.legacy.canonical import canonical_bytes
    from moth_runtime_v5_3.surface import recover_surface_value

    natural = _json("experiments/runtime_v5_3_conversational_reasoning/fixtures/legacy-0.json")
    rich = _json("experiments/runtime_v5_3_conversational_reasoning/fixtures/legacy-1.json")
    python = _json("experiments/runtime_v5_3_conversational_reasoning/fixtures/legacy-2.json")
    requests = [item["request"] for item in natural["size_requests"]]
    requests += [request for family in rich["families"] for request in family["requests"]]
    requests += [
        "Return compact JSON.",
        "Single-line output.",
        "Return readable JSON.",
        "Return compact Python.",
        "Return readable Python.",
    ]
    requests += [item["request"] for item in python["presentation_requests"]]
    if len(requests) != 21:
        raise QualificationFailure("surface route panel changed")
    count = 0
    modes: dict[str, int] = {}
    for case in natural["answer_cases"]:
        for request in requests:
            conversation = runtime.create_conversation("")
            result = runtime.turn(conversation, case["prompt"], presentation=request)
            if result["status"] != "ANSWER" or result["surface"] is None:
                raise QualificationFailure(f"surface case refused: {case['id']} / {request}")
            recovered = recover_surface_value(
                result["surface"]["text"], result["surface"]["mode"]
            )
            if canonical_bytes(recovered) != canonical_bytes(case["expected"]):
                raise QualificationFailure(f"surface meaning changed: {case['id']} / {request}")
            if result["surface"]["execution"] != {
                "performed": False,
                "dispatch_count": 0,
            }:
                raise QualificationFailure("surface attempted execution")
            if result["deterministic"]["candidate_dictionary_reconstructions"] != 0:
                raise QualificationFailure("candidate dictionary was reconstructed")
            modes[result["surface"]["mode"]] = modes.get(result["surface"]["mode"], 0) + 1
            count += 1
    if count != 168:
        raise QualificationFailure(f"surface panel count is {count}")
    return {
        "outputs": count,
        "semantic_preservation": count,
        "candidate_dictionary_reconstructions": 0,
        "generated_python_executions": 0,
        "modes": modes,
    }


def _plan_panel(runtime: Any) -> dict[str, Any]:
    from moth_runtime_v5_3.legacy.canonical import canonical_bytes

    panel = _json("experiments/runtime_v5_3_conversational_reasoning/fixtures/legacy-3.json")
    primary = next(
        item for item in runtime.artifact.skills.values()
        if item["profile_id"] == "SAFE_TEXT_PATCH"
    )
    composite = next(
        item for item in runtime.artifact.skills.values()
        if item["profile_id"] == "SAFE_TEXT_PATCH+EVIDENCE_LEDGER"
    )
    paraphrase = runtime.compile_skill(
        "bounded-agent-skill-en-1.0",
        (ROOT / "experiments/runtime_v5_3_conversational_reasoning/fixtures/legacy-4.md").read_text(encoding="utf-8"),
    )
    accepted = 0
    count = 0
    for compilation in (primary, paraphrase, composite):
        for task in panel["tasks"]:
            snapshot = deepcopy(task)
            before = canonical_bytes(snapshot)
            result = runtime.plan_skill(compilation["compilation_id"], snapshot)
            expected = {
                "ANSWER": "ACTION_PLAN",
                "REFUSED": "REFUSAL",
            }.get(task["expected_status"], task["expected_status"])
            if result["status"] != expected or result["code"] != task["expected_code"]:
                raise QualificationFailure(f"skill plan changed: {task['id']}")
            if canonical_bytes(snapshot) != before or result["execution"] != {
                "performed": False,
                "dispatch_count": 0,
                "writes": 0,
            }:
                raise QualificationFailure("skill planner mutated or dispatched")
            accepted += int(result["status"] == "ACTION_PLAN")
            count += 1
    if count != 36:
        raise QualificationFailure(f"skill panel count is {count}")
    return {
        "cases": count,
        "accepted": accepted,
        "dispatch_count": 0,
        "task_workspace_writes": 0,
    }


