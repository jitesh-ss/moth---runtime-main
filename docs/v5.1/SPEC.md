# Runtime 5.1 implementation specification

## Required behavior

- Load and hash-check a `moth-runtime-foundation/5.1` manifest, one or more BASE
  HCF fields, exactly three Runtime 5.0 World archives, encoder identity, context
  limits, and Surface modes.
- Derive one foundation identity from the attached field, entry, World, bundle,
  and encoder hashes; bind it to the store and every turn receipt.
- Reject missing or duplicate fields, altered members, mismatched World roles,
  changed foundation bindings, and any undeclared member such as a weight list.
- Compile bounded system text into immutable SYSTEM entries.
- Persist every system, user, and assistant message in a separate 5.1 store.
- Select response candidates by verified lexicographic HCF energy.
- Execute the preserved three-World kernel exactly once for an accepted turn.
- Archive context, HCF, kernel, response, and result-chain evidence.
- Provide commands and an interactive REPL for operation and inspection.
- Verify `moth-model-artifact/5.1` images, embedded runtime-package closure,
  exact members, foundation, five compiled field kinds, canonical skills, and
  the capability index before opening a store.
- Compile primary and paraphrased skill documents to one semantic policy and
  support only declared L6 composition.
- Bind an artifact, its field hashes, and conversation-fixed skill policy hashes
  into persistence and replay evidence.
- Settle presentation independently of the semantic prompt and verify pure
  Surface realization by exact semantic recovery.
- Produce inert `ACTION_PLAN`, `AUTHORITY_REQUIRED`, or `REFUSAL` receipts from
  embedded task snapshots without performing an action.

## Fixed boundaries

The implementation is console-only, performs no dispatch, uses no network, loads
no weights, provides no World mutation commands, and does not treat operational metrics as
deterministic evidence. Unsupported system text, ambiguous HCF entries, invalid
delegations, ambiguous references, context overflow, or corrupted assets refuse
closed.

## Acceptance

Focused HCF, conversation, persistence, replay, CLI, foundation-integrity, and 5.0
compatibility tests must pass. Runtime 5.0 source and configuration hashes must
remain equal to the frozen baseline.

Artifact qualification additionally requires two byte-identical clean builds,
all retained primary/paraphrased policy pairs, 168 semantic-preserving Surface
outputs, 36 inert operational cases, embedded-package isolation, and tamper
detection. The bounded verdict is
`WEIGHT_FREE_COMPILED_MODEL_ARTIFACT_5_1_CONFIRMED`.
