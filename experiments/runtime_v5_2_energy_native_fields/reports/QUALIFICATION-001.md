# Qualification 001

Verdict: `ENERGY_NATIVE_MUTABLE_RUNTIME_5_2_CONFIRMED`.

The canonical compact report is
[`reports/RUNTIME-5.2-ENERGY-NATIVE-QUALIFICATION-001.md`](../../../reports/RUNTIME-5.2-ENERGY-NATIVE-QUALIFICATION-001.md).

Reproduce with:

```sh
.venv/bin/python -B -m experiments.runtime_v5_2_energy_native_fields.campaign
```

It passed three-build byte determinism, 72.8276% compiled storage, faster
median settlement, lower incremental peak RSS, 168 surface outputs, 36 inert
plans, mutable revision replay, Runtime 5.1 independence, and tamper rejection.
