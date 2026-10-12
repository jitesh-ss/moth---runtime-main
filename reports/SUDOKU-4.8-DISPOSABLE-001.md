# Runtime 4.8 Disposable Sudoku Field Record

Date: 2026-08-31  
Verdict: **`COMPILED_SUDOKU_CONFIRMED`**

## What this record contains

This is the surviving audit record from one disposable Runtime 4.8 Sudoku episode. The temporary three-World SQLite store, test extension, caches, and raw result were deleted after verification. The exact controlled-language source compiled into each World, the exact prompt, and the actual response are retained below.

This result demonstrates a structured compiled Sudoku constraint World using a bounded disposable `SOLVE_FINITE_CSP` primitive. It does **not** show that prose-only Sudoku explanations become executable, and it does not add Sudoku capability to the canonical Runtime 4.8 package.

## Exact Input World source

```text
# Runtime 4.8 disposable Sudoku World, generated before the query.
Entity "R1C1" is declared.
Entity "R1C2" is declared.
Entity "R1C3" is declared.
Entity "R1C4" is declared.
Entity "R1C5" is declared.
Entity "R1C6" is declared.
Entity "R1C7" is declared.
Entity "R1C8" is declared.
Entity "R1C9" is declared.
Entity "R2C1" is declared.
Entity "R2C2" is declared.
Entity "R2C3" is declared.
Entity "R2C4" is declared.
Entity "R2C5" is declared.
Entity "R2C6" is declared.
Entity "R2C7" is declared.
Entity "R2C8" is declared.
Entity "R2C9" is declared.
Entity "R3C1" is declared.
Entity "R3C2" is declared.
Entity "R3C3" is declared.
Entity "R3C4" is declared.
Entity "R3C5" is declared.
Entity "R3C6" is declared.
Entity "R3C7" is declared.
Entity "R3C8" is declared.
Entity "R3C9" is declared.
Entity "R4C1" is declared.
Entity "R4C2" is declared.
Entity "R4C3" is declared.
Entity "R4C4" is declared.
Entity "R4C5" is declared.
Entity "R4C6" is declared.
Entity "R4C7" is declared.
Entity "R4C8" is declared.
Entity "R4C9" is declared.
Entity "R5C1" is declared.
Entity "R5C2" is declared.
Entity "R5C3" is declared.
Entity "R5C4" is declared.
Entity "R5C5" is declared.
Entity "R5C6" is declared.
Entity "R5C7" is declared.
Entity "R5C8" is declared.
Entity "R5C9" is declared.
Entity "R6C1" is declared.
Entity "R6C2" is declared.
Entity "R6C3" is declared.
Entity "R6C4" is declared.
Entity "R6C5" is declared.
Entity "R6C6" is declared.
Entity "R6C7" is declared.
Entity "R6C8" is declared.
Entity "R6C9" is declared.
Entity "R7C1" is declared.
Entity "R7C2" is declared.
Entity "R7C3" is declared.
Entity "R7C4" is declared.
Entity "R7C5" is declared.
Entity "R7C6" is declared.
Entity "R7C7" is declared.
Entity "R7C8" is declared.
Entity "R7C9" is declared.
Entity "R8C1" is declared.
Entity "R8C2" is declared.
Entity "R8C3" is declared.
Entity "R8C4" is declared.
Entity "R8C5" is declared.
Entity "R8C6" is declared.
Entity "R8C7" is declared.
Entity "R8C8" is declared.
Entity "R8C9" is declared.
Entity "R9C1" is declared.
Entity "R9C2" is declared.
Entity "R9C3" is declared.
Entity "R9C4" is declared.
Entity "R9C5" is declared.
Entity "R9C6" is declared.
Entity "R9C7" is declared.
Entity "R9C8" is declared.
Entity "R9C9" is declared.
Entity "DIGIT-1" is declared.
Entity "DIGIT-2" is declared.
Entity "DIGIT-3" is declared.
Entity "DIGIT-4" is declared.
Entity "DIGIT-5" is declared.
Entity "DIGIT-6" is declared.
Entity "DIGIT-7" is declared.
Entity "DIGIT-8" is declared.
Entity "DIGIT-9" is declared.
Entity "BLANK-0" is declared.
Entity "BLANK-DOT" is declared.
Entity "ROW-1" is declared.
Entity "ROW-2" is declared.
Entity "ROW-3" is declared.
Entity "ROW-4" is declared.
Entity "ROW-5" is declared.
Entity "ROW-6" is declared.
Entity "ROW-7" is declared.
Entity "ROW-8" is declared.
Entity "ROW-9" is declared.
Entity "COLUMN-1" is declared.
Entity "COLUMN-2" is declared.
Entity "COLUMN-3" is declared.
Entity "COLUMN-4" is declared.
Entity "COLUMN-5" is declared.
Entity "COLUMN-6" is declared.
Entity "COLUMN-7" is declared.
Entity "COLUMN-8" is declared.
Entity "COLUMN-9" is declared.
Entity "BOX-1" is declared.
Entity "BOX-2" is declared.
Entity "BOX-3" is declared.
Entity "BOX-4" is declared.
Entity "BOX-5" is declared.
Entity "BOX-6" is declared.
Entity "BOX-7" is declared.
Entity "BOX-8" is declared.
Entity "BOX-9" is declared.
Entity "RULE-CELL-DOMAIN" is declared.
Entity "RULE-EXACTLY-ONE" is declared.
Entity "RULE-ROW-ALL-DIFFERENT" is declared.
Entity "RULE-COLUMN-ALL-DIFFERENT" is declared.
Entity "RULE-BOX-ALL-DIFFERENT" is declared.
Entity "RULE-IMMUTABLE-GIVENS" is declared.
Entity "RULE-DETECT-CONTRADICTION" is declared.
Entity "RULE-UNIQUE-SOLUTION" is declared.
Entity "RULE-CANONICAL-RENDERING" is declared.
Directional relation "member-of" maps Meaning to Meaning and is multi-valued.
Relation form "membership-form" for relation "member-of" accepts "Cell {SOURCE} belongs to unit {DESTINATION}.".
Operation "solve-finite-csp" selects kernel primitive "SOLVE_FINITE_CSP".
Output schema "sudoku-grid" selects kernel schema "ANSWER_WITH_PROOF".
Program "sudoku-solver" is canonical step JSON "[{\"operation\":\"PARSE_COMPILED_GRID\"},{\"operation\":\"CLAMP_GIVENS\"},{\"operation\":\"PROPAGATE_DOMAINS\"},{\"operation\":\"SELECT_MINIMUM_DOMAIN\"},{\"operation\":\"EXPLORE_CANONICAL_CANDIDATES\"},{\"operation\":\"REJECT_VIOLATING_BRANCHES\"},{\"operation\":\"VERIFY_COMPLETE_ASSIGNMENT\"},{\"operation\":\"SEARCH_FOR_SECOND_SOLUTION\"},{\"operation\":\"RENDER_COMPILED_GRID\"}]".
Instruction "solve-sudoku" selects operation "solve-finite-csp" accepts "Solve {PROGRAM} with {BINDINGS} using {SCHEMA}.".
```

The Input World contains the permitted cells, digits, blanks, units, rule identities, operation, program, instruction envelope, and output schema. It intentionally contains no Sudoku membership edges.

## Exact Main World source

```text
# Runtime 4.8 disposable Sudoku World, generated before the query.
Entity "R1C1" is declared.
Entity "R1C2" is declared.
Entity "R1C3" is declared.
Entity "R1C4" is declared.
Entity "R1C5" is declared.
Entity "R1C6" is declared.
Entity "R1C7" is declared.
Entity "R1C8" is declared.
Entity "R1C9" is declared.
Entity "R2C1" is declared.
Entity "R2C2" is declared.
Entity "R2C3" is declared.
Entity "R2C4" is declared.
Entity "R2C5" is declared.
Entity "R2C6" is declared.
Entity "R2C7" is declared.
Entity "R2C8" is declared.
Entity "R2C9" is declared.
Entity "R3C1" is declared.
Entity "R3C2" is declared.
Entity "R3C3" is declared.
Entity "R3C4" is declared.
Entity "R3C5" is declared.
Entity "R3C6" is declared.
Entity "R3C7" is declared.
Entity "R3C8" is declared.
Entity "R3C9" is declared.
Entity "R4C1" is declared.
Entity "R4C2" is declared.
Entity "R4C3" is declared.
Entity "R4C4" is declared.
Entity "R4C5" is declared.
Entity "R4C6" is declared.
Entity "R4C7" is declared.
Entity "R4C8" is declared.
Entity "R4C9" is declared.
Entity "R5C1" is declared.
Entity "R5C2" is declared.
Entity "R5C3" is declared.
Entity "R5C4" is declared.
Entity "R5C5" is declared.
Entity "R5C6" is declared.
Entity "R5C7" is declared.
Entity "R5C8" is declared.
Entity "R5C9" is declared.
Entity "R6C1" is declared.
Entity "R6C2" is declared.
Entity "R6C3" is declared.
Entity "R6C4" is declared.
Entity "R6C5" is declared.
Entity "R6C6" is declared.
Entity "R6C7" is declared.
Entity "R6C8" is declared.
Entity "R6C9" is declared.
Entity "R7C1" is declared.
Entity "R7C2" is declared.
Entity "R7C3" is declared.
Entity "R7C4" is declared.
Entity "R7C5" is declared.
Entity "R7C6" is declared.
Entity "R7C7" is declared.
Entity "R7C8" is declared.
Entity "R7C9" is declared.
Entity "R8C1" is declared.
Entity "R8C2" is declared.
Entity "R8C3" is declared.
Entity "R8C4" is declared.
Entity "R8C5" is declared.
Entity "R8C6" is declared.
Entity "R8C7" is declared.
Entity "R8C8" is declared.
Entity "R8C9" is declared.
Entity "R9C1" is declared.
Entity "R9C2" is declared.
Entity "R9C3" is declared.
Entity "R9C4" is declared.
Entity "R9C5" is declared.
Entity "R9C6" is declared.
Entity "R9C7" is declared.
Entity "R9C8" is declared.
Entity "R9C9" is declared.
Entity "DIGIT-1" is declared.
Entity "DIGIT-2" is declared.
Entity "DIGIT-3" is declared.
Entity "DIGIT-4" is declared.
Entity "DIGIT-5" is declared.
Entity "DIGIT-6" is declared.
Entity "DIGIT-7" is declared.
Entity "DIGIT-8" is declared.
Entity "DIGIT-9" is declared.
Entity "BLANK-0" is declared.
Entity "BLANK-DOT" is declared.
Entity "ROW-1" is declared.
Entity "ROW-2" is declared.
Entity "ROW-3" is declared.
Entity "ROW-4" is declared.
Entity "ROW-5" is declared.
Entity "ROW-6" is declared.
Entity "ROW-7" is declared.
Entity "ROW-8" is declared.
Entity "ROW-9" is declared.
Entity "COLUMN-1" is declared.
Entity "COLUMN-2" is declared.
Entity "COLUMN-3" is declared.
Entity "COLUMN-4" is declared.
Entity "COLUMN-5" is declared.
Entity "COLUMN-6" is declared.
Entity "COLUMN-7" is declared.
Entity "COLUMN-8" is declared.
Entity "COLUMN-9" is declared.
Entity "BOX-1" is declared.
Entity "BOX-2" is declared.
Entity "BOX-3" is declared.
Entity "BOX-4" is declared.
Entity "BOX-5" is declared.
Entity "BOX-6" is declared.
Entity "BOX-7" is declared.
Entity "BOX-8" is declared.
Entity "BOX-9" is declared.
Entity "RULE-CELL-DOMAIN" is declared.
Entity "RULE-EXACTLY-ONE" is declared.
Entity "RULE-ROW-ALL-DIFFERENT" is declared.
Entity "RULE-COLUMN-ALL-DIFFERENT" is declared.
Entity "RULE-BOX-ALL-DIFFERENT" is declared.
Entity "RULE-IMMUTABLE-GIVENS" is declared.
Entity "RULE-DETECT-CONTRADICTION" is declared.
Entity "RULE-UNIQUE-SOLUTION" is declared.
Entity "RULE-CANONICAL-RENDERING" is declared.
Directional relation "member-of" maps Meaning to Meaning and is multi-valued.
Relation form "membership-form" for relation "member-of" accepts "Cell {SOURCE} belongs to unit {DESTINATION}.".
Operation "solve-finite-csp" selects kernel primitive "SOLVE_FINITE_CSP".
Output schema "sudoku-grid" selects kernel schema "ANSWER_WITH_PROOF".
Program "sudoku-solver" is canonical step JSON "[{\"operation\":\"PARSE_COMPILED_GRID\"},{\"operation\":\"CLAMP_GIVENS\"},{\"operation\":\"PROPAGATE_DOMAINS\"},{\"operation\":\"SELECT_MINIMUM_DOMAIN\"},{\"operation\":\"EXPLORE_CANONICAL_CANDIDATES\"},{\"operation\":\"REJECT_VIOLATING_BRANCHES\"},{\"operation\":\"VERIFY_COMPLETE_ASSIGNMENT\"},{\"operation\":\"SEARCH_FOR_SECOND_SOLUTION\"},{\"operation\":\"RENDER_COMPILED_GRID\"}]".
Instruction "solve-sudoku" selects operation "solve-finite-csp" accepts "Solve {PROGRAM} with {BINDINGS} using {SCHEMA}.".
Cell "R1C1" belongs to unit "ROW-1".
Cell "R1C1" belongs to unit "COLUMN-1".
Cell "R1C1" belongs to unit "BOX-1".
Cell "R1C2" belongs to unit "ROW-1".
Cell "R1C2" belongs to unit "COLUMN-2".
Cell "R1C2" belongs to unit "BOX-1".
Cell "R1C3" belongs to unit "ROW-1".
Cell "R1C3" belongs to unit "COLUMN-3".
Cell "R1C3" belongs to unit "BOX-1".
Cell "R1C4" belongs to unit "ROW-1".
Cell "R1C4" belongs to unit "COLUMN-4".
Cell "R1C4" belongs to unit "BOX-2".
Cell "R1C5" belongs to unit "ROW-1".
Cell "R1C5" belongs to unit "COLUMN-5".
Cell "R1C5" belongs to unit "BOX-2".
Cell "R1C6" belongs to unit "ROW-1".
Cell "R1C6" belongs to unit "COLUMN-6".
Cell "R1C6" belongs to unit "BOX-2".
Cell "R1C7" belongs to unit "ROW-1".
Cell "R1C7" belongs to unit "COLUMN-7".
Cell "R1C7" belongs to unit "BOX-3".
Cell "R1C8" belongs to unit "ROW-1".
Cell "R1C8" belongs to unit "COLUMN-8".
Cell "R1C8" belongs to unit "BOX-3".
Cell "R1C9" belongs to unit "ROW-1".
Cell "R1C9" belongs to unit "COLUMN-9".
Cell "R1C9" belongs to unit "BOX-3".
Cell "R2C1" belongs to unit "ROW-2".
Cell "R2C1" belongs to unit "COLUMN-1".
Cell "R2C1" belongs to unit "BOX-1".
Cell "R2C2" belongs to unit "ROW-2".
Cell "R2C2" belongs to unit "COLUMN-2".
Cell "R2C2" belongs to unit "BOX-1".
Cell "R2C3" belongs to unit "ROW-2".
Cell "R2C3" belongs to unit "COLUMN-3".
Cell "R2C3" belongs to unit "BOX-1".
Cell "R2C4" belongs to unit "ROW-2".
Cell "R2C4" belongs to unit "COLUMN-4".
Cell "R2C4" belongs to unit "BOX-2".
Cell "R2C5" belongs to unit "ROW-2".
Cell "R2C5" belongs to unit "COLUMN-5".
Cell "R2C5" belongs to unit "BOX-2".
Cell "R2C6" belongs to unit "ROW-2".
Cell "R2C6" belongs to unit "COLUMN-6".
Cell "R2C6" belongs to unit "BOX-2".
Cell "R2C7" belongs to unit "ROW-2".
Cell "R2C7" belongs to unit "COLUMN-7".
Cell "R2C7" belongs to unit "BOX-3".
Cell "R2C8" belongs to unit "ROW-2".
Cell "R2C8" belongs to unit "COLUMN-8".
Cell "R2C8" belongs to unit "BOX-3".
Cell "R2C9" belongs to unit "ROW-2".
Cell "R2C9" belongs to unit "COLUMN-9".
Cell "R2C9" belongs to unit "BOX-3".
Cell "R3C1" belongs to unit "ROW-3".
Cell "R3C1" belongs to unit "COLUMN-1".
Cell "R3C1" belongs to unit "BOX-1".
Cell "R3C2" belongs to unit "ROW-3".
Cell "R3C2" belongs to unit "COLUMN-2".
Cell "R3C2" belongs to unit "BOX-1".
Cell "R3C3" belongs to unit "ROW-3".
Cell "R3C3" belongs to unit "COLUMN-3".
Cell "R3C3" belongs to unit "BOX-1".
Cell "R3C4" belongs to unit "ROW-3".
Cell "R3C4" belongs to unit "COLUMN-4".
Cell "R3C4" belongs to unit "BOX-2".
Cell "R3C5" belongs to unit "ROW-3".
Cell "R3C5" belongs to unit "COLUMN-5".
Cell "R3C5" belongs to unit "BOX-2".
Cell "R3C6" belongs to unit "ROW-3".
Cell "R3C6" belongs to unit "COLUMN-6".
Cell "R3C6" belongs to unit "BOX-2".
Cell "R3C7" belongs to unit "ROW-3".
Cell "R3C7" belongs to unit "COLUMN-7".
Cell "R3C7" belongs to unit "BOX-3".
Cell "R3C8" belongs to unit "ROW-3".
Cell "R3C8" belongs to unit "COLUMN-8".
Cell "R3C8" belongs to unit "BOX-3".
Cell "R3C9" belongs to unit "ROW-3".
Cell "R3C9" belongs to unit "COLUMN-9".
Cell "R3C9" belongs to unit "BOX-3".
Cell "R4C1" belongs to unit "ROW-4".
Cell "R4C1" belongs to unit "COLUMN-1".
Cell "R4C1" belongs to unit "BOX-4".
Cell "R4C2" belongs to unit "ROW-4".
Cell "R4C2" belongs to unit "COLUMN-2".
Cell "R4C2" belongs to unit "BOX-4".
Cell "R4C3" belongs to unit "ROW-4".
Cell "R4C3" belongs to unit "COLUMN-3".
Cell "R4C3" belongs to unit "BOX-4".
Cell "R4C4" belongs to unit "ROW-4".
Cell "R4C4" belongs to unit "COLUMN-4".
Cell "R4C4" belongs to unit "BOX-5".
Cell "R4C5" belongs to unit "ROW-4".
Cell "R4C5" belongs to unit "COLUMN-5".
Cell "R4C5" belongs to unit "BOX-5".
Cell "R4C6" belongs to unit "ROW-4".
Cell "R4C6" belongs to unit "COLUMN-6".
Cell "R4C6" belongs to unit "BOX-5".
Cell "R4C7" belongs to unit "ROW-4".
Cell "R4C7" belongs to unit "COLUMN-7".
Cell "R4C7" belongs to unit "BOX-6".
Cell "R4C8" belongs to unit "ROW-4".
Cell "R4C8" belongs to unit "COLUMN-8".
Cell "R4C8" belongs to unit "BOX-6".
Cell "R4C9" belongs to unit "ROW-4".
Cell "R4C9" belongs to unit "COLUMN-9".
Cell "R4C9" belongs to unit "BOX-6".
Cell "R5C1" belongs to unit "ROW-5".
Cell "R5C1" belongs to unit "COLUMN-1".
Cell "R5C1" belongs to unit "BOX-4".
Cell "R5C2" belongs to unit "ROW-5".
Cell "R5C2" belongs to unit "COLUMN-2".
Cell "R5C2" belongs to unit "BOX-4".
Cell "R5C3" belongs to unit "ROW-5".
Cell "R5C3" belongs to unit "COLUMN-3".
Cell "R5C3" belongs to unit "BOX-4".
Cell "R5C4" belongs to unit "ROW-5".
Cell "R5C4" belongs to unit "COLUMN-4".
Cell "R5C4" belongs to unit "BOX-5".
Cell "R5C5" belongs to unit "ROW-5".
Cell "R5C5" belongs to unit "COLUMN-5".
Cell "R5C5" belongs to unit "BOX-5".
Cell "R5C6" belongs to unit "ROW-5".
Cell "R5C6" belongs to unit "COLUMN-6".
Cell "R5C6" belongs to unit "BOX-5".
Cell "R5C7" belongs to unit "ROW-5".
Cell "R5C7" belongs to unit "COLUMN-7".
Cell "R5C7" belongs to unit "BOX-6".
Cell "R5C8" belongs to unit "ROW-5".
Cell "R5C8" belongs to unit "COLUMN-8".
Cell "R5C8" belongs to unit "BOX-6".
Cell "R5C9" belongs to unit "ROW-5".
Cell "R5C9" belongs to unit "COLUMN-9".
Cell "R5C9" belongs to unit "BOX-6".
Cell "R6C1" belongs to unit "ROW-6".
Cell "R6C1" belongs to unit "COLUMN-1".
Cell "R6C1" belongs to unit "BOX-4".
Cell "R6C2" belongs to unit "ROW-6".
Cell "R6C2" belongs to unit "COLUMN-2".
Cell "R6C2" belongs to unit "BOX-4".
Cell "R6C3" belongs to unit "ROW-6".
Cell "R6C3" belongs to unit "COLUMN-3".
Cell "R6C3" belongs to unit "BOX-4".
Cell "R6C4" belongs to unit "ROW-6".
Cell "R6C4" belongs to unit "COLUMN-4".
Cell "R6C4" belongs to unit "BOX-5".
Cell "R6C5" belongs to unit "ROW-6".
Cell "R6C5" belongs to unit "COLUMN-5".
Cell "R6C5" belongs to unit "BOX-5".
Cell "R6C6" belongs to unit "ROW-6".
Cell "R6C6" belongs to unit "COLUMN-6".
Cell "R6C6" belongs to unit "BOX-5".
Cell "R6C7" belongs to unit "ROW-6".
Cell "R6C7" belongs to unit "COLUMN-7".
Cell "R6C7" belongs to unit "BOX-6".
Cell "R6C8" belongs to unit "ROW-6".
Cell "R6C8" belongs to unit "COLUMN-8".
Cell "R6C8" belongs to unit "BOX-6".
Cell "R6C9" belongs to unit "ROW-6".
Cell "R6C9" belongs to unit "COLUMN-9".
Cell "R6C9" belongs to unit "BOX-6".
Cell "R7C1" belongs to unit "ROW-7".
Cell "R7C1" belongs to unit "COLUMN-1".
Cell "R7C1" belongs to unit "BOX-7".
Cell "R7C2" belongs to unit "ROW-7".
Cell "R7C2" belongs to unit "COLUMN-2".
Cell "R7C2" belongs to unit "BOX-7".
Cell "R7C3" belongs to unit "ROW-7".
Cell "R7C3" belongs to unit "COLUMN-3".
Cell "R7C3" belongs to unit "BOX-7".
Cell "R7C4" belongs to unit "ROW-7".
Cell "R7C4" belongs to unit "COLUMN-4".
Cell "R7C4" belongs to unit "BOX-8".
Cell "R7C5" belongs to unit "ROW-7".
Cell "R7C5" belongs to unit "COLUMN-5".
Cell "R7C5" belongs to unit "BOX-8".
Cell "R7C6" belongs to unit "ROW-7".
Cell "R7C6" belongs to unit "COLUMN-6".
Cell "R7C6" belongs to unit "BOX-8".
Cell "R7C7" belongs to unit "ROW-7".
Cell "R7C7" belongs to unit "COLUMN-7".
Cell "R7C7" belongs to unit "BOX-9".
Cell "R7C8" belongs to unit "ROW-7".
Cell "R7C8" belongs to unit "COLUMN-8".
Cell "R7C8" belongs to unit "BOX-9".
Cell "R7C9" belongs to unit "ROW-7".
Cell "R7C9" belongs to unit "COLUMN-9".
Cell "R7C9" belongs to unit "BOX-9".
Cell "R8C1" belongs to unit "ROW-8".
Cell "R8C1" belongs to unit "COLUMN-1".
Cell "R8C1" belongs to unit "BOX-7".
Cell "R8C2" belongs to unit "ROW-8".
Cell "R8C2" belongs to unit "COLUMN-2".
Cell "R8C2" belongs to unit "BOX-7".
Cell "R8C3" belongs to unit "ROW-8".
Cell "R8C3" belongs to unit "COLUMN-3".
Cell "R8C3" belongs to unit "BOX-7".
Cell "R8C4" belongs to unit "ROW-8".
Cell "R8C4" belongs to unit "COLUMN-4".
Cell "R8C4" belongs to unit "BOX-8".
Cell "R8C5" belongs to unit "ROW-8".
Cell "R8C5" belongs to unit "COLUMN-5".
Cell "R8C5" belongs to unit "BOX-8".
Cell "R8C6" belongs to unit "ROW-8".
Cell "R8C6" belongs to unit "COLUMN-6".
Cell "R8C6" belongs to unit "BOX-8".
Cell "R8C7" belongs to unit "ROW-8".
Cell "R8C7" belongs to unit "COLUMN-7".
Cell "R8C7" belongs to unit "BOX-9".
Cell "R8C8" belongs to unit "ROW-8".
Cell "R8C8" belongs to unit "COLUMN-8".
Cell "R8C8" belongs to unit "BOX-9".
Cell "R8C9" belongs to unit "ROW-8".
Cell "R8C9" belongs to unit "COLUMN-9".
Cell "R8C9" belongs to unit "BOX-9".
Cell "R9C1" belongs to unit "ROW-9".
Cell "R9C1" belongs to unit "COLUMN-1".
Cell "R9C1" belongs to unit "BOX-7".
Cell "R9C2" belongs to unit "ROW-9".
Cell "R9C2" belongs to unit "COLUMN-2".
Cell "R9C2" belongs to unit "BOX-7".
Cell "R9C3" belongs to unit "ROW-9".
Cell "R9C3" belongs to unit "COLUMN-3".
Cell "R9C3" belongs to unit "BOX-7".
Cell "R9C4" belongs to unit "ROW-9".
Cell "R9C4" belongs to unit "COLUMN-4".
Cell "R9C4" belongs to unit "BOX-8".
Cell "R9C5" belongs to unit "ROW-9".
Cell "R9C5" belongs to unit "COLUMN-5".
Cell "R9C5" belongs to unit "BOX-8".
Cell "R9C6" belongs to unit "ROW-9".
Cell "R9C6" belongs to unit "COLUMN-6".
Cell "R9C6" belongs to unit "BOX-8".
Cell "R9C7" belongs to unit "ROW-9".
Cell "R9C7" belongs to unit "COLUMN-7".
Cell "R9C7" belongs to unit "BOX-9".
Cell "R9C8" belongs to unit "ROW-9".
Cell "R9C8" belongs to unit "COLUMN-8".
Cell "R9C8" belongs to unit "BOX-9".
Cell "R9C9" belongs to unit "ROW-9".
Cell "R9C9" belongs to unit "COLUMN-9".
Cell "R9C9" belongs to unit "BOX-9".
```

The Main World contains the same closed vocabulary and program plus all 243 exact cell-to-row, cell-to-column, and cell-to-box membership edges.

## Exact Surface World source

```text
Operation "realize-semantic-result" selects kernel primitive "REALIZE_SEMANTIC_RESULT".
Instruction "realize-semantic-result" selects operation "realize-semantic-result" accepts "Realize the verified semantic result.".
```

The Surface World only realizes the already verified semantic result; it cannot alter the solution.

## Exact prompt

```text
Solve this Sudoku using the compiled Sudoku rules:
530070000
600195000
098000060
800060003
400803001
700020006
060000280
000419005
000080079
```

The 81-character grid was transient query data. It was not inserted into any persistent World source.

## Actual response

```json
{"kind":"SUDOKU_GRID","value":{"rows":["534678912","672195348","198342567","859761423","426853791","713924856","961537284","287419635","345286179"],"unique":true}}
```

Rendered grid:

```text
534678912
672195348
198342567
859761423
426853791
713924856
961537284
287419635
345286179
```

## Verification receipt

```json
{
  "bundle_hash": "95ee13aa09322e8fdd34d6df18ee384f2ad55956e40e6b3ce30cfbbbdf35ce09",
  "bundle_id": "d091361add0877995f78a4ae2d9b9d0093fbcc871521c77f5508504c9ce1486b",
  "dispatch_count": 0,
  "disposable_store_status_before_deletion": {
    "active_bundle": "d091361add0877995f78a4ae2d9b9d0093fbcc871521c77f5508504c9ce1486b",
    "bundles": 1,
    "episodes": 1,
    "generations": 3,
    "heads": {
      "INPUT": "91992252b587d09b6ef1fb9cb03defdeb2daebb72b24cb80f85c6f2e9c478c37",
      "MAIN": "cb2d0171bd7c5a31a327fb94ae6a99c5a747f993e7cf7b26034661d07fc86d5a",
      "SURFACE": "dec9241a67e5913768d445a99b243dea9f00bf1590e9c1ca63cf6a6946cee6d7"
    },
    "runtime": "4.8",
    "schema": "proof-energy-world-store/4.8"
  },
  "encoder_free_replay_byte_exact": true,
  "episode_id": "06871e0a991401800d6bd756eceefadd475b4cd3b091118e972befdc1552fdfd",
  "execution_performed": false,
  "handoff_hashes": [
    "3d1a426546e4483fd25d3678ed117435e4745a2d78cb443dfaefed7273698af7",
    "f1a616280289099a7001874da2c138715fb118efa794ff814d9bd0f6d423e5f9"
  ],
  "independent_solution_and_uniqueness_verified": true,
  "input_hash": "43badced6a24548bb1aefc20cc18bf7c57ae842f9d3d90bb423aca83ba8d6e5e",
  "main_constraint_proof_edges": 243,
  "network_attempts": 0,
  "prompt_or_solution_present_in_persistent_source": false,
  "result_hash": "7b7e71cf57399412e25b055b8ce8562c53a0dc39cf780cba7a212620ad6bf316",
  "result_schema": "moth-world-result/4.8",
  "runtime": "4.8",
  "stage_energy_units": [
    0,
    0,
    0
  ],
  "stage_output_kinds": [
    "MAIN_REQUEST",
    "SEMANTIC_RESULT",
    "SURFACE_RESPONSE"
  ],
  "stage_proof_counts": [
    1,
    1,
    1
  ],
  "stage_roles": [
    "INPUT",
    "MAIN",
    "SURFACE"
  ],
  "stage_violation_counts": [
    0,
    0,
    0
  ],
  "worlds": {
    "INPUT": {
      "generation_id": "91992252b587d09b6ef1fb9cb03defdeb2daebb72b24cb80f85c6f2e9c478c37",
      "source_sha256": "93c25970c0006a9c245abf481f6df17ff45fd921e21374f6cb99d14b6bc5285a",
      "world_hash": "7f285d36c7fa18654a3cc4166f5980aebea324ff0a394363493046509d0cc235"
    },
    "MAIN": {
      "generation_id": "cb2d0171bd7c5a31a327fb94ae6a99c5a747f993e7cf7b26034661d07fc86d5a",
      "membership_edges": 243,
      "source_sha256": "0fd2e0d9f8ad7289ae48668f0f5a940afaf250232c1fab00457584b7fc8ddc27",
      "world_hash": "59cca662b6d21477836f2bea4cd9f3e2446c42de2c0894d67ecf2eb6db37ac05"
    },
    "SURFACE": {
      "generation_id": "dec9241a67e5913768d445a99b243dea9f00bf1590e9c1ca63cf6a6946cee6d7",
      "source_sha256": "75aec1ef7589f3b502fe73e6950258449d3538221a34787f34a060d981f3f12c",
      "world_hash": "d1dce1d45186126df32c4dc30278f217d698e106e7c9567076df9df8722f67af"
    }
  }
}
```

## Meaning of the result

- Prompt grounding happened once, before Input World settlement.
- Input World emitted a typed, identifier-only `MAIN_REQUEST`.
- Main World solved the transient grid under compiled unit memberships and constraint identities.
- Surface World returned the verified grid without re-grounding text.
- A separate verifier checked every given, row, column, box, and uniqueness.
- Encoder-free replay reproduced the exact proof-bearing result bytes.
- Runtime execution and dispatch were zero; no network connection occurred.
- The disposable field and all executable experiment material were removed.
