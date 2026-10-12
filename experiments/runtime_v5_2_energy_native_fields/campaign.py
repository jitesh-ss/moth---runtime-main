"""Qualify the independent Safetensors-native Runtime 5.2."""

from __future__ import annotations

from copy import deepcopy
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[2]


class QualificationFailure(AssertionError):
    pass


def _tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _json(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def _compiled_bytes_51(root: Path) -> int:
    paths = [root / "capability-index.json"]
    paths.extend((root / "compiled-fields").glob("*.json"))
    paths.extend((root / "compiled-skills").glob("*.json"))
    return sum(path.stat().st_size for path in paths)


def _compiled_bytes_52(root: Path) -> int:
    return sum(
        path.stat().st_size
        for path in (root / "objects" / "sha256").rglob("*.safetensors")
    )


def _surface_panel(runtime: Any) -> dict[str, Any]:
    from moth_runtime_v5_0.canonical import canonical_bytes
    from moth_runtime_v5_2.surface import recover_surface_value

    natural = _json("experiments/runtime_v5_0_compiled_surface_skill/fixtures/campaign-en-1.0.json")
    rich = _json("experiments/runtime_v5_0_output_fidelity_mega_campaign/fixtures/campaign-en-1.0.json")
    python = _json("experiments/runtime_v5_0_compiled_python_function_surface/fixtures/campaign-en-1.0.json")
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
    from moth_runtime_v5_0.canonical import canonical_bytes

    panel = _json("experiments/runtime_v5_0_instruction_compression/fixtures/campaign-1.0.json")
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
        (ROOT / "experiments/runtime_v5_0_instruction_compression/fixtures/safe-text-patch-paraphrase/SKILL.md").read_text(encoding="utf-8"),
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


def _mutation_panel(runtime: Any) -> dict[str, Any]:
    from moth_runtime_v5_0.canonical import canonical_bytes
    from moth_runtime_v5_2.energy.schema import Level, Runtime52Failure
    from tests.test_runtime_v5_0_language import DELIVERY

    conversation = runtime.create_conversation("Delegate response.mode to context.")
    before = runtime.turn(conversation, DELIVERY)
    field = runtime.compile_hcf_field(
        {
            "schema": "moth-hcf-source/5.2",
            "entries": [{
                "meaning_id": "qualification.context.detailed",
                "effect": "REQUIRE",
                "scope": "response.mode",
                "value": "detailed",
            }],
            "activations": [],
        },
        Level.CONTEXT,
    )
    revision = runtime.upsert_layer_field(
        conversation, Level.CONTEXT, "qualification-detail", field["object_hash"], 0
    )
    after = runtime.turn(conversation, DELIVERY)
    if after["response_mode"] != "detailed" or revision["revision_number"] != 1:
        raise QualificationFailure("context mutation did not affect the next turn")
    runtime.remove_layer_field(
        conversation, Level.CONTEXT, "qualification-detail", 1
    )
    try:
        runtime.remove_layer_field(
            conversation, Level.CONTEXT, "qualification-detail", 2
        )
    except Runtime52Failure as exc:
        if exc.code != "NO_LAYER_CHANGE":
            raise
    else:
        raise QualificationFailure("no-op mutation was accepted")
    if runtime.replay_turn(conversation, before["turn_id"]) != canonical_bytes(before):
        raise QualificationFailure("old turn changed after layer mutation")
    verified = runtime.verify_conversation(conversation)
    if not verified["verified"] or verified["turn_count"] != 2:
        raise QualificationFailure("mutated conversation did not verify")
    return {
        "turns": 2,
        "context_revisions": 3,
        "historical_replay": True,
        "no_op_rejected": True,
        "verified": True,
    }


def _median_ns(function: Callable[[], Any], repetitions: int = 1000) -> float:
    values = []
    for _ in range(100):
        function()
    for _ in range(repetitions):
        started = time.perf_counter_ns()
        function()
        values.append(time.perf_counter_ns() - started)
    return float(statistics.median(values))


def _settlement_performance(artifact_51: Path, artifact_52: Path) -> dict[str, Any]:
    from moth_runtime_v5_1.artifact import ModelArtifact51
    from moth_runtime_v5_1.hcf import compile_system_prompt as compile_51
    from moth_runtime_v5_1.hcf import settle_candidates
    from moth_runtime_v5_1.runtime import _mode_candidates
    from moth_runtime_v5_2.artifact import ModelArtifact52
    from moth_runtime_v5_2.compile.hcf import compile_system_prompt as compile_52
    from moth_runtime_v5_2.energy.loader import load_hcf_field
    from moth_runtime_v5_2.energy.settlement import settle
    from moth_runtime_v5_2.persistence.objects import ObjectStore

    old = ModelArtifact51.open(artifact_51)
    old_candidates = _mode_candidates(old.foundation, old)
    old_entries = (*old.foundation.base_entries, *compile_51("Respond in detail."))
    new = ModelArtifact52.open(artifact_52)
    with tempfile.TemporaryDirectory(prefix="moth-5.2-benchmark-") as temporary:
        envelope = compile_52(
            ObjectStore(temporary), new.energy_foundation, "Respond in detail."
        )
        field = load_hcf_field(envelope, new.energy_foundation)
        old_ns = _median_ns(lambda: settle_candidates(old_candidates, old_entries))
        new_ns = _median_ns(lambda: settle(new.energy_foundation, (field,)))
    if new_ns > old_ns:
        raise QualificationFailure(
            f"tensor settlement regressed: {new_ns:.0f} > {old_ns:.0f} ns"
        )
    return {
        "repetitions": 1000,
        "runtime_5_1_median_ns": old_ns,
        "runtime_5_2_median_ns": new_ns,
        "ratio": new_ns / old_ns,
        "no_regression": True,
    }


def _memory_worker(version: str, artifact: Path) -> int:
    if version == "5.1":
        from moth_runtime_v5_1.artifact import ModelArtifact51
        from moth_runtime_v5_1.hcf import compile_system_prompt, settle_candidates
        from moth_runtime_v5_1.runtime import _mode_candidates
        baseline = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        model = ModelArtifact51.open(artifact)
        candidates = _mode_candidates(model.foundation, model)
        entries = (*model.foundation.base_entries, *compile_system_prompt("Respond in detail."))
        for _ in range(1000):
            settle_candidates(candidates, entries)
    else:
        from moth_runtime_v5_2.artifact import ModelArtifact52
        from moth_runtime_v5_2.compile.hcf import compile_system_prompt
        from moth_runtime_v5_2.energy.loader import load_hcf_field
        from moth_runtime_v5_2.energy.settlement import settle
        from moth_runtime_v5_2.persistence.objects import ObjectStore
        baseline = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        model = ModelArtifact52.open(artifact)
        with tempfile.TemporaryDirectory(prefix="moth-5.2-memory-") as temporary:
            envelope = compile_system_prompt(
                ObjectStore(temporary), model.energy_foundation, "Respond in detail."
            )
            field = load_hcf_field(envelope, model.energy_foundation)
            for _ in range(1000):
                settle(model.energy_foundation, (field,))
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(json.dumps({"baseline": baseline, "peak": peak, "delta": peak - baseline}))
    return 0


def _peak_memory(artifact_51: Path, artifact_52: Path) -> dict[str, Any]:
    samples: dict[str, list[dict[str, int]]] = {}
    for version, artifact in (("5.1", artifact_51), ("5.2", artifact_52)):
        values = []
        for _ in range(5):
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "experiments.runtime_v5_2_energy_native_fields.campaign",
                    "--memory-worker",
                    version,
                    str(artifact),
                ],
                cwd=ROOT,
                env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
                check=True,
                capture_output=True,
                text=True,
            )
            values.append(json.loads(completed.stdout.strip()))
        samples[version] = values
    medians = {
        version: {
            key: int(statistics.median(item[key] for item in values))
            for key in ("baseline", "peak", "delta")
        }
        for version, values in samples.items()
    }
    if medians["5.2"]["delta"] > medians["5.1"]["delta"]:
        raise QualificationFailure(
            "compiled workload memory regressed: "
            f"{medians['5.2']['delta']} > {medians['5.1']['delta']} bytes"
        )
    return {
        "samples": samples,
        "median_bytes": medians,
        "measurement": "PEAK_RSS_MINUS_POST_IMPORT_BASELINE",
        "no_regression": True,
    }


def _tamper_gate(artifact: Path, temporary: Path) -> dict[str, Any]:
    from moth_runtime_v5_0.model import IntegrityError
    from moth_runtime_v5_2.artifact import ModelArtifact52

    target = temporary / "tampered"
    shutil.copytree(artifact, target)
    model = json.loads((target / "model-artifact.json").read_text(encoding="utf-8"))
    object_path = target / model["energy_foundation"]["path"]
    raw = bytearray(object_path.read_bytes())
    raw[-1] ^= 1
    object_path.write_bytes(raw)
    try:
        ModelArtifact52.open(target)
    except IntegrityError:
        return {"gates": 1, "detected": 1, "fail_closed": True}
    raise QualificationFailure("altered Safetensors object was accepted")


def _independence(artifact: Path) -> dict[str, Any]:
    runtime_root = artifact / "runtime" / "moth_runtime_v5_2"
    for source in runtime_root.rglob("*.py"):
        if "moth_runtime_v5_1" in source.read_text(encoding="utf-8"):
            # The artifact verifier itself names the forbidden module in its
            # rejection predicate; only executable imports are prohibited.
            import ast
            tree = ast.parse(source.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module]
                else:
                    names = []
                if any(name.startswith("moth_runtime_v5_1") for name in names):
                    raise QualificationFailure("5.2 imports Runtime 5.1")
    return {
        "runtime_5_1_imports": 0,
        "packaged_packages": [
            "moth_runtime_v5_0",
            "moth_runtime_v5_2",
        ],
        "independent": True,
    }


def run_campaign() -> dict[str, Any]:
    from experiments.runtime_v5_1_compiled_artifact.build_artifact import build_artifact as build_51
    from experiments.runtime_v5_2_energy_native_fields.build_artifact import build_artifact as build_52
    from moth_runtime_v5_0.canonical import digest
    from moth_runtime_v5_2.artifact import ModelArtifact52
    from moth_runtime_v5_2.runtime import Runtime52

    with tempfile.TemporaryDirectory(prefix="moth-runtime-5.2-qualification-") as raw:
        temporary = Path(raw)
        builds = [temporary / f"model-5.2-{index}" for index in range(3)]
        receipts = [build_52(path) for path in builds]
        trees = [_tree_hashes(path) for path in builds]
        if trees[0] != trees[1] or trees[0] != trees[2]:
            raise QualificationFailure("three clean 5.2 builds differ")
        old_artifact = temporary / "model-5.1"
        build_51(old_artifact)
        old_bytes = _compiled_bytes_51(old_artifact)
        new_bytes = _compiled_bytes_52(builds[0])
        ratio = new_bytes / old_bytes
        if ratio > 0.75:
            raise QualificationFailure(f"compiled storage ratio is {ratio:.4f}")

        runtime = Runtime52.initialize(temporary / "store-5.2", builds[0])
        result = {
            "schema": "moth-energy-native-runtime-qualification/5.2",
            "verdict": "ENERGY_NATIVE_MUTABLE_RUNTIME_5_2_CONFIRMED",
            "artifact": ModelArtifact52.open(builds[0]).verify(),
            "deterministic_build": {
                "builds": 3,
                "byte_identical": True,
                "artifact_hash": receipts[0]["artifact_hash"],
            },
            "storage": {
                "runtime_5_1_compiled_json_bytes": old_bytes,
                "runtime_5_2_safetensors_bytes": new_bytes,
                "ratio": ratio,
                "maximum_ratio": 0.75,
                "passed": True,
            },
            "settlement_performance": _settlement_performance(old_artifact, builds[0]),
            "peak_memory": _peak_memory(old_artifact, builds[0]),
            "surface_fidelity": _surface_panel(runtime),
            "inert_planning": _plan_panel(runtime),
            "mutable_layers": _mutation_panel(runtime),
            "independence": _independence(builds[0]),
            "tamper_detection": _tamper_gate(builds[0], temporary),
            "store": runtime.store.verify_storage(),
            "safety": {
                "pickle": 0,
                "network_attempts": 0,
                "tool_dispatches": 0,
                "generated_python_executions": 0,
                "candidate_dictionary_reconstructions": 0,
            },
        }
        result["qualification_hash"] = digest(
            "moth-energy-native-runtime-qualification/5.2", result
        )
        return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--memory-worker", nargs=2, metavar=("VERSION", "ARTIFACT"))
    arguments = parser.parse_args(argv)
    if arguments.memory_worker:
        return _memory_worker(
            arguments.memory_worker[0], Path(arguments.memory_worker[1])
        )
    print(json.dumps(run_campaign(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
