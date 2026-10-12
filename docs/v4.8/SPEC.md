# Specification: Moth Runtime 4.8 Three-World Runtime

## Objective

Add an independent, opt-in Runtime 4.8 to `/Users/jitesh-ss/work/Moth` while keeping
Runtime 4.7 byte-identical and canonical. Runtime 4.8 must ground a transient
prompt before World execution, settle three ordinary compiled Worlds in the
fixed order Input, Main, Surface, independently verify every stage, and pass
only typed hash-bound values between stages.

The delivered 4.8 production store must be initialized but empty. This release
establishes orchestration, isolation, storage, replay, and terminal selection;
it does not populate or qualify language-fidelity or surface-realization
content.

## Technology and frozen identities

- Python 3.11 with the standalone project's sealed dependency versions.
- SQLite with WAL, `synchronous=FULL`, and foreign keys enabled.
- Existing read-only local `BAAI/bge-large-en-v1.5` assets.
- Runtime label: `4.8`.
- Store schema: `proof-energy-world-store/4.8`.
- Result schema: `moth-world-result/4.8`.
- Handoff schema: `moth-world-handoff/4.8`.
- Bundle schema: `moth-world-bundle/4.8`.
- Default store: `data/store-4.8.sqlite3`.
- Package: `src/moth_runtime_v4_8/`.
- Neutral launcher: `src/moth_launcher/`.

Runtime 4.8 must not import `moth_runtime`. Both packages may independently use
the same model files through configuration.

## Commands

```sh
# Runtime selection
.venv/bin/moth --runtime 4.7 status
.venv/bin/moth --runtime 4.8 status

# Runtime 4.8 lifecycle
.venv/bin/moth --runtime 4.8 init
.venv/bin/moth --runtime 4.8 sync --world input <directory>
.venv/bin/moth --runtime 4.8 sync --world main <directory>
.venv/bin/moth --runtime 4.8 sync --world surface <directory>
.venv/bin/moth --runtime 4.8 add --world <input|main|surface> <source.moth>
.venv/bin/moth --runtime 4.8 remove --world <input|main|surface> <source-id>
.venv/bin/moth --runtime 4.8 activate
.venv/bin/moth --runtime 4.8 query "<prompt>"
.venv/bin/moth --runtime 4.8 replay <episode-id> --encoder-free
.venv/bin/moth --runtime 4.8 sources --world <input|main|surface>
.venv/bin/moth --runtime 4.8 history
.venv/bin/moth --runtime 4.8 status
.venv/bin/moth --runtime 4.8 verify
.venv/bin/moth --runtime 4.8 export <destination>
.venv/bin/moth --runtime 4.8 doctor
.venv/bin/moth --runtime 4.8 repl

# Verification
.venv/bin/python -m pytest -q tests/test_runtime_v4_8.py tests/test_launcher.py
.venv/bin/python -m pytest -q
```

The launcher does not reinterpret runtime-specific options. Selected Runtime
4.7 retains its existing `--store`, `--generation`, `--json`, and `--quiet`
behavior. Runtime 4.8 exposes `--store`, `--json`, and `--quiet`; its query uses
the active bundle and its replay uses the immutable bundle recorded by the
episode. World publication commands require `--world`.

## Project structure

- `src/moth_runtime/`: protected Runtime 4.7 implementation.
- `src/moth_runtime_v4_8/`: independent Runtime 4.8 compiler, model, grounding,
  settlement, verification, store, runtime, and CLI.
- `src/moth_launcher/`: version-selector parser and argument dispatcher.
- `config/v4.8/`: Runtime 4.8 descriptors, World contracts, grounding, and
  encoder descriptors.
- `docs/v4.8/`: 4.8 architecture, product, and specification documents.
- `tests/test_runtime_v4_8.py`: three-World runtime and store checks.
- `tests/test_launcher.py`: version selection and 4.7 forwarding checks.
- `data/store-4.8.sqlite3`: ignored, initialized, empty production store.

## Public and internal interfaces

### Runtime selector

The neutral launcher owns the `moth` entry point. It accepts exactly one
selection in either form:

```text
--runtime 4.7
--runtime=4.7
--runtime 4.8
--runtime=4.8
```

Selection may appear before the selected CLI arguments. The launcher removes
only the selector tokens and forwards every remaining argument in original
order. It rejects no selection, empty values, unsupported values, and duplicate
selectors even when duplicates agree. It directly calls the selected Python
CLI entry point rather than starting a subprocess. `moth-4.7` continues to call
the unmodified Runtime 4.7 CLI and is documented as deprecated. No 4.8 alias is
registered.

### Semantic types

Runtime 4.8 defines these immutable contracts:

```python
class WorldRole(StrEnum):
    INPUT = "INPUT"
    MAIN = "MAIN"
    SURFACE = "SURFACE"

@dataclass(frozen=True)
class WorldBundle:
    bundle_id: str
    input_generation_id: str
    main_generation_id: str
    surface_generation_id: str
    interface_hash: str
    bundle_hash: str

@dataclass(frozen=True)
class WorldHandoff:
    bundle_id: str
    source_role: WorldRole
    target_role: WorldRole
    source_generation_id: str
    target_generation_id: str
    payload_kind: str
    payload: object
    source_settlement_hash: str
    provenance_hash: str
    handoff_hash: str
```

`CompiledWorld` is structurally equivalent to the copied 4.7 compiled field but
adds a mandatory `world_role` and uses only 4.8 identifier domains. The compiler
must reject an archive whose role or schema does not match the requested World.

The only handoff payload kinds in this release are `MAIN_REQUEST` and
`SEMANTIC_RESULT`. The permitted transitions are exactly `INPUT -> MAIN` and
`MAIN -> SURFACE` respectively.

`MAIN_REQUEST` is ID-only canonical data:

```text
{
  schema,
  interface_id,
  instruction_id,
  operation_id,
  primitive,
  slots: {slot_enum: meaning_id},
  bindings: {field_meaning_id: value_meaning_id}
}
```

It contains no names, aliases, prompt text, grounding evidence, or serialized
program steps. When a `PROGRAM` identifier is present, Main reloads its steps
from its immutable generation. `SEMANTIC_RESULT` contains the semantic kind,
value, proof identifiers/count, and Main generation identifier. Surface binds
that payload transiently to exactly one compiled `REALIZE_SEMANTIC_RESULT`
operation and emits a hash-bound `SURFACE_RESPONSE` without replaying Main.

### Query result

An `ANSWER` under `moth-world-result/4.8` contains:

- runtime, schema, episode, bundle, and three generation identifiers;
- the pre-World grounding receipt;
- an ordered `stages` object with Input, Main, and Surface settlement and
  independent-verification receipts;
- the two complete handoff receipts;
- separate energy coordinates for each World;
- the final `output` emitted by Surface;
- complete active provenance;
- `execution.performed=false` and `dispatch_count=0`;
- canonical input, bundle, and result replay hashes.

A `REFUSAL` includes `stage`, stable code, message, grounded context, and only
the verified receipts produced before the stop. `WORLD_NOT_READY` is returned
before grounding when no active bundle exists. Bundle, archive, handoff, proof,
or receipt corruption returns `INTEGRITY_FAILURE`.

Default CLI rendering prints `output.value`, reducing the exact identity object
to `canonical_name` as Runtime 4.7 does. Structured values use compact sorted
canonical JSON. Refusals print `CODE: message`. `--json` prints the complete
result. `--quiet` prints nothing. Replay always returns the complete stored
result, never concise presentation.

## Compilation and bundle lifecycle

1. `init` creates the Runtime 4.8 descriptor and nullable heads without a
   generation or bundle.
2. `sync` or `add` compiles one selected role outside the publication
   transaction using independent Runtime 4.8 code and hash domains.
3. Publication begins an immediate transaction, compares the snapshotted role
   head, inserts an immutable archive, and advances only that role head.
4. `remove` recompiles the selected role without the source; it does not alter
   either other role or the active bundle.
5. `activate` loads the current three role heads, requires all to be non-null,
   verifies their role/schema/archive integrity, and verifies the two interface
   contracts.
6. A valid activation inserts or reuses an immutable content-addressed bundle
   and atomically updates the active-bundle head.
7. An invalid or concurrent activation rolls back without modifying the prior
   active bundle.

Publishing a newer World generation does not affect queries until a new bundle
is explicitly activated.

## Query flow

1. Open the active bundle and verify its identifier, generation membership,
   archives, and interface hash.
2. Normalize and validate the transient prompt.
3. Ground it only against the Input World meaning index, producing one
   `GroundedProgram` and grounding receipt.
4. Settle the Input World exactly once by validating and projecting the
   grounded state through the activation-frozen ID interface; do not execute
   the Main domain primitive; independently verify its unique, zero-violation
   `MAIN_REQUEST`.
5. Create and verify the `INPUT -> MAIN` handoff.
6. Settle the Main World exactly once from the typed payload, without receiving
   or grounding raw prompt text; independently verify `SEMANTIC_RESULT`.
7. Create and verify the `MAIN -> SURFACE` handoff.
8. Settle the Surface World exactly once from the typed payload; independently
   verify `SURFACE_RESPONSE` and semantic preservation.
9. Construct one canonical result, compute its receipt, and atomically persist
   the episode and all stage/handoff receipts.

Any stage refusal or integrity failure stops immediately. No placeholder
downstream stage or handoff is fabricated.

## Energy and verification

Each World uses:

\[
E_w(y_w)=(K_w+1)Q\,V_w(y_w)+C_w(y_w),\qquad Q=1{,}000{,}000.
\]

A stage can hand off only one independently reconstructed state with
`violation_count == 0` and `proof_count == 1`. The independent verifier checks
generation and bundle identity, typed slots, program compatibility, every hard
factor, integer energy, proof identity, active provenance, and output contract.

The Surface verifier additionally proves that the realized output represents
the exact Main semantic result. It must reject added claims, dropped required
content, suppressed refusals, uncompiled text/keys/values, and renderer/schema
disagreement.

## Canonical hashing

Use sorted-key UTF-8 canonical JSON with no insignificant whitespace, finite
numbers only, normalized text, and deterministic collection ordering. Define
new domain separators for all 4.8 identifiers, including:

- `moth-world-meaning/4.8`;
- `moth-world-generation/4.8`;
- `moth-world-bundle/4.8`;
- `moth-world-settlement/4.8`;
- `moth-world-handoff/4.8`;
- `moth-world-input/4.8`;
- `moth-world-episode/4.8`;
- `moth-world-result/4.8`.

Hash payloads exclude only the field that stores their own final hash. Runtime
4.7 hash domains and identifiers must not be accepted as Runtime 4.8 assets.

## Store requirements

The Runtime 4.8 SQLite schema contains these logical groups:

- one descriptor row with exact store schema;
- immutable `world_generations` keyed by generation ID and role;
- three `world_heads`, one per closed role;
- immutable `bundles` binding three valid generation IDs;
- one nullable `active_bundle` head;
- episodes bound to an immutable bundle;
- ordered stage settlements and handoffs bound to an episode;
- purge and export receipts.

Foreign keys must prevent deletion or mismatching of referenced generations.
`verify` runs SQLite integrity checking, descriptor verification, archive hash
verification, role closure, bundle reconstruction, active-head reconstruction,
and episode/replay verification. Opening a 4.7 store with 4.8, or a 4.8 store
with 4.7, must fail before mutation.

## Replay

`replay <episode-id> --encoder-free` must:

1. Load the exact stored canonical result bytes.
2. Verify result, input, and bundle receipts.
3. Load all three archived generations referenced by that bundle.
4. Verify each stored settlement and its independent-verification receipt.
5. Verify both handoffs and their ordered role transitions.
6. Verify final Surface output and result canonicality.
7. Return byte-for-byte the originally stored result without loading BGE.

Replay never changes the active bundle or any role head.

## Code style

Use typed Python 3.11, frozen dataclasses for semantic state, `StrEnum` for
closed public enums, canonical JSON for every persisted/hashable value,
domain-separated identifiers, explicit exception/refusal mapping, deterministic
ordering, and dependency injection for the passage/query encoder.

Do not hide stage errors behind broad best-effort fallback. The outer runtime
may translate a caught integrity exception into a typed refusal but must not
continue the cascade.

## Testing strategy

Use temporary stores and generated fixture Worlds. No fixture may enter the
production 4.8 store.

### Launcher and preservation

- Accept both runtime-selector syntaxes for 4.7 and 4.8.
- Reject missing, empty, unsupported, or duplicate selectors.
- Prove exact argument order forwarding.
- Prove tagged 4.7 behavior and `moth-4.7` parity.
- Hash tracked 4.7 code, configuration, architecture locks, result fixtures,
  and `data/store-4.7.sqlite3` before and after; require byte identity.

### Store and lifecycle

- Initialize null role heads and null bundle with zero content.
- Reject cross-runtime stores before mutation.
- Publish independent role histories.
- Reject activation when any role is absent or interfaces mismatch.
- Prove atomic activation, rollback, and concurrent-head conflict behavior.
- Prove publishing a role does not silently replace the active bundle.

### Cascade and integrity

- Prove execution order is exactly Input, Main, Surface.
- Count exactly one settlement and one verification per successful role.
- Prove Main and Surface never receive raw prompt text or call the grounder.
- Verify typed handoffs and generation/bundle binding.
- Stop downstream settlement after every upstream refusal class.
- Reject forged stage output, proof, energy, provenance, generation, role,
  bundle, interface, and handoff receipts.
- Prove final concise output comes only from the verified Surface result.
- Prove `--json` retains complete evidence and `--quiet` emits nothing.
- Prove encoder-free replay is byte-exact.
- Prove source-order invariance per World and for the activated bundle.
- Assert zero code execution, patch application, tool dispatch, and network use.

### Offline smoke

Compile disposable minimal Input, Main, and Surface Worlds with the real local
BGE encoder. Activate one bundle, run one exact prompt and one supported
paraphrase, verify all three settlements and two handoffs, replay one episode
without the encoder, then delete the fixture Worlds and stores. This smoke is
architectural only and must not be reported as language-fidelity or output-
length qualification.

Run the focused 4.8 and launcher modules, then the complete lightweight
standalone suite. Any 4.7 regression blocks completion.

## Boundaries

- Always: keep Runtime 4.8 independent, verify every stage and handoff, use an
  atomic bundle, preserve prompt isolation, fail closed, preserve 4.7 hashes.
- Ask first: populate production Worlds, change thresholds or dependencies,
  add operations or modalities, qualify or promote 4.8, make 4.8 canonical.
- Never: edit Runtime 4.7 implementation/config/store, migrate stores, re-ground
  between Worlds, execute code, apply patches, dispatch tools, use network
  authority, learn from a prompt, or claim untested language fidelity.

## Success criteria

- `moth --runtime 4.7` remains behaviorally and byte-for-byte preserved.
- `moth --runtime 4.8` selects only the independent package and store.
- Untagged `moth` refuses with a usage error.
- The empty production store has the 4.8 descriptor, three null role heads,
  null active bundle, and zero semantic or episode content.
- A disposable minimal cascade verifies exactly three settlements and two
  handoffs and replays byte-exactly without the encoder.
- Every tested forged stage/handoff fails closed.
- All focused and existing lightweight tests pass.
- Documentation and configuration consistently label 4.8 opt-in, empty,
  unqualified, non-canonical, and non-default.

## Assumptions

- Runtime 4.7 remains the canonical qualified runtime. Terminal selection is
  explicit: the neutral launcher has no implicit default.
- Prompt grounding occurs once before Input World settlement.
- The Input World generation supplies grounding candidates.
- Input language-fidelity and Surface realization contents are future work.
- All three Worlds share one implementation and differ only by compiled role,
  content, and typed interface contract.
- No Runtime 4.7 store migration exists.
