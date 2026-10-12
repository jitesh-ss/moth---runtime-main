# Moth Runtime 4.7 Architecture Lock

Status: qualified, promoted, canonical, default.

Runtime 4.7 is a closed-world proof-carrying compiled energy field. It compiles
controlled language, structured values and schemas, linear programs, inert tool
descriptions, and statically resolvable Python structure into immutable typed
meanings. Dense BGE vectors are used only to ground a transient prompt to those
compiled meanings. Exact sparse operators, type constraints, source hashes, and
provenance determine truth and output.

For grounded state \(y=(g,x,J,D,\pi)\), the integer energy is

\[
E(y)=(K+1)Q\,V(y)+C(y),\qquad Q=1{,}000{,}000.
\]

\(V\) counts hard violations and \(C\) is quantized vector-grounding cost.
Because one violation dominates every possible grounding improvement, only a
unique independently verified state with \(V=0\) may answer. Exact chain and
mixed-relation settlement uses deterministic dynamic programming through depth
50. Linear acyclic pipelines are limited to 16 steps.

The prompt is transient. It may select and compose compiled entities, relations,
operations, values, schemas, tools, code symbols, spans, and replacement
fragments, but it cannot create any of them. Unknown, ambiguous, missing,
incompatible, or unsupported meanings produce typed refusals.

Structured JSON is rendered only from compiled keys, values, and schemas.
Python is parsed but never imported or executed. Patch output is an inert,
hash-bound plan and is never applied. Tool output is inert JSON only; Runtime
4.7 contains no dispatcher. Every result states
`execution.performed=false` and `dispatch_count=0`.

The authoritative standalone package is `src/moth_runtime/`; configuration is
`config/`; the store schema is
`proof-energy-capability-store/4.7`; the result schema is
`moth-capability-result/4.7`. Earlier runtime stores are never migrated.

Evidence: capability-lab Attempt 002 passed 1,688/1,688 quick cases and
2,400/2,400 held-out cases. Independent Runtime 4.7 qualification Attempt 001
passed promoted-package parity, depth, output, integrity, and replay gates.

This file is the human-readable architecture lock. The content-addressed lock
is `config/ARCHITECTURE-LOCK.json`.
