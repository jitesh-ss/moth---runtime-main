"""Run the frozen compositional-language cascade campaign."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time
from typing import Any

from moth_runtime_v4_9.canonical import canonical_bytes, sha256_file

from .compiler import FIXTURE, load_contract
from .input_world import settle_input
from .model import LanguageRefusal
from .runtime import build_runtime

ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = Path(__file__).resolve().parent
CASES_PATH = EXPERIMENT / "fixtures/cases-en-1.0.json"
RUNTIME_HASH = "3ddad5a0f486179c3a9d56665bdbd1aeb1f770a660bcaf7828a490c7746beccb"
ATTEMPT_001_HASH = "e1b92641fc6dddc642977e32b4278f19d3da986083647ee6ec911ba3930404a3"


def _runtime_hash() -> str:
    completed = subprocess.run(
        [
            "git", "ls-files", "src/moth_runtime", "src/moth_runtime_v4_8",
            "src/moth_runtime_v4_9", "config/v4.8", "config/v4.9", "docs/v4.8", "docs/v4.9",
        ], cwd=ROOT, check=True, capture_output=True, text=True,
    )
    payload = bytearray()
    for relative in sorted(completed.stdout.splitlines()):
        digest = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        payload.extend(f"{digest}  {relative}\n".encode())
    return hashlib.sha256(payload).hexdigest()


def _attempt_001_hash() -> str:
    folder = ROOT / "experiments/runtime_v4_9_semantic_equivalence"
    paths = [
        path for path in folder.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and "runs" not in path.parts
    ]
    payload = bytearray()
    for path in sorted(paths):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        payload.extend(f"{digest}  {path.relative_to(ROOT).as_posix()}\n".encode())
    return hashlib.sha256(payload).hexdigest()


def _manifest() -> dict[str, str]:
    return {
        path.relative_to(EXPERIMENT).as_posix(): sha256_file(path)
        for path in sorted(EXPERIMENT.glob("*.py"))
    }


def run() -> dict[str, Any]:
    started = time.perf_counter()
    contract = load_contract()
    runtime = build_runtime()
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    accepted_results: dict[str, dict[str, Any]] = {}

    for case in cases["accepted"]:
        try:
            result = runtime.query(case["prompt"])
            runtime.verify_result(case["prompt"], result)
            repeated = runtime.query(case["prompt"])
            actual = result["surface"]["value"]
            passed = (
                result["input"]["domain"] == case["domain"]
                and actual == case["expected"]
                and canonical_bytes(result) == canonical_bytes(repeated)
                and result["main"]["factor_energy"]["total_units"] == 0
            )
            accepted_results[case["id"]] = result
            rows.append({
                "id": case["id"],
                "kind": "accepted",
                "domain": case["domain"],
                "equivalence_group": case.get("equivalence_group"),
                "expected": case["expected"],
                "actual": actual,
                "refusal": None,
                "input_fact_hash": hashlib.sha256(canonical_bytes(result["input"]["facts"])).hexdigest(),
                "result_hash": result["result_hash"],
                "passed": passed,
            })
        except LanguageRefusal as exc:
            rows.append({
                "id": case["id"], "kind": "accepted", "domain": case["domain"],
                "expected": case["expected"], "actual": None, "refusal": exc.code.value,
                "passed": False,
            })

    for case in cases["refusals"]:
        try:
            result = runtime.query(case["prompt"])
            rows.append({
                "id": case["id"], "kind": "refusal", "domain": case["domain"],
                "expected_refusal": case["expected_refusal"], "actual": result["surface"]["value"],
                "refusal": None, "passed": False,
            })
        except LanguageRefusal as exc:
            rows.append({
                "id": case["id"], "kind": "refusal", "domain": case["domain"],
                "expected_refusal": case["expected_refusal"], "actual": None,
                "refusal": exc.code.value, "passed": exc.code.value == case["expected_refusal"],
            })

    equivalence_groups: dict[str, list[dict[str, Any]]] = {}
    for case in cases["accepted"]:
        if group := case.get("equivalence_group"):
            equivalence_groups.setdefault(group, []).append(accepted_results.get(case["id"], {}))
    equivalence_checks = {
        group: bool(results) and len(results) == len([
            case for case in cases["accepted"] if case.get("equivalence_group") == group
        ]) and len({canonical_bytes(result["input"]["facts"]) for result in results}) == 1
        and len({canonical_bytes(result["surface"]["value"]) for result in results}) == 1
        for group, results in equivalence_groups.items()
    }

    pronoun_case = next(case for case in cases["accepted"] if case["id"] == "d02-resource-repair-pronouns")
    try:
        settle_input(contract, pronoun_case["prompt"], enable_anaphora=False)
        anaphora_causal = False
    except LanguageRefusal:
        anaphora_causal = True
    runtime_actual = _runtime_hash()
    attempt_001_actual = _attempt_001_hash()
    all_rows = all(row["passed"] for row in rows)
    main_worlds = {
        result["main"]["world_hash"] for result in accepted_results.values()
    }
    causal_checks = {
        "anaphora_required_for_pronoun_panel": anaphora_causal,
        "equivalent_fact_graphs_and_results": all(equivalence_checks.values()),
        "one_main_world_serves_both_domains": len(main_worlds) == 1,
        "zero_unsafe_acceptances": all_rows,
        "runtime_preserved": runtime_actual == RUNTIME_HASH,
        "attempt_001_preserved": attempt_001_actual == ATTEMPT_001_HASH,
    }
    verdict = (
        "COMPOSITIONAL_LANGUAGE_CASCADE_CONFIRMED_WITHIN_FROZEN_BOUNDARY"
        if all_rows and all(causal_checks.values()) else "NO_GO"
    )
    return {
        "schema": "moth-compositional-language-campaign/1.0",
        "attempt": "001",
        "verdict": verdict,
        "base_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
        ).stdout.strip(),
        "contract_hash": contract.contract_hash,
        "contract_fixture_sha256": sha256_file(FIXTURE),
        "cases_fixture_sha256": sha256_file(CASES_PATH),
        "generic_main_world_hash": next(iter(main_worlds)) if len(main_worlds) == 1 else None,
        "metrics": {
            "passed": sum(int(row["passed"]) for row in rows),
            "total": len(rows),
            "accepted": sum(row["kind"] == "accepted" and row["passed"] for row in rows),
            "safe_refusals": sum(row["kind"] == "refusal" and row["passed"] for row in rows),
            "unsafe_acceptances": sum(row["kind"] == "refusal" and row.get("actual") is not None for row in rows),
            "domains": sorted({row["domain"] for row in rows}),
            "equivalence_groups": equivalence_checks,
        },
        "causal_checks": causal_checks,
        "protected": {
            "runtime": {"expected": RUNTIME_HASH, "actual": runtime_actual},
            "attempt_001": {"expected": ATTEMPT_001_HASH, "actual": attempt_001_actual},
        },
        "implementation_manifest": _manifest(),
        "rows_hash": hashlib.sha256(canonical_bytes(rows)).hexdigest(),
        "rows": rows,
        "machine": {"python": platform.python_version(), "platform": platform.platform()},
        "wall_seconds": round(time.perf_counter() - started, 6),
    }


def main() -> int:
    print(json.dumps(run(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
