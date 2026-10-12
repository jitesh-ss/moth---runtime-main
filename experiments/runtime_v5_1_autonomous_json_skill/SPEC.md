# Spec: Runtime 5.1 autonomous JSON skill

Status: `DRAFT — OWNER REVIEW REQUIRED`

## Assumptions

1. A "separate instance" is a new experiment-local Runtime 5.1 artifact and
   SQLite store. The existing qualified artifact, its hashes, and its runtime
   sources remain unchanged.
2. The experiment compiles one detailed Markdown skill exactly once. All
   positive campaign turns use that one immutable compilation id and policy
   hash.
3. "Without babysitting" means no per-case skill id, presentation mode,
   schema/template id, structured task snapshot, retry instruction, manual
   correction, or hidden oracle is supplied at inference time.
4. "Natural LLM like" means a user supplies ordinary English containing data
   and the desired JSON organization, and the runtime autonomously determines
   whether the JSON skill applies, binds the requested structure, and emits the
   result. It does not mean using an LLM, weights, a model API, or unconstrained
   generation.
5. "Vast variety" means materially different JSON structures and layout
   requirements, not many whitespace variants of the same object.
6. An honest failure is a valid experimental conclusion. Unsupported requests
   must refuse; they must not be counted as successes through partial output or
   relaxed comparison.

## Objective

Determine whether a compiled Runtime 5.1 field plus one detailed real-world
skill can provide autonomous, general JSON-formatting behavior across unseen
natural requests while preserving exact data, deterministic replay, HCF
authority, and closed execution.

The causal claim under test is:

> After a generic JSON-formatting field is compiled, compiling and making one
> detailed JSON skill available causes relevant natural prompts to route to a
> stable policy that emits many exact JSON shapes; removing or corrupting that
> skill removes the capability.

This experiment is about skill-derived capability. It must not hide every
answer shape in the field, campaign code, prompt ids, or Surface templates.

## Non-goals

- Promoting Runtime 5.1 or changing its qualified artifact.
- General natural-language understanding.
- Reading or writing arbitrary user files.
- Executing generated Python, tools, subprocesses, or network requests.
- Claiming support for YAML, XML, JSON5, JSON Lines, or programming-language
  object literals as strict JSON.
- Repairing malformed JSON unless the skill explicitly defines a bounded,
  separately tested repair grammar.
- Judging aesthetic quality by hand.

## Technical approach

### Isolated instance

The campaign builds an experiment-local artifact and fresh store under `runs/`.
It imports the existing Runtime 5.1 implementation as a dependency but must not
edit `src/moth_runtime_v5_1/`, `config/v5.1/`, or the qualified artifact.

The experiment may implement an adapter local to this directory for the missing
prompt-to-skill routing step. Any such adapter is part of the candidate under
test and must be fully hash-bound and causally ablated.

### Candidate base field

The candidate field may provide only generic JSON primitives and operators,
such as:

```text
PARSE_SOURCE_DATA
DETECT_JSON_INTENT
BIND_OUTPUT_SHAPE
SELECT_FIELDS
RENAME_FIELDS
NEST_FIELDS
GROUP_RECORDS
BUILD_ARRAY
BUILD_KEYED_MAP
BUILD_ENVELOPE
INCLUDE_NULL
OMIT_ABSENT
ORDER_KEYS
FORMAT_MINIFIED
FORMAT_PRETTY
PARSE_EMITTED_JSON
VERIFY_EXACT_DATA
VERIFY_REQUESTED_SHAPE
EMIT_JSON
```

The base field may define types, safety conditions, and generic composition
operators. It must not contain campaign case ids, literal expected documents,
or one profile per test case.

### Single detailed skill

One human-readable `SKILL.md` describes:

- its natural trigger and explicit non-triggers;
- source-data identification;
- shape selection and field binding;
- flat, nested, array, keyed-map, envelope, metadata, sparse/null, union, and
  projection behavior;
- key renaming, grouping, ordering, and layout rules;
- exact preservation of scalar value and JSON type;
- duplicate-key, missing-field, ambiguity, malformed-input, and unsupported-
  transformation refusals;
- parse-back verification and completion criteria.

The document must compile through the candidate field's ordinary clause
compiler. Campaign code must use the resulting canonical policy rather than
reinterpreting the original Markdown on every turn.

### Autonomous routing

Each campaign conversation starts from the same artifact configuration. A turn
contains only the natural user request. The runtime must autonomously:

1. recognize whether the JSON skill applies;
2. bind the input data and formatting requirements;
3. select the compiled JSON policy through a recorded settlement;
4. produce JSON or a typed refusal;
5. record the compilation id, policy hash, route evidence, and result hash.

There may be no per-turn call to `plan_skill(compilation_id, ...)`, no explicit
`presentation=`, and no test-provided template identifier.

## Campaign design

### Frozen split

Before the first scored execution, create and hash:

- a development panel used only to validate infrastructure;
- a sealed held-out qualification panel;
- a source manifest covering the field, skill, panels, generator, runtime
  dependency hashes, and campaign code.

After sealing the qualification panel, no code, field, skill, thresholds, or
fixtures may be tuned against its results. A failed attempt remains preserved;
repairs require a new numbered attempt and a newly declared policy.

### Positive qualification panel

The held-out panel contains at least 240 positive cases, with at least 12 cases
from each of these 16 families:

1. flat object selection;
2. nested objects of depth two through five;
3. arrays of scalar values;
4. arrays of heterogeneous records within a declared union;
5. arrays of homogeneous records;
6. objects keyed by a selected identifier;
7. result envelopes containing `data`, `status`, and metadata;
8. paginated envelopes;
9. success/error discriminated unions;
10. nullable and explicitly sparse records;
11. field projection and renaming;
12. grouping records into nested collections;
13. canonical key ordering;
14. source-order preservation when explicitly requested;
15. compact single-line JSON;
16. pretty JSON with two- or four-space indentation.

Cases must vary strings, escaped characters, Unicode, integers, negative
numbers, decimals, booleans, nulls, empty arrays, empty objects, and nested
mixtures. At least half of the prompts are paraphrases not present in the skill
or interpretation-rule examples. No qualification prompt is a byte copy of a
development prompt.

### Negative and ambiguity panel

At least 96 additional cases cover:

- requests unrelated to JSON;
- malformed or multiply delimited source data;
- contradictory layout requests;
- ambiguous field references;
- requested fields absent from the source;
- duplicate output keys after renaming;
- loss-inducing transformations not authorized by the request;
- unsupported computation or aggregation;
- JSON5, YAML, XML, Python literal, and JSON Lines requests;
- attempts to activate network, tools, file writes, or code execution;
- prompt injection asking the runtime to ignore the compiled skill;
- oversized/depth-exhausting inputs;
- same-level HCF conflicts.

Every negative case has one frozen expected refusal class. A refusal with the
wrong class is a failure.

### Metamorphic panel

At least 64 transformations test invariants:

- paraphrasing the request does not change the JSON value;
- changing only whitespace does not change semantic output;
- changing only requested indentation changes bytes but not parsed value;
- permuting unordered input members preserves canonical output;
- changing a source scalar changes only its bound output locations;
- an irrelevant sentence cannot activate another capability;
- repeated execution is byte-identical.

## Causal controls

All controls are mandatory:

1. **No-skill ablation:** the same candidate field without the compiled skill
   must not pass the supported panel.
2. **Unrelated-skill control:** replacing the JSON skill with an unrelated valid
   policy must refuse JSON requests.
3. **Trigger corruption:** changing the trigger hash must be detected or remove
   activation.
4. **Workflow corruption:** deleting or reordering a material verification step
   must be detected or fail the relevant cases.
5. **Policy-hash corruption:** must be rejected before inference.
6. **Router ablation:** disabling autonomous routing must remove the capability;
   fallback Surface defaults cannot accidentally pass.
7. **Oracle-leak scan:** case ids, expected-output hashes, and complete expected
   documents must not occur in candidate field, skill, router, or runtime code.
8. **Fresh-store replay:** a clean store rebuilt from the same artifact must
   reproduce identical deterministic result bytes.

These controls distinguish "the skill caused the capability" from "the base or
test harness already knew every answer."

## Success criteria

The experiment passes only if every gate passes:

| Gate | Required result |
| --- | --- |
| Skill compilation | one compile; deterministic bytes across 10 rebuilds |
| Positive semantic accuracy | 240/240 exact parsed-value matches |
| Requested shape accuracy | 240/240 exact structural matches |
| Byte-layout accuracy | 100% for cases specifying indentation/order/minification |
| Natural paraphrase subset | 100% without prompt-specific additions |
| Negative safety | 96/96 correct typed refusals |
| Metamorphic invariants | 64/64 |
| Autonomous route | 100%; no explicit skill/presentation/template per turn |
| Policy attribution | every answer binds the same expected policy hash |
| Replay | byte-identical deterministic receipts in fresh stores |
| Repeated runs | identical outcomes over 5 runs and 2 hash seeds |
| Causal controls | 8/8 pass |
| Side effects | zero network, tool dispatch, code execution, and workspace writes |
| Existing 5.1 preservation | qualified artifact hashes unchanged; focused tests pass |

There is no partial PASS. Any supported wrong answer, unsafe acceptance,
unattributed answer, oracle leak, or post-seal tuning produces `FAIL`. An
infrastructure failure produces `INCONCLUSIVE`, not PASS.

## Evidence and reporting

The compact report must include:

- exact artifact, foundation, field, skill, policy, router, panel, and source
  hashes;
- environment and replay commands;
- aggregate and per-family matrices;
- every failing case id with expected/observed status and minimal diagnostics;
- all causal-control results;
- counts of model calls, tool dispatches, execution attempts, and writes;
- wall-clock and deterministic operation counts stored separately;
- a final verdict limited to the frozen claim.

Raw prompts, outputs, stores, and repeated row streams remain under ignored
`runs/`. Compact manifests and conclusions belong under `reports/`.

## Tech stack

- Python 3.11.
- Existing `moth_runtime_v5_0` and `moth_runtime_v5_1` packages.
- Standard library JSON and SQLite facilities.
- `pytest` for unit and integration gates.
- No new dependencies without owner approval.

## Commands

Planned commands, run from `/Users/jitesh-ss/work/Moth`:

```sh
./.venv/bin/python -m pytest \
  experiments/runtime_v5_1_autonomous_json_skill/tests -q

./.venv/bin/python -m \
  experiments.runtime_v5_1_autonomous_json_skill.campaign \
  --attempt 001

./.venv/bin/python -m pytest \
  tests/test_runtime_v5_1.py \
  tests/test_launcher_v5_1.py \
  experiments/runtime_v5_1_hcf/tests \
  experiments/runtime_v5_1_compiled_artifact/tests -q
```

The campaign command must refuse to overwrite an existing attempt.

## Project structure

```text
experiments/runtime_v5_1_autonomous_json_skill/
├── README.md
├── SPEC.md
├── PLAN.md
├── TASKS.md
├── campaign.py
├── candidate_runtime.py
├── compiler.py
├── fixtures/
│   ├── json-formatting-field-en-1.0.json
│   ├── json-formatting/SKILL.md
│   ├── development-panel-1.0.json
│   ├── qualification-panel-1.0.json
│   ├── metamorphic-panel-1.0.json
│   └── SOURCE-MANIFEST.json
├── reports/
│   ├── README.md
│   └── RESULT-001.json
├── runs/
│   └── .gitignore
└── tests/
    ├── test_compiler.py
    ├── test_autonomous_routing.py
    ├── test_json_realization.py
    ├── test_causal_controls.py
    └── test_campaign.py
```

## Code style

Candidate decisions return typed, hash-bound data rather than exceptions or
free-form strings at the experiment boundary:

```python
def settle_json_request(prompt: str, policy: dict[str, object]) -> dict[str, object]:
    route = compile_route(prompt, policy)
    if route.status != "SUPPORTED":
        return refusal(route.code, route.evidence)
    value = realize_json(route.source_value, route.format_plan)
    verify_realization(value, route)
    return finish_result(value, route, policy)
```

Use descriptive snake-case filenames, type annotations, canonical serialization,
pure functions for compilation and settlement, explicit resource limits, and
typed refusal codes. Timing data must never enter deterministic hashes.

## Testing strategy

1. Unit-test parsing, clause interpretation, plan construction, JSON escaping,
   structural verification, limits, and refusal typing.
2. Integration-test natural prompt through autonomous routing, settlement,
   realization, receipt generation, and replay.
3. Run the frozen positive, negative, and metamorphic qualification panels once
   per sealed attempt.
4. Run independent causal and tamper tests against the built artifact.
5. Re-run the existing Runtime 5.1 focused suites and compare qualified artifact
   hashes to prove isolation.

Expected accuracy is 100%, because the system is closed and the supported panel
is declared. Statistical thresholds would conceal unsupported behavior.

## Boundaries

### Always

- Work only under this experiment directory except for read-only imports and
  tests of existing Runtime 5.1.
- Compile the base field before compiling the skill.
- Compile the skill before opening the scored qualification panel.
- Bind every answer to artifact, field, compilation, policy, route, and result
  hashes.
- Preserve every sealed attempt and all failures.
- Fail closed on ambiguity, unsupported structure, resource exhaustion, or
  integrity mismatch.

### Ask first

- Add a dependency.
- Modify existing Runtime 5.1 source or configuration.
- Change a sealed panel, gate, or threshold.
- Create a qualification or promotion record.
- Enable filesystem mutation, tool dispatch, network access, or code execution.

### Never

- Put expected outputs or case identifiers into the candidate implementation.
- Select a skill, presentation, schema, or template on behalf of an individual
  campaign case.
- retry a failed case with a corrected prompt;
- tune against the sealed qualification output;
- overwrite an attempt;
- count malformed, partial, or semantically altered JSON as correct;
- claim open-domain language understanding or production readiness.

## Deliverables after approval

1. Reviewed `PLAN.md` describing architecture, risks, and verification points.
2. Reviewed `TASKS.md` with bounded implementation tasks and per-task checks.
3. Candidate field and one detailed skill fixture.
4. Frozen development, qualification, negative, and metamorphic panels.
5. Experiment-local autonomous router and JSON realizer.
6. Unit, integration, causal, integrity, and preservation tests.
7. One non-overwritten raw attempt and compact result report.
8. A conclusion of `PASS`, `FAIL`, or `INCONCLUSIVE` with no promotion.

## Open questions

The specification assumes strict RFC-compatible JSON documents and excludes
JSON Lines and JSON5. It also assumes an experiment-local autonomous router is
part of the capability being tested. Owner approval of this specification
accepts those two boundaries.

