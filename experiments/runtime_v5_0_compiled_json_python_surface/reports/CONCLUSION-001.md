# Runtime 5.0 compiled JSON/Python Surface conclusion 001

## Decisive verdict

`BOUNDED_COMPILED_JSON_PYTHON_SURFACE_CONFIRMED`

One ordinary structured-output skill compiled into an executable Surface policy
that rendered unchanged Runtime 5.0 decisions as exact JSON and safe inert
Python. Every artifact parsed back to the original semantic value, and no
generated Python was executed.

This confirms structured/code realization for the frozen plan-decision schema.
It does not establish general Python programming, arbitrary schema generation,
or safe execution of generated programs.

## Skill compilation

The 14-clause skill and an independently worded paraphrase compiled to one
49-unit policy, a 3.5x instruction expansion. Both matched the pre-authored
granular oracle exactly:

```text
policy  50a2fc83c6c77d7925745ca801940756f40db3d06b36635c1e9f7255f1481ac7
field   06ca9105b8f204c865371c7c8929564ecc2a6f0642d81a2229b576b80bf2da56
```

Compilation repeated deterministically 10/10 times. Removing the Python safety
clause failed with `INCOMPLETE_SKILL`; execution and field-self-modification
instructions failed with `UNSUPPORTED_INSTRUCTION`.

## Artifact results

Eight accepted semantic cases ran under the default route and four explicit
format/layout requests.

| Gate | Result |
| --- | ---: |
| Total artifacts | 40/40 |
| JSON artifacts | 24/24 |
| Python artifacts | 16/16 |
| Parsed exact value | 40/40 |
| Runtime byte parity | 40/40 |
| Archive replay | 40/40 |
| Semantic drift | 0 |
| Schema violations | 0 |
| Layout violations | 0 |
| Unsafe Python | 0 |
| Python executions | 0 |

Default output was compact JSON. Observed byte ranges were:

| Format/layout | Bytes |
| --- | ---: |
| JSON compact | 98–103 |
| JSON readable | 115–120 |
| Python compact | 116–121 |
| Python readable | 135–140 |

Representative compact JSON:

```json
{"backup-valid":"true","failure-reason":"RESOURCE","proposed-valid":"false","selected-plan":"BACKUP"}
```

Representative readable Python:

```python
decision = {
    "backup-valid": "true",
    "failure-reason": "RESOURCE",
    "proposed-valid": "false",
    "selected-plan": "BACKUP",
}
```

JSON was verified with `json.loads`. Python was verified with `ast.parse`, a
one-assignment AST allowlist, and `ast.literal_eval`. Imports, calls,
attributes, control flow, and executable behavior were outside the accepted AST
subset.

The two equivalent Input prompts converged to one Runtime semantic graph. Both
frozen Runtime refusals remained byte-identical to the control and were never
serialized as successful artifacts. An unknown JavaScript request and a
malformed semantic result both refused.

## Causality, tampering, and isolation

Removing the format router, JSON serializer, Python serializer, exact-value
verifier, safe-AST verifier, or semantic hash binder independently caused the
policy to fail closed.

The campaign detected changes to JSON values, Python AST shape, layout,
Runtime semantics, declared format, and the archive envelope. Several probes
recomputed the affected outer hash, so detection depended on semantic and
structural reconstruction rather than the envelope alone.

Control and candidate ran in distinct temporary Runtime 5.0 stores, both
removed after the campaign. Production-store accesses, network calls,
dispatches, and Python executions were zero. Runtime 5.0 source,
configuration, launcher, documentation, prior language/instruction evidence,
the natural-Surface experiment, and the production store remained unchanged.

## Exact supported boundary

The evidence supports:

> Within a frozen semantic schema and compiled presentation language, an
> ordinary skill can make a separate Runtime 5.0 Surface emit deterministic,
> exact JSON and safe data-only Python in compact and readable layouts.

The evidence does not support:

> The skill can write arbitrary Python programs, invent schemas, generate
> algorithms, use imports or calls safely, or execute its output.

Those require separate experiments with typed program semantics and stronger
static or execution isolation. The present candidate remains an
experiment-local overlay and is not promoted.

