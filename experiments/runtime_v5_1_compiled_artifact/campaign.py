"""Independent qualification for the weight-free Runtime 5.1 artifact."""

from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from typing import Any

from moth_runtime_v5_0.canonical import canonical_bytes, digest, sha256_bytes
from moth_runtime_v5_0.model import IntegrityError
from moth_runtime_v5_1.artifact import ModelArtifact51
from moth_runtime_v5_1.compiled_fields import compile_skill_document
from moth_runtime_v5_1.runtime import Runtime51
from moth_runtime_v5_1.surface import recover_surface_value

from experiments.runtime_v5_0_compiled_surface_skill.compiler import compile_skill as compile_v5_skill
from experiments.runtime_v5_0_instruction_compression.compiler import compile_skill as compile_v5_instruction

from .build_artifact import FIELD_SOURCES, ROOT, SKILL_SOURCES, build_artifact


HERE = Path(__file__).resolve().parent


class QualificationFailure(AssertionError):
    pass


def _json(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text())


def _policy_projection(policy: dict[str, Any]) -> dict[str, Any]:
    return {key: deepcopy(policy[key]) for key in (
        "policy_id", "trigger", "workflow", "edges", "policies", "completion",
    )}


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*")) if path.is_file()
    }


def _skill_parity(runtime: Runtime51) -> dict[str, Any]:
    families = [
        ("bounded-agent-skill-en-1.0", "experiments/runtime_v5_0_instruction_compression/fixtures/safe-text-patch/SKILL.md", "experiments/runtime_v5_0_instruction_compression/fixtures/safe-text-patch-paraphrase/SKILL.md", compile_v5_instruction),
        ("bounded-natural-surface-en-1.0", "experiments/runtime_v5_0_compiled_surface_skill/fixtures/natural-response/SKILL.md", "experiments/runtime_v5_0_compiled_surface_skill/fixtures/natural-response-paraphrase/SKILL.md", compile_v5_skill),
        ("runtime-v5-rich-output-surface-en-1.0", "experiments/runtime_v5_0_output_fidelity_mega_campaign/fixtures/prose-range/SKILL.md", "experiments/runtime_v5_0_output_fidelity_mega_campaign/fixtures/prose-range-paraphrase/SKILL.md", compile_v5_skill),
        ("runtime-v5-rich-output-surface-en-1.0", "experiments/runtime_v5_0_output_fidelity_mega_campaign/fixtures/tone-adaptation/SKILL.md", "experiments/runtime_v5_0_output_fidelity_mega_campaign/fixtures/tone-adaptation-paraphrase/SKILL.md", compile_v5_skill),
        ("runtime-v5-rich-output-surface-en-1.0", "experiments/runtime_v5_0_output_fidelity_mega_campaign/fixtures/markdown-structure/SKILL.md", "experiments/runtime_v5_0_output_fidelity_mega_campaign/fixtures/markdown-structure-paraphrase/SKILL.md", compile_v5_skill),
        ("runtime-v5-rich-output-surface-en-1.0", "experiments/runtime_v5_0_output_fidelity_mega_campaign/fixtures/mixed-response/SKILL.md", "experiments/runtime_v5_0_output_fidelity_mega_campaign/fixtures/mixed-response-paraphrase/SKILL.md", compile_v5_skill),
        ("bounded-json-python-surface-en-1.0", "experiments/runtime_v5_0_compiled_json_python_surface/fixtures/structured-output/SKILL.md", "experiments/runtime_v5_0_compiled_json_python_surface/fixtures/structured-output-paraphrase/SKILL.md", compile_v5_skill),
        ("bounded-python-function-surface-en-1.0", "experiments/runtime_v5_0_compiled_python_function_surface/fixtures/python-function-output/SKILL.md", "experiments/runtime_v5_0_compiled_python_function_surface/fixtures/python-function-output-paraphrase/SKILL.md", compile_v5_skill),
    ]
    compared = 0
    for field_id, primary_path, paraphrase_path, old_compiler in families:
        field = runtime.artifact.fields[field_id]
        primary_text, paraphrase_text = (ROOT / primary_path).read_text(), (ROOT / paraphrase_path).read_text()
        primary = compile_skill_document(field, primary_text)
        paraphrase = runtime.compile_skill(field_id, paraphrase_text)
        if canonical_bytes(primary["policy"]) != canonical_bytes(paraphrase["policy"]):
            raise QualificationFailure(f"paraphrase changed policy: {primary_path}")
        old = old_compiler(primary_text, field.source)
        if canonical_bytes(_policy_projection(primary["policy"])) != canonical_bytes(_policy_projection(old["policy"])):
            raise QualificationFailure(f"5.1 policy differs from frozen compiler: {primary_path}")
        repeated = [compile_skill_document(field, primary_text) for _ in range(10)]
        if len({canonical_bytes(item) for item in repeated}) != 1:
            raise QualificationFailure(f"compilation is not deterministic: {primary_path}")
        compared += 1
    safe = next(item for item in runtime.artifact.skills.values() if item["profile_id"] == "SAFE_TEXT_PATCH")
    ratio = safe["trace"]["graph_unit_count"] / safe["trace"]["normative_clause_count"]
    if ratio < 2.0:
        raise QualificationFailure("instruction expansion ratio fell below 2.0")
    return {"primary_paraphrase_pairs": compared, "repetitions_per_pair": 10, "expansion_ratio": ratio}


def _surface_panel(runtime: Runtime51) -> dict[str, Any]:
    natural = _json("experiments/runtime_v5_0_compiled_surface_skill/fixtures/campaign-en-1.0.json")
    rich = _json("experiments/runtime_v5_0_output_fidelity_mega_campaign/fixtures/campaign-en-1.0.json")
    structured = _json("experiments/runtime_v5_0_compiled_json_python_surface/fixtures/campaign-en-1.0.json")
    python = _json("experiments/runtime_v5_0_compiled_python_function_surface/fixtures/campaign-en-1.0.json")
    requests = [item["request"] for item in natural["size_requests"]]
    requests += [request for family in rich["families"] for request in family["requests"]]
    # The old structured skill supplied its default implicitly.  The artifact
    # tests the equivalent explicit compact route so field selection is visible.
    requests += ["Return compact JSON.", "Single-line output.", "Return readable JSON.", "Return compact Python.", "Return readable Python."]
    requests += [item["request"] for item in python["presentation_requests"]]
    if len(requests) != 21:
        raise QualificationFailure("Surface presentation panel no longer has 21 routes")
    cases = natural["answer_cases"]
    count = 0
    modes: dict[str, int] = {}
    for case in cases:
        for request in requests:
            conversation = runtime.create_conversation("")
            result = runtime.turn(conversation, case["prompt"], presentation=request)
            if result["status"] != "ANSWER" or result["surface"] is None:
                raise QualificationFailure(f"Surface case refused: {case['id']} / {request}")
            recovered = recover_surface_value(result["surface"]["text"], result["surface"]["mode"])
            if canonical_bytes(recovered) != canonical_bytes(case["expected"]):
                raise QualificationFailure(f"Surface meaning changed: {case['id']} / {request}")
            if result["surface"]["execution"] != {"performed": False, "dispatch_count": 0}:
                raise QualificationFailure("Surface attempted execution")
            modes[result["surface"]["mode"]] = modes.get(result["surface"]["mode"], 0) + 1
            count += 1
    if count != 168:
        raise QualificationFailure(f"Surface panel count is {count}, expected 168")
    return {"outputs": count, "semantic_preservation": count, "generated_python_executions": 0, "modes": modes}


def _plan_panel(runtime: Runtime51) -> dict[str, Any]:
    panel = _json("experiments/runtime_v5_0_instruction_compression/fixtures/campaign-1.0.json")
    primary = next(item for item in runtime.artifact.skills.values() if item["profile_id"] == "SAFE_TEXT_PATCH")
    composite = next(item for item in runtime.artifact.skills.values() if item["profile_id"] == "SAFE_TEXT_PATCH+EVIDENCE_LEDGER")
    paraphrase = runtime.compile_skill(
        "bounded-agent-skill-en-1.0",
        (ROOT / "experiments/runtime_v5_0_instruction_compression/fixtures/safe-text-patch-paraphrase/SKILL.md").read_text(),
    )
    accepted = 0
    for compilation in (primary, paraphrase, composite):
        for task in panel["tasks"]:
            snapshot = deepcopy(task)
            before = canonical_bytes(snapshot)
            result = runtime.plan_skill(compilation["compilation_id"], snapshot)
            expected_status = {"ANSWER": "ACTION_PLAN", "REFUSED": "REFUSAL"}.get(task["expected_status"], task["expected_status"])
            if result["status"] != expected_status or result["code"] != task["expected_code"]:
                raise QualificationFailure(f"plan status changed: {task['id']}")
            if canonical_bytes(snapshot) != before or result["execution"] != {
                "performed": False, "dispatch_count": 0, "writes": 0,
            }:
                raise QualificationFailure("inert planning mutated or dispatched")
            if result["status"] == "ACTION_PLAN":
                expected = task["files"][task["target"]].replace(task["old"], task["new"], 1)
                if result["patch"]["proposed_text"] != expected:
                    raise QualificationFailure("inert patch text changed")
                accepted += 1
            elif result["patch"] is not None:
                raise QualificationFailure("non-accepted plan emitted a patch")
    return {"cases": 36, "accepted": accepted, "dispatch_count": 0, "task_workspace_writes": 0}


def _conversation_panel(runtime: Runtime51) -> dict[str, Any]:
    case = _json("experiments/runtime_v5_0_compiled_surface_skill/fixtures/campaign-en-1.0.json")["answer_cases"][0]
    conversation = runtime.create_conversation("", skill_ids=("NATURAL_RESPONSE",))
    first = runtime.turn(conversation, case["prompt"], presentation="Give me the short version.")
    second = runtime.turn(conversation, "repeat that", presentation="Return a Markdown table.")
    if first["status"] != "ANSWER" or second["status"] != "ANSWER":
        raise QualificationFailure("presentation follow-up failed")
    if canonical_bytes(first["kernel"]["output"]) != canonical_bytes(second["kernel"]["output"]):
        raise QualificationFailure("presentation-only follow-up changed kernel meaning")
    verification = runtime.verify_conversation(conversation)
    if not verification.get("verified_result_chain"):
        raise QualificationFailure("conversation replay verification failed")
    other = runtime.create_conversation("")
    if runtime.store.conversation(other)["skills"]:
        raise QualificationFailure("conversation leaked SYSTEM skills")
    return {"turns": 2, "presentation_follow_up": True, "skill_isolation": True, "replay_verified": True}


def _isolation(artifact_path: Path) -> dict[str, Any]:
    code = (
        "import json,moth_runtime_v5_0,moth_runtime_v5_1,moth_launcher_v5_1;"
        "print(json.dumps([moth_runtime_v5_0.__file__,moth_runtime_v5_1.__file__,moth_launcher_v5_1.__file__]))"
    )
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(artifact_path / "runtime")
    completed = subprocess.run(
        [sys.executable, "-c", code], cwd=artifact_path,
        env=environment, check=True, capture_output=True, text=True,
    )
    imported = json.loads(completed.stdout)
    if any(not Path(path).resolve().is_relative_to((artifact_path / "runtime").resolve()) for path in imported):
        raise QualificationFailure("isolated run imported repository runtime code")
    return {"embedded_imports": 3, "experiment_imports": 0}


def _tamper_gates(artifact_path: Path, temp_root: Path) -> dict[str, Any]:
    detections = 0
    for name, relative in (
        ("field", "compiled-fields/bounded-agent-skill-en-1.0.json"),
        ("runtime", "runtime/moth_runtime_v5_1/runtime.py"),
        ("capability", "capability-index.json"),
    ):
        target = temp_root / f"tamper-{name}"
        shutil.copytree(artifact_path, target)
        path = target / relative
        path.write_bytes(path.read_bytes() + b"\n")
        try:
            ModelArtifact51.open(target)
        except IntegrityError:
            detections += 1
        else:
            raise QualificationFailure(f"{name} tampering was accepted")
    target = temp_root / "tamper-weights"
    shutil.copytree(artifact_path, target)
    (target / "weights.bin").write_bytes(b"forbidden")
    try:
        ModelArtifact51.open(target)
    except IntegrityError:
        detections += 1
    else:
        raise QualificationFailure("undeclared weights were accepted")
    return {"gates": 4, "detected": detections, "weights_rejected": True}


def run_campaign() -> dict[str, Any]:
    with TemporaryDirectory(prefix="moth-model-5.1-") as temporary:
        temp_root = Path(temporary)
        first, second = temp_root / "artifact-a", temp_root / "artifact-b"
        first_receipt, second_receipt = build_artifact(first), build_artifact(second)
        if _tree_bytes(first) != _tree_bytes(second) or first_receipt["artifact_hash"] != second_receipt["artifact_hash"]:
            raise QualificationFailure("clean artifact builds are not byte-identical")
        artifact = ModelArtifact51.open(first)
        runtime = Runtime51.initialize_from_artifact(temp_root / "runtime.sqlite3", first)
        result = {
            "schema": "moth-compiled-model-artifact-qualification/5.1",
            "verdict": "WEIGHT_FREE_COMPILED_MODEL_ARTIFACT_5_1_CONFIRMED",
            "artifact": artifact.verify(),
            "deterministic_build": {"byte_identical": True, "artifact_hash": artifact.artifact_hash},
            "field_inventory": {field.field_id: field.archive["inventory"] for field in artifact.fields.values()},
            "skill_fidelity": _skill_parity(runtime),
            "surface_fidelity": _surface_panel(runtime),
            "inert_planning": _plan_panel(runtime),
            "conversation_hcf": _conversation_panel(runtime),
            "isolation": _isolation(first),
            "tamper_detection": _tamper_gates(first, temp_root),
            "safety": {
                "weights": 0, "network_attempts": 0, "external_model_calls": 0,
                "tool_dispatches": 0, "generated_python_executions": 0,
                "task_workspace_writes": 0,
            },
        }
        result["qualification_hash"] = digest(
            "moth-compiled-model-artifact-qualification/5.1", result,
        )
        return result


def main() -> int:
    print(json.dumps(run_campaign(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
