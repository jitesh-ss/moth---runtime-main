"""Deterministic HCF qualification campaign."""

from __future__ import annotations

import json

from moth_runtime_v5_0.canonical import canonical_bytes, digest
from moth_runtime_v5_1.hcf import (
    HcfEffect, HcfFailure, HierarchyLevel, make_entry, settle_candidates,
    validate_entries, verify_trace,
)


def entry(level, effect, value=None, target=None, redelegable=False, suffix=""):
    return make_entry(
        meaning_id=f"campaign.{level.value.lower()}.{effect.value.lower()}.{suffix or value or target.value}",
        level=level, effect=effect, scope="response.mode", value=value,
        target_level=target, redelegable=redelegable, source_hash="1" * 64,
    )


def candidate(mode, cost=0):
    return {
        "candidate_id": mode, "semantic": {"mode": mode},
        "properties": {"response.mode": mode}, "grounding_cost_units": cost,
    }


def expected_failure(candidates, entries, code, winner=None):
    try:
        settle_candidates(candidates, entries)
    except HcfFailure as exc:
        if exc.code != code:
            raise AssertionError(f"expected {code}, observed {exc.code}") from exc
        if winner is not None and exc.context["trace"]["winner_id"] != winner:
            raise AssertionError("hierarchy selected the wrong minimum")
        return
    raise AssertionError(f"expected {code}")


def run_campaign():
    modes = [candidate("concise", 999_999), candidate("detailed", 0)]
    expected_failure(modes, (
        entry(HierarchyLevel.BASE, HcfEffect.REQUIRE, "concise"),
        entry(HierarchyLevel.CONTEXT, HcfEffect.REQUIRE, "detailed"),
    ), "HCF_CONFLICT", "concise")
    expected_failure(modes, (
        entry(HierarchyLevel.SYSTEM, HcfEffect.REQUIRE, "concise"),
        entry(HierarchyLevel.CONTEXT, HcfEffect.REQUIRE, "detailed"),
    ), "HCF_CONFLICT", "concise")

    direct = (
        entry(HierarchyLevel.BASE, HcfEffect.REQUIRE, "concise"),
        entry(HierarchyLevel.BASE, HcfEffect.DELEGATE,
              target=HierarchyLevel.CONTEXT, suffix="direct"),
        entry(HierarchyLevel.CONTEXT, HcfEffect.REQUIRE, "detailed"),
    )
    winner, trace = settle_candidates(modes, direct)
    if winner["candidate_id"] != "detailed":
        raise AssertionError("direct delegation failed")
    verify_trace(modes, direct, trace)

    chain = (
        entry(HierarchyLevel.BASE, HcfEffect.REQUIRE, "concise"),
        entry(HierarchyLevel.BASE, HcfEffect.DELEGATE,
              target=HierarchyLevel.SYSTEM, redelegable=True, suffix="first"),
        entry(HierarchyLevel.SYSTEM, HcfEffect.DELEGATE,
              target=HierarchyLevel.CONTEXT, suffix="second"),
        entry(HierarchyLevel.CONTEXT, HcfEffect.REQUIRE, "detailed"),
    )
    winner, chain_trace = settle_candidates(modes, chain)
    if winner["candidate_id"] != "detailed":
        raise AssertionError("redelegation chain failed")
    verify_trace(modes, chain, chain_trace)

    try:
        validate_entries((
            entry(HierarchyLevel.SYSTEM, HcfEffect.REQUIRE, "concise"),
            entry(HierarchyLevel.SYSTEM, HcfEffect.REQUIRE, "detailed"),
        ))
    except HcfFailure as exc:
        if exc.code != "AMBIGUOUS_HCF":
            raise
    else:
        raise AssertionError("same-level conflict was accepted")
    expected_failure(
        [candidate("concise"), candidate("detailed")], (), "AMBIGUOUS_HCF",
    )
    result = {
        "schema": "moth-hcf-campaign-result/1.0", "runtime": "5.1",
        "case_count": 6, "passed": 6, "failed": 0,
        "hierarchy": ["BASE", "SYSTEM", "CONTEXT", "GROUNDING"],
        "direct_trace_hash": trace["trace_hash"],
        "chain_trace_hash": chain_trace["trace_hash"],
        "verdict": "THREE_LEVEL_HCF_SETTLEMENT_CONFIRMED",
    }
    result["result_hash"] = digest("moth-hcf-campaign-result/1.0", result)
    return result


def main():
    print(canonical_bytes(run_campaign()).decode("utf-8"))


if __name__ == "__main__":
    main()
