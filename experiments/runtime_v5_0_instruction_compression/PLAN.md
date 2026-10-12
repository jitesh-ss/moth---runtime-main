# Plan: instruction-compression hierarchy

1. Freeze the base instruction field, ordinary skill sources, granular oracle,
   task panel, and protected production hashes.
2. Implement a standalone canonical model and field validator.
3. Implement bounded skill parsing, semantic rule matching, macro expansion,
   policy validation, and deterministic composition.
4. Implement a temporary filesystem instance that executes only declared
   granular primitives and emits verifiable receipts.
5. Run L1-L6 gates, oracle behavior comparison, adverse cases, ablations,
   determinism, tampering, and production-isolation checks.
6. Preserve only the compact result, hashes, replay command, and conclusion.

The sequence is intentionally strict: source interpretation cannot be tested
before the lower field validates, and behavior cannot be credited before the
compiled policy equals the independently frozen oracle.

