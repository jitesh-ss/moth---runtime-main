# Moth Runtime Family

Runtime 4.7 remains Moth's qualified canonical closed-world proof-carrying
energy runtime. Runtime 4.8 is an independent, opt-in three-World architecture
with empty production Input, Main, and Surface Worlds. Runtime 4.9 is an
independent opt-in successor that adds active compiled factor settlement while
leaving both earlier runtimes unchanged. Runtime 5.0 adds bounded compiled
language fidelity. Runtime 5.1 is the preserved standalone conversational HCF
extension. Runtime 5.2 is its independently packaged, Safetensors-native
successor with revisioned mutable SYSTEM and persistent CONTEXT layers.
Runtime 5.3 adds its own kernel, persistent conversational assertions, bounded
plan construction, independent checking, and historical reexecution. It remains
opt-in; natural-language coverage is limited to compiled constructions.

The definitive system-level design is
[Mother-Architecture.md](Mother-Architecture.md). Version-specific documents
freeze individual runtime contracts, and [reports/README.md](reports/README.md)
indexes the surviving experimental and qualification evidence.

## Setup

The local working copy may contain a Python environment and the pinned BGE
model, but neither is committed to Git. Runtime inference never downloads a
model automatically.

Create the environment:

```sh
uv venv --python 3.11 .venv
uv sync
```

Place the verified `BAAI/bge-large-en-v1.5` assets at:

```text
models/bge-large-en-v1.5/
```

```sh
./.venv/bin/moth --runtime 4.7 doctor
./.venv/bin/moth --runtime 4.7 status
```

Initialize a fresh, untracked field:

```sh
./.venv/bin/moth --runtime 4.7 init
```

## Compile and query

```sh
./.venv/bin/moth --runtime 4.7 sync /absolute/path/to/compiled-world
./.venv/bin/moth --runtime 4.7 query \
  "Starting from Asterion, follow route for 8 steps using answer-json."
./.venv/bin/moth --runtime 4.7 verify
```

By default, `query` prints only the actual response. Identity answers print
their canonical name, structured answers print as compact canonical JSON, and
typed refusals print as `CODE: message`.

```text
Node-08
```

Use `--json` before `query` to print the complete proof-bearing result,
including grounding, energy, provenance, episode, and replay evidence:

```sh
./.venv/bin/moth --runtime 4.7 --json query \
  "Starting from Asterion, follow route for 8 steps using answer-json."
```

The interactive REPL follows the same convention. The legacy `moth-4.7`
command remains available, but new commands should use the explicit runtime
tag. Untagged `moth` commands are rejected.

Use `--store /path/to/other.sqlite3` to keep different compiled worlds separate.
The runtime still records canonical JSON with exact energy, proof, provenance,
replay, and execution receipts internally. Encoder-free replay returns that
complete stored evidence. Tool-call-shaped JSON and patch plans are inert:
execution and dispatch remain zero.

## Runtime 4.8

Initialize and inspect the independent empty three-World store:

```sh
./.venv/bin/moth --runtime 4.8 init
./.venv/bin/moth --runtime 4.8 status
./.venv/bin/moth --runtime 4.8 query "hello"
```

Until compatible World contents are separately compiled and activated, query
returns:

```text
WORLD_NOT_READY: Runtime 4.8 has no active three-world bundle.
```

Later World generations are compiled independently and then atomically bound:

```sh
./.venv/bin/moth --runtime 4.8 sync --world input /path/to/input-world
./.venv/bin/moth --runtime 4.8 sync --world main /path/to/main-world
./.venv/bin/moth --runtime 4.8 sync --world surface /path/to/surface-world
./.venv/bin/moth --runtime 4.8 activate
```

Prompt grounding occurs once against Input World meanings before the Input
World settles. Main and Surface receive only typed, hash-bound handoffs. See
[`docs/v4.8/ARCHITECTURE.md`](docs/v4.8/ARCHITECTURE.md) and
[`docs/v4.8/SPEC.md`](docs/v4.8/SPEC.md).

## Runtime 4.9

Runtime 4.9 keeps the three-World flow and adds a separately selected Main
World `FACTOR_SETTLEMENT` path. Compiled programs may create transient
finite-domain variables, instantiate compiled allowed-tuple factors, bind
shared ports, apply compiled prompt/literal clamps, and expose outputs. The
generic kernel performs deterministic search-free domain narrowing; it contains
no task-specific solver.

```sh
./.venv/bin/moth --runtime 4.9 init
./.venv/bin/moth --runtime 4.9 status
```

Its production store is deliberately empty. See
[`docs/v4.9/ARCHITECTURE.md`](docs/v4.9/ARCHITECTURE.md),
[`docs/v4.9/PRODUCT.md`](docs/v4.9/PRODUCT.md), and
[`docs/v4.9/SPEC.md`](docs/v4.9/SPEC.md). The currently supported claim and
its limitations are summarized in
[`reports/RUNTIME-4.9-FACTOR-QUALIFICATION-001.md`](reports/RUNTIME-4.9-FACTOR-QUALIFICATION-001.md).

## Runtime 5.0

Runtime 5.0 is an independent opt-in Runtime 4.9 derivative with bounded
compiled language fidelity in the Input World. It preserves exact 4.9
instruction envelopes and additionally settles compiled paraphrases,
multi-clause facts, bounded singular pronouns, and intents into typed fact
graphs and ID-only Main bindings. Ambiguous, incomplete, conflicting, unknown,
or unsupported language refuses closed.

```sh
./.venv/bin/moth --runtime 5.0 init
./.venv/bin/moth --runtime 5.0 status
```

Its production store is deliberately empty. Runtime 4.7 remains canonical.
See [`docs/v5.0/ARCHITECTURE.md`](docs/v5.0/ARCHITECTURE.md),
[`docs/v5.0/PRODUCT.md`](docs/v5.0/PRODUCT.md),
[`docs/v5.0/SPEC.md`](docs/v5.0/SPEC.md), and
[`reports/RUNTIME-5.0-LANGUAGE-FIDELITY-QUALIFICATION-001.md`](reports/RUNTIME-5.0-LANGUAGE-FIDELITY-QUALIFICATION-001.md).

## Verify

```sh
./.venv/bin/python -m pytest -q
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 ./.venv/bin/python tests/smoke_real.py
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 ./.venv/bin/python tests/smoke_real_v4_8.py
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 ./.venv/bin/python tests/smoke_real_v5_0.py
```

See [Mother-Architecture.md](Mother-Architecture.md) for the complete system,
[ARCHITECTURE.md](ARCHITECTURE.md) for Runtime 4.7, and
[reports/README.md](reports/README.md) for the evidence history.

## Runtime 5.1

Runtime 5.1 attaches a fixed, hash-verified foundation containing BASE fields and
compiled Input, Main, and Surface Worlds, then adds three-level
`BASE > SYSTEM > CONTEXT` settlement, append-only conversations, bounded active
context, compiled response modes, replay, and console analytics around the
preserved Runtime 5.0 kernel. It intentionally exposes no World-management,
tool-execution, network-provider, or OpenCode interface.

It also supports a self-contained weight-free compiled model artifact. That image
packages the runtime, foundation, five qualified L1-L5 field families, bounded L6
skill composition, ten canonical skills, and sixteen verified Surface modes.

```sh
./.venv/bin/python -m experiments.runtime_v5_1_hcf.build_assets /tmp/moth-5.1-foundation
./.venv/bin/moth --runtime 5.1 init --foundation /tmp/moth-5.1-foundation
./.venv/bin/moth --runtime 5.1 inspect foundation
./.venv/bin/moth --runtime 5.1 session create --system /path/to/system.txt
./.venv/bin/moth --runtime 5.1 repl --session CONVERSATION_ID

# Or build and open the complete weight-free artifact:
./.venv/bin/python -m experiments.runtime_v5_1_compiled_artifact.build_artifact /tmp/moth-model-5.1
./.venv/bin/moth --runtime 5.1 artifact verify /tmp/moth-model-5.1
./.venv/bin/moth --runtime 5.1 init --artifact /tmp/moth-model-5.1
./.venv/bin/moth --runtime 5.1 field list
```

The weight-free attachment contract is documented by
`config/v5.1/foundation-manifest.schema.json` and
`config/v5.1/model-artifact.schema.json`.
See `docs/v5.1/PRODUCT.md`, `docs/v5.1/ARCHITECTURE.md`, and
`docs/v5.1/SPEC.md` for the bounded implementation claim.

## Runtime 5.2

Runtime 5.2 stores compiled fields, the candidate/property matrix, BASE and
mutable HCF entries, activation directives, capability routing, and inert skill
policies in deterministic Safetensors objects. SQLite stores the catalog,
conversation state, immutable messages, revision chains, turn bindings, and
object references. Energy settlement reads typed arrays directly and performs
no candidate-dictionary reconstruction.

BASE remains immutable. SYSTEM and persistent CONTEXT changes create immutable
membership snapshots and atomically move their conversation-local head
pointers. Every turn captures both heads, and historical replay resolves those
exact revisions. Runtime 5.2 rejects 5.1 stores and artifacts rather than
migrating them.

```sh
./.venv/bin/python -B -m experiments.runtime_v5_2_energy_native_fields.build_artifact /tmp/model-5.2
./.venv/bin/moth --runtime 5.2 --store /tmp/store-5.2 init --artifact /tmp/model-5.2
./.venv/bin/moth --runtime 5.2 --store /tmp/store-5.2 artifact verify
./.venv/bin/moth --runtime 5.2 --store /tmp/store-5.2 session create
```

See `docs/v5.2/ARCHITECTURE.md`, `docs/v5.2/PRODUCT.md`, and
`reports/RUNTIME-5.2-ENERGY-NATIVE-QUALIFICATION-001.md`.

## Runtime 5.3

Runtime 5.3 is an independent conversational reasoning runtime with its own kernel, immutable compiled foundation, revisioned knowledge, bounded action composition, independent plan checking and historical reexecution. It preserves earlier runtimes and is not the canonical default.

Use `moth --runtime 5.3`; see [the operator guide](docs/v5.3/PRODUCT.md), [architecture](docs/v5.3/ARCHITECTURE.md), and [qualification](reports/RUNTIME-5.3-CONVERSATIONAL-REASONING-001.md). Natural conversation is bounded to compiled capabilities; plans are never executed.
See [current implementation notes](docs/v5.3/IMPLEMENTATION-NOTES.md) and the
[post-promotion conversation trial](reports/RUNTIME-5.3-CONVERSATION-TRIAL-001.md)
for observed language and explanation gaps. In particular, accepting `Why?`
does not yet provide a causal explanation.
