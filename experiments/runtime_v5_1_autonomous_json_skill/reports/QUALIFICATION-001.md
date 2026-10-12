# Runtime 5.1 autonomous JSON skill — qualification 001

Verdict: `PASS`

Qualified claim: `ONE_COMPILED_JSON_SKILL_AUTONOMOUS_VARIETY_CONFIRMED`

## Result

One detailed 14-clause Markdown skill compiled into a 50-unit canonical policy.
The same compilation was then used for every natural prompt. No scored turn was
given a skill id, presentation mode, schema id, template id, task snapshot,
retry, or correction.

- Positive JSON outputs: **240/240** exact semantic values.
- Requested structures: **240/240** exact.
- Emitted bytes: **240/240** exact.
- Explicit layout cases: **60/60** exact.
- Autonomous skill routes: **240/240**.
- Expected policy attribution: **240/240**.
- Typed negative refusals: **96/96**.
- Metamorphic invariants: **64/64**.
- Causal controls: **8/8**.
- Compilation rebuilds: **10/10 byte-identical**.
- Repeated qualification digests: **10/10 identical** over five runs each with
  `PYTHONHASHSEED=1` and `PYTHONHASHSEED=777`.
- Existing Runtime 5.1 preservation tests: **30 passed**.
- Network, tool dispatch, generated-code execution, and writes: **0**.

Candidate identities:

```text
base artifact     bae305a2c7b92459443608730c3788b9123b2767b7fa0defff6ef05b1546a9c5
candidate artifact f2cc39fc6b5f5cd9124f2e9513c8b457a582765899a253e750a2f2784469040f
field              16d5650d2aa70666e636340fab3e68035ca2b49e7b2730764eb4363d975939a2
skill compilation  b1cb136ca50233a5450d29fbcfc22e7805b8074bb057210e6b5c7190e57bca0c
skill policy       18ee133863026ea671dea0af2707eba57af887085b93e575a9d7803bd8ac6b2c
report             9372655c6b23fed5e0662bce083f9294ba703b158089031ce5bdae8417dde60e
```

## JSON variations exercised

Each family contains 15 distinct data cases, for 240 total emitted documents.
The complete prompt, route, output, parsed value, and result hash for every case
is preserved in `VARIATIONS-001.json`.

| Family | Cases | Behavior |
| --- | ---: | --- |
| Flat selection | 15 | Select named object fields without inventing values |
| Nested object | 15 | Wrap data beneath paths of depth two through four |
| Scalar array | 15 | Project one field from records into a scalar array |
| Heterogeneous array | 15 | Preserve mixed strings, numbers, booleans, nulls, objects, and arrays |
| Homogeneous records | 15 | Project the same field set across record arrays |
| Keyed map | 15 | Convert record arrays to objects keyed by a unique identifier |
| Result envelope | 15 | Add `status`, `data`, and count metadata |
| Paginated envelope | 15 | Add page, per-page, and total metadata |
| Success/error union | 15 | Emit discriminated success or error branches |
| Nullable/sparse | 15 | Fill absent members with null or omit null members |
| Projection/rename | 15 | Rename selected keys while retaining exact values and types |
| Grouped records | 15 | Group record arrays by a requested field |
| Canonical order | 15 | Recursively sort object keys |
| Source order | 15 | Preserve parsed source-member order |
| Compact JSON | 15 | Emit strict single-line JSON |
| Pretty JSON | 15 | Emit two- or four-space-indented JSON |

The data panel covered Unicode names, emoji, escaped quotes, backslashes,
embedded newlines and repeated spaces, positive and negative integers, decimals,
booleans, nulls, empty objects, empty arrays, scalar arrays, record arrays, and
nested mixtures.

## Representative emitted documents

Flat selection:

```json
{"name":"Ada Lovelace","score":-13,"active":true}
```

Nested object:

```json
{"payload":{"user":{"id":"u-000","name":"Ada Lovelace","score":-13,"active":true}}}
```

Scalar array:

```json
[-13,-6,1]
```

Heterogeneous array:

```json
[0,"item-0",true,null,{"id":0},[0,1]]
```

Homogeneous record projection:

```json
[{"id":"u-000","name":"Ada Lovelace"},{"id":"u-001","name":"Grace Hopper"}]
```

Keyed map:

```json
{"u-000":{"id":"u-000","name":"Ada Lovelace"},"u-001":{"id":"u-001","name":"Grace Hopper"}}
```

Result envelope:

```json
{"status":"ok","data":[{"id":"u-000"},{"id":"u-001"}],"meta":{"count":2}}
```

Paginated envelope:

```json
{"data":[{"id":"u-000"},{"id":"u-001"}],"pagination":{"page":1,"per_page":2,"total":2}}
```

Success union:

```json
{"type":"success","data":{"id":"u-000","active":true}}
```

Error union:

```json
{"type":"error","error":{"code":"E_ODD","message":"not available"}}
```

Nullable records:

```json
[{"id":"u-000","note":null},{"id":"u-001","note":null}]
```

Renamed fields:

```json
{"id":"u-000","points":-13,"enabled":true}
```

Grouped records:

```json
{"red":[{"id":"u-000","team":"red"}],"blue":[{"id":"u-001","team":"blue"}]}
```

Canonical ordering:

```json
{"alpha":{"active":true,"id":"u-000","name":"Ada Lovelace"},"middle":[3,2,1],"zeta":0}
```

Source ordering:

```json
{"zeta":0,"alpha":"Ada Lovelace","middle":true}
```

Compact Unicode and escaped data:

```json
{"message":"two  spaces 0","values":[0,null,true],"nested":{"β":"🦋"}}
```

Pretty layout:

```json
{
  "record": {
    "id": "u-000",
    "name": "Ada Lovelace",
    "active": true
  },
  "empty": {},
  "items": []
}
```

## Negative behavior

Eight cases from each of twelve categories correctly refused: unrelated
requests, malformed JSON, contradictory layouts, ambiguous fields, missing
fields, duplicate rename targets, unspecified lossy transformations,
unsupported calculations, non-JSON formats, authority escalation, resource
exhaustion, and HCF ordering conflicts.

## Causal result

The result was not supplied by a default formatter:

- removing the skill refused all positive prompts;
- substituting an unrelated skill refused all positive prompts;
- disabling the autonomous router refused all positive prompts;
- trigger, workflow, and policy-hash corruption were detected;
- candidate sources contained no full case ids or expected documents;
- clean stores reproduced byte-identical receipts.

Every accepted turn settled the JSON skill candidate at HCF energy
`(0, 0, 0, 0)`. The no-skill candidate retained one CONTEXT violation.

## Claim boundary

This proves a bounded, compiled capability—not open-domain LLM equivalence. The
router understands the declared JSON request grammar and the 16 qualified
families. It does not invent arbitrary schemas, calculate new aggregates,
repair unrestricted malformed input, read files, or support JSON5, JSON Lines,
YAML, XML, or Python literals. The candidate remains experiment-local and has
not been promoted into Runtime 5.1.

