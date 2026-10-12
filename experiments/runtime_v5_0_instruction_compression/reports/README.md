# Reports

- `RESULT-001.json`: compact machine-readable frozen campaign result.
- `CONCLUSION-001.md`: decisive interpretation and supported boundary.

Replay:

```sh
./.venv/bin/python -m experiments.runtime_v5_0_instruction_compression.campaign
./.venv/bin/python -m pytest experiments/runtime_v5_0_instruction_compression/tests -q
```

