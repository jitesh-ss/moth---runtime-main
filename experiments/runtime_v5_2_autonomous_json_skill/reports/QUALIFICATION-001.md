# Runtime 5.2 autonomous JSON skill — qualification 001

Verdict: `PASS`

Qualified claim: `SAFETENSORS_AUTONOMOUS_JSON_PARITY_CONFIRMED`

## Result

One generic JSON field and one detailed Markdown skill were compiled into
verified Runtime 5.2 Safetensors objects. A two-candidate Safetensors energy
foundation and transient Safetensors HCF field routed every accepted request
through direct typed-array lexicographic settlement.

- Prompt-only positive outputs: **240/240 exact**.
- JSON families: **16/16**, with 15 data variations per family.
- Typed negative refusals: **96/96**.
- Metamorphic invariants: **64/64**.
- Deterministic builds: **3/3 byte-identical**.
- Winning energy: **`(0, 0, 0, 0)`** for every accepted request.
- Network, tool dispatch, generated-code execution, and turn writes: **0**.
- Promoted Runtime 5.2 files changed by the candidate: **0**.

The complete 240 prompt/output pairs are preserved in
[`VARIATIONS-001.json`](VARIATIONS-001.json). Machine-readable counts and
object hashes are in [`RESULT-001.json`](RESULT-001.json).

## Compiled object identities

```text
field      32cd31b5b8c60507b3b7b186bed198f5c962c26e33019a031706c0ab67073f48
skill      76dd760f5e60132f2592aaa085187759ecc33fa3fc6ab762a9e45c0cd54156d8
foundation be3eba9170026fe87ce590ef75c83710f362287d48c17696da83de8267bca329
report     4b42c3a6362e4bb4c996cb6222b2af0975f864ed2e840cddb923f2de58cd8e39
```

## Variations confirmed

1. Flat field selection.
2. Nested objects.
3. Scalar arrays.
4. Heterogeneous arrays.
5. Homogeneous record projections.
6. Identifier-keyed maps.
7. Result envelopes.
8. Paginated envelopes.
9. Success/error unions.
10. Nullable and sparse records.
11. Projection and key renaming.
12. Grouped record collections.
13. Canonical key ordering.
14. Source-order preservation.
15. Compact single-line JSON.
16. Pretty two- and four-space JSON.

Inputs covered Unicode, emoji, escaped quotes, backslashes, embedded newlines,
repeated spaces, integers, decimals, booleans, nulls, empty containers, and
nested mixtures.

## Boundary

This demonstrates that the missing behavior can be implemented cleanly on the
5.2 Safetensors and tensor-settlement architecture. It remains an isolated
candidate. It is not yet reachable through the promoted `Runtime52.turn()`
entrypoint and has not changed the promoted artifact.

## Replay

```sh
.venv/bin/python -m pytest experiments/runtime_v5_2_autonomous_json_skill/tests
.venv/bin/python -m experiments.runtime_v5_2_autonomous_json_skill.campaign
```
