"""Run the frozen semantic-equivalence campaign and print compact JSON evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time
from typing import Any

from moth_runtime_v4_9.canonical import canonical_bytes, sha256_file
from moth_runtime_v4_9.encoder import LocalBGEEncoder

from .compiler import FIXTURE, load_semantic_world
from .downstream import compile_downstream_world, settle_downstream
from .model import SemanticRefusal
from .reference import verify_against_compiled_world
from .settlement import settle_internal, settle_text, verify_settlement

ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = Path(__file__).resolve().parent
CASES_PATH = EXPERIMENT / "fixtures/cases-en-1.0.json"
PROTECTED_HASH = "3ddad5a0f486179c3a9d56665bdbd1aeb1f770a660bcaf7828a490c7746beccb"


def protected_tree_hash() -> str:
    completed = subprocess.run(
        [
            "git", "ls-files", "src/moth_runtime", "src/moth_runtime_v4_8",
            "src/moth_runtime_v4_9", "config/v4.8", "config/v4.9", "docs/v4.8", "docs/v4.9",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = bytearray()
    for relative in sorted(completed.stdout.splitlines()):
        file_hash = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        payload.extend(f"{file_hash}  {relative}\n".encode("utf-8"))
    return hashlib.sha256(payload).hexdigest()


def implementation_manifest() -> dict[str, str]:
    return {
        path.relative_to(EXPERIMENT).as_posix(): sha256_file(path)
        for path in sorted(EXPERIMENT.glob("*.py"))
    }


def _record(
    case: dict[str, Any],
    *,
    actual_meaning: str | None,
    actual_refusal: str | None,
    result_hash: str | None,
) -> dict[str, Any]:
    expected_meaning = case.get("expected_meaning")
    expected_refusal = case.get("expected_refusal")
    passed = (
        actual_meaning == expected_meaning and actual_refusal is None
        if expected_meaning is not None
        else actual_refusal == expected_refusal and actual_meaning is None
    )
    return {
        "id": case["id"],
        "group": case["group"],
        "expected_meaning": expected_meaning,
        "expected_refusal": expected_refusal,
        "actual_meaning": actual_meaning,
        "actual_refusal": actual_refusal,
        "result_hash": result_hash,
        "passed": passed,
    }


def run() -> dict[str, Any]:
    started = time.perf_counter()
    world = load_semantic_world()
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    encoder = LocalBGEEncoder()
    encoder_status = encoder.verify_assets()
    meaning_names = {item.meaning_id: item.key for item in world.meanings}
    rows: list[dict[str, Any]] = []

    for case in cases["text_cases"]:
        try:
            result = settle_text(world, case["text"], encoder=encoder)
            verify_settlement(world, result, text=case["text"], encoder=encoder)
            verify_against_compiled_world(world, result)
            rows.append(_record(
                case,
                actual_meaning=meaning_names[result.meaning_id],
                actual_refusal=None,
                result_hash=hashlib.sha256(canonical_bytes(result.canonical())).hexdigest(),
            ))
        except SemanticRefusal as exc:
            rows.append(_record(
                case,
                actual_meaning=None,
                actual_refusal=exc.code.value,
                result_hash=None,
            ))

    for case in cases["internal_cases"]:
        try:
            result = settle_internal(world, case["observation"])
            verify_settlement(world, result, observation=case["observation"])
            verify_against_compiled_world(world, result)
            rows.append(_record(
                case,
                actual_meaning=meaning_names[result.meaning_id],
                actual_refusal=None,
                result_hash=hashlib.sha256(canonical_bytes(result.canonical())).hexdigest(),
            ))
        except SemanticRefusal as exc:
            rows.append(_record(
                case,
                actual_meaning=None,
                actual_refusal=exc.code.value,
                result_hash=None,
            ))

    by_group: dict[str, dict[str, int]] = {}
    for row in rows:
        group = by_group.setdefault(row["group"], {"passed": 0, "total": 0})
        group["total"] += 1
        group["passed"] += int(row["passed"])

    target_texts = [
        "Direct courier lacks cold storage.",
        "The proposed courier does not have refrigerated storage.",
        "Refrigeration is unavailable to the direct carrier.",
        "The primary delivery operator lacks cold-chain equipment.",
    ]
    target_internal = [
        {"relation": "LACKS", "arguments": {"holder": "direct-courier", "capability": "cold-storage"}},
        {"relation": "CAPABILITY_UNAVAILABLE_TO", "arguments": {"capability": "cold-storage", "recipient": "direct-courier"}},
        {"relation": "HAS_CAPABILITY_NEGATIVE", "arguments": {"subject": "direct-courier", "object": "cold-storage"}},
    ]
    converged_ids = {
        *(settle_text(world, value, encoder=encoder).meaning_id for value in target_texts),
        *(settle_internal(world, value).meaning_id for value in target_internal),
    }
    downstream_world, downstream_encoder = compile_downstream_world()
    downstream_outputs = {
        settle_downstream(
            downstream_world,
            downstream_encoder,
            meaning_names[meaning_id],
        ).output
        for meaning_id in converged_ids
    }
    try:
        settle_text(world, target_texts[-1], encoder=None)
        semantic_prior_ablation = False
    except SemanticRefusal:
        semantic_prior_ablation = True

    protected_actual = protected_tree_hash()
    all_rows_pass = all(row["passed"] for row in rows)
    causal_checks = {
        "text_internal_convergence": len(converged_ids) == 1,
        "unmodified_v4_9_downstream_convergence": downstream_outputs == {"PLAN_INVALID"},
        "semantic_prior_required_for_unseen_surfaces": semantic_prior_ablation,
        "no_unsafe_collapses": all_rows_pass,
        "protected_runtime_preserved": protected_actual == PROTECTED_HASH,
    }
    verdict = (
        "SEMANTIC_EQUIVALENCE_CONFIRMED_WITHIN_FROZEN_LANGUAGE_FIELD"
        if all_rows_pass and all(causal_checks.values())
        else "NO_GO"
    )
    return {
        "schema": "moth-semantic-equivalence-campaign/1.0",
        "attempt": "001",
        "verdict": verdict,
        "runtime_base_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
        ).stdout.strip(),
        "semantic_world_hash": world.world_hash,
        "semantic_world_fixture_sha256": sha256_file(FIXTURE),
        "cases_fixture_sha256": sha256_file(CASES_PATH),
        "encoder": encoder_status,
        "machine": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "metrics": {
            "passed": sum(int(row["passed"]) for row in rows),
            "total": len(rows),
            "accepted": sum(row["actual_meaning"] is not None for row in rows),
            "safe_refusals": sum(row["actual_refusal"] is not None and row["passed"] for row in rows),
            "unsafe_collapses": sum(not row["passed"] and row["actual_meaning"] is not None for row in rows),
            "by_group": dict(sorted(by_group.items())),
        },
        "causal_checks": causal_checks,
        "converged_meaning_id": next(iter(converged_ids)) if len(converged_ids) == 1 else None,
        "protected_runtime_tree": {
            "expected": PROTECTED_HASH,
            "actual": protected_actual,
        },
        "implementation_manifest": implementation_manifest(),
        "rows_hash": hashlib.sha256(canonical_bytes(rows)).hexdigest(),
        "rows": rows,
        "wall_seconds": round(time.perf_counter() - started, 6),
    }


def main() -> int:
    print(json.dumps(run(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
