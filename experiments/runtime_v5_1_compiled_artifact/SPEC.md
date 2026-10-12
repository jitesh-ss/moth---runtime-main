# Runtime 5.1 compiled artifact specification

## Question

Can the qualified Runtime 5.0 compiled fields be packaged with Runtime 5.1 as
a deterministic, independently verifiable, weight-free model artifact that
preserves kernel semantics, supports HCF conversations, realizes verified
Surface formats, and produces only inert operational plans?

## Frozen boundaries

- Artifact schema: `moth-model-artifact/5.1`.
- Authority: `BASE > SYSTEM > CONTEXT`.
- Field hierarchy: L1 through L5, with bounded optional L6 composition.
- Three Worlds: Input, Main, and Surface.
- No weights, network, external model, tool dispatch, generated-code
  execution, task-workspace writes, or World mutation.
- Test panels and oracles remain outside the artifact.

## Hard gates

1. Two clean builds have identical member bytes and aggregate hashes.
2. All five field kinds and ten canonical policies verify.
3. Primary/paraphrased skills produce equal semantic policies.
4. Frozen Runtime 5.0 kernel meanings remain unchanged.
5. The 168-case Surface panel preserves semantic values.
6. The 36 inert-plan cases match frozen statuses without writes.
7. Conversation HCF, context isolation, replay, and tamper detection pass.
8. The extracted image imports only its embedded runtime packages.

The only successful bounded verdict is
`WEIGHT_FREE_COMPILED_MODEL_ARTIFACT_5_1_CONFIRMED`.
