# Runtime 5.1 compiled model artifact qualification 001

Verdict: `WEIGHT_FREE_COMPILED_MODEL_ARTIFACT_5_1_CONFIRMED`

## Qualified image

- Model: `moth-compiled-model/5.1-dev`
- Artifact hash: `bae305a2c7b92459443608730c3788b9123b2767b7fa0defff6ef05b1546a9c5`
- Foundation hash: `81add2e58024f60200abdf1a905ba94ab54178de21612f54ab793e72d857a583`
- Compiled fields: 5
- Canonical compiled skills: 10
- Surface modes: 16
- Weights: 0

Two clean builds produced identical member bytes and the same aggregate hash.
The extracted image loaded its three runtime packages from its embedded
`runtime/` tree and imported no experiment package.

## Fidelity evidence

- Eight primary/paraphrased skill pairs compiled to equal semantic policies.
- Every promoted policy matched the projection produced by its frozen Runtime
  5.0 compiler.
- Ten repeated compilations per pair were byte-identical.
- The instruction-compression expansion ratio was 2.5x.
- The field archive retained L1-L5 inventories for all five families and one
  declared L6 composition for safe patch plus evidence ledger.
- 168/168 Surface outputs recovered the exact settled semantic value.
- All 16 modes were exercised, including natural prose, tone, Markdown, mixed
  explanation/JSON, action plan, strict JSON, inert Python literals, and Python
  function source.
- 36/36 instruction cases produced the frozen-equivalent action-plan,
  authority-required, or refusal status.
- Multi-turn presentation replacement, conversation-fixed skill binding,
  conversation isolation, result chaining, and replay verification passed.

## Safety and integrity evidence

- Network attempts: 0
- External model calls: 0
- Tool dispatches: 0
- Generated Python executions: 0
- Task-workspace writes: 0
- Weight members: 0
- Field, runtime-source, capability-index, and extra-weight tampering: 4/4
  detected

The Python claim is limited to deterministic source realization plus AST and
literal inspection. Runtime 5.1 never executes the produced source. Inert plans
contain proposed bytes and before/after hashes but never apply them.

## Replay

```sh
.venv/bin/python -m pytest \
  experiments/runtime_v5_1_compiled_artifact/tests -q

.venv/bin/python -m experiments.runtime_v5_1_compiled_artifact.campaign
```

This verdict does not claim open-domain language, arbitrary skill
understanding, tool execution, cloud inference, GPU deployment, or production
weights.
