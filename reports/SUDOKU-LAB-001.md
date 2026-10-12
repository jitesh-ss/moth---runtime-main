# Runtime 4.7 Disposable Sudoku Test

Date: 2026-08-30  
Verdict: **`COMPILED_SUDOKU_CONFIRMED`**

## Result

A disposable Runtime 4.7 extension successfully solved six prompt-supplied Sudoku puzzles using structured rules compiled into an isolated constraint field.

- Grounding diagnostics: 18/18
- Prose-only instruction refusals: 6/6
- Supported puzzle outcomes: 18/18
- Invalid, contradictory, and ambiguous inputs: 18/18
- Structural and causal controls: 16/16
- Invariance and integrity checks: 12/12
- Independent reference-solver agreement: 18/18
- Runtime execution, tool dispatch, and network attempts: 0

The named decisive groups total 70 outcomes, not 64 as stated in the original test plan. All 70 passed. The frozen harness printed `NO_GO_CONSTRAINT_SOLVER` only because it compared 70/70 with the mistaken expected total of 64; no semantic or safety check failed.

## Capability conclusion

- `PROSE_ONLY_SUDOKU_INSTRUCTIONS`: `UNSUPPORTED_EXPECTED`
- `STRUCTURED_COMPILED_SUDOKU_CONSTRAINTS`: `SUPPORTED`
- `PROMPT_SUPPLIED_TRANSIENT_GRID`: `SAFE`

The experiment demonstrates that granular compiled Sudoku rules can drive exact global constraint solving when a disposable generic `SOLVE_FINITE_CSP` primitive is present. The prompt supplied only transient grid values; it did not add rules or mutate the field.

This does not mean unmodified Runtime 4.7 contains a Sudoku solver. The CSP primitive existed only in the disposable experiment.

## Representative solution

```text
693784512
487512936
125963874
932651487
568247391
741398625
319475268
856129743
274836159
```

The representative result had zero energy violations, one unique solution, 138 compiled proof meanings, complete rule provenance, preserved givens, and exact replay.

## Evidence identifiers

- Compiled field: `f12b7cdf7af447e7a808c215056b9d49c13c0ffafb2b87374469f1f2b3eb5832`
- Generation: `74e8868ca4450343452e7584bb1f49cda42b7c88ec06fd49864fbd9b099610cf`
- Representative solution: `fce6e5048c998116622f1ecc51c31d124839e06293d3a8ee8d8263231f1ccf8b`
- Representative result: `9583e041f8d1994d1b4acb586c3a864bed9f5e0c04188dee6e82cefc6922b160`
- Temporary extension: `8a1c1f5814b33891b4c41d0a1ac36a1e7b1d4c3740d374a0b14f296fb649f1e2`
- Temporary harness: `8ff17b2a9e657921907bb18191d2d8a4a93187ad85e231bcc9279d12257c8b50`
- Campaign rows: `a1910264dbb9d724012d2411824063a0dab8a00253817f4e2270719957d30702`

## Isolation

The temporary runtime, field, solver, puzzle fixtures, SQLite store, caches, and raw results were deleted after the campaign. The canonical Runtime 4.7 source, configuration, BGE assets, populated prime field, and pre-existing Git state remained byte-identical.
