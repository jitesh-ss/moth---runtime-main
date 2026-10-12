# Runtime 5.1 HCF experiment

Status: candidate qualification evidence.

This isolated campaign tests three-level lexicographic precedence, typed
delegation, equal authority within a level, exact traces, and resistance to
lower-level numeric inversion.

Run from the repository root:

```sh
./.venv/bin/python -m experiments.runtime_v5_1_hcf.campaign
./.venv/bin/python -m pytest experiments/runtime_v5_1_hcf/tests -q
```

Build a minimal deterministic, weight-free foundation for manual console testing:

```sh
./.venv/bin/python -m experiments.runtime_v5_1_hcf.build_assets /tmp/moth-5.1-foundation
./.venv/bin/moth --runtime 5.1 init --foundation /tmp/moth-5.1-foundation
./.venv/bin/moth --runtime 5.1 inspect foundation
```
