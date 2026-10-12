# Runtime 5.1 compiled model artifact

Status: qualified. Verdict:
`WEIGHT_FREE_COMPILED_MODEL_ARTIFACT_5_1_CONFIRMED`.

This experiment integrates the qualified Runtime 5.0 language, Surface, and
instruction-compression fields with Runtime 5.1 conversations and HCF. It
builds a self-contained, deterministic directory image with no weights and no
execution authority.

The frozen requirements and gates are in [SPEC.md](SPEC.md). Build with:

```sh
.venv/bin/python -m experiments.runtime_v5_1_compiled_artifact.build_artifact \
  experiments/runtime_v5_1_compiled_artifact/runs/moth-model-5.1
```

The compact retained evidence is in
[reports/QUALIFICATION-001.md](reports/QUALIFICATION-001.md).
