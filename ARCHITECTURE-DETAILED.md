# Moth Runtime 4.7: Detailed Architecture and Formal System Description

## Abstract

Moth Runtime 4.7 is a deterministic, closed-world, proof-carrying execution
system for knowledge and programs compiled in advance from controlled language
and statically inspected Python. It is not a generative language model, an
open-world question-answering system, a general theorem prover, or a tool
executor. Its purpose is narrower and more auditable: it grounds a transient
text prompt to meanings already present in an immutable compiled generation,
executes one of a small number of exact kernel operations, rejects ambiguous or
unsupported requests, and emits a canonical result with energy coordinates,
semantic proof edges, provenance, and replay receipts.

The architecture deliberately separates two kinds of representation:

1. Dense 1,024-dimensional BGE vectors provide fallible but gated lexical and
   paraphrastic grounding.
2. Content-addressed meanings, directional semantic edges, typed values,
   schemas, programs, code spans, and source hashes provide authoritative
   semantics.

Vectors may select a compiled meaning; vectors cannot make a proposition true.
Truth, output structure, code locations, and proof identity are determined by
exact compiled state. This division is the central safety property of Runtime
4.7.

The runtime describes accepted states with the scalar integer energy

\[
E(y)=(K+1)Q\,V(y)+C(y),\qquad Q=1{,}000{,}000,
\]

where \(V(y)\) is a nonnegative hard-violation count, \(C(y)\) is quantized
grounding cost, and \(K\) is the number of grounded slots and bindings. Runtime
4.7 returns an answer only for an independently reconstructed state with
\(V=0\) and a unique semantic proof. In the current implementation, exact
dynamic programming and deterministic construction produce the candidate;
energy is an exact admissibility coordinate and certificate rather than a
continuous Hopfield settlement process.

This document is the detailed companion to ARCHITECTURE.md. The short file is
the frozen human-readable architecture lock. This document explains the actual
standalone implementation in src/moth_runtime, the frozen configuration in
config, and the evidence in reports. It does not change the content-addressed
architecture lock.

---

## 1. Status, authority, and scope

### 1.1 Runtime identity

| Property | Value |
|---|---|
| Runtime label | 4.7 |
| Runtime identifier | moth-runtime/4.7 |
| Python package | moth_runtime |
| Store schema | proof-energy-capability-store/4.7 |
| Field archive schema | proof-energy-capability-archive/4.7 |
| Query result schema | moth-capability-result/4.7 |
| Canonical status | Qualified, canonical, default |
| Enabled modality | Text |
| Maximum relational depth | 50 |
| Maximum linear program steps | 16 |
| External execution | Permanently disabled |
| Tool dispatch | Permanently disabled |

### 1.2 Sources of architectural truth

The sources have different roles:

- ARCHITECTURE.md is the concise architecture lock.
- config/ARCHITECTURE-LOCK.json binds the locked architecture and product
  documents to hashes and qualification records.
- PRODUCT.md states the user-facing capability boundary.
- SPEC.md records the standalone release requirements.
- src/moth_runtime is authoritative for operational behavior.
- config/runtime.json, config/grounding-en-1.0.json, and
  config/encoder-text-en-1.0.json freeze runtime identity, grounding gates, and
  encoder identity.
- reports/CAPABILITY-LAB-001.md and reports/REAL-MULTIHOP-LAB-001.md preserve
  empirical evidence and limitations.

When prose and implementation differ, this document describes the
implementation and explicitly marks the difference.

### 1.3 Included capabilities

Runtime 4.7 includes:

- controlled-language compilation;
- exact and vector-assisted typed grounding;
- content-addressed immutable meanings;
- directional relation edges;
- lookup;
- repeated single-relation traversal;
- mixed-relation sequence traversal;
- typed structured values and a bounded JSON Schema subset;
- canonical compiled JSON construction;
- linear acyclic programs;
- static Python 3.11 structure compilation;
- provenance-backed code relation queries;
- inert, hash-bound patch plans;
- inert tool-call-shaped JSON;
- immutable SQLite generations;
- canonical encoder-free replay.

### 1.4 Explicitly excluded capabilities

Canonical Runtime 4.7 does not include:

- free-form text generation;
- arbitrary Python synthesis;
- execution or importing of compiled Python;
- patch application;
- tool dispatch, SDK callbacks, or network calls;
- prompt-supplied new entities, facts, values, rules, tools, or schemas;
- query-time learning;
- arbitrary graph discovery;
- Horn-rule interpretation from ordinary prose;
- conjunction, negation, branching proof DAGs, or open-world classification;
- generic finite-domain constraint solving;
- the disposable Python-synthesis or Sudoku experimental primitives.

Those last two experiments demonstrated possible extension architectures but
were deleted and are not part of the canonical runtime.

---

## 2. Architectural thesis

Runtime 4.7 rests on five claims.

### 2.1 Compilation precedes use

The runtime may use only meanings present in a selected immutable generation.
Compilation is the authority boundary. A prompt is not a source document and
cannot extend the generation.

### 2.2 Dense grounding is not semantic truth

The encoder answers:

> Which compiled meaning is this prompt span most likely selecting?

It does not answer:

> Is this relation true, is this value allowed, or is this proof valid?

The first question is approximate and gated. The second class is answered only
by exact identifiers, edge tables, schemas, types, hashes, and kernel
constraints.

### 2.3 Direction is explicit

A relation edge is an ordered triple \((r,s,d)\). Reversing \(s\) and \(d\)
produces a different proposition and a different edge identifier. No symmetric
similarity matrix is used as relational truth.

### 2.4 Invalid states are never softened into answers

Hard violations dominate grounding preference. A lower lexical cost cannot
compensate for a missing relation, wrong type, stale code span, incompatible
schema, or ambiguous proof.

### 2.5 Results must be replayable and inspectable

The store records the exact canonical result bytes, selected generation,
normalized input receipt, and field hash. Replay verifies these bytes without
loading the encoder.

---

## 3. End-to-end system flow

The canonical data flow is:

~~~text
Controlled .moth files ─┐
                        ├─> deterministic compiler ─> immutable compiled field
Optional Python tree ───┘                                 │
                                                         │ publish
                                                         ▼
                                              immutable SQLite generation
                                                         │
Transient text prompt ─> normalize ─> instruction envelope match
                                      │
                                      ▼
                         exact aliases / typed vector grounding
                                      │
                                      ▼
                              grounded exact program
                                      │
                                      ▼
                  exact kernel settlement and proof counting
                                      │
                                      ▼
                    independent settlement reconstruction
                                      │
                         ┌────────────┴────────────┐
                         ▼                         ▼
                  canonical answer           typed refusal
                         │                         │
                         └────────────┬────────────┘
                                      ▼
                         episode bytes and replay receipt
~~~

The prompt is never passed to the compiler. Query episodes are stored in the
episodes table, which is not read as a compilation source.

---

## 4. Formal semantic objects

### 4.1 Meaning universe

Let \(\mathcal{M}\) be the finite set of compiled meanings in one generation.
Each meaning is:

\[
m=(id,\tau,n,p,O),
\]

where:

- \(id\) is a SHA-256 content address;
- \(\tau\) is a meaning type;
- \(n\) is the canonical human-readable name;
- \(p\) is the canonical typed payload;
- \(O\) is a nonempty ordered set of provenance owners.

The implementation defines these meaning types:

| Family | Meaning types |
|---|---|
| Core knowledge | ENTITY, RELATION, NUMERAL |
| Query language | OPERATION, INSTRUCTION, INSTRUCTION_PROTOTYPE, RELATION_FORM, ALIAS |
| Output | OUTPUT_SCHEMA, STRUCTURED_SCHEMA, SCHEMA_FIELD |
| Values | SCALAR_TYPE, VALUE, ENUM_MEMBER, LIST_VALUE |
| Programs | RELATION_SEQUENCE, PROGRAM, PROGRAM_STEP |
| Inert tools | TOOL, TOOL_ARGUMENT |
| Python structure | CODE_FILE, CODE_SYMBOL, CODE_SPAN |
| Patch planning | TEXT_FRAGMENT, PATCH_TEMPLATE |

### 4.2 Content addressing

Canonical JSON is UTF-8, key-sorted, compact, and finite-number-only. For a
meaning type \(\tau\) and canonical payload \(p\):

\[
id(m)=\operatorname{SHA256}\left(
\text{domain}_{meaning}\parallel 0x00\parallel
\operatorname{CanonicalJSON}(4.7,\tau,p)
\right).
\]

The exact domain is moth-capability-meaning/4.7. Meaning identifiers do not
depend on SQLite row IDs, insertion order, timestamps, or filesystem inode
numbers.

### 4.3 Directional semantic edges

The exact semantic graph is:

\[
\mathcal{E}\subseteq\mathcal{R}\times\mathcal{M}\times\mathcal{M}.
\]

An edge is:

\[
e=(id_e,r,s,d,O_e),
\]

with identifier:

\[
id_e=H(\text{domain}_{edge},r,s,d).
\]

Provenance owners do not change semantic edge identity. If multiple sources
assert the identical typed edge, the compiler creates one semantic edge with
multiple owners. This means duplicate provenance is not counted as multiple
semantic proofs.

### 4.4 Dense vectors

For each groundable meaning \(m\), compilation may store:

\[
v_m=\frac{f_\theta(t_m)}{\|f_\theta(t_m)\|_2}\in\mathbb{R}^{1024}.
\]

The passage text \(t_m\) is the instruction template when present; otherwise it
is the canonical meaning name. ALIAS, RELATION_FORM, PROGRAM_STEP, and
CODE_SPAN meanings are excluded from vector materialization.

The vector record contains:

- meaning ID;
- passage text;
- vector hash;
- the complete float32 vector.

### 4.5 Compiled field

A CompiledField contains:

\[
F=(S,M,N,A,E,V,h_F,h_C,h_\theta,g,L),
\]

where:

- \(S\) is the source map;
- \(M\) is the meaning map;
- \(N\) is the canonical-name index;
- \(A\) is the alias index;
- \(E\) is the sorted semantic edge tuple;
- \(V\) is the vector map;
- \(h_F\) is the field hash;
- \(h_C\) is the compiler hash;
- \(h_\theta\) is the encoder fingerprint;
- \(g\) is the generation ID;
- \(L\) is capability level L0 through L8.

---

## 5. Controlled compilation language

### 5.1 Lexical rules

Compilation accepts UTF-8 source documents. The implementation:

- normalizes line endings to LF;
- treats lines beginning with # after indentation as comments;
- requires one period-terminated statement per non-comment line;
- parses quoted strings through JSON string decoding;
- normalizes non-multiline text using Unicode NFC and whitespace collapse;
- records both character and byte offsets.

The compiler rejects any nonempty statement that matches neither a declaration
pattern nor exactly one compiled relation form.

### 5.2 Frozen declaration forms

The compiler recognizes the following source-level forms:

~~~text
Entity "name" is declared.
Directional relation "name" maps Meaning to Meaning and is functional.
Directional relation "name" maps Entity to Entity and is multi-valued.
Numeral "name" denotes N steps.
Operation "name" selects kernel primitive "PRIMITIVE".
Relation form "name" for relation "relation" accepts "template".
Instruction "name" selects operation "operation" accepts "template".
Instruction prototype "name" for instruction "instruction" is "template".
Output schema "name" selects kernel schema "SCHEMA".
Scalar type "name" selects kernel type "TYPE".
Value "name" has type "type" and canonical JSON "json".
Enum member "name" has type "type" and canonical JSON "json".
List value "name" has element type "type" and canonical JSON "json".
Structured schema "name" is canonical JSON Schema "json".
Schema field "name" in schema "schema" has type "type" and is required.
Relation sequence "name" is "relation-1,relation-2".
Program "name" is canonical step JSON "json".
Tool "name" uses schema "schema".
Tool argument "name" for tool "tool" selects field "field".
Text fragment "name" is "text".
Patch template "name" selects operation "REPLACE_SPAN".
Alias "surface" denotes Entity "name".
~~~

Alias target kinds extend beyond Entity to the complete KIND_SURFACES mapping
implemented by the compiler.

### 5.3 Compilation passes

Compilation is deterministic and multi-pass:

1. Sort source IDs and parse source statements.
2. Classify statements against frozen declaration patterns.
3. Declare independent meanings: entities, relations, numerals, operations,
   output schemas, scalar types, structured schemas, fragments, and patch
   templates.
4. Resolve typed values against scalar types.
5. Resolve relation forms, instructions, prototypes, schema fields, relation
   sequences, programs, tools, and tool arguments.
6. Resolve aliases.
7. Interpret unmatched statements through compiled relation forms.
8. Optionally compile a Python source tree.
9. Verify program reference closure.
10. Materialize and validate directional edges.
11. Enforce functional relation cardinality.
12. Construct name and alias indexes.
13. Encode groundable meanings.
14. Compute compiler, field, and generation hashes.

No partial field is returned after a compilation error.

### 5.4 Limits enforced at compilation

| Resource | Limit |
|---|---:|
| Individual source | 16 MiB |
| Total source collection | 1 GiB |
| Source count | 10,000 |
| Meaning count | 50,000 |
| Semantic edge count | 250,000 |
| Numeral depth | 50 |
| Relation sequence length | 1 to 50 |
| Program length | 1 to 16 |
| List value length | 256 |

Program steps may not contain branch, loop, or goto keys. This is a syntactic
and architectural rejection of general control flow.

### 5.5 Source-order semantics

Content-addressed semantic meaning and edge IDs are independent of declaration
order. However, a generation also commits to source document hashes and
provenance spans. Reordering statements inside a source changes the source hash
and therefore can change field and generation identity even when the semantic
compiler hash remains the same.

This distinction is intentional:

- semantic identity captures what was asserted;
- generation identity also captures exactly which source bytes asserted it.

---

## 6. Provenance model

### 6.1 Provenance record

Every source-owned meaning or edge records:

- source ID;
- source SHA-256;
- normalized statement SHA-256;
- character start and end;
- byte start and end;
- line;
- column;
- compiler version.

Python-derived provenance uses exact AST byte spans and the source-file hash.

### 6.2 Ownership and semantic identity

Meaning and edge identities exclude provenance ownership. Ownership is attached
after semantic identity is computed. Therefore:

- repeated identical declarations merge owners;
- removing one owner leaves the semantic object if another owner remains;
- different semantic paths remain different proofs even if their source text is
  similar;
- different owners of one edge do not create proof ambiguity.

### 6.3 Provenance in public results

For relational answers, the public proof expands every semantic edge ID to its
active provenance owners.

An important implementation detail is that public proof provenance is
edge-oriented. Lookup and structured-rendering outputs can have an empty
semantic-edge proof even though their selected meanings retain provenance in
the field archive. The current public result does not expand all non-edge
meaning owners into the proof section.

---

## 7. Encoder subsystem

### 7.1 Frozen encoder

The production encoder is BAAI/bge-large-en-v1.5 with:

- 1,024 output dimensions;
- normalized embeddings;
- little-endian float32 storage;
- deterministic CPU execution;
- batch size 8;
- local-files-only loading;
- a frozen query prefix;
- explicit hashes for six required model/tokenizer files.

The encoder fingerprint is content-addressed from the manifest excluding the
installation path. Relocating identical model assets therefore does not alter
encoder identity.

### 7.2 Determinism controls

At model load, Runtime 4.7:

- selects CPU;
- sets one Torch thread;
- enables deterministic algorithms;
- places the model in evaluation mode;
- disables parameter gradients;
- refuses a dimension mismatch;
- validates configured asset hashes.

### 7.3 Query and passage asymmetry

Compiled meanings use passage encoding. Prompt spans use query encoding with:

~~~text
Represent this sentence for searching relevant passages:
~~~

This asymmetry follows the encoder configuration and is part of the frozen
grounding identity.

### 7.4 Encoder authority boundary

The encoder is used only when exact canonical-name and alias resolution fail.
It cannot:

- create a meaning;
- create an edge;
- select a candidate of the wrong type;
- bypass an instruction envelope;
- change a schema;
- establish a code span;
- resolve semantic proof ambiguity.

---

## 8. Prompt grounding

### 8.1 Prompt normalization and isolation

A query prompt is Unicode-NFC normalized and whitespace-collapsed. The current
text adapter therefore treats line breaks as whitespace; it is designed around
single-envelope controlled requests, not raw multiline payload protocols.

The prompt:

- is never compiled;
- is never inserted into the name or alias index;
- is never added to semantic edges;
- may be stored in the episode table for replay and audit;
- is not consulted by later compilation.

### 8.2 Instruction-envelope selection

Instructions and instruction prototypes contain exact templates with typed
slots such as ENTITY, RELATION, NUMERAL, STRUCTURE, BINDINGS, TOOL, SPAN, PATCH,
and FRAGMENT.

Template matching is anchored over the entire normalized prompt. Slot capture
is non-greedy. The runtime requires exactly one distinct instruction and slot
assignment. Zero matches yield UNSUPPORTED_INSTRUCTION; multiple distinct
matches yield AMBIGUOUS_GROUNDING.

Instruction envelopes themselves are structurally matched. The frozen
INSTRUCTION vector threshold is not used to choose between arbitrary
instruction sentences in the current implementation.

### 8.3 Typed candidate restriction

Each slot name maps to exactly one MeaningType. Vector ranking occurs only
within that type. For example, an ENTITY span is never compared against TOOL or
OUTPUT_SCHEMA vectors.

### 8.4 Exact resolution

For a typed span \(q\), exact resolution checks:

1. canonical names;
2. compiled aliases.

One match succeeds with score 1 and cost 0. Multiple matches refuse as
ambiguous. Exact matches bypass vector thresholds but not type and program
checks.

### 8.5 Vector resolution

If exact resolution fails:

\[
s_i=\operatorname{round}_6(\hat q^\top v_i).
\]

Candidates are sorted by descending score and then canonical meaning ID.
Define:

\[
s_{(1)}=\max_i s_i,\qquad
\Delta=\operatorname{round}_6(s_{(1)}-s_{(2)}).
\]

With one candidate, the implementation uses \(s_{(2)}=-1\).

Acceptance requires strict inequalities:

\[
s_{(1)}>\theta_\tau,\qquad \Delta>\delta_\tau.
\]

Equality at either boundary refuses as AMBIGUOUS_GROUNDING.

Frozen thresholds are:

| Type | Score | Margin |
|---|---:|---:|
| Default | 0.82 | 0.05 |
| INSTRUCTION configuration entry | 0.82 | 0.08 |

Most slot types use the default because instruction selection is structural.

### 8.6 Grounding cost

For accepted cosine \(s\):

\[
c(s)=\operatorname{round}
\left(Q\frac{1-\operatorname{clip}(s,-1,1)}{2}\right).
\]

Exact resolution has zero cost. The grounded program sums costs across slots
and binding field/value resolutions.

### 8.7 Structured bindings

BINDINGS syntax is:

~~~text
field = value, field = value
~~~

The parser rejects malformed, empty, or duplicate bindings. Field names resolve
as SCHEMA_FIELD meanings. Values resolve among VALUE, ENUM_MEMBER, LIST_VALUE,
ENTITY, and CODE_SYMBOL, with exact cross-kind ambiguity checks before vector
fallback.

---

## 9. Exact energy semantics

### 9.1 State

The operational query state is:

\[
y=(g,x,J,D,\pi),
\]

where:

- \(g\) is the grounded instruction, operation, slots, and bindings;
- \(x\) is exact relational or intermediate state;
- \(J\) is a structured JSON value when applicable;
- \(D\) is an inert patch plan when applicable;
- \(\pi\) is the ordered semantic-edge proof.

### 9.2 Hard violations

Conceptually, factors may reject:

- absent or mistyped meanings;
- instruction/operation mismatch;
- missing directional transitions;
- nonunique paths;
- invalid schema binding;
- type mismatch;
- undeclared tool arguments;
- stale code files or spans;
- overlapping patches;
- syntactically invalid in-memory Python after a proposed patch;
- invalid pipeline topology;
- generation mismatch;
- missing proof provenance.

Let \(V(y)\) be their nonnegative count.

### 9.3 Scalar energy

For \(K\) grounded slots and bindings:

\[
M=(K+1)Q,\qquad Q=10^6,
\]

\[
E(y)=M\,V(y)+C(y).
\]

The intended dominance property is:

\[
M>\max C(y),
\]

so no grounding preference can compensate for one hard violation.

The implementation additionally validates that grounding cost lies between
zero and \(KQ\). Binding grounding can include both a field and value cost while
the public grounded-slot count counts one binding entry; this is a practical
implementation constraint to consider when extending vector-grounded
structured bindings.

### 9.4 Meaning of settlement

Runtime 4.7 does not numerically relax a dense state. It:

1. grounds to a finite exact program;
2. deterministically constructs or traverses exact state;
3. refuses on any hard failure;
4. reports the energy of the valid state;
5. independently reconstructs the settlement.

Thus the runtime is an exact discrete proof-energy system. Its energy is a
lexicographically dominating scalar certificate, not a physical simulation and
not the attention-derived Hopfield experiment that preceded it.

---

## 10. Kernel operation registry

The frozen operation set is:

| Primitive | Function |
|---|---|
| LOOKUP | Return one compiled entity or code meaning |
| CHAIN_ADVANCE | Repeat one relation for a compiled number of steps |
| RELATION_SEQUENCE | Apply an exact compiled relation list |
| VALIDATE_STRUCTURE | Validate and materialize compiled structured data |
| RENDER_COMPILED_JSON | Render schema-bound compiled values |
| LINEAR_PIPELINE | Compose 1 to 16 supported primitive steps |
| CODE_RELATION_QUERY | Traverse compiled Python relations |
| BUILD_PATCH_PLAN | Construct a verified inert patch plan |

Any other primitive is rejected at compilation.

---

## 11. Relational settlement

### 11.1 Layered dynamic programming

Given start meaning \(x_0\) and relation list
\((r_1,\ldots,r_n)\), settlement builds frontiers:

\[
F_0=\{x_0\mapsto(1,\epsilon)\}.
\]

At layer \(t\), each edge:

\[
(r_t,s,d)\in\mathcal{E}
\]

extends each proof ending at \(s\). For each destination, the message stores:

- proof count saturated at two;
- canonical representative proof, selected lexicographically by edge IDs.

Counts saturate because the public decision distinguishes only:

- no proof;
- exactly one proof;
- more than one proof.

### 11.2 Failure conditions

- An empty next frontier yields MISSING_PREMISE.
- More than one semantic proof or endpoint yields AMBIGUOUS_PROOF.
- A unique frontier and count one yields the destination and ordered proof.

Canonical ordering stabilizes enumeration. It never converts semantic
ambiguity into an answer.

### 11.3 Complexity

For depth \(n\) and the relevant indexed edge set:

\[
T=O\left(\sum_{t=1}^{n}|E_{r_t,F_{t-1}}|\right),
\]

with frontier storage bounded by the number of reachable meanings. The runtime
caps relation lists at 50.

### 11.4 Exhaustive oracle

The energy module also provides exhaustive_paths for small-field test parity.
It enumerates every exact path without dynamic-programming aggregation and is
used as an optimization oracle in qualification, not as the production path.

---

## 12. Structured values and canonical JSON

### 12.1 Supported schema subset

Supported JSON types:

- object;
- array;
- string;
- integer;
- finite number;
- boolean;
- null.

Supported schema keywords:

- type;
- properties;
- required;
- additionalProperties;
- items;
- enum;
- const;
- x-moth-field.

Objects must set additionalProperties to false. Schema nesting is limited to
eight. Objects may contain at most 64 fields. Arrays may contain at most 256
items. Output is limited to 64 KiB of canonical JSON.

### 12.2 Materialization

Materialization recursively traverses the compiled schema:

- x-moth-field nodes consume one compiled binding;
- const nodes emit a compiled schema constant;
- object nodes visit declared properties;
- required unbound fields fail;
- unused bindings fail as extra fields;
- type, enum, and const constraints are rechecked after construction.

Arrays must be supplied through a compiled binding or constant; the current
generic materializer does not synthesize array items recursively from a series
of independent field bindings.

### 12.3 Tool-shaped output

A TOOL meaning selects a compiled structured schema. TOOL_ARGUMENT meanings
bind permitted schema fields to the tool. RENDER_COMPILED_JSON validates these
relationships and returns ordinary inert JSON.

There is no dispatcher. A tool-shaped object has no greater authority than any
other structured value.

---

## 13. Linear programs

### 13.1 Program form

A PROGRAM stores one to sixteen canonical step dictionaries. Compilation
rejects branch, loop, and goto. Runtime rejects recursive LINEAR_PIPELINE steps.

### 13.2 Data flow

The current pipeline carries:

- accumulated semantic proof edges;
- saturated proof count;
- the latest output;
- the latest output meaning ID when the output is a compiled meaning.

For render steps with a compiled schema and field reference, the latest meaning
ID can be rebound into a temporary exact structured-rendering program.

This is a deliberately small linear composition model, not a general typed
intermediate representation. Arbitrary intermediate JSON, multiple outputs,
branches, joins, and loops are unsupported.

---

## 14. Python 3.11 static compilation

### 14.1 Security boundary

Python sources are decoded and parsed with ast.parse. They are never imported
and never executed.

The adapter rejects:

- a non-directory root;
- symlinked Python paths;
- paths escaping the selected root;
- files larger than 16 MiB;
- invalid UTF-8;
- syntax-invalid Python.

### 14.2 Compiled code meanings

The adapter creates:

- CODE_FILE for each Python file;
- CODE_SYMBOL for modules, classes, functions, async functions, parameters, and
  unresolved external names;
- CODE_SPAN for function, async-function, and class definitions.

Each code span includes exact character/byte offsets and a span hash.

### 14.3 Static code relations

The source field must declare these relations:

- contains;
- defines;
- imports;
- calls;
- inherits;
- decorated-by;
- references;
- tests.

The adapter materializes directional edges from AST evidence.

### 14.4 Resolution limits

Static resolution is intentionally conservative and shallow:

- name and attribute expressions are converted to textual names;
- local simple names use a per-file first-match index;
- unresolved names become explicit external symbols;
- dynamic dispatch, reflection, monkey patching, runtime imports, and dataflow
  are not inferred;
- a call from a function named with a test_ prefix emits a tests edge.

The resulting graph is provenance-backed static structure, not a complete
Python semantic model.

---

## 15. Inert patch planning

### 15.1 Patch operations

Compiled patch templates may select:

- REPLACE_SPAN;
- INSERT_BEFORE;
- INSERT_AFTER;
- DELETE_SPAN.

One BUILD_PATCH_PLAN query currently creates one edit, while the lower-level
builder supports one to sixteen edits.

### 15.2 Integrity checks

For every edit, the planner verifies:

- compiled code span type;
- compiled patch-template type;
- compiled replacement fragment when required;
- selected generation;
- code-file source availability;
- exact file hash;
- byte bounds;
- exact span hash;
- non-overlap between edits.

### 15.3 In-memory parse validation

Edits are applied only to an in-memory byte string, in reverse byte order. The
candidate file must decode as UTF-8 and parse as Python.

The returned plan contains expected hashes and replacement text, but no file is
written. Runtime 4.7 contains no patch application path.

---

## 16. Independent settlement verification

The solver may not certify itself. verify_settlement:

1. reruns settlement from the grounded program;
2. requires dataclass equality with the candidate;
3. checks every proof edge exists;
4. checks every proof edge has provenance;
5. recomputes scalar energy;
6. refuses any mismatch as INTEGRITY_FAILURE.

This is independent reconstruction at the operation level. It does not use a
second implementation of every algorithm, but it prevents a mutated or forged
Settlement object from reaching rendering.

Qualification supplements this with exhaustive small-field parity and
corruption tests.

---

## 17. Public query result

### 17.1 Answer shape

An answer contains:

~~~json
{
  "schema": "moth-capability-result/4.7",
  "runtime": "4.7",
  "capability_level": "L8",
  "status": "ANSWER",
  "generation_id": "...",
  "episode_id": "...",
  "grounded_program": {
    "instruction_id": "...",
    "operation_id": "...",
    "operation": "...",
    "slots": {},
    "bindings": {},
    "steps": [],
    "grounding": {}
  },
  "output": {
    "kind": "...",
    "value": {}
  },
  "energy": {
    "total_units": 0,
    "violation_count": 0,
    "grounding_cost_units": 0
  },
  "proof": {
    "proof_count": 1,
    "semantic_edge_ids": [],
    "provenance": []
  },
  "execution": {
    "performed": false,
    "dispatch_count": 0
  },
  "replay": {
    "input_hash": "...",
    "field_hash": "...",
    "result_hash": "..."
  }
}
~~~

### 17.2 Refusal shape

A refusal contains no speculative output or proof:

~~~json
{
  "schema": "moth-capability-result/4.7",
  "runtime": "4.7",
  "status": "REFUSAL",
  "refusal": {
    "code": "UNSUPPORTED_INSTRUCTION",
    "message": "...",
    "grounded_context": {}
  },
  "execution": {
    "performed": false,
    "dispatch_count": 0
  },
  "replay": {
    "input_hash": "...",
    "field_hash": "...",
    "result_hash": "..."
  }
}
~~~

### 17.3 Result hash

The result hash is computed over canonical result content with result_hash
itself omitted. This prevents self-reference while binding every other field.

---

## 18. Refusal taxonomy

The runtime defines:

| Category | Codes |
|---|---|
| Unknown compiled meanings | UNKNOWN_ENTITY, UNKNOWN_NUMERAL, UNKNOWN_TOOL, UNKNOWN_VALUE |
| Unsupported language | UNSUPPORTED_RELATION, UNSUPPORTED_INSTRUCTION, UNSUPPORTED_OPERATION, UNSUPPORTED_OUTPUT, UNSUPPORTED_PROGRAM, UNSUPPORTED_MODALITY, UNSUPPORTED_CODE_LANGUAGE |
| Ambiguity | AMBIGUOUS_GROUNDING, AMBIGUOUS_PROOF, AMBIGUOUS_PROGRAM |
| Missing semantics | MISSING_PREMISE |
| Type and argument safety | UNSUPPORTED_ARGUMENT, TYPE_MISMATCH, INVALID_SCHEMA |
| Code integrity | INVALID_PATCH_TARGET, STALE_SOURCE |
| Global safety | INTEGRITY_FAILURE, RESOURCE_LIMIT, COMPILATION_ERROR |

Compiler errors occur before query publication and are surfaced by the CLI as
exceptions rather than query-result refusals.

Operational query precedence is:

1. source and edge integrity;
2. prompt resource limit;
3. modality;
4. instruction grounding;
5. typed slot grounding;
6. operation and settlement constraints;
7. independent verification;
8. answer rendering.

---

## 19. Immutable SQLite store

### 19.1 Store identity

The store is one SQLite file with schema:

~~~text
proof-energy-capability-store/4.7
~~~

Opening another runtime schema is refused. Earlier stores are not migrated.

SQLite is configured with:

- WAL journal mode;
- synchronous FULL;
- foreign keys enabled.

### 19.2 Tables

#### descriptor

Singleton store-schema identity.

#### generations

Stores:

- generation ID;
- parent generation ID;
- capability level;
- field hash;
- archive hash;
- canonical archive bytes.

Rows are immutable after insertion.

#### head

Singleton pointer to the selected current generation.

#### episodes

Stores:

- episode ID;
- generation ID;
- raw prompt;
- modality;
- normalized input hash;
- result byte hash;
- canonical result bytes.

#### purge_receipts

Stores logical source-removal receipts.

### 19.3 Atomic publication

Publication follows:

1. initialize and verify store schema;
2. snapshot head;
3. compile outside the publication transaction;
4. serialize and hash the archive;
5. begin an immediate transaction;
6. re-read head;
7. abort on concurrent change;
8. insert immutable generation;
9. atomically update head;
10. commit.

This prevents a long encoder run from holding the write transaction and avoids
publishing against a stale parent.

### 19.4 Source lifecycle

- sync compiles all nonsymlink .moth files in a directory and optionally the
  Python tree when Python files are present.
- add republishes active controlled-language sources with one addition or
  replacement.
- remove republishes without one source.
- history lists generation ancestry.
- export performs a verified SQLite backup to a new destination.

The current purge operation is logical, not physical secure erasure. It
publishes a generation without the source and records a receipt, but immutable
historical generation archives remain in the SQLite store. Operators requiring
physical deletion must use a separately designed retention or store-rewrite
procedure; Runtime 4.7 does not implement cryptographic erasure.

Also, add and remove reconstruct active .moth sources only. They do not retain
an earlier sync code_root automatically, so a later language-only publication
may omit previously compiled Python structure unless the code tree is synced
again.

---

## 20. Field archives

The archive contains:

- schema ID;
- capability level;
- field, compiler, encoder, and generation hashes;
- complete sources;
- meanings and owners;
- indexes;
- semantic edges and owners;
- complete dense vectors;
- archive hash.

Archive loading:

1. verifies archive schema;
2. recomputes archive hash;
3. reconstructs immutable dataclasses;
4. checks edge identifier closure;
5. requires nonempty edge provenance;
6. checks meaning-map keys.

Because the archive hash covers the full canonical payload, source text,
vectors, indexes, and provenance are transitively protected by that receipt.

---

## 21. Encoder-free replay

Replay is not a fresh semantic query. It is exact receipt verification.

Given episode ID:

1. fetch stored generation, prompt, modality, input hash, result hash, and bytes;
2. hash result bytes;
3. parse and verify the result receipt;
4. load and verify the immutable generation archive;
5. recompute normalized input hash;
6. compare field hash;
7. require stored JSON bytes to equal canonical serialization;
8. return the original bytes.

No encoder is loaded or required. Replay therefore proves byte stability and
receipt integrity, not continued semantic behavior under a changed compiler.

---

## 22. Hash hierarchy

Runtime 4.7 uses domain-separated SHA-256 throughout.

| Hash | Commits to |
|---|---|
| Meaning ID | runtime, type, canonical semantic payload |
| Edge ID | relation, source, destination IDs |
| Vector hash | encoder fingerprint and float32 vector bytes |
| Compiler hash | semantic meanings, aliases, edges, capability level |
| Field hash | compiler hash, encoder, vector hashes, parent, source hashes |
| Generation ID | same field payload under a generation domain |
| Archive hash | complete canonical archived field |
| Input hash | generation, modality, normalized prompt |
| Episode ID | input hash |
| Result hash | canonical answer or refusal receipt |

Domain separation prevents identical raw JSON used for two conceptual objects
from producing the same identifier.

---

## 23. Determinism model

Determinism depends on:

- Unicode NFC and deterministic whitespace normalization;
- sorted source IDs;
- sorted meaning and edge construction;
- content-addressed IDs;
- quantized cosine scores;
- canonical ID tie-breaking;
- deterministic CPU encoder configuration;
- exact dynamic programming;
- proof counts saturated at two;
- canonical JSON;
- immutable generation selection;
- explicit source and model hashes.

The system does not use timestamps, random seeds, sampling temperature, or
unordered database row IDs in semantic decisions.

---

## 24. Security and threat model

### 24.1 Protected assets

The architecture protects:

- semantic field integrity;
- source provenance;
- code-file and code-span identity;
- closed-world meaning boundaries;
- output schema boundaries;
- proof uniqueness;
- replay integrity;
- non-execution guarantees.

### 24.2 Adversarial prompt

An adversarial prompt may attempt to:

- state a new fact;
- inject a schema key;
- request an unknown tool;
- smuggle JSON syntax through a value;
- select an ambiguous alias;
- name a stale code span;
- request an unsupported program;
- exceed prompt limits.

These attempts cannot enter the field. They either fail instruction matching,
typed grounding, schema materialization, or exact settlement.

### 24.3 Malicious compiled source

Compilation validates syntax, types, references, program topology, relation
cardinality, resource limits, schemas, Python paths, and Python syntax.

Compilation is nevertheless an authority grant: an accepted source can declare
meanings and facts. Source review and generation selection remain operator
responsibilities.

### 24.4 Non-execution guarantee

Canonical Runtime 4.7 has no:

- eval or exec path for compiled source;
- Python import path for compiled code;
- patch writer;
- tool registry callback;
- network client;
- subprocess dispatcher.

Every public result states performed false and dispatch_count zero.

### 24.5 Residual risks

- Vector grounding can produce false positives within a type if calibration
  does not cover a lexical region.
- Instruction templates use regular-expression slot capture and should not be
  treated as a general natural-language parser.
- Static Python name resolution is approximate.
- The SQLite store contains raw prompts and historical source payloads.
- Logical purge is not physical deletion.
- Python parsing and model loading inherit the security posture of their local
  dependencies.
- Hash integrity detects changes but does not provide confidentiality.

---

## 25. Complexity and resource behavior

### 25.1 Compilation

Ignoring encoder cost:

\[
T_{compile}=O(|S|+|M|\log|M|+|E|\log|E|).
\]

Encoder cost scales with the number of groundable meanings and model inference
cost.

### 25.2 Grounding

Exact lookup is index-based. Vector fallback for one slot is:

\[
O(|M_\tau|d),
\]

where \(d=1024\) and \(M_\tau\) is the candidate set of the required type.
There is no approximate-nearest-neighbor index in the current standalone
implementation.

### 25.3 Relational execution

Traversal is linear in relevant frontier expansion through at most 50 layers.
Proof counts are constant-sized because they saturate at two.

### 25.4 Structured rendering

Rendering is linear in the selected schema and output size, bounded by the
schema and 64-KiB limits.

### 25.5 Python compilation

AST parsing and visitation are approximately linear in source size, with
content-addressed record and edge construction overhead.

---

## 26. Operational lifecycle

### 26.1 Initialize

~~~sh
moth init
~~~

Creates the Runtime 4.7 descriptor and null head. It does not create a field
generation.

### 26.2 Compile and publish

~~~sh
moth sync path/to/compiled-world
~~~

Compiles .moth files and any Python files under the selected directory into one
new immutable L8 generation.

### 26.3 Query

~~~sh
moth query "Starting from Asterion, follow route for fifty steps using answer-json."
~~~

The runtime uses the current head unless a generation is explicitly selected.

### 26.4 Replay

~~~sh
moth replay EPISODE_ID --encoder-free
~~~

Returns verified original canonical result bytes.

### 26.5 Verify and export

~~~sh
moth verify
moth export path/to/snapshot.sqlite3
~~~

verify checks SQLite integrity and every generation archive. export refuses to
overwrite an existing destination.

---

## 27. Worked relational example

Assume the field declares:

~~~text
Entity "Asterion" is declared.
Entity "Belisar" is declared.
Directional relation "route" maps Entity to Entity and is functional.
Relation form "route-leads" for relation "route" accepts
"The route from {SOURCE} leads to {DESTINATION}.".
The route from "Asterion" leads to "Belisar".
~~~

Compilation creates:

- two ENTITY meanings;
- one RELATION meaning;
- one RELATION_FORM meaning;
- one edge \((route,Asterion,Belisar)\);
- one or more provenance owners for that edge.

After an instruction grounds the start, relation, numeral one, and schema, the
frontier evolves:

\[
F_0=\{Asterion\},
\]

\[
F_1=\{Belisar\}.
\]

The result has:

- endpoint Belisar;
- one semantic edge ID;
- that edge's source owners;
- violation count zero;
- grounding cost determined by exact or vector slot resolution;
- execution false.

Removing the edge produces MISSING_PREMISE. Adding a second route edge from
Asterion violates functional cardinality at compilation. For a multi-valued
relation, two valid endpoint proofs produce AMBIGUOUS_PROOF at query time.

---

## 28. Worked structured-output example

Assume a schema:

~~~json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "message": {
      "type": "string",
      "x-moth-field": "message"
    }
  },
  "required": ["message"]
}
~~~

The field must separately declare:

- the scalar string type;
- the structured schema;
- schema field message;
- one or more compiled string values;
- an output schema and instruction.

The prompt may bind message to a compiled value. It cannot supply arbitrary raw
message text. Materialization consumes the compiled value and emits:

~~~json
{"message":"compiled value"}
~~~

An extra field, unknown value, wrong type, or missing required binding refuses.

---

## 29. Worked Python and patch example

When a Python tree is synced:

1. The adapter parses a function definition.
2. It creates CODE_FILE, CODE_SYMBOL, and CODE_SPAN meanings.
3. It records defines and contains edges.
4. Calls, imports, inheritance, decorators, references, and tests become
   directional edges when statically visible.
5. A query may traverse these edges.
6. A patch-plan query may select a compiled span, patch operation, and compiled
   replacement fragment.
7. The planner checks hashes and parses the in-memory candidate.
8. It returns an inert plan.

It does not generate a replacement fragment from the prompt and does not write
the candidate file.

---

## 30. Empirical evidence

The preserved capability report records:

- 1,688 of 1,688 quick-gate cases;
- 2,400 of 2,400 held-out cases;
- 2,400 of 2,400 supplemental closed-world reconstruction checks;
- exact small-field solver/exhaustive parity;
- byte-exact encoder-free replay;
- zero code execution;
- zero patch application;
- zero tool dispatch;
- zero campaign network attempts.

The real multi-hop boundary audit records:

- actual ProofWriter test data projected into query-independent positive
  single-premise chains;
- 300 of 300 projected proof outcomes;
- 540 of 540 causal and invariance controls;
- 200 of 200 native-boundary refusals;
- explicit confirmation that native ProofWriter conjunction, rule discovery,
  negation, branching proofs, and True/False/Unknown classification remain
  unsupported.

These results support the frozen boundary. They do not prove correctness for
all possible compiled fields or natural-language paraphrases.

---

## 31. Interpretation of the phrase energy field

Runtime 4.7 is an energy field in the discrete optimization sense:

- compiled meanings define variables and candidate assignments;
- semantic edges and schemas define compatibility constraints;
- grounding defines finite candidate costs;
- hard violations receive dominating energy;
- the accepted answer is a unique zero-violation state;
- the state is reconstructed independently.

It is not:

- a continuous attractor network;
- an associative Hopfield memory;
- an attention-derived global relaxation;
- a neural system that invents intermediate semantics;
- a prompt-time learned reasoner.

The field metaphor describes a persistent compiled constraint landscape. The
current execution algorithms exploit exact structure rather than numerically
settling arbitrary energy landscapes.

---

## 32. Extension discipline

A future operation should be admitted only if all of the following exist:

1. A controlled declaration format.
2. Content-addressed semantic meanings.
3. Exact typed prompt slots.
4. Hard compatibility factors.
5. A deterministic bounded solver.
6. Independent candidate reconstruction.
7. Unique-proof or explicit ambiguity behavior.
8. Complete source provenance.
9. Canonical result and replay receipts.
10. Resource limits and causal controls.
11. Evidence that prompt-only semantics cannot enter output.
12. A qualification record before promotion.

The disposable Python-synthesis and Sudoku tests followed this general pattern,
but their temporary primitives were deleted. They are evidence about possible
future directions, not Runtime 4.7 architecture.

---

## 33. Known limitations and research questions

### 33.1 Grounding

- Frozen cosine gates are corpus-calibrated, not formal semantic guarantees.
- Exact instruction envelope matching limits linguistic breadth.
- Candidate ranking is linear scan.
- Multilingual and multimodal adapters are not enabled.

### 33.2 Reasoning

- Relational programs are chain-shaped.
- Programs are linear and single-output.
- No arbitrary conjunction, disjunction, negation, quantification, recursion,
  loops, or high-treewidth CSP execution exists.
- The prompt must select relevant starting meanings; the runtime does not
  discover a proof program from a hypothesis.

### 33.3 Proofs

- Proof identity is an edge sequence.
- Non-edge outputs have limited public proof provenance.
- Independent verification reuses settlement code rather than a fully diverse
  second solver for every operation.

### 33.4 Storage

- Historical generation payloads remain after logical purge.
- Prompts are stored in plaintext in episodes.
- Archives include full dense vectors and source text, increasing storage.
- No built-in encryption or access-control layer exists.

### 33.5 Python

- Static call resolution is approximate.
- Dynamic Python behavior is intentionally omitted.
- Patch plans rely on precompiled replacement fragments.
- No source generation or patch application exists.

### 33.6 Formal verification

The runtime has extensive empirical qualification but no machine-checked proof
in a proof assistant. A stronger research program could formalize:

- canonical compilation;
- uniqueness-count correctness;
- energy dominance;
- structured materialization;
- archive and replay integrity;
- noninterference between prompt episodes and persistent fields.

---

## 34. Core invariants

The architecture can be summarized by these invariants:

1. Every answer meaning existed before the query.
2. Every semantic transition existed before the query.
3. Every accepted slot is typed.
4. Exact aliases and vector candidates cannot cross types.
5. A hard semantic failure cannot be offset by lexical similarity.
6. Directional edges are never silently symmetrized.
7. Multiple semantic proofs refuse.
8. Missing semantic transitions refuse.
9. Structured keys and values are compiled.
10. Python is parsed but never imported or executed.
11. Patch plans are hash-bound and inert.
12. Tool-shaped JSON is inert.
13. Published generations are immutable.
14. Head publication is atomic.
15. Replay is encoder-free and byte-exact.
16. Every public result declares zero external execution and dispatch.

---

## 35. Implementation map

| Subsystem | Primary implementation |
|---|---|
| Immutable semantic contracts | src/moth_runtime/model.py |
| Canonical JSON and hashes | src/moth_runtime/canonical.py |
| Controlled compiler | src/moth_runtime/compiler.py |
| Local BGE encoder | src/moth_runtime/encoder.py |
| Prompt grounding | src/moth_runtime/grounding.py |
| Energy and exact settlement | src/moth_runtime/energy.py |
| Structured values | src/moth_runtime/structure.py |
| Python AST adapter | src/moth_runtime/python_adapter.py |
| Public results | src/moth_runtime/runtime.py |
| Field archives | src/moth_runtime/archive.py |
| Immutable store | src/moth_runtime/store.py |
| Operator CLI | src/moth_runtime/cli.py |

---

## 36. Conclusion

Moth Runtime 4.7 is best understood as a closed-world semantic virtual machine
whose programs, data, relations, schemas, and permitted outputs are compiled
before query time. Dense vectors provide a constrained interface between
ordinary phrasing and compiled identifiers. Exact sparse state provides
authority. The integer energy makes hard validity lexicographically dominant
over grounding preference. Deterministic solvers produce candidates;
independent reconstruction, provenance, hashes, immutable generations, and
canonical replay make those candidates auditable.

The architecture gains reliability by refusing generality. It can perform deep
compiled chains, mixed relations, typed rendering, static code queries, inert
patch planning, and inert tool-shaped output. It cannot learn new semantics
from a prompt or improvise beyond the compiled world. Any future expansion
should preserve that separation: approximate grounding may choose among
compiled meanings, but only exact compiled constraints may determine what is
true and what the runtime is authorized to emit.
