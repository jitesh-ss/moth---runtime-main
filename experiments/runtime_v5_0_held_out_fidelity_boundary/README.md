# Runtime 5.0 held-out fidelity boundary

Status: `HELD_OUT_FIDELITY_BOUNDARY_CONFIRMED`

This final disposable campaign measures Runtime 5.0 against genuinely unlisted
language using the pinned real offline BGE encoder. It distinguishes correct
generalization from safe refusal and unsafe semantic collapse.

See [SPEC.md](SPEC.md) and
[reports/CONCLUSION-001.md](reports/CONCLUSION-001.md). Run:

```sh
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  ./.venv/bin/python -m experiments.runtime_v5_0_held_out_fidelity_boundary.campaign
```

The campaign uses a temporary independent store and does not alter Runtime 5.0
or `data/store-5.0.sqlite3`.
