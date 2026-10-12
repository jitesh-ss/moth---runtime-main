# Specification: Runtime 4.9 semantic-equivalence field

## Objective

Test whether a canonical proposition compiled once can be recovered from
previously unseen equivalent English expressions and from alternate internal
relation representations through one proof-carrying semantic settlement
mechanism. Prompt fidelity must be a consequence of internal semantic
canonicalization, not a separate list of domain-specific prompt templates.

The experiment is bounded English semantic interpretation, not unrestricted
language understanding. It must preserve Runtime 4.7, Runtime 4.8, Runtime 4.9,
their configuration, documentation, stores, and public behavior byte-for-byte.

## Technical stack

- Python 3.11 from the existing `.venv`.
- Existing pinned offline BGE-large-en-v1.5 encoder for candidate retrieval.
- Existing Runtime 4.9 canonical hashing utilities, used read-only.
- Experiment-owned immutable semantic model, compiler, settlement, verifier,
  fixtures, tests, and reports.
- No network access, query-time learning, LLM execution, tool dispatch, or
  production-store access.

## Commands

```sh
.venv/bin/python -m pytest -q experiments/runtime_v4_9_semantic_equivalence/tests
.venv/bin/python -m experiments.runtime_v4_9_semantic_equivalence.campaign
.venv/bin/python -m pytest -q tests/test_runtime_v4_9.py tests/test_launcher.py
.venv/bin/python -m pytest -q
```

## Project structure

```text
experiments/runtime_v4_9_semantic_equivalence/
  SPEC.md                 frozen question, boundaries, and gates
  README.md               status and replay commands
  fixtures/               semantic world and held-out cases
  model.py                immutable experiment contracts
  compiler.py             deterministic semantic-world compiler
  settlement.py           text/internal semantic settlement and verification
  reference.py            independent direct semantic reference
  campaign.py             frozen campaign and compact report generation
  tests/                  focused deterministic and real-BGE gates
  runs/                   ignored disposable row streams
  reports/                compact conclusions and manifests
```

## Code style

Use immutable dataclasses, explicit typed refusal boundaries, canonical JSON,
domain-separated hashes, deterministic ordering, and no hidden mutable state.

```python
@dataclass(frozen=True)
class SemanticCoordinate:
    predicate: str
    subject: str
    object: str
    polarity: str
    modality: str
    time: str
```

## Mechanism

The compiler freezes:

1. typed entities and their language surfaces;
2. typed predicates and ordered roles;
3. canonical propositions;
4. reusable language frames independent of domain entities;
5. reusable internal relation transformations.

Text produces transient observations, never persistent meanings. A frame fixes
predicate, role direction, polarity, modality, and time while captured spans
produce typed entity candidate domains. Exact surfaces cost zero. The pinned
encoder may propose additional compiled entities of the required type and
contributes quantized semantic cost.

Settlement enumerates only already compiled canonical proposition rows. Hard
type, role, predicate, polarity, modality, time, and closed-world constraints
dominate semantic cost. It accepts only one uniquely minimal compatible row
with the frozen margin. No compatible row returns `UNSUPPORTED_MEANING`; a tie
or insufficient margin returns `AMBIGUOUS_SEMANTICS`.

Internal observations pass through compiled typed relation transformations and
then the identical canonical-proposition settlement. Text and internal paths
must therefore produce the same result contract and canonical meaning ID.

## Testing strategy

Focused tests must cover:

- unseen positive paraphrases across reusable frames;
- active/passive role reordering;
- exact and encoder-proposed entity surfaces;
- positive/negative polarity contrasts;
- subject/object reversal;
- wrong-entity contrasts;
- asserted/possible modality contrasts;
- current/past temporal contrasts;
- multiple internal relation representations;
- ambiguous entity evidence and unsupported language;
- trace tampering and independent reference verification;
- deterministic compilation and repeated settlement;
- causal ablations of type, polarity, role, and semantic evidence;
- frozen Runtime 4.9 tree preservation;
- existing runtime and launcher regression tests.

Real-BGE cases are frozen before execution. Test expectations come from the
fixture's canonical semantic coordinates, not encoder scores.

## Boundaries

- Always: preserve closed-world meaning IDs, verify every accepted settlement,
  record candidate evidence, refuse ambiguity, keep raw prompts transient, and
  run runtime-preservation checks.
- Ask first: add a dependency or model, modify a promoted runtime/config/store,
  promote the experiment, or broaden the claim beyond the frozen fixtures.
- Never: treat vector similarity as truth, generate a persistent meaning from a
  prompt, execute or dispatch output, access the network, hide a domain solver,
  or alter an existing production store.

## Success criteria

The verdict is `SEMANTIC_EQUIVALENCE_CONFIRMED_WITHIN_FROZEN_LANGUAGE_FIELD`
only if all conditions hold:

1. Every positive text case settles to its expected compiled meaning.
2. Every alternate internal representation settles to the same expected ID.
3. Every contrast settles to its distinct expected ID or safely refuses.
4. No unsafe semantic collapse occurs.
5. Ambiguous and unsupported inputs refuse with the expected stable code.
6. Independent reference checks agree with every accepted result.
7. Altered trace evidence is rejected.
8. Deterministic replay is byte-identical.
9. Required causal ablations fail the relevant positive gate.
10. Protected runtime tree hash remains
    `3ddad5a0f486179c3a9d56665bdbd1aeb1f770a660bcaf7828a490c7746beccb`.
11. Existing focused Runtime 4.9 and launcher tests pass.

Any unsafe collapse, integrity failure, protected change, or expectation edit
after observing results is a `NO_GO`. A pass establishes only a reusable
bounded semantic-equivalence field. It does not establish unrestricted English
understanding or promote a new runtime.

## Frozen assumptions

- A pretrained language prior is permitted for candidate retrieval.
- Generic English frames may be compiled once and reused across domain facts.
- Domain meanings are compiled once each; per-case paraphrase lists are banned.
- Internal equivalence is part of the primary claim, not an optional extension.
