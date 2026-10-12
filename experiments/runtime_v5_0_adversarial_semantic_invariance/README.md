# Runtime 5.0 adversarial semantic invariance

Status: `ADVERSARIAL_SEMANTIC_INVARIANCE_CONFIRMED`

This disposable experiment tests whether one compiled Runtime 5.0 language
contract preserves meaning across novel recombinations of its admitted
surfaces and frames while distinguishing or refusing nearby semantic changes.

See [SPEC.md](SPEC.md). Run:

```sh
./.venv/bin/python -m experiments.runtime_v5_0_adversarial_semantic_invariance.campaign
./.venv/bin/python -m pytest experiments/runtime_v5_0_adversarial_semantic_invariance/tests -q
```

The campaign creates its SQLite store in a temporary directory. It does not
write to `data/store-5.0.sqlite3` or modify any Runtime 5.0 asset.

The frozen 50-case campaign passed. See
[reports/CONCLUSION-001.md](reports/CONCLUSION-001.md).
