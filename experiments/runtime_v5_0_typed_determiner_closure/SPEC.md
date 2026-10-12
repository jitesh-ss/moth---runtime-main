# Spec: Runtime 5.0 typed-determiner closure

## Objective

Fix the exact grammatical gap found by the sealed compositional-closure
campaign without changing Runtime 5.0 or weakening its safety boundary. Extend
the frozen base field with an optional typed determiner operator for capability
noun phrases, then test old failures as regressions and new complete prompts as
the blind qualification evidence.

## Technology and commands

- Base evidence: immutable `runtime_v5_0_blind_compositional_closure` field and implementation.
- Extension: experiment-local deterministic grammar compiler and instance subclass.
- Runtime kernels: unchanged `moth_runtime_v5_0` Input/Main/Surface.
- Encoder: pinned offline `BAAI/bge-large-en-v1.5`.
- Stores: fresh temporary Runtime 5.0 databases only.
- Run: `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 ./.venv/bin/python -m experiments.runtime_v5_0_typed_determiner_closure.campaign`
- Test: `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 ./.venv/bin/python -m pytest experiments/runtime_v5_0_typed_determiner_closure/tests -q`
- Regression: `./.venv/bin/python -m pytest tests/test_runtime_v5_0.py tests/test_runtime_v5_0_language.py tests/test_launcher_v5.py -q`

## Project structure

- `fixtures/determiner-extension-en-1.0.json`: sealed typed grammar extension.
- `fixtures/blind-campaign-en-1.0.json`: new prompts created only after extension seal.
- `grammar.py`: validates and compiles the extension over the immutable base field.
- `instance.py`: determiner-aware isolated Input settlement.
- `campaign.py`: regression, A/B, closure, contrast, refusal, ablation, and integrity gates.
- `tests/`: grammar and end-to-end qualification tests.
- `reports/`: compact result and conclusion.

## Grammar contract

The only new production-independent rule is:

```text
CAPABILITY_NOUN_PHRASE := DETERMINER? + COMPILED_CAPABILITY_SURFACE
DETERMINER := a | an | the
```

It applies only to roles `RESOURCE`, `PERMISSION`, and `DEADLINE`, permits at
most one prefix, contributes zero semantic meaning, and records the removed
operator in the settlement trace. Existing surfaces that already contain a
determiner remain exact and cannot receive another.

## Code style

```python
candidate = {
    "surface": "the delivery deadline",
    "determiner": "the",
    "meaning": "delivery deadline",
    "role": "DEADLINE",
}
```

No unrestricted stop-word removal is permitted. The rule must resolve exactly
one compiled typed capability or refuse.

## Testing strategy

- Regression: the four immutable failures `e03`, `e04`, `e08`, `e10` from the
  prior campaign must now settle to its baseline graph/output.
- Blind closure: 12 new equivalent prompts, each dependent on the extension,
  must all converge to one baseline graph/output.
- Contrasts: 6 new prompts must produce their specified different outputs and
  six distinct graphs.
- Refusals: 10 new double-determiner, misplaced-determiner, unknown meaning,
  wrong type, modality, time, intent, incomplete, ambiguous, or conflicting
  prompts must refuse.
- Causality: the same 12 blind prompts must fail on the sealed base field, and
  determiner-rule ablation must break its representative case.
- Integrity: all results replay byte-exactly; composition and semantic tampering
  fail; protected hashes remain unchanged.

## Boundaries

- Always: seal extension before new prompts; embed both base and extension
  hashes in the campaign; preserve all thresholds and frozen prior evidence;
  distinguish refusal from understanding.
- Ask first: alter the base field, change thresholds/dependencies, or promote
  behavior into production Runtime 5.0.
- Never: add complete test sentences to the field, learn from blind prompts,
  remove arbitrary words, permit multiple determiners, use network, or edit
  Runtime 5.0/configuration/production stores.

## Success criteria

- Extension compilation is deterministic and unsafe shapes fail atomically.
- Extension is sealed before new prompt creation and no complete test sentence leaks into either field fixture.
- Old failures repair 4/4.
- Base-field control accepts 0/12 new determiner-dependent equivalents.
- Extended field accepts 12/12 and yields exactly one baseline graph/output.
- Contrasts pass 6/6 with six distinct graphs.
- Refusals pass 10/10; unsafe acceptance is zero.
- Determiner ablation breaks the dependent case.
- Nested replay is byte-exact and both tamper checks pass.
- Network/execution/dispatch are zero and protected hashes are unchanged.

## Open questions

None. The user authorized the isolated corrective implementation and test on
2026-09-02.

