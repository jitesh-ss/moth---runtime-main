# Runtime 5.2 frozen specification

## Boundary

Runtime 5.2 is an independently selectable runtime derived behaviorally from
5.1. It imports no 5.1 module. The only earlier runtime dependency is the
frozen Runtime 5.0 world kernel, reached through one adapter. The isolated
artifact entrypoint is the version-specific 5.2 CLI; the separately installed
neutral launcher is not part of the artifact closure.

Safetensors 0.8.0 is the sole compiled-content container. No pickle, CBOR,
Arrow, HDF5, custom tensor pack, object tensor, or executable serialization is
permitted. SQLite is the sole catalog and transactional state journal.

JSON is permitted for human source, manifests, diagnostics, post-settlement
traces, results, and verification receipts. JSON is forbidden for executable
compiled fields, candidate/property tables, HCF rules, activation directives,
capability indexes, and compiled skill policy IR.

## Tensor schemas

`moth-energy-foundation/5.2` stores candidate and semantic hashes, the default
activation mask, int64 grounding costs, modality, dense candidate-property
presence/value matrices, field/skill/payload handles, presentation routing,
and immutable BASE entries/delegations.

`moth-hcf-field/5.2` stores a declared SYSTEM or CONTEXT level, entry IDs and
hashes, effect opcodes, foundation scope indexes, value hashes, delegation
targets, redelegation bits, provenance, source spans, and activation rows.

`moth-compiled-field/5.2` stores validated L1–L6 structure as numeric node,
binding, capability, literal-byte, and sparse integer-operand tensors. It does
not store a JSON archive.

`moth-compiled-skill/5.2` stores binding indexes, workflow opcode labels and
edges, completion labels, literal bytes, and the policy hash. Planning is inert:
dispatch count and writes remain zero.

All hashes are 32-byte uint8 rows. Current HCF settlement uses integers and
bytes only. Feature banks for future modalities require a new versioned object
schema and must not alter the HCF schema.

## Identity and publication

Logical identity hashes the schema plus tensor names in lexical order and each
tensor's fixed dtype, shape, and C-order bytes. Exact file identity is SHA-256
over the complete Safetensors file. Metadata is one canonical JSON string under
the Safetensors `moth` metadata key; the single key prevents metadata-map order
from changing exact file bytes.

Inputs must be numeric, little-endian, contiguous, within fixed bounds, and
schema exact. Publication writes a sibling temporary file, flushes and fsyncs
it, atomically renames it into the SHA-256 CAS, and verifies existing objects
instead of overwriting them.

## Energy and activation

Settlement consumes read-only arrays directly and produces `energy[N,4]` in
this exact order:

```text
(BASE violations, SYSTEM violations, CONTEXT violations, grounding cost units)
```

Candidates are filtered by the effective activation mask before true tuple
comparison. Equal energy and distinct semantic hashes return `AMBIGUOUS_HCF`;
equal semantics use the lowest candidate hash bytewise. A nonzero hierarchy
coordinate on the selected minimum returns `HCF_CONFLICT`. An empty effective
mask returns `NO_CANDIDATE`. A diagnostic scalar may be emitted but never used
for selection.

BASE activation is immutable. SYSTEM activation requires BASE delegation.
CONTEXT activation requires direct BASE delegation or a redelegable
BASE-to-SYSTEM plus SYSTEM-to-CONTEXT chain. Conflicting lower-level
constraints require the corresponding delegation. Invalid prospective layer
snapshots fail before their head pointer moves.

## Store and mutation

The store is a directory containing `catalog.sqlite3`, a self-contained
verified artifact copy, and `objects/sha256`. Every connection enables foreign
keys, WAL, and FULL synchronous writes.

BASE never mutates. Every conversation has independent SYSTEM and persistent
CONTEXT revision chains whose revision zero is empty. Upsert/remove creates a
complete immutable membership snapshot and compare-and-swaps the head using an
expected revision number. Messages remain immutable and append-only. Transient
message CONTEXT is distinct from persistent CONTEXT attachments.

A turn captures conversation, SYSTEM, and CONTEXT heads before computation and
rechecks all three in one immediate transaction. Historical turns bind exact
layer revisions and replay against those revisions after later mutations.

## Gates

- No Runtime 5.1 import or packaged dependency.
- Three clean artifact builds have identical member and artifact hashes.
- Compiled Safetensors bytes are at most 75% of equivalent 5.1 compiled JSON.
- Median settlement time and one-MiB-resolution median peak RSS do not regress.
- All 168 qualified surface cases and 36 inert skill-plan cases preserve their
  semantic result.
- Candidate dictionary reconstruction, tool dispatch, network access, pickle,
  generated-code execution, and task writes are zero.
- Mutation, stale/no-op, replay, cross-version, and tamper paths fail closed.
