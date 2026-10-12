# Moth Runtime 4.8 Architecture

Status: implemented, independent, opt-in, unqualified, and not canonical.

Runtime 4.7 remains the qualified canonical runtime. Runtime 4.8 does not
import, migrate, modify, or replace Runtime 4.7. It adds a three-World execution
pipeline while retaining Moth's closed-world, proof-carrying semantics.

The delivered Runtime 4.8 production store is intentionally empty. Runtime 4.8
can execute populated disposable or user-compiled Worlds, but the production
store cannot answer until compatible Input, Main, and Surface World generations
are compiled and activated together.

## 1. System overview

Runtime 4.8 processes a query in one fixed order:

```text
Transient prompt
    |
    v
Pre-World grounding against Input World meanings
    |
    v
Input World settlement and independent verification
    |
    v
Typed INPUT -> MAIN handoff
    |
    v
Main World settlement and independent verification
    |
    v
Typed MAIN -> SURFACE handoff
    |
    v
Surface World settlement and independent verification
    |
    v
Final response
```

The Worlds are not agents, services, models, or separate processes. They are
three independently compiled immutable fields executed by one orchestrator.
All three use Runtime 4.8's compiler, canonical data model, integer energy
contract, verifier, provenance model, and archive format.

The orchestrator only routes verified typed values. It does not perform a
fourth settlement, add knowledge, re-ground handoff text, or rewrite answers.

## 2. Isolation and identities

Runtime 4.8 lives under:

```text
src/moth_runtime_v4_8/   independent Runtime 4.8 implementation
src/moth_launcher/       neutral runtime selector
config/v4.8/             Runtime 4.8 descriptors
docs/v4.8/               Runtime 4.8 documentation
data/store-4.8.sqlite3   ignored production store
```

Runtime 4.7 remains under `src/moth_runtime/` with its own configuration,
schemas, identifiers, replay format, and store.

Runtime 4.8 uses these public identities:

| Contract | Identity |
|---|---|
| Runtime | `4.8` |
| Store | `proof-energy-world-store/4.8` |
| World archive | `proof-energy-world-archive/4.8` |
| Bundle | `moth-world-bundle/4.8` |
| Handoff | `moth-world-handoff/4.8` |
| Result | `moth-world-result/4.8` |
| Default store | `data/store-4.8.sqlite3` |

Runtime 4.8 refuses Runtime 4.7 stores, archives, bundles, handoffs, and
results. Both runtimes may read the same local BGE model files, but their code
and persistent semantic assets remain independent.

## 3. Core invariants

1. Grounding finishes before Input settlement begins.
2. Grounding candidates come only from the active Input World.
3. The prompt remains transient and is never compiled into a World.
4. Main and Surface never receive or re-ground the raw prompt.
5. Only `INPUT -> MAIN` and `MAIN -> SURFACE` handoffs are legal.
6. One immutable bundle fixes all three World generations for an episode.
7. Each completed stage requires one zero-violation state, proof count one,
   independent verification, and active provenance.
8. Main alone establishes domain truth and the semantic answer.
9. Surface may realize the semantic answer but may not change it.
10. A refusal or integrity failure stops all downstream stages.
11. Queries cannot mutate Worlds, bundles, or compiled knowledge.
12. Python execution, patch application, tool dispatch, network actions, and
    query-time learning remain absent.

## 4. Compiled World representation

`WorldRole` has exactly three values:

```text
INPUT
MAIN
SURFACE
```

A generation is bound to one role. The role participates in archive checks,
store rows, generation hashes, bundle position, and handoff validation.

An immutable `CompiledWorld` contains:

- normalized sources and source hashes;
- typed meanings and content-addressed meaning identifiers;
- canonical-name and alias indexes;
- normalized dense grounding vectors;
- exact directional semantic edges;
- operations, instructions, prototypes, relation forms, programs, and schemas;
- complete meaning and edge provenance;
- compiler and encoder fingerprints;
- World hash, generation ID, capability level, and World role.

Implemented meaning types are:

```text
ENTITY, RELATION, NUMERAL, OPERATION, INSTRUCTION,
INSTRUCTION_PROTOTYPE, RELATION_FORM, OUTPUT_SCHEMA, ALIAS,
SCALAR_TYPE, VALUE, ENUM_MEMBER, LIST_VALUE, STRUCTURED_SCHEMA,
SCHEMA_FIELD, RELATION_SEQUENCE, PROGRAM, PROGRAM_STEP, TOOL,
TOOL_ARGUMENT, CODE_FILE, CODE_SYMBOL, CODE_SPAN, TEXT_FRAGMENT,
PATCH_TEMPLATE
```

The representation has four coordinated layers:

- **Grounding layer:** names, aliases, instruction envelopes, prototypes, and
  dense vectors select already compiled meanings.
- **Semantic layer:** exact typed meanings and directional edges determine
  truth.
- **Program layer:** compiled operations, programs, types, and schemas determine
  legal computation and output.
- **Provenance layer:** source owners and exact spans license every meaning and
  edge used by a proof.

Dense similarity never creates a fact, operation, schema, value, or proof.

### 4.1 Directional semantic edges

A semantic edge is:

\[
e=(r,s,d),
\]

where `r` is a compiled relation ID, `s` is a source meaning ID, and `d` is a
destination meaning ID. Direction is exact: `(r,s,d)` and `(r,d,s)` are
different edges.

Several source statements may own the same edge. That produces one semantic
edge with several provenance owners, not several semantic proofs.

### 4.2 Dense vectors

Groundable meanings may store normalized 1024-dimensional `float32` vectors
from the pinned local `BAAI/bge-large-en-v1.5` encoder. Passage vectors are
compiled into a World; query vectors are transient.

Every vector is bound to its meaning ID, grounding text, vector hash, and
encoder fingerprint. Archive verification checks membership, dimension,
finiteness, canonical `float32` bytes, and hashes.

### 4.3 Provenance

Every meaning and edge has at least one owner containing:

```text
source ID and SHA-256
statement SHA-256
character start/end
UTF-8 byte start/end
line and column
compiler version
```

Archive verification reconstructs each source span and verifies every offset
and hash.

## 5. Canonical encoding and hashing

All persisted and hashable values use canonical JSON:

- UTF-8;
- sorted object keys;
- no insignificant whitespace;
- normalized Unicode text;
- deterministic ordering;
- finite numbers only.

The content-addressing rule is:

\[
\operatorname{digest}(d,x)=
\operatorname{SHA256}(\operatorname{UTF8}(d)\parallel 0x00\parallel
\operatorname{CanonicalJSON}(x)).
\]

Runtime 4.8 has separate domains for meanings, edges, compiler state, Worlds,
generations, archives, interfaces, bundles, settlements, provenance, handoffs,
query inputs, episodes, and semantic results. Meaning IDs therefore depend on
the runtime, meaning type, and canonical payload—not source order, database row
number, filesystem iteration, or compilation time.

## 6. Compilation

Each World is compiled separately from controlled `.moth` sources.

The deterministic compiler:

1. Normalizes line endings and validates UTF-8.
2. Ignores blank lines and `#` comments.
3. Requires one supported period-terminated statement per logical line.
4. Captures exact source and statement provenance.
5. Declares base meanings.
6. Resolves dependent values, schemas, interfaces, programs, tools, and aliases.
7. Resolves relation premises after all referenced meanings exist.
8. Optionally compiles static Python AST data without importing or executing it.
9. Enforces type, schema, cardinality, program, and resource rules.
10. Encodes eligible grounding surfaces.
11. Canonically orders all semantic assets.
12. Computes compiler, vector, World, generation, and archive hashes.
13. Produces one immutable role-bound World archive.

Compilation is all-or-nothing. Unsupported language, unresolved references,
ambiguous forms, invalid schemas, illegal operations, or broken provenance
prevent publication.

Implemented kernel primitives are:

```text
LOOKUP
CHAIN_ADVANCE
RELATION_SEQUENCE
VALIDATE_STRUCTURE
RENDER_COMPILED_JSON
LINEAR_PIPELINE
CODE_RELATION_QUERY
BUILD_PATCH_PLAN
REALIZE_SEMANTIC_RESULT
```

Programs contain at most 16 linear steps. Loops, branches, recursive pipelines,
and query-time program discovery are unsupported. Relation depth is limited to
50. A World is limited to 50,000 meanings, 250,000 edges, 10,000 sources,
16 MiB per source, and 1 GiB total source payload.

Patch plans remain inert. Runtime 4.8 validates compiled files, spans,
replacement fragments, edit overlap, and an in-memory parse result, but never
writes the patch to a repository.

## 7. World heads and atomic bundles

The store maintains independent nullable heads for Input, Main, and Surface.
A query does not read those moving heads. It reads one immutable bundle:

```text
WorldBundle {
  schema,
  bundle_id,
  input_generation_id,
  main_generation_id,
  surface_generation_id,
  interface_hash,
  bundle_hash
}
```

Activation requires:

1. One current generation for every role.
2. Canonical and role-correct archives.
3. An identical Input-to-Main interface for every Input instruction: instruction
   ID, operation ID, primitive, and typed slot set.
4. Every transferable Input meaning to exist in Main under the same ID and
   meaning type.
5. Exactly one Surface `REALIZE_SEMANTIC_RESULT` operation and exactly one
   instruction selecting it.
6. Exact reconstruction of the interface, bundle, and bundle ID hashes.

Surface does not need copies of Main's domain meanings. It consumes only a
verified `SEMANTIC_RESULT`.

Activation snapshots the three heads, validates outside the publication
transaction, then starts `BEGIN IMMEDIATE` and compares the heads again. A
concurrent change or failed check rolls back and leaves the prior active bundle
unchanged. Publishing a new World does not affect queries until a new compatible
bundle is activated.

## 8. Pre-World grounding

Grounding is separate from Input settlement. The active Input World supplies
its instruction, name, alias, and vector indexes.

The grounder:

1. Accepts only the text modality.
2. Normalizes Unicode and whitespace.
3. Enforces the 128-token limit.
4. Matches compiled instruction envelopes and prototypes.
5. Extracts typed slots.
6. Resolves exact canonical names and aliases first.
7. Resolves structured data only through compiled `field = value` bindings.
8. Uses dense similarity only for unresolved spans of the required type.
9. Returns one complete `GroundedProgram` or a typed refusal.

For query span `q` and compiled candidate vector `v_i`:

\[
s_i=\operatorname{round}(\hat q^\top v_i,6).
\]

The top score and top-two margin must both strictly pass their frozen gates;
equality refuses. Vector grounding cost is:

\[
c(s)=\operatorname{round}
\left(10^6\frac{1-\operatorname{clip}(s,-1,1)}{2}\right).
\]

Exact matches cost zero. A `GroundedProgram` records instruction and operation
IDs, primitive, typed slot IDs, compiled value bindings, selected program steps,
grounding cost, and grounding evidence.

The grounder runs exactly once. Main and Surface never call it.

## 9. Input World

Input receives the verified `GroundedProgram`. It validates and projects the
request through the activation-frozen Input-to-Main interface.

Input uses a role-specific contract settlement; it does not execute Main's
domain `settle()` path. It verifies:

- instruction ID, operation ID, primitive, and slot set;
- every selected Input identifier and type;
- the same identifier and type in Main;
- compiled program-step agreement when a `PROGRAM` is selected.

It settles to an ID-only payload:

```text
MAIN_REQUEST {
  schema,
  interface_id,
  instruction_id,
  operation_id,
  primitive,
  slots: {slot_name: meaning_id},
  bindings: {schema_field_id: compiled_value_id}
}
```

The request contains no prompt text, names, aliases, grounding evidence,
source statements, or serialized program steps. Main reloads steps from its
own immutable `PROGRAM` meaning.

Input therefore performs compiled request transformation—not prompt grounding,
domain reasoning, or answer generation.

## 10. Main World

The verified Input settlement becomes an `INPUT -> MAIN` handoff. Main resolves
the exact interface and reconstructs a `GroundedProgram` only from request IDs.

Main owns domain truth. It executes the selected exact primitive over Main's
compiled semantic state.

For a start state `x_0` and relation sequence `r_1,...,r_n`:

\[
x_t\in R_{r_t}(x_{t-1}),\qquad t=1,\ldots,n.
\]

The deterministic dynamic program carries ordered edge IDs and a proof count
saturated at two. Missing transitions return `MISSING_PREMISE`; more than one
semantic path returns `AMBIGUOUS_PROOF`. Canonical ordering makes execution
deterministic but never chooses between ambiguous proofs.

Structured rendering uses only compiled schemas, fields, and values. Static
code queries use only compiled code meanings and edges. Inert patch plans use
only compiled targets, hashes, operations, and fragments.

Main settles to:

```text
SEMANTIC_RESULT {
  semantic_kind,
  value,
  proof_ids,
  proof_count,
  source_generation_id
}
```

This is the authoritative semantic answer.

## 11. Surface World

The verified Main settlement becomes a `MAIN -> SURFACE` handoff. Surface
receives only `SEMANTIC_RESULT`; it never receives the prompt or performs domain
reasoning.

The current Surface World must contain exactly one compiled
`REALIZE_SEMANTIC_RESULT` operation and one instruction selecting it. The
realizer:

1. Verifies the semantic payload shape, proof count, source generation, and
   semantic-result hash.
2. Preserves the semantic kind.
3. Preserves the semantic value under canonical JSON.
4. Emits `SURFACE_RESPONSE {kind, value, semantic_result_hash}`.
5. Independently reconstructs that response.

The orchestrator then checks again that Surface kind and canonical value equal
Main kind and canonical value.

The implemented Surface is therefore a semantic-preserving bridge. It is not
yet a free language generator. Compiled vocabulary, grammar, style, and output-
length behavior are future Surface contents and are not claimed here.

## 12. Scalar energy and verification

Every stage uses the integer energy contract:

\[
E_w(y_w)=(K_w+1)Q\,V_w(y_w)+C_w(y_w),
\qquad Q=1{,}000{,}000.
\]

- `K_w` is the number of grounded slots and structured bindings.
- `V_w` is the number of hard-factor violations.
- `C_w` is quantized grounding cost.
- `y_w` is the complete state for the role's contract.

One violation costs more than every grounding improvement available to that
state. A stage advances only when `V_w=0` and proof count is exactly one.

The coordinates remain separate:

- Input carries pre-World grounding cost and certifies request projection.
- Main adds no new vector cost and certifies domain semantics and proof.
- Surface has no vector-grounded slots and certifies semantic preservation.

Solver output never self-certifies. Main and Surface rerun kernel settlement
during verification; Input's projection is independently reconstructed. The
verifier checks bundle and generation identity, types, program compatibility,
hard factors, energy, proof, provenance, output kind, output bytes, and every
role-specific rule.

Forged output, proof, energy, provenance, generation, bundle, interface, role,
or hash produces `INTEGRITY_FAILURE` and stops the cascade.

## 13. Stage receipts and handoffs

Every completed stage emits:

```text
WorldStageReceipt {
  role,
  bundle_id,
  generation_id,
  world_hash,
  input_hash,
  settlement_hash,
  provenance_hash,
  output_kind,
  output_hash,
  total_energy_units,
  violation_count,
  proof_count,
  verified
}
```

The input hash binds the bundle and typed program. The provenance hash binds
owners of selected meanings and proof edges. A receipt authorizes a handoff only
when its role, bundle, generation, World hash, settlement, provenance, energy,
violation count, and proof count all verify.

The canonical handoff is:

```text
WorldHandoff {
  schema,
  bundle_id,
  source_role,
  target_role,
  source_generation_id,
  target_generation_id,
  payload_kind,
  payload,
  source_settlement_hash,
  provenance_hash,
  handoff_hash
}
```

The only legal transitions are:

| Source | Target | Payload |
|---|---|---|
| `INPUT` | `MAIN` | `MAIN_REQUEST` |
| `MAIN` | `SURFACE` | `SEMANTIC_RESULT` |

The handoff hash covers every other handoff field. Changed roles, generations,
payload, bundle, settlement, provenance, encoding, or hash fail closed. There
is no reverse, bypass, direct Input-to-Surface, or textual handoff path.

## 14. End-to-end orchestration and failure behavior

A successful query performs:

1. Load and verify the active bundle and three archives.
2. Ground the normalized transient prompt once against Input.
3. Settle and verify Input.
4. Create and verify `MAIN_REQUEST` handoff.
5. Reconstruct, settle, and verify Main.
6. Create and verify `SEMANTIC_RESULT` handoff.
7. Reconstruct, settle, and verify Surface.
8. Verify exact Main-to-Surface semantic preservation.
9. Construct and hash the complete result.
10. Reconstruct all evidence again before persistence.
11. Atomically store the episode and receipt ledgers.
12. Present only the verified Surface value by default.

Failure short-circuits exactly:

- Grounding failure: no World stage.
- Input failure: no handoff and no downstream stage.
- Main failure: only verified Input evidence and its handoff remain.
- Surface failure: verified Input and Main evidence remains, but no answer.
- Store or bundle integrity failure: runtime-level refusal before episode
  persistence.

A refusal is never passed downstream as a semantic answer.

## 15. Result contract

An `ANSWER` under `moth-world-result/4.8` records:

- runtime, episode, bundle, and three World identities;
- pre-World grounding evidence;
- ordered Input, Main, and Surface programs, settlements, proofs, energies,
  provenance, and receipts;
- both handoffs;
- final output copied only from verified Surface;
- `execution.performed=false` and `dispatch_count=0`;
- input, bundle, and result replay hashes.

A `REFUSAL` records its stopping stage, stable code, message, safe context, and
only the verified evidence produced before the stop. It contains no speculative
answer or fabricated downstream proof.

`WORLD_NOT_READY` occurs before grounding when no active bundle exists. It is
receipt-hashed but not stored as a replayable episode. Store or bundle corruption
similarly returns an unpersisted runtime-level `INTEGRITY_FAILURE`. Grounding and
World-stage refusals under a verified bundle are persisted.

## 16. SQLite store

Runtime 4.8 uses one independent SQLite database with:

```text
descriptor
world_generations
world_heads
bundles
active_bundle
episodes
settlement_receipts
handoff_receipts
purge_receipts
export_receipts
```

SQLite uses WAL, `synchronous=FULL`, and foreign keys.

`world_generations` stores canonical archives, archive SHA-256, role, parent,
capability level, and World hash. `world_heads` stores one nullable pointer per
role. `bundles` binds three immutable generation IDs. `active_bundle` holds one
nullable bundle pointer.

Publication compiles outside the transaction, then uses `BEGIN IMMEDIATE` and a
compare-and-swap head check. The store API treats generation, bundle, and
episode rows as append-only and content-addressed. Direct database tampering is
not made impossible by triggers; it is detected by reconstruction and integrity
verification when the affected records are read.

An episode stores the normalized prompt, modality, bundle-bound input hash,
exact canonical result bytes and SHA-256, plus separately persisted ordered
stage and handoff receipts. Reusing a deterministic episode ID is allowed only
when every byte and receipt is identical.

`verify` checks the store descriptor, SQLite integrity, foreign keys, every
World archive and provenance span, World heads, bundles, active bundle, and all
episodes through replay. Cross-runtime stores are refused before mutation.

## 17. World lifecycle and replay

The lifecycle is:

1. `init` creates the descriptor, three null World heads, and null bundle head.
2. `sync --world` compiles a directory for one role.
3. `add --world` publishes a new role generation with one added or replaced
   source.
4. `remove --world` publishes a new role generation without one source.
5. `activate` verifies and atomically publishes a three-World bundle.
6. `query` uses only the active bundle.
7. `export` verifies and snapshots the SQLite store with a receipt.

No operation mutates an existing generation or bundle.

`replay <episode-id> --encoder-free`:

1. Verifies stored result SHA-256, UTF-8, JSON, and canonical bytes.
2. Loads the immutable bundle and all three archived Worlds.
3. Reconstructs every recorded successful stage and receipt.
4. Verifies every recorded handoff and its order.
5. Compares reconstructed evidence with separate receipt tables.
6. Recomputes input, bundle, output, and result commitments.
7. Returns the original result bytes unchanged without loading BGE weights.

For a refusal, replay verifies the successful recorded prefix and immutable
refusal receipt. It does not re-ground the prompt or re-execute the failing next
stage. Replay never changes any head, bundle, World, episode, or model asset.

## 18. Terminal routing and presentation

The neutral `moth` command requires exactly one runtime selector:

```sh
moth --runtime 4.7 status
moth --runtime=4.7 status
moth --runtime 4.8 status
moth --runtime=4.8 status
```

The launcher consumes only that selector, preserves all other arguments in
order, and lazy-loads the chosen runtime in-process. Missing, empty, unsupported,
duplicated, or conflicting selectors return exit status 2. `moth-4.7` remains a
compatibility alias; there is no `moth-4.8` alias.

Runtime 4.8 commands are:

```text
init
sync --world <input|main|surface> <directory>
add --world <input|main|surface> <source.moth>
remove --world <input|main|surface> <source-id>
activate
query <prompt>
replay <episode-id> --encoder-free
sources --world <input|main|surface>
history [--world <input|main|surface>]
status
verify
export <destination>
doctor
repl
```

Global options are `--store`, `--json`, and `--quiet`.

Default query and REPL output contains only the verified Surface value. Identity
objects reduce to `canonical_name`; strings print as text; structured values
print as compact sorted JSON; refusals print `CODE: message`.

`--json query` and `--json repl` show the full proof-bearing result as formatted
JSON. Replay instead writes the exact archived canonical bytes, adds no newline,
and is unaffected by `--json`. `--quiet` suppresses result output. CLI usage and
integrity errors are written to standard error and return status 2.

## 19. Closed-world safety boundary

- Prompts select compiled meanings but cannot add them.
- Vectors select candidates but cannot assert facts.
- Main uses only exact compiled operators, schemas, values, and edges.
- Surface cannot introduce a value absent from Main's verified result.
- Queries cannot publish or activate Worlds.
- Patch plans are never applied.
- Tool-shaped JSON is never dispatched.
- Python is parsed statically and never imported or executed.
- No stage performs network access or learns from prompts.
- Integrity failures stop instead of degrading to approximate output.

Runtime 4.8 provides deterministic reasoning and provenance over compiled
knowledge. It does not provide open-world knowledge, probabilistic truth,
unconstrained generation, or LLM-style completion.

## 20. Production posture and current claim

The initialized production store contains:

```text
Runtime descriptor: present
Input head: null
Main head: null
Surface head: null
Active bundle: null
World generations: 0
Bundles: 0
Episodes: 0
Compiled meanings: 0
Semantic edges: 0
```

Its query response is therefore:

```text
WORLD_NOT_READY: Runtime 4.8 has no active three-world bundle.
```

The implemented claim is architectural: Runtime 4.8 can isolate, activate,
settle, verify, hand off, persist, and replay three compiled Worlds in the fixed
Input-to-Main-to-Surface order.

It does not yet claim LLM-like Input language fidelity, general Main knowledge,
or Surface control over prose style and output length. Those require separately
compiled World contents and separate evidence without changing this
orchestration boundary.
