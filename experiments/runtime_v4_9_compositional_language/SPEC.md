# Specification: Runtime 4.9 compositional-language cascade

## Objective

Compile a generic two-candidate decision program once, then interpret unseen
multi-clause English from two different domains into the same typed six-fact
decision graph and requested intent. Equivalent prompts must produce the same
verified Main result. Negation, candidate identity, ambiguity, missing facts,
conflicts, and unsupported intent must remain distinct or refuse safely.

This is a separate experiment. It must not change Runtime 4.7, 4.8, 4.9,
Attempt 001, their stores, or public launchers.

## Technical stack

- Python 3.11 and existing dependencies only.
- Experiment-owned compiled domain/language contract and semantic Input stage.
- Typed content-addressed Input-to-Main handoff.
- Disposable in-memory Main World compiled and settled by the unmodified
  Runtime 4.9 compiler, factor kernel, and verifier.
- Experiment-owned deterministic semantic-preserving Surface stage.
- No network, model download, execution, dispatch, or persistent store.

## Commands

```sh
.venv/bin/python -m pytest -q experiments/runtime_v4_9_compositional_language/tests
.venv/bin/python -m experiments.runtime_v4_9_compositional_language.campaign
.venv/bin/python -m pytest -q experiments/runtime_v4_9_semantic_equivalence/tests
.venv/bin/python -m pytest -q tests/test_runtime_v4_9.py tests/test_launcher.py
.venv/bin/python -m pytest -q
```

## Structure

```text
experiments/runtime_v4_9_compositional_language/
  SPEC.md
  README.md
  fixtures/domain-contracts-en-1.0.json
  fixtures/cases-en-1.0.json
  model.py
  compiler.py
  input_world.py
  main_world.py
  runtime.py
  campaign.py
  tests/
  runs/
  reports/
```

## Code style

Immutable dataclasses, deterministic ordering, canonical JSON, domain-separated
hashes, explicit refusal codes, typed facts, and no mutable global state.

```python
@dataclass(frozen=True)
class DecisionFact:
    candidate: str
    requirement: str
    satisfied: bool
```

## Compiled contract

The compiler freezes two domains (`delivery` and `deployment`), two candidate
roles (`PROPOSED`, `BACKUP`), and three generic requirements (`RESOURCE`,
`PERMISSION`, `DEADLINE`). Domain entities and capabilities map into those
generic coordinates. The reasoning program is domain-independent.

Reusable language laws cover possession/lack, capability unavailability,
authorization, deadline feasibility, explicit entity aliases, and singular
anaphora to the most recent unambiguous agent. Intent laws cover validation plus
selection/repair. Prompt-specific sentence templates are forbidden.

## Settlement and cascade

Input normalizes and segments the prompt, resolves the domain, extracts typed
facts, resolves permitted anaphora, and settles exactly one intent. It must
produce exactly one truth value for all six candidate/requirement coordinates.
Missing or conflicting coordinates refuse.

Input emits a content-addressed typed handoff containing only the domain ID,
intent, and six canonical facts. Main converts those facts into bindings for a
single generic compiled factor program. Runtime 4.9 settles proposed validity,
backup validity, selected plan, and deterministic failure diagnosis. Surface
copies the verified semantic result into a stable response without changing it.

## Testing strategy

- Baseline and unseen paraphrases in delivery.
- The same generic reasoning program in deployment.
- Reordered facts and singular pronouns.
- Resource, permission, and deadline failures.
- Proposed-valid, backup-repair, and no-valid-plan outcomes.
- Negation and candidate-identity contrasts.
- Ambiguous pronoun, missing fact, conflicting fact, unknown entity, and
  unsupported-intent refusals.
- Handoff and result tampering rejection.
- Clause-order invariance and byte-exact repeated replay.
- Causal removal of anaphora, intent, and one fact family.
- Protected Runtime and Attempt 001 hashes.

## Boundaries

- Always: accept only compiled domains/entities/capabilities; retain complete
  Input evidence; verify Main factor evidence; refuse incomplete or ambiguous
  graphs; preserve protected hashes.
- Ask first: add dependencies/models, edit promoted runtime files, widen the
  claim, or promote the candidate.
- Never: use expected answers during settlement, synthesize missing facts,
  choose an ambiguous referent, mutate a production store, execute output, or
  describe this bounded grammar as unrestricted language understanding.

## Success criteria

Attempt 001 of this experiment receives
`COMPOSITIONAL_LANGUAGE_CASCADE_CONFIRMED_WITHIN_FROZEN_BOUNDARY` only when:

1. Every frozen accepted prompt produces its expected fact graph and result.
2. Equivalent and reordered prompts have identical semantic outputs.
3. Both domains use a byte-identical Main program.
4. Every frozen refusal returns its expected code.
5. No unsafe accepted interpretation occurs.
6. Main settlements verify under unmodified Runtime 4.9.
7. Tampered handoffs/results fail integrity checks.
8. Repeated runs are byte-identical except timing.
9. Required causal ablations break their target cases.
10. Protected runtime hash remains
   `3ddad5a0f486179c3a9d56665bdbd1aeb1f770a660bcaf7828a490c7746beccb`.
11. Attempt 001 experiment hash remains
   `e1b92641fc6dddc642977e32b4278f19d3da986083647ee6ec911ba3930404a3`.

Any unsafe acceptance, post-result fixture change, protected change, or hidden
domain-specific reasoning path is a `NO_GO`.

## Claim boundary

A pass establishes multi-clause typed composition, bounded anaphora, intent
selection, and end-to-end factor reasoning for the frozen language laws. It
does not establish arbitrary syntax, general coreference, quantifiers, implicit
world knowledge, open-domain facts, or unrestricted conversational fidelity.
