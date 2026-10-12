# Runtime 5.2 energy-native qualification 001

## Verdict

`ENERGY_NATIVE_MUTABLE_RUNTIME_5_2_CONFIRMED`

Runtime 5.2 is an independently selectable Safetensors-native successor to the
Runtime 5.1 conversational behavior. It imports no Runtime 5.1 module, packages
the frozen Runtime 5.0 kernel closure, settles directly over typed arrays, and
stores mutable SYSTEM and persistent CONTEXT state as immutable objects plus
revisioned SQLite head pointers.

## Environment

- Python 3.11.15
- NumPy 2.4.6
- Safetensors 0.8.0
- SQLite 3.50.4 with WAL and `synchronous=FULL`

## Results

| Gate | Result |
|---|---:|
| Clean artifact builds | 3/3 byte-identical |
| Artifact hash | `8652fbbc6842fd3e6781be465055eca8666e4d32a611e97c5513dbfa680ebcf5` |
| Energy logical hash | `3242040be6750822ab4c540bd9a9da2360f3510f14446b1285c78369cfb8568f` |
| Energy file hash | `3ba8d291507614a6359cd8fc577bbb3b6089042997eb86bba2a6342ed2760377` |
| Runtime 5.0 foundation hash | `763371dff4060e4a8eae8259ca515e041b881a734adba38d3da3caa660da9da6` |
| Candidates / fields / skills | 16 / 5 / 10 |
| Runtime 5.1 compiled JSON | 99,406 bytes |
| Runtime 5.2 Safetensors | 72,395 bytes |
| Storage ratio | 72.8276% (maximum 75%) |
| Median 5.1 settlement | 247,791.5 ns |
| Median 5.2 settlement | 205,500 ns |
| Settlement ratio | 82.9326% |
| Incremental peak RSS median, 5.1 | 6,356,992 bytes |
| Incremental peak RSS median, 5.2 | 5,701,632 bytes |
| Qualified surface outputs | 168/168 |
| Inert skill plans | 36/36 |
| Mutable-layer historical replay | passed |
| Safetensors tamper detection | passed |
| Runtime 5.1 imports | 0 |
| Candidate dictionary reconstructions | 0 |
| Tool dispatches / task writes | 0 / 0 |

Memory is measured as peak RSS minus a post-import baseline in five isolated
processes. Absolute medians are also retained in raw campaign output: 42,778,624
bytes for 5.1 and 42,582,016 bytes for 5.2. This separates the fixed native
Safetensors library residency from the compiled load-and-settle working set.

Qualification hash:
`edc14b46260dea57989359d9305af5dd865292fa790ae6b75dea83f2b02e4cf3`.

## Commands and regression state

```sh
.venv/bin/python -B -m pytest tests/test_runtime_v5_0.py -q
.venv/bin/python -B -m pytest tests/test_runtime_v5_1.py tests/test_launcher_v5_1.py -q
.venv/bin/python -B -m pytest tests/test_runtime_v5_2.py tests/test_launcher_v5_2.py -q
.venv/bin/python -B -m pytest tests -q
.venv/bin/python -B -m experiments.runtime_v5_2_energy_native_fields.campaign
```

The protected focused suites passed 21/21 for Runtime 5.0, 22/22 for Runtime
5.1, and 18/18 for Runtime 5.2 after adding the promotion-lock check. The
historical aggregate suite before that final check reported 185
passes and the same five pre-existing failures documented during 5.1: four
legacy tests hard-code the pre-5.1 launcher usage string, and the old Runtime
4.8 architecture-lock mismatch remains. Runtime 5.2 does not modify those
sealed older areas.

The campaign builds its 5.1 comparison artifact from committed sources in a
temporary directory. Qualification does not depend on ignored `runs/` output.
The promoted artifact packages only `moth_runtime_v5_0` and
`moth_runtime_v5_2`; its entrypoint is the version-specific 5.2 CLI. The
installed neutral launcher remains outside that isolated closure so it can
continue selecting preserved runtimes, including 5.1.

## Boundaries

JSON remains in source, manifests, results, traces, diagnostics, and receipts.
All compiled 5.2 fields, candidate/property matrices, BASE and mutable HCF,
activation directives, capabilities, and inert skill policies are Safetensors.
The frozen 5.0 world archives remain JSON by explicit compatibility contract.

No store or artifact migration from 5.1 is provided. Cross-version inputs fail
closed. Multimodal compilers remain future work; the foundation only reserves
modality-neutral identities and payload handles.
