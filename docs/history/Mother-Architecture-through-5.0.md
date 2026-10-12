> Historical snapshot, retained before the Runtime 5.3 family documentation update.
> Its family-wide invariants describe the earlier architecture, not current 5.3 behavior.
> See [the current Mother architecture](../../Mother-Architecture.md).

# Moth Mother Architecture

Status: definitive architecture description for the standalone Moth runtime
family.

This document describes Moth as one system rather than as a sequence of
experiments. Version-specific documents remain the authority for the exact
schemas and implementation details of a particular release. This document is
the authority for the overall product model, invariants, computational
architecture, safety boundary, and extension path.

Moth is a **closed-bounded, proof-carrying, energy-based reasoning runtime**.
It reasons only with meanings, values, facts, instructions, constraints,
programs, and output contracts that have already been compiled into immutable
Worlds. A prompt may select compiled meanings and provide permitted transient
bindings. It may not silently create knowledge, rules, operations, values, or
output semantics.

The architectural objective is not unrestricted text generation. It is a
deterministic reasoning substrate in which a result is released only when the
runtime can construct one admissible zero-violation state and independently
verify the complete computation and provenance that produced it.

---

## 1. Architectural identity

### 1.1 What “closed” means

The persistent semantic universe is fixed by the active compiled World bundle.
Every persistent object must originate in accepted source material and receive
a canonical identifier. The prompt is not a source document. It cannot add a
new fact by asserting one, invent a relation, define an operation, create an
output field, or teach the runtime a procedure.

A prompt can do only the following:

- select an instruction that already exists;
- select already compiled entities, relations, programs, schemas, or tools;
- bind transient inputs to already compiled values;
- request an output contract already licensed by the Worlds.

If any required meaning is absent, ambiguous, mistyped, unsupported, or lacks
provenance, the runtime refuses.

### 1.2 What “bounded” means

Every executable episode has finite declared boundaries:

- finite meaning indexes;
- finite value domains;
- finite factor tables;
- finite programs;
- finite prompt length;
- finite World generations;
- finite settlement sweeps;
- finite proof and trace sizes;
- finite output schemas.

The runtime does not silently truncate a semantic problem to make it fit. A
resource violation is a typed refusal.

### 1.3 What “energy-based” means

An episode is represented as a constrained state. Compiled factors assign
violations or ambiguity to that state. The runtime applies one deterministic,
task-independent settlement law. A result is admissible only at a verified
zero-violation, zero-ambiguity fixed point.

Moth therefore uses energy as an exact semantic contract, not as a metaphor
for neural confidence and not as an approximate score that permits a “best bad
answer.”

### 1.4 What “proof-carrying” means

The answer is only the visible projection of a larger verified record. The
record binds:

- the exact runtime and schema;
- the immutable three-World bundle;
- the grounded instruction and inputs;
- every stage settlement;
- every typed handoff;
- the transient factor construction trace when used;
- the energy coordinates;
- semantic proof or factor witnesses;
- active source provenance;
- canonical input, output, and replay hashes.

The terminal may display only the answer, but the runtime still produces and
stores the full proof-bearing result.

### 1.5 What “general reasoning” means here

Moth’s generality is **mechanism generality inside a compiled boundary**. The
same kernel can operate on arithmetic, graph coloring, scheduling, routing,
permissions, inventory, or another finite domain when those domains are
expressed through compatible compiled meanings and factors.

It does not mean that the current runtime understands arbitrary prose,
discovers an unknown algorithm, searches every possible program, or possesses
open-world knowledge.

---

## 2. Runtime lineage and status

The standalone repository contains independently versioned runtimes.

| Runtime | Architectural role | Status |
|---|---|---|
| 4.7 | Closed-world exact semantic runtime | Qualified and canonical |
| 4.8 | Independent three-World orchestration | Opt-in structural successor |
| 4.9 | Three Worlds plus active compiled factor settlement | Opt-in confirmed candidate |
| 5.0 | Runtime 4.9 plus compiled Input World language fidelity | Opt-in bounded-language successor |

Runtime 4.9 is not implemented by mutating Runtime 4.8. It has an independent
package, configuration, schema domains, store family, archive identities, and
CLI route. Runtime 4.8 remains an immutable historical boundary showing that
compiled instruction names and prose are passive without an execution
substrate.

Runtime selection is explicit:

```sh
moth --runtime 4.7 status
moth --runtime 4.8 status
moth --runtime 4.9 status
moth --runtime 5.0 status
```

An untagged `moth` command is refused. Runtime 4.7 remains canonical until a
separate promotion decision changes that product posture.

---

## 3. End-to-end execution

The complete flow is:

```text
Transient prompt
    |
    v
Closed-world grounding against the Input World index
    |
    v
Verified GroundedProgram
    |
    v
Input World settlement and verification
    |
    v
Hash-bound MAIN_REQUEST
    |
    v
Main World settlement and verification
    |
    v
Hash-bound SEMANTIC_RESULT
    |
    v
Surface World settlement and verification
    |
    v
SURFACE_RESPONSE
    |
    +--> concise terminal value
    |
    +--> complete proof-bearing episode record
```

There are exactly three World settlements. The outer runtime coordinates them
but performs no hidden fourth reasoning step.

Grounding happens once, before Input World settlement. Main and Surface never
receive raw prompt text and never re-ground a textual handoff.

---

## 4. Persistent state and transient state

### 4.1 Persistent compiled state

An immutable World generation may contain:

- canonical entities and symbols;
- directional relations and exact premises;
- numerals and scalar values;
- aliases and instruction envelopes;
- operation identifiers;
- structured output schemas and fields;
- relation sequences and exact programs;
- finite domains;
- factor templates and allowed tuples;
- one immutable meaning per program step;
- dense grounding vectors;
- source documents, spans, and ownership records.

Persistent state is content-addressed and published only as a complete valid
generation.

### 4.2 Transient episode state

Transient state includes:

- raw and normalized prompt text;
- prompt hashes;
- grounding scores and selected identifiers;
- typed bindings;
- transient factor variables and instances;
- current variable domains;
- factor port couplings;
- domain reductions;
- candidate fixed points;
- stage and handoff receipts.

No transient value becomes a persistent meaning. A query cannot train or
extend the field. Audit storage may retain an episode, but audit records are
excluded from future grounding and compilation.

---

## 5. Canonical meanings

Every meaning is typed and content-addressed. Conceptually:

\[
id(m)=\operatorname{SHA256}
(\text{runtime domain}\parallel\text{meaning type}\parallel
\text{canonical payload})
\]

The identifier does not depend on a SQLite row number, compilation timestamp,
filesystem path, or source ordering.

Runtime 4.9 includes the established semantic types and adds:

- `FINITE_DOMAIN`;
- `FACTOR_TEMPLATE`.

Factor programs remain typed `PROGRAM` meanings marked with
`program_kind = FACTOR`. Each instruction becomes a `PROGRAM_STEP` meaning so
the runtime can identify the exact compiled statement that licensed every
transient effect.

### 5.1 Provenance ownership

Every compiled meaning has one or more provenance owners. An owner records:

- source identifier and source SHA-256;
- normalized statement SHA-256;
- byte and character span;
- line and column;
- compiler version.

Identical semantic content from multiple sources produces one meaning with
multiple owners, not multiple meanings. Removing one source preserves the
meaning while another active owner remains.

---

## 6. Compilation contract

Compilation is staged and atomic:

1. Normalize source text.
2. Parse declarations into a typed syntax tree.
3. Declare canonical meanings.
4. Resolve every reference.
5. Validate types, limits, topology, and provenance.
6. Materialize vectors and exact semantic structures.
7. Compute generation and asset hashes.
8. Publish an immutable generation atomically.

An unresolved, ambiguous, mistyped, unsupported, or oversized declaration
rejects the complete staged generation. There is no partially published World.

### 6.1 Finite domains

A finite domain is an ordered set of already compiled values:

\[
D=\{v_1,v_2,\ldots,v_n\},\qquad 1\le n\le256
\]

Every member must be a compiled `VALUE` or `ENUM_MEMBER`. All members share one
scalar type. A domain does not contain raw prompt strings.

### 6.2 Factor templates

A factor template is:

\[
F=(P,\tau,T)
\]

where:

- \(P=(p_1,\ldots,p_k)\) is an ordered port list;
- \(\tau(p_i)\) is the finite domain assigned to port \(p_i\);
- \(T\subseteq\tau(p_1)\times\cdots\times\tau(p_k)\) is the set of allowed tuples.

Every tuple has exactly the declared arity. Every tuple value belongs to its
port’s domain. Duplicate tuples and duplicate ports are rejected.

The template is domain data. Runtime code has no knowledge of whether a table
represents addition, inequality, precedence, permissions, or another relation.

---

## 7. Dense grounding layer

Dense vectors provide closed-world selection, not truth and not reasoning.

For a compiled surface \(t_m\), the encoder produces:

\[
v_m=\frac{f_\theta(t_m)}{\|f_\theta(t_m)\|_2}
\]

Grounding follows this order:

1. Normalize Unicode and whitespace.
2. Enforce prompt resource limits.
3. Match compiled instruction envelopes.
4. Extract typed spans.
5. Resolve exact canonical names.
6. Resolve exact aliases.
7. Use dense similarity only for an unresolved span of a known required type.
8. Quantize scores and apply frozen score and margin gates.
9. Bind a complete `GroundedProgram` or return a typed refusal.

For candidate cosine scores \(s_i\), vector grounding accepts only if:

\[
s_{(1)}>\theta_\tau
\quad\land\quad
s_{(1)}-s_{(2)}>\delta_\tau
\]

Equality at either threshold refuses. Candidate comparison is limited to the
required semantic type.

The prompt cannot use similarity to introduce a new value. A paraphrase works
only when it resolves confidently to one compiled meaning.

---

## 8. The three Worlds

### 8.1 Input World

The Input World owns the grounding-facing vocabulary and compiled instruction
interface. It receives a verified `GroundedProgram`, not an unstructured task
to solve.

It verifies:

- selected instruction identity;
- operation compatibility;
- typed slot identities;
- transient field-to-value bindings;
- program identity;
- requested output contract;
- active bundle and generation identity.

Its successful output is a typed, identifier-only `MAIN_REQUEST`. Input does
not solve domain constraints.

### 8.2 Main World

The Main World is responsible for semantic truth and reasoning. Legacy exact
operations retain their established paths, including lookup, directional
relation execution, compiled JSON, inert tool-shaped output, code relations,
and inert patch planning.

When the selected operation is `FACTOR_SETTLEMENT`, Main:

1. verifies the selected program is a compiled factor program;
2. starts with an empty transient field;
3. executes the compiled construction instructions;
4. applies compiled clamps;
5. settles the factor field;
6. independently verifies the candidate;
7. emits a `SEMANTIC_RESULT`.

### 8.3 Surface World

The Surface World receives only the independently verified semantic result. It
does not see the raw prompt and cannot change the answer’s meaning.

It may realize a compiled string, scalar, object, array, code value, patch plan,
or other licensed output. It cannot add claims, manufacture a value, suppress
a refusal, dispatch a tool, or execute code.

---

## 9. Bundles and typed handoffs

A query never combines arbitrary current World heads. An immutable bundle
atomically binds exactly one Input, Main, and Surface generation.

A handoff contains, conceptually:

```text
schema
bundle_id
source_role
target_role
source_generation_id
target_generation_id
payload_kind
typed payload
source_settlement_hash
provenance_hash
handoff_hash
```

Only `INPUT -> MAIN` and `MAIN -> SURFACE` are legal. The target verifies every
identifier against its bound generation. Any changed role, payload, generation,
settlement, provenance, or hash fails closed.

---

## 10. Active compiled instruction settlement

Runtime 4.8 established the critical negative boundary: storing an instruction
name, description, or program-shaped payload does not execute it. Passive
semantic memories cannot create working variables or propagate consequences.

Runtime 4.9 introduces a small active language with six generic opcodes.

### 10.1 `CREATE_VARIABLE`

Creates one transient variable with one compiled finite domain. The variable
begins with the complete domain. The instruction cannot provide an answer.

### 10.2 `INSTANTIATE_FACTOR`

Creates one transient instance of a compiled factor template, bound to the
active immutable generation.

### 10.3 `BIND_PORT`

Connects one factor port to one transient variable of exactly the required
domain. Binding the same variable to ports on multiple factors creates shared
state and therefore causal coupling.

### 10.4 `CLAMP_FROM_PROMPT`

Reduces a variable to a singleton value selected from a verified prompt
binding. Both the field and value must already be compiled and type-compatible.

### 10.5 `CLAMP_LITERAL`

Reduces a variable to a singleton value explicitly selected by the compiled
program. This represents constants such as an initial carry value.

### 10.6 `EXPOSE_OUTPUT`

Selects an existing transient variable as part of the compiled output contract.
The instruction supplies a canonical ordinal and label, not a result value.

These opcodes can construct a field. They do not implement any domain-specific
algorithm.

---

## 11. Transient field materialization

The field begins empty. Program steps execute in immutable canonical order.
Every step produces an effect receipt containing its instruction-step meaning
identifier and the identifiers of the transient and persistent objects it
affected.

Static compilation guarantees:

- declaration before use;
- no duplicate variable or factor instance;
- domain-compatible port bindings;
- exactly one binding for every required port;
- compiled prompt fields and literals;
- valid, contiguous output ordinals;
- frozen resource limits.

Materialization creates no persistent meanings. Transient identifiers are
content-addressed from the program, step index, instance name, domain or
template, and generation context.

---

## 12. Settlement law

Let \(D_v\) be the current domain of transient variable \(v\). Initially,
\(D_v\) equals the complete compiled finite domain. Clamps reduce selected
domains to singleton values.

For each factor instance \(f\), let \(T_f\) be its compiled allowed tuples and
let \(b_f(p)\) identify the variable bound to port \(p\).

A tuple \(t\in T_f\) is compatible with the current state when:

\[
\forall p\in P_f:\quad t[p]\in D_{b_f(p)}
\]

The compatible tuple set is:

\[
C_f(D)=\{t\in T_f\mid
\forall p\in P_f, t[p]\in D_{b_f(p)}\}
\]

If \(C_f(D)=\varnothing\), the state contradicts a compiled factor and
settlement returns `UNSATISFIABLE`.

For each port, its supported values are:

\[
S_{f,p}(D)=\{t[p]\mid t\in C_f(D)\}
\]

The update is:

\[
D_{b_f(p)}\leftarrow D_{b_f(p)}\cap S_{f,p}(D)
\]

Factors are visited in canonical creation order. Ports are visited in compiled
order. Every strict reduction is recorded. Sweeps repeat until no domain
changes.

This is deterministic search-free table-factor domain narrowing. It contains
no branch selection, backtracking, exhaustive enumeration, stochastic restart,
target-aware heuristic, task-specific propagation, LLM, or query-time learner.

---

## 13. Scalar energy

Remaining ambiguity is:

\[
A(D)=\sum_v(|D_v|-1)
\]

The maximum ambiguity for the materialized field is:

\[
A_{max}=\sum_v(|D^{full}_v|-1)
\]

The hard-dominance multiplier is:

\[
M=A_{max}+1
\]

The violation count is:

\[
V(D)=\#\{f\mid C_f(D)=\varnothing\}
\]

The factor energy is:

\[
E(D)=M\,V(D)+A(D)
\]

One hard violation therefore costs more than the largest possible reduction in
ambiguity. The runtime never returns the least-invalid candidate.

A successful field requires:

\[
V(D^*)=0,qquad A(D^*)=0
\]

Consequently every created variable—not merely every exposed output—must be a
singleton, and every factor must have one compatible singleton witness tuple.

If a fixed point has no violation but retains a non-singleton domain, the
runtime returns `AMBIGUOUS_SETTLEMENT`. It does not guess or search.

The three Worlds keep separate stage energies. They are not combined into a
misleading single score.

---

## 14. Independent verification

The settlement engine cannot certify itself. A separate verifier receives the
compiled World, grounded program, candidate output, and factor evidence.

It independently:

1. Resolves the factor program and every step meaning.
2. Reconstructs variables and complete domains.
3. Reconstructs factor instances and port bindings.
4. Reapplies prompt and literal clamps.
5. Reconstructs exposed outputs.
6. Recomputes the canonical reduction sequence.
7. Replays and validates every reported reduction.
8. Proves the reported final state is a fixed point.
9. Requires every created domain to be singleton.
10. Recomputes one compatible witness tuple for every factor.
11. Recomputes the output values.
12. Recomputes scalar energy.
13. Expands and validates active provenance.
14. Verifies generation and trace hashes.

It rejects unlicensed variables, absent factors, altered bindings, changed
clamps, skipped or reordered reductions, invalid tuples, unresolved outputs,
false uniqueness, changed energy, missing provenance, changed generation, and
receipt corruption.

---

## 15. Proof model

Legacy relation programs carry ordered semantic edge proofs. Factor programs
carry a computation proof consisting of:

- the selected compiled program;
- ordered instruction-effect receipts;
- materialized variable and factor identifiers;
- port-binding receipts;
- prompt and literal clamp receipts;
- ordered domain reductions;
- final singleton domains;
- one allowed-tuple witness per factor;
- exposed output bindings;
- scalar energy coordinates;
- complete active provenance;
- a canonical trace hash.

The proof explains both **what answer was produced** and **which compiled
instructions and constraints caused it**.

---

## 16. Refusal model

Refusal is a normal safe result, not a degraded answer.

Grounding refusals include unknown entities, unsupported relations or
instructions, unknown values, unsupported output contracts, and ambiguous
grounding.

Program refusals include unsupported operations, incompatible programs,
missing bindings, and unsupported topology.

Factor refusals include:

- `MISSING_FACTOR`;
- `UNBOUND_PORT`;
- `MISSING_BINDING`;
- `UNSATISFIABLE`;
- `AMBIGUOUS_SETTLEMENT`.

Integrity refusals cover corrupted generations, provenance, settlements,
handoffs, stores, traces, and replay receipts. Resource refusals cover frozen
limits. Refusals contain no speculative answer or unverified proof.

---

## 17. Storage and immutable publication

Each runtime has an independent SQLite store family. Runtime 4.9 uses a store
containing:

- the runtime descriptor;
- immutable World generations;
- separate nullable Input, Main, and Surface heads;
- immutable three-World bundles;
- one nullable active bundle head;
- episodes;
- stage receipts;
- handoff receipts;
- replay data;
- export and purge receipts.

Publication compiles and validates outside the publication transaction, then
uses an immediate transaction and compare-and-swap head check. Existing
generations and bundles are never rewritten.

The delivered Runtime 4.9 production store is intentionally empty:

```text
Input head: null
Main head: null
Surface head: null
Active bundle: null
Generations: 0
Bundles: 0
Episodes: 0
```

Experimental and qualified content must be compiled into separate stores until
an explicit product decision publishes canonical Worlds.

---

## 18. Replay

Encoder-free replay does not re-answer the prompt. It verifies and reconstructs
the archived episode.

Replay verifies:

1. canonical result bytes and result SHA-256;
2. the selected immutable bundle;
3. all three archived World generations;
4. the grounded program record;
5. successful stage settlements;
6. both typed handoffs;
7. factor materialization and reduction traces when present;
8. proofs, witnesses, provenance, and energy;
9. output and receipt commitments.

It returns the original result bytes unchanged without loading the encoder.
Replay never modifies a World head, bundle, source, meaning, or episode.

---

## 19. Terminal and API presentation

The Python API and `--json` interface expose the complete proof-bearing result.
The default terminal renderer displays only the actual response:

- identity results become their canonical names;
- strings become plain text;
- structured values become compact canonical JSON;
- refusals become `CODE: message`.

Concise presentation is a view-layer decision. It does not remove proof,
energy, provenance, episode, or replay evidence.

---

## 20. Safety and non-capabilities

The runtime does not:

- execute generated Python;
- apply patch plans;
- dispatch tool-call-shaped JSON;
- open network connections as part of settlement;
- import a compiled codebase;
- learn from a prompt;
- persist prompt assertions as facts;
- use an LLM to fill missing semantics;
- silently coerce an unknown value;
- return a partially valid state;
- search when domain narrowing is ambiguous.

Compiled Python inspection and patch-plan production remain static and inert.
Tool-shaped output is data, not an executed call.

---

## 21. Frozen Runtime 4.9 limits

The current factor path freezes these primary limits:

| Resource | Limit |
|---|---:|
| Prompt | 128 tokens |
| Meanings per generation | 50,000 |
| Semantic edges | 250,000 |
| Factor variables | 1,024 |
| Factor instances | 4,096 |
| Ports per factor | 16 |
| Allowed tuples per template | 4,096 |
| Values per finite domain | 256 |
| Factor instructions | 16,384 |
| Aggregate tuple-port cells | 16,777,216 |
| Settlement sweeps | 1,024 |
| Factor trace | 64 MiB |

Limits are verified during compilation, materialization, settlement, and
replay as applicable.

---

## 22. Evidence and established boundaries

### 22.1 Runtime 4.7

Runtime 4.7 established exact closed-world grounding, directional compiled
relations, proof-carrying JSON, inert tool and patch outputs, immutable stores,
typed refusals, and exact replay. Disposable campaigns confirmed its frozen
capability corpus and projected linear ProofWriter boundary.

### 22.2 Runtime 4.8

Runtime 4.8 established the three-World pipeline and the boundary between
passive compiled instruction descriptions and executable computation.
Field-only decimal addition and Sudoku audits decisively showed that adding
more instruction names does not create settlement dynamics.

### 22.3 Runtime 4.9

Runtime 4.9 confirmed active structured factor settlement with:

- 8/8 full-adder truth-table cases;
- 7/7 unseen multi-bit additions;
- 4-, 8-, and 16-bit carry chains;
- graph-color propagation;
- a small scheduling constraint field;
- correct ambiguous and unsatisfiable refusals;
- forged-trace rejection;
- a complete three-World cascade;
- offline real-BGE grounding smoke evidence;
- byte-exact encoder-free replay.

Further disposable evidence confirms meta-reasoning within a frozen factor
boundary. A separate real-world prompt audit confirms the current language
boundary: ordinary narrative prompts do not yet compile themselves into the
typed transient facts required by factor programs.

---

## 23. Exact capability claim

The strongest supported claim is:

> Moth Runtime 4.9 is a programmable closed-world reasoning substrate in which
> structured compiled instructions can construct transient finite-domain factor
> fields, and a generic deterministic energy settlement law can derive and
> independently verify unique results across multiple compiled domains.

This is meaningful because changing from addition to coloring or scheduling
changes compiled values, tables, and programs—not the runtime settlement code.

It is not evidence of:

- unrestricted general reasoning;
- open-world knowledge;
- natural-language program induction;
- LLM-level language fidelity;
- search-complete SAT/CSP reasoning;
- arbitrary cyclic constraint solution;
- unconstrained code generation;
- human- or engine-level chess;
- AGI.

---

## 24. Adding a new domain

A domain expressible by the current substrate is added without changing the
factor kernel:

1. Compile scalar types and values.
2. Compile finite domains.
3. Compile domain facts and exact relations where needed.
4. Compile allowed-tuple factor templates.
5. Compile a structured factor-construction program.
6. Compile instruction envelopes and aliases.
7. Compile output schemas and Surface realizers.
8. Publish compatible Input, Main, and Surface generations.
9. Activate one immutable bundle.
10. Qualify unseen cases, causal removals, corruptions, invariance, provenance,
    and exact replay.

If a domain requires branching search, optimization, continuous variables,
dynamic topology, or an unsupported computation model, it is outside Runtime
4.9 and must refuse rather than hiding a domain-specific solver in runtime
code.

---

## 25. Future architecture direction

### 25.1 Reusable instruction compression

The first objective is to precompile reusable reasoning vocabulary so each new
domain does not restate generic notions such as variable creation, equality,
inequality, conjunction, contradiction, completion, proof, and verification.
New work should then contribute primarily domain meanings, facts, schemas, and
factor tables.

Compression must preserve exact execution and provenance. It must not turn
underspecified prose into an unverified program.

### 25.2 Language fidelity

The Input World needs broader but still safe language fidelity: multiple
surface forms should resolve to the same compiled typed request. The current
real-world prompt boundary shows that this is not solved merely by increasing
factor capability.

Language fidelity must remain separate from semantic truth. A language layer
may normalize or select compiled meanings, but it may not invent a missing
fact or program.

### 25.3 Multi-domain reasoning

The next major evidence target is an unseen query whose unique fixed point
requires factors from several independently compiled domains—for example
people and roles, permissions, inventory, scheduling, and routing—using the
same frozen kernel.

Every answer must identify the required factors and premises from each domain.
Removing any causally necessary component must eliminate the answer or produce
the applicable refusal.

### 25.4 Later computation substrates

Search, optimization, recursion, continuous energy, or other computation laws
would be separate architectural additions. Each must be generic,
task-independent, independently verified, resource-bounded, and qualified
across unrelated domains before becoming part of the Mother Architecture.

---

## 26. Architectural invariants

The following invariants define Moth regardless of later version:

1. Persistent semantics originate only from compiled sources.
2. Prompts remain transient and cannot add knowledge.
3. Dense vectors select meanings but do not determine truth.
4. Exact typed state and constraints determine admissibility.
5. World generations are immutable and content-addressed.
6. One bundle fixes all World generations for an episode.
7. Inter-World handoffs are typed, hash-bound, and never re-grounded text.
8. Every accepted result has one independently verified admissible state.
9. Hard violations cannot be traded for a better soft score.
10. Every computation step is licensed by compiled instructions.
11. Every proof component has active source provenance.
12. Unsupported or ambiguous requests refuse.
13. Replay is exact and does not require the encoder.
14. Runtime execution, tool dispatch, and persistent mutation are separate
    capabilities and remain disabled unless explicitly architected and
    qualified.
15. A new domain must not require hidden task-specific reasoning code when it
    claims to use a general substrate.

These invariants are the stable center of Moth. Runtime versions may expand the
set of compiled structures or settlement laws, but they must not weaken the
closed-world, proof-carrying, independently verified contract.
