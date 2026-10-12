# Runtime 5.2 autonomous JSON skill experiment

Status: `QUALIFIED EXPERIMENT — PASS`

This isolated experiment ports the bounded, prompt-only autonomous JSON
capability to Runtime 5.2 storage and settlement. It does not modify promoted
Runtime 5.2 code, configuration, or artifacts.

The normative contract is in [SPEC.md](SPEC.md). The experiment reuses the
frozen 5.1 qualification panels as its immutable behavioral oracle and writes
only compact evidence under `reports/`.

Qualification result: 240/240 exact prompt-only JSON outputs, 96/96 typed
refusals, and 64/64 metamorphic checks. See
[`reports/QUALIFICATION-001.md`](reports/QUALIFICATION-001.md).
