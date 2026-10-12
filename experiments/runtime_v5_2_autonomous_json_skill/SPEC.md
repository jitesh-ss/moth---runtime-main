# Spec: Runtime 5.2 autonomous JSON skill experiment

## Objective

Determine whether one generic JSON field and one detailed skill can be
compiled into Runtime 5.2 Safetensors objects and, from a prompt alone, emit
the same bounded JSON variations as the qualified Runtime 5.1 experiment.

## Tech stack

Python 3.11, NumPy, Safetensors 0.8.0, Runtime 5.2 tensor compilers and direct
lexicographic energy settlement. SQLite is not needed for this stateless
qualification probe; temporary content-addressed object stores hold compiled
objects.

## Commands

```sh
.venv/bin/python -m pytest experiments/runtime_v5_2_autonomous_json_skill/tests
.venv/bin/python -m experiments.runtime_v5_2_autonomous_json_skill.campaign
```

## Project structure

- `compiler.py`: compiles and reopens field, skill, foundation, and HCF objects.
- `operations.py`: bounded prompt parser and JSON transformation interpreter.
- `campaign.py`: parity, refusal, metamorphic, integrity, and determinism gates.
- `tests/`: focused regression tests.
- `reports/`: compact qualification evidence.

The frozen panels and human-authored field/skill sources are reused from
`experiments/runtime_v5_1_autonomous_json_skill/fixtures/` and hash-bound by
the report.

## Code style

```python
result = settle_json_prompt(candidate, prompt)
assert result["status"] in {"ANSWER", "REFUSAL"}
```

Use deterministic functions, typed dataclasses, explicit failure codes, and
canonical hashes. No callbacks or executable serialization are permitted.

## Testing strategy

- 240 prompt-only positive cases across 16 JSON families.
- 96 typed negative refusals.
- 64 metamorphic relations.
- Repeated byte-identical Safetensors compilation.
- Corrupt/missing-skill causal controls.
- Direct Runtime 5.2 tensor settlement with zero dictionary reconstruction.

## Boundaries

- Always: keep compiled content in Safetensors and parse emitted JSON back.
- Ask first: promotion or edits to `src/moth_runtime_v5_2` and `config/v5.2`.
- Never: use Runtime 5.1 runtime code, embed expected documents, execute tools,
  access the network, or modify the promoted 5.2 artifact.

## Success criteria

- 240/240 exact semantic, shape, and byte results.
- 96/96 expected refusals and 64/64 metamorphic invariants.
- One compiled field and one compiled skill for every positive case.
- Compiled field, skill, candidate matrix, BASE rules, and transient HCF are
  verified Safetensors objects.
- Every accepted request settles at energy `(0, 0, 0, 0)`.
- No `moth_runtime_v5_1` import and no promoted-runtime mutation.

## Open questions

None for the isolated qualification. Promotion remains a separate decision.

