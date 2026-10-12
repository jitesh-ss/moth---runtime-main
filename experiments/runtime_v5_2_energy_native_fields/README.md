# Runtime 5.2 energy-native fields

Status: **qualified and promoted**.

This experiment replaces Runtime 5.1 compiled JSON object graphs with canonical
Safetensors objects while preserving its observable HCF, kernel, surface, and
inert-skill behavior. It also makes SYSTEM and persistent CONTEXT attachments
logically mutable through immutable objects and revisioned SQLite snapshots.

Runtime 5.2 is independent of Runtime 5.1. It calls the frozen Runtime 5.0
kernel through `moth_runtime_v5_2.kernel` and packages the complete required
5.0/5.2 closure.

Documents:

- [SPEC.md](SPEC.md) freezes the storage and runtime contract.
- [PLAN.md](PLAN.md) records implementation phases.
- [TASKS.md](TASKS.md) records completion state.
- [reports/QUALIFICATION-001.md](reports/QUALIFICATION-001.md) records the
  passing campaign.

Reproduce:

```sh
.venv/bin/python -B -m experiments.runtime_v5_2_energy_native_fields.campaign
.venv/bin/python -B -m experiments.runtime_v5_2_energy_native_fields.build_artifact /tmp/model-5.2
```

Raw campaign output belongs under `runs/` and is ignored. The compact baseline
and conclusion are committed under `fixtures/` and `reports/`.
