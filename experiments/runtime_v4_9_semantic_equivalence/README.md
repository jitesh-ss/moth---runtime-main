# Runtime 4.9 semantic-equivalence field experiment

Status: **ATTEMPT 001 PASS — bounded semantic equivalence confirmed**

This experiment asks whether a meaning compiled once can act as a canonical
attractor for unseen equivalent language and for differently represented
internal propositions. It is an isolated candidate built beside Runtime 4.9.
It does not edit, import into, migrate, or activate any production runtime or
store.

The frozen claim and gates are in [SPEC.md](SPEC.md). Inputs are under
`fixtures/`, raw disposable output belongs under ignored `runs/`, and compact
evidence belongs under `reports/`.

Attempt 001 settled 26/26 frozen text and internal cases with zero unsafe
collapses. Equivalent text and internal propositions converged to one canonical
meaning and drove the same unmodified Runtime 4.9 downstream factor result.
See [reports/CONCLUSION-001.md](reports/CONCLUSION-001.md).

Run from the repository root:

```sh
.venv/bin/python -m pytest -q experiments/runtime_v4_9_semantic_equivalence/tests
.venv/bin/python -m experiments.runtime_v4_9_semantic_equivalence.campaign
```
