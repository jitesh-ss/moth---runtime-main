# Compiled Surface-skill reports

Attempt 001 is frozen as
`BOUNDED_COMPILED_NATURAL_SURFACE_CONFIRMED`.

Replay from the repository root:

```sh
./.venv/bin/python -m experiments.runtime_v5_0_compiled_surface_skill.campaign
./.venv/bin/python -m pytest experiments/runtime_v5_0_compiled_surface_skill/tests -q
./.venv/bin/python -m pytest tests/test_runtime_v5_0.py tests/test_runtime_v5_0_language.py tests/test_launcher_v5.py -q
```

See [`RESULT-001.json`](RESULT-001.json) for machine-readable evidence and
[`CONCLUSION-001.md`](CONCLUSION-001.md) for the exact supported boundary.

