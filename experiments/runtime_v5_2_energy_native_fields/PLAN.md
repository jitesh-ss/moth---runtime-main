# Runtime 5.2 implementation plan

1. Freeze Runtime 5.1 behavior and its compiled JSON size oracle.
2. Freeze Safetensors schemas, logical hashing, JSON boundaries, SQLite schema,
   mutation semantics, failure codes, and gates.
3. Create `moth_runtime_v5_2` without Runtime 5.1 imports and retain one narrow
   Runtime 5.0 kernel adapter.
4. Implement deterministic Safetensors CAS writing, strict reopening, and
   read-only arrays.
5. Compile fields, HCF entries, activations, capabilities, candidates, and
   inert skill policies into typed tensors.
6. Implement direct-array activation, delegation, lexicographic settlement,
   ambiguity handling, and post-settlement JSON traces.
7. Implement the self-contained SQLite/CAS store and cross-runtime rejection.
8. Implement immutable SYSTEM/CONTEXT revision chains with atomic head moves,
   authorization validation, and concurrent-turn checks.
9. Integrate turns, frozen-kernel calls, surface realization, replay, and store
   verification.
10. Add the 5.2 CLI, versioned executable, and neutral launcher generation.
11. Run deterministic, parity, mutation, tamper, storage, performance, memory,
    independence, and repository regression campaigns.
12. Promote the verified artifact, metadata, architecture lock, documentation,
    and compact qualification evidence.
