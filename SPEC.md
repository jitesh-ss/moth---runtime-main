# Specification: Standalone Moth Runtime 4.7

## Objective

Provide an independent Runtime 4.7 under `/Users/jitesh-ss/work/Moth`. The runtime
compiles controlled language into a closed-world proof-carrying energy field.
Prompts may select and compose compiled meanings but never add semantics.

## Technology

- Python 3.11
- SQLite with WAL, full synchronous durability, and immutable generations
- NumPy 2.4.6, SciPy 1.17.1, sentence-transformers 5.6.1, Torch 2.13.0
- Local BAAI/bge-large-en-v1.5 assets; no model downloads

## Commands

```sh
.venv/bin/python -m pytest -q
.venv/bin/python tests/smoke_real.py
.venv/bin/moth init
.venv/bin/moth sync <directory>
.venv/bin/moth query "<prompt>"
.venv/bin/moth verify
```

## Structure

- `src/moth_runtime/`: runtime implementation
- `config/`: frozen Runtime 4.7 and encoder descriptors
- `models/`: pinned local encoder
- `data/`: fresh production store
- `tests/fixtures/`: disposable verification inputs

## Style

Use typed Python 3.11, immutable dataclasses for semantic state, canonical JSON,
content-addressed identifiers, explicit refusal codes, and deterministic ordering.

## Testing

One focused deterministic test module covers identity, exact settlement, closed
world refusal, structured JSON, inert tools, replay, and store isolation. One
real-model smoke script verifies local encoder assets and the end-to-end flow.

## Boundaries

- Always: verify source/model hashes, preserve exact proof provenance, fail closed.
- Ask first: new operations, dependencies, schemas, or output authority.
- Never: execute Python, apply patches, dispatch tools, use the network, learn
  from prompts, or import the original repository at runtime.

## Success

All focused tests and the real-model smoke pass. The production store has the
4.7 descriptor, a null head, and zero generations/episodes after verification.
