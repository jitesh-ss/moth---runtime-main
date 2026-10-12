# Spec: Runtime 5.0 compiled JSON/Python Surface skill

## Objective

Decisively test whether one ordinary output-format skill can compile into an
executable Surface policy that serializes verified Runtime 5.0 plan decisions
as either JSON or Python while preserving the exact semantic value.

JSON must be parsed with the standard JSON parser and equal the Runtime value.
Python must parse with `ast`, consist only of one assignment to `decision`, and
have a right-hand side accepted by `ast.literal_eval` that equals the Runtime
value. Python is never executed.

The skill also controls layout as a Surface-size concern: compact artifacts use
one line and readable artifacts use deterministic multiline indentation. The
bounded claim covers the frozen four-field plan-decision schema. It does not
claim arbitrary JSON-schema generation, general Python coding, or safe
execution of generated programs.

## Technology and commands

- Python 3.11 standard library plus the existing Runtime 5.0 package.
- Compile candidate:
  `./.venv/bin/python -m experiments.runtime_v5_0_compiled_json_python_surface.campaign --compile-only`
- Focused tests:
  `./.venv/bin/python -m pytest experiments/runtime_v5_0_compiled_json_python_surface/tests -q`
- Frozen campaign:
  `./.venv/bin/python -m experiments.runtime_v5_0_compiled_json_python_surface.campaign`
- Runtime regression:
  `./.venv/bin/python -m pytest tests/test_runtime_v5_0.py tests/test_runtime_v5_0_language.py tests/test_launcher_v5.py -q`
- No network, model inference, generated-code execution, dispatch, or
  production-store access.

## Project structure

- `fixtures/structured-output/SKILL.md`: primary ordinary output skill.
- `fixtures/structured-output-paraphrase/SKILL.md`: equivalent wording control.
- `fixtures/structured-surface-field-en-1.0.json`: reusable instruction field.
- `fixtures/granular-structured-oracle-1.0.json`: pre-authored policy oracle.
- `fixtures/campaign-en-1.0.json`: format/layout requests and semantic panel.
- `fixtures/FREEZE.json`: pre-execution fixture and protected-path commitments.
- `model.py`: canonical artifact records and typed failures.
- `serializer.py`: policy executor plus independent JSON/Python verification.
- `instance.py`: disposable Runtime 5.0 instance and replay boundary.
- `campaign.py`: compilation, format, fidelity, safety, causal, replay, and
  isolation gates.
- `tests/`: focused deterministic verification.
- `runs/`: ignored raw output.
- `reports/`: compact result and decisive conclusion.

## Code style

Use canonical records, standard parsers, typed failures, and no execution:

```python
tree = ast.parse(source, mode="exec")
value = ast.literal_eval(tree.body[0].value)
if value != runtime_value:
    raise ArtifactFidelityFailure("SEMANTIC_DRIFT")
```

Skill documents and format requests are inert input. Format selection cannot
grant imports, calls, attributes, control flow, execution, or external writes.

## Testing strategy

Freeze the field, primary/paraphrased skills, granular oracle, complete
campaign, and protected paths before execution. Both skill wordings must
compile to one canonical policy equal to the oracle.

Run eight accepted Runtime 5.0 semantic cases under five requests:

- default output, which must be compact JSON;
- explicit compact JSON;
- readable JSON;
- compact Python;
- readable Python.

Hard gates:

- candidate Runtime results remain byte-identical to a separate unchanged
  Runtime 5.0 control;
- every JSON artifact parses and equals the exact Runtime value;
- every Python artifact parses, contains one safe literal assignment, and
  yields the exact Runtime value through `ast.literal_eval`;
- no key, value, type, or decision changes; no extra field is introduced;
- compact outputs are exactly one line and readable outputs have deterministic
  multiline layouts;
- output bytes, semantic result, compiled policy, format, and layout are
  content-addressed and replay exactly;
- malformed results and unsupported requests fail closed;
- Runtime refusals remain byte-identical and are never serialized as answers.

Causal ablations remove the format router, JSON serializer, Python serializer,
schema/value verifier, safe-AST verifier, and hash binder independently. Each
must break or reject its dependent case. Tamper probes alter JSON values,
Python AST shape, layout, semantic bindings, and archive bytes.

## Boundaries

- Always: compile skill text as inert source; use independent temporary stores;
  parse every artifact; compare recovered values exactly; inspect Python AST;
  preserve refusal and Runtime bytes; verify protected hashes before and after.
- Ask first: change frozen fixtures after execution, add dependencies, change
  the supported Python subset, modify/promote a runtime, or execute generated code.
- Never: use `eval`, `exec`, subprocess execution, imports from generated code,
  the network, production stores, or an approximate textual fidelity score.

## Success criteria

- Primary and paraphrased skills compile identically and match the granular oracle.
- All 40 accepted format/layout cases parse and recover the exact Runtime value.
- JSON canonical/readable and Python compact/readable layout gates all pass.
- Python safe-subset violations and every semantic/layout tamper are detected.
- Runtime output parity and archive replay are 40/40; semantic drift is zero.
- Both expected refusals remain byte-identical and un-realized.
- All compiler, malformed-input, causal-ablation, determinism, isolation, and
  protected-hash gates pass with zero execution, dispatch, and external writes.
- Any failed hard gate yields a no-go or partial verdict.

## Open questions

None for this bounded experiment. The user authorized the same isolated test
pattern for JSON and Python on 2026-09-02.

