# Runtime 5.0 Language-Fidelity Specification

## Objective

Runtime 5.0 is an independent, opt-in Runtime 4.9 derivative whose only new
capability is bounded compiled language fidelity in the Input World. Existing
4.9 envelopes remain valid; compiled semantic contracts additionally allow
equivalent phrasing, multi-clause facts, bounded singular pronouns, intent
selection, typed projection, and safe refusal.

The supported claim is **bounded compiled language fidelity over Runtime 4.9**.
This is not unrestricted English understanding or open-world reasoning.

## Technology and commands

- Python 3.11, pytest, SQLite, NumPy, SciPy, Torch, sentence-transformers.
- Focused test: `./.venv/bin/python -m pytest tests/test_runtime_v5_0.py`
- Regression test: `./.venv/bin/python -m pytest`
- CLI: `./.venv/bin/moth --runtime 5.0 <command>`
- Production store: `data/store-5.0.sqlite3`

## Project structure

- `src/moth_runtime_v5_0/`: independent runtime implementation.
- `config/v5.0/`: runtime, World, encoder, grounding, and architecture locks.
- `tests/test_runtime_v5_0.py`: parity, semantic, safety, replay, and integrity tests.
- `docs/v5.0/`: frozen product, architecture, specification, and task records.
- `reports/RUNTIME-5.0-LANGUAGE-FIDELITY-QUALIFICATION-001.md`: qualification evidence.

## Public contracts

- Runtime label: `5.0`
- Store: `proof-energy-world-store/5.0`
- Archive: `proof-energy-world-archive/5.0`
- Bundle: `moth-world-bundle/5.0`
- Handoff: `moth-world-handoff/5.0`
- Result: `moth-world-result/5.0`
- Factor trace: `moth-factor-settlement/5.0`
- Semantic trace: `moth-semantic-settlement/5.0`
- Default store: `data/store-5.0.sqlite3`

Runtime 5.0 never imports Runtime 4.9. Runtime 4.7 remains canonical. There is
no compatibility alias and untagged launcher commands remain invalid.

## Controlled language and data model

Two meaning types are added: `SEMANTIC_CONTRACT` and `SEMANTIC_SURFACE`.
Semantic contracts are declared only in Input Worlds:

```text
Semantic contract "delivery-en" is canonical semantic JSON "{...}".
```

The JSON contract contains a domain, typed entities and roles, aliases and
surfaces, typed predicates, anchored language frames, polarity/modality/time
coordinates, equivalence transformations, singular pronoun policy, intents,
and projection rules into an existing instruction/operation/program/schema.
All named targets must already exist and compilation is atomic. Raw regular
expressions are forbidden. Templates permit literal text plus typed
placeholders such as `{SUBJECT}` and `{OBJECT}`.

Limits: 64 contracts/Input World, 4,096 entities/contract, 32 surfaces/entity,
256 frames/contract, 32 clauses/prompt, 64 candidates/clause, 128 facts/prompt,
128 prompt tokens, and 64 MiB semantic trace.

## Routing and settlement

Pre-World validates UTF-8-normalized text, whitespace, modality, and token
limit only. Input tries every legacy 4.9 instruction/prototype envelope first.
Exactly one match uses the unchanged legacy path at zero semantic cost;
multiple matches refuse; no match invokes semantic settlement.

Semantic settlement selects exactly one compiled domain and intent, segments
explicit clauses, matches anchored frames, resolves exact typed entities before
optional BGE retrieval, resolves singular pronouns only by
`MOST_RECENT_UNAMBIGUOUS`, creates coordinate-preserving canonical facts, and
projects those facts to ID-only Main bindings. Hard type, direction, polarity,
modality, time, quantity, and closed-world constraints dominate vector cost.
Ambiguity refuses and no global search or branching is introduced.

The semantic result records mode, contract/domain/intent IDs, ordered facts,
projected bindings, clause and entity evidence, costs, semantic energy,
semantic graph hash, and semantic trace hash. Raw language never crosses into
Main. Vector evidence includes normalized query vector/hash, ranked candidate
IDs, rounded scores, and costs for encoder-free replay.

New refusal codes are `UNKNOWN_DOMAIN`, `UNKNOWN_ENTITY`,
`UNKNOWN_CAPABILITY`, `AMBIGUOUS_REFERENCE`, `UNSUPPORTED_LANGUAGE`,
`UNSUPPORTED_INTENT`, `INCOMPLETE_FACT_GRAPH`, and `CONFLICTING_FACTS`.

## Code style

Runtime records are immutable dataclasses, identifiers are content-addressed,
canonical JSON is byte-stable, and failures use typed refusals:

```python
raise GroundingFailure(
    RefusalCode.AMBIGUOUS_REFERENCE,
    "singular reference has no unique compatible antecedent",
    {"clause_index": clause_index},
)
```

## Testing strategy

Tests cover 4.9 namespace parity, deterministic compilation/archive, legacy
precedence, equivalence, multi-clause and order invariance, bounded pronouns,
two-domain reuse of one Main program, hard semantic contrasts and refusals,
causal ablations, tampering, exact replay, empty store, and cross-runtime
rejection. Qualification requires zero unsafe acceptances, zero Main factor
violations, zero Surface changes, no execution/network, exact replay, and no
changes to protected Runtime 4.9 or experiment evidence.

## Boundaries

- Always: fail closed, retain provenance, bind semantic hashes through receipts,
  verify archives and results independently, and keep the 5.0 store separate.
- Ask first: add dependencies, migrate stores, change canonical runtime, add a
  model, or broaden beyond compiled contracts.
- Never: import 4.9 or experiment code, accept raw regex, allow prompts to create
  meanings, add execution/search/learning, or modify protected evidence.

## Success criteria

All frozen semantic and legacy parity tests pass; all expected refusals occur;
unsafe acceptances, factor violations, Surface semantic changes, dispatches,
network calls, and protected hash changes are zero; encoder-free replay is
byte-exact. The pre-existing 4.8 architecture-lock mismatch may remain the only
known full-suite failure.

## Open questions

None. The implementation scope and opt-in/empty-store policy were approved by
the user on 2026-09-01.
