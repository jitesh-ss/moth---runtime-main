# Spec: Runtime 5.0 adversarial semantic invariance

## Objective

Test the strongest bounded language-fidelity claim currently supported by
Runtime 5.0: after compiling one language field, compositionally novel uses of
the same meanings settle invariantly, while minimal semantic differences do
not collapse into the baseline meaning.

## Technology and commands

- Runtime under test: production `moth_runtime_v5_0` at the current architecture lock.
- Store: a fresh temporary Runtime 5.0 SQLite store per campaign.
- Encoder: deterministic compilation encoder; queries use exact compiled
  surfaces, so BGE is not loaded and cannot hide language/frame behavior.
- Campaign: `./.venv/bin/python -m experiments.runtime_v5_0_adversarial_semantic_invariance.campaign`
- Tests: `./.venv/bin/python -m pytest experiments/runtime_v5_0_adversarial_semantic_invariance/tests -q`

## Project structure

- `fixtures/campaign-en-1.0.json`: frozen generation matrix and adversarial prompts.
- `campaign.py`: isolated store construction, execution, replay, and verification.
- `tests/`: deterministic campaign regression.
- `reports/`: compact conclusion and result manifest; no raw row stream.

## Campaign

Exactly 50 cases are frozen before execution:

- 20 delivery equivalence cases.
- 20 deployment equivalence cases.
- 3 valid minimal contrasts that must produce a different graph and the
  specified different factor result.
- 7 invalid or ambiguous contrasts that must refuse with the specified code.

The 40 equivalence prompts recombine compiled subject aliases, relation frames,
object aliases, static permission/deadline forms, singular pronouns, intent
surfaces, and clause orders. No generated prompt duplicates the Runtime 5.0
qualification prompts.

## Code style

Cases and results are canonical dictionaries. Assertions fail closed:

```python
if result["status"] != "ANSWER":
    raise CampaignFailure(case_id, "equivalent prompt refused")
```

## Testing strategy

For each equivalence domain, every result must have the expected Surface value,
one shared semantic graph hash, one shared Main World hash, three stages, two
handoffs, zero dispatch, and byte-exact encoder-free replay. Valid contrasts
must answer with a graph different from their domain baseline and the specified
result. Invalid contrasts must refuse with the exact frozen code. One altered
semantic trace must fail verification.

## Boundaries

- Always: use a new temporary store, compile from frozen fixtures, verify every
  result and replay, and compare protected hashes before/after.
- Ask first: modify Runtime 5.0, its configuration, architecture lock, launcher,
  production store, or dependencies.
- Never: accept unknown vocabulary as success, load the network, import an
  earlier runtime for execution, or rewrite a failed case after seeing output.

## Success criteria

- 50/50 cases satisfy their frozen expectations.
- 40/40 equivalent prompts are accepted.
- Exactly one semantic graph exists within each equivalence domain.
- 3/3 valid contrasts change the graph and produce the expected different result.
- 7/7 unsafe/unsupported contrasts refuse with the expected code.
- Unsafe semantic acceptances: zero.
- Main factor violations and Surface semantic changes: zero.
- All 50 archived results replay byte-exactly without an encoder.
- Semantic trace tampering is detected.
- Runtime 5.0 implementation/configuration/lock and production-store hashes do not change.

## Open questions

None. The user explicitly requested this isolated test on 2026-09-02.
