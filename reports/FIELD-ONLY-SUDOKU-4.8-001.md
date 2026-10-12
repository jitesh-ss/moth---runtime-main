# Runtime 4.8 Field-Only Sudoku Audit

Date: 2026-08-31  
Verdict: **`NO_GO_INSTRUCTION_EXECUTION`**

## Decisive result

The unmodified Runtime 4.8 field did **not** solve the unseen Sudoku from granular compiled instruction meanings.

The required prompt matched the compiled instruction envelope and Program alias, but grounding refused the transient grid because Runtime 4.8 only parses structured input as compiled `field = value` pairs. Therefore the required prompt produced no World settlement. A diagnostic containing the same puzzle values in that existing binding syntax reached Input World, which produced a verified `MAIN_REQUEST`; Main World then refused `UNSUPPORTED_PROGRAM`. The compiled candidate-elimination, branching, restoration, completion, and uniqueness names were passive memories and step metadata, not executable state transitions.

No `SOLVE_FINITE_CSP`, Sudoku solver, propagation, search, enumeration, SAT/CSP/SMT library, solution-producing verifier, runtime patch, query-time learning, LLM, hidden target, or hardcoded Sudoku behavior was used.

## Exact baseline source compiled into Input and Main Worlds

```text
# Exact field-only Sudoku compilation for Runtime 4.8.
# These are provenance-bearing memories; no solver primitive is declared.
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
Entity "0" is declared.
Entity "1" is declared.
Entity "2" is declared.
Entity "3" is declared.
Entity "4" is declared.
Entity "5" is declared.
Entity "6" is declared.
Entity "7" is declared.
Entity "8" is declared.
Entity "9" is declared.
Entity "." is declared.
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
Entity "DOMAIN-R1C1" is declared.
Entity "DOMAIN-R1C2" is declared.
Entity "DOMAIN-R1C3" is declared.
Entity "DOMAIN-R1C4" is declared.
Entity "DOMAIN-R1C5" is declared.
Entity "DOMAIN-R1C6" is declared.
Entity "DOMAIN-R1C7" is declared.
Entity "DOMAIN-R1C8" is declared.
Entity "DOMAIN-R1C9" is declared.
Entity "DOMAIN-R2C1" is declared.
Entity "DOMAIN-R2C2" is declared.
Entity "DOMAIN-R2C3" is declared.
Entity "DOMAIN-R2C4" is declared.
Entity "DOMAIN-R2C5" is declared.
Entity "DOMAIN-R2C6" is declared.
Entity "DOMAIN-R2C7" is declared.
Entity "DOMAIN-R2C8" is declared.
Entity "DOMAIN-R2C9" is declared.
Entity "DOMAIN-R3C1" is declared.
Entity "DOMAIN-R3C2" is declared.
Entity "DOMAIN-R3C3" is declared.
Entity "DOMAIN-R3C4" is declared.
Entity "DOMAIN-R3C5" is declared.
Entity "DOMAIN-R3C6" is declared.
Entity "DOMAIN-R3C7" is declared.
Entity "DOMAIN-R3C8" is declared.
Entity "DOMAIN-R3C9" is declared.
Entity "DOMAIN-R4C1" is declared.
Entity "DOMAIN-R4C2" is declared.
Entity "DOMAIN-R4C3" is declared.
Entity "DOMAIN-R4C4" is declared.
Entity "DOMAIN-R4C5" is declared.
Entity "DOMAIN-R4C6" is declared.
Entity "DOMAIN-R4C7" is declared.
Entity "DOMAIN-R4C8" is declared.
Entity "DOMAIN-R4C9" is declared.
Entity "DOMAIN-R5C1" is declared.
Entity "DOMAIN-R5C2" is declared.
Entity "DOMAIN-R5C3" is declared.
Entity "DOMAIN-R5C4" is declared.
Entity "DOMAIN-R5C5" is declared.
Entity "DOMAIN-R5C6" is declared.
Entity "DOMAIN-R5C7" is declared.
Entity "DOMAIN-R5C8" is declared.
Entity "DOMAIN-R5C9" is declared.
Entity "DOMAIN-R6C1" is declared.
Entity "DOMAIN-R6C2" is declared.
Entity "DOMAIN-R6C3" is declared.
Entity "DOMAIN-R6C4" is declared.
Entity "DOMAIN-R6C5" is declared.
Entity "DOMAIN-R6C6" is declared.
Entity "DOMAIN-R6C7" is declared.
Entity "DOMAIN-R6C8" is declared.
Entity "DOMAIN-R6C9" is declared.
Entity "DOMAIN-R7C1" is declared.
Entity "DOMAIN-R7C2" is declared.
Entity "DOMAIN-R7C3" is declared.
Entity "DOMAIN-R7C4" is declared.
Entity "DOMAIN-R7C5" is declared.
Entity "DOMAIN-R7C6" is declared.
Entity "DOMAIN-R7C7" is declared.
Entity "DOMAIN-R7C8" is declared.
Entity "DOMAIN-R7C9" is declared.
Entity "DOMAIN-R8C1" is declared.
Entity "DOMAIN-R8C2" is declared.
Entity "DOMAIN-R8C3" is declared.
Entity "DOMAIN-R8C4" is declared.
Entity "DOMAIN-R8C5" is declared.
Entity "DOMAIN-R8C6" is declared.
Entity "DOMAIN-R8C7" is declared.
Entity "DOMAIN-R8C8" is declared.
Entity "DOMAIN-R8C9" is declared.
Entity "DOMAIN-R9C1" is declared.
Entity "DOMAIN-R9C2" is declared.
Entity "DOMAIN-R9C3" is declared.
Entity "DOMAIN-R9C4" is declared.
Entity "DOMAIN-R9C5" is declared.
Entity "DOMAIN-R9C6" is declared.
Entity "DOMAIN-R9C7" is declared.
Entity "DOMAIN-R9C8" is declared.
Entity "DOMAIN-R9C9" is declared.
Entity "EQUALITY" is declared.
Entity "INEQUALITY" is declared.
Entity "ASSIGNMENT" is declared.
Entity "EXCLUSION" is declared.
Entity "EXACTLY-ONE-VALUE-REQUIREMENT" is declared.
Entity "ALL-DIFFERENT-REQUIREMENT" is declared.
Entity "IMMUTABLE-GIVEN-REQUIREMENT" is declared.
Entity "CONTRADICTION" is declared.
Entity "COMPLETE-ASSIGNMENT" is declared.
Entity "UNIQUE-ASSIGNMENT" is declared.
Entity "SUDOKU-GRANULAR-PROGRAM" is declared.
Entity "INSTRUCTION-EXACTLY-ONE" is declared.
Entity "INSTRUCTION-ROW-ALL-DIFFERENT" is declared.
Entity "INSTRUCTION-COLUMN-ALL-DIFFERENT" is declared.
Entity "INSTRUCTION-BOX-ALL-DIFFERENT" is declared.
Entity "INSTRUCTION-IMMUTABLE-GIVENS" is declared.
Entity "INSTRUCTION-CONTRADICTION-DETECTION" is declared.
Entity "INSTRUCTION-CANDIDATE-ELIMINATION" is declared.
Entity "INSTRUCTION-MINIMUM-DOMAIN-SELECTION" is declared.
Entity "INSTRUCTION-BRANCHING" is declared.
Entity "INSTRUCTION-CONTRADICTION-REJECTION" is declared.
Entity "INSTRUCTION-RESTORATION" is declared.
Entity "INSTRUCTION-COMPLETION" is declared.
Entity "INSTRUCTION-UNIQUENESS-CHECKING" is declared.
Entity "INSTRUCTION-DETERMINISTIC-RENDERING" is declared.
Directional relation "member-of" maps Meaning to Meaning and is multi-valued.
Relation form "form-1" for relation "member-of" accepts "Cell {SOURCE} belongs to unit {DESTINATION}.".
Directional relation "has-domain" maps Meaning to Meaning and is multi-valued.
Relation form "form-2" for relation "has-domain" accepts "Cell {SOURCE} has candidate domain {DESTINATION}.".
Directional relation "domain-allows" maps Meaning to Meaning and is multi-valued.
Relation form "form-3" for relation "domain-allows" accepts "Domain {SOURCE} allows digit {DESTINATION}.".
Directional relation "equal-to" maps Meaning to Meaning and is multi-valued.
Relation form "form-4" for relation "equal-to" accepts "Digit {SOURCE} equals digit {DESTINATION}.".
Directional relation "not-equal-to" maps Meaning to Meaning and is multi-valued.
Relation form "form-5" for relation "not-equal-to" accepts "Digit {SOURCE} differs from digit {DESTINATION}.".
Directional relation "requires" maps Meaning to Meaning and is multi-valued.
Relation form "form-6" for relation "requires" accepts "Program {SOURCE} requires rule {DESTINATION}.".
Directional relation "precedes" maps Meaning to Meaning and is multi-valued.
Relation form "form-7" for relation "precedes" accepts "Rule {SOURCE} precedes rule {DESTINATION}.".
Directional relation "licenses" maps Meaning to Meaning and is multi-valued.
Relation form "form-8" for relation "licenses" accepts "Rule {SOURCE} licenses semantic action {DESTINATION}.".
Scalar type "cell-value" selects kernel type "STRING".
Structured schema "sudoku-transient-bindings-1" is canonical JSON Schema "{\"additionalProperties\":false,\"properties\":{\"R1C1\":{\"type\":\"string\",\"x-moth-field\":\"R1C1\"},\"R1C2\":{\"type\":\"string\",\"x-moth-field\":\"R1C2\"},\"R1C3\":{\"type\":\"string\",\"x-moth-field\":\"R1C3\"},\"R1C4\":{\"type\":\"string\",\"x-moth-field\":\"R1C4\"},\"R1C5\":{\"type\":\"string\",\"x-moth-field\":\"R1C5\"},\"R1C6\":{\"type\":\"string\",\"x-moth-field\":\"R1C6\"},\"R1C7\":{\"type\":\"string\",\"x-moth-field\":\"R1C7\"},\"R1C8\":{\"type\":\"string\",\"x-moth-field\":\"R1C8\"},\"R1C9\":{\"type\":\"string\",\"x-moth-field\":\"R1C9\"},\"R2C1\":{\"type\":\"string\",\"x-moth-field\":\"R2C1\"},\"R2C2\":{\"type\":\"string\",\"x-moth-field\":\"R2C2\"},\"R2C3\":{\"type\":\"string\",\"x-moth-field\":\"R2C3\"},\"R2C4\":{\"type\":\"string\",\"x-moth-field\":\"R2C4\"},\"R2C5\":{\"type\":\"string\",\"x-moth-field\":\"R2C5\"},\"R2C6\":{\"type\":\"string\",\"x-moth-field\":\"R2C6\"},\"R2C7\":{\"type\":\"string\",\"x-moth-field\":\"R2C7\"},\"R2C8\":{\"type\":\"string\",\"x-moth-field\":\"R2C8\"},\"R2C9\":{\"type\":\"string\",\"x-moth-field\":\"R2C9\"},\"R3C1\":{\"type\":\"string\",\"x-moth-field\":\"R3C1\"},\"R3C2\":{\"type\":\"string\",\"x-moth-field\":\"R3C2\"},\"R3C3\":{\"type\":\"string\",\"x-moth-field\":\"R3C3\"},\"R3C4\":{\"type\":\"string\",\"x-moth-field\":\"R3C4\"},\"R3C5\":{\"type\":\"string\",\"x-moth-field\":\"R3C5\"},\"R3C6\":{\"type\":\"string\",\"x-moth-field\":\"R3C6\"},\"R3C7\":{\"type\":\"string\",\"x-moth-field\":\"R3C7\"},\"R3C8\":{\"type\":\"string\",\"x-moth-field\":\"R3C8\"},\"R3C9\":{\"type\":\"string\",\"x-moth-field\":\"R3C9\"},\"R4C1\":{\"type\":\"string\",\"x-moth-field\":\"R4C1\"},\"R4C2\":{\"type\":\"string\",\"x-moth-field\":\"R4C2\"},\"R4C3\":{\"type\":\"string\",\"x-moth-field\":\"R4C3\"},\"R4C4\":{\"type\":\"string\",\"x-moth-field\":\"R4C4\"},\"R4C5\":{\"type\":\"string\",\"x-moth-field\":\"R4C5\"},\"R4C6\":{\"type\":\"string\",\"x-moth-field\":\"R4C6\"},\"R4C7\":{\"type\":\"string\",\"x-moth-field\":\"R4C7\"},\"R4C8\":{\"type\":\"string\",\"x-moth-field\":\"R4C8\"},\"R4C9\":{\"type\":\"string\",\"x-moth-field\":\"R4C9\"},\"R5C1\":{\"type\":\"string\",\"x-moth-field\":\"R5C1\"},\"R5C2\":{\"type\":\"string\",\"x-moth-field\":\"R5C2\"},\"R5C3\":{\"type\":\"string\",\"x-moth-field\":\"R5C3\"},\"R5C4\":{\"type\":\"string\",\"x-moth-field\":\"R5C4\"},\"R5C5\":{\"type\":\"string\",\"x-moth-field\":\"R5C5\"}},\"required\":[\"R1C1\",\"R1C2\",\"R1C3\",\"R1C4\",\"R1C5\",\"R1C6\",\"R1C7\",\"R1C8\",\"R1C9\",\"R2C1\",\"R2C2\",\"R2C3\",\"R2C4\",\"R2C5\",\"R2C6\",\"R2C7\",\"R2C8\",\"R2C9\",\"R3C1\",\"R3C2\",\"R3C3\",\"R3C4\",\"R3C5\",\"R3C6\",\"R3C7\",\"R3C8\",\"R3C9\",\"R4C1\",\"R4C2\",\"R4C3\",\"R4C4\",\"R4C5\",\"R4C6\",\"R4C7\",\"R4C8\",\"R4C9\",\"R5C1\",\"R5C2\",\"R5C3\",\"R5C4\",\"R5C5\"],\"type\":\"object\"}".
Structured schema "sudoku-transient-bindings-2" is canonical JSON Schema "{\"additionalProperties\":false,\"properties\":{\"R5C6\":{\"type\":\"string\",\"x-moth-field\":\"R5C6\"},\"R5C7\":{\"type\":\"string\",\"x-moth-field\":\"R5C7\"},\"R5C8\":{\"type\":\"string\",\"x-moth-field\":\"R5C8\"},\"R5C9\":{\"type\":\"string\",\"x-moth-field\":\"R5C9\"},\"R6C1\":{\"type\":\"string\",\"x-moth-field\":\"R6C1\"},\"R6C2\":{\"type\":\"string\",\"x-moth-field\":\"R6C2\"},\"R6C3\":{\"type\":\"string\",\"x-moth-field\":\"R6C3\"},\"R6C4\":{\"type\":\"string\",\"x-moth-field\":\"R6C4\"},\"R6C5\":{\"type\":\"string\",\"x-moth-field\":\"R6C5\"},\"R6C6\":{\"type\":\"string\",\"x-moth-field\":\"R6C6\"},\"R6C7\":{\"type\":\"string\",\"x-moth-field\":\"R6C7\"},\"R6C8\":{\"type\":\"string\",\"x-moth-field\":\"R6C8\"},\"R6C9\":{\"type\":\"string\",\"x-moth-field\":\"R6C9\"},\"R7C1\":{\"type\":\"string\",\"x-moth-field\":\"R7C1\"},\"R7C2\":{\"type\":\"string\",\"x-moth-field\":\"R7C2\"},\"R7C3\":{\"type\":\"string\",\"x-moth-field\":\"R7C3\"},\"R7C4\":{\"type\":\"string\",\"x-moth-field\":\"R7C4\"},\"R7C5\":{\"type\":\"string\",\"x-moth-field\":\"R7C5\"},\"R7C6\":{\"type\":\"string\",\"x-moth-field\":\"R7C6\"},\"R7C7\":{\"type\":\"string\",\"x-moth-field\":\"R7C7\"},\"R7C8\":{\"type\":\"string\",\"x-moth-field\":\"R7C8\"},\"R7C9\":{\"type\":\"string\",\"x-moth-field\":\"R7C9\"},\"R8C1\":{\"type\":\"string\",\"x-moth-field\":\"R8C1\"},\"R8C2\":{\"type\":\"string\",\"x-moth-field\":\"R8C2\"},\"R8C3\":{\"type\":\"string\",\"x-moth-field\":\"R8C3\"},\"R8C4\":{\"type\":\"string\",\"x-moth-field\":\"R8C4\"},\"R8C5\":{\"type\":\"string\",\"x-moth-field\":\"R8C5\"},\"R8C6\":{\"type\":\"string\",\"x-moth-field\":\"R8C6\"},\"R8C7\":{\"type\":\"string\",\"x-moth-field\":\"R8C7\"},\"R8C8\":{\"type\":\"string\",\"x-moth-field\":\"R8C8\"},\"R8C9\":{\"type\":\"string\",\"x-moth-field\":\"R8C9\"},\"R9C1\":{\"type\":\"string\",\"x-moth-field\":\"R9C1\"},\"R9C2\":{\"type\":\"string\",\"x-moth-field\":\"R9C2\"},\"R9C3\":{\"type\":\"string\",\"x-moth-field\":\"R9C3\"},\"R9C4\":{\"type\":\"string\",\"x-moth-field\":\"R9C4\"},\"R9C5\":{\"type\":\"string\",\"x-moth-field\":\"R9C5\"},\"R9C6\":{\"type\":\"string\",\"x-moth-field\":\"R9C6\"},\"R9C7\":{\"type\":\"string\",\"x-moth-field\":\"R9C7\"},\"R9C8\":{\"type\":\"string\",\"x-moth-field\":\"R9C8\"},\"R9C9\":{\"type\":\"string\",\"x-moth-field\":\"R9C9\"}},\"required\":[\"R5C6\",\"R5C7\",\"R5C8\",\"R5C9\",\"R6C1\",\"R6C2\",\"R6C3\",\"R6C4\",\"R6C5\",\"R6C6\",\"R6C7\",\"R6C8\",\"R6C9\",\"R7C1\",\"R7C2\",\"R7C3\",\"R7C4\",\"R7C5\",\"R7C6\",\"R7C7\",\"R7C8\",\"R7C9\",\"R8C1\",\"R8C2\",\"R8C3\",\"R8C4\",\"R8C5\",\"R8C6\",\"R8C7\",\"R8C8\",\"R8C9\",\"R9C1\",\"R9C2\",\"R9C3\",\"R9C4\",\"R9C5\",\"R9C6\",\"R9C7\",\"R9C8\",\"R9C9\"],\"type\":\"object\"}".
Schema field "R1C1" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R1C2" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R1C3" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R1C4" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R1C5" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R1C6" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R1C7" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R1C8" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R1C9" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R2C1" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R2C2" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R2C3" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R2C4" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R2C5" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R2C6" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R2C7" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R2C8" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R2C9" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R3C1" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R3C2" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R3C3" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R3C4" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R3C5" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R3C6" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R3C7" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R3C8" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R3C9" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R4C1" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R4C2" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R4C3" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R4C4" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R4C5" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R4C6" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R4C7" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R4C8" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R4C9" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R5C1" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R5C2" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R5C3" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R5C4" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R5C5" in schema "sudoku-transient-bindings-1" has type "cell-value" and is required.
Schema field "R5C6" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R5C7" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R5C8" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R5C9" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R6C1" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R6C2" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R6C3" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R6C4" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R6C5" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R6C6" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R6C7" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R6C8" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R6C9" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R7C1" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R7C2" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R7C3" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R7C4" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R7C5" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R7C6" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R7C7" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R7C8" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R7C9" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R8C1" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R8C2" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R8C3" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R8C4" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R8C5" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R8C6" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R8C7" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R8C8" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R8C9" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R9C1" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R9C2" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R9C3" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R9C4" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R9C5" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R9C6" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R9C7" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R9C8" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Schema field "R9C9" in schema "sudoku-transient-bindings-2" has type "cell-value" and is required.
Operation "sudoku-instruction-sequence" selects kernel primitive "LINEAR_PIPELINE".
Program "sudoku-granular-program" is canonical step JSON "[{\"compiled_instruction\":\"INSTRUCTION-EXACTLY-ONE\",\"operation\":\"LOOKUP\"},{\"compiled_instruction\":\"INSTRUCTION-ROW-ALL-DIFFERENT\",\"operation\":\"LOOKUP\"},{\"compiled_instruction\":\"INSTRUCTION-COLUMN-ALL-DIFFERENT\",\"operation\":\"LOOKUP\"},{\"compiled_instruction\":\"INSTRUCTION-BOX-ALL-DIFFERENT\",\"operation\":\"LOOKUP\"},{\"compiled_instruction\":\"INSTRUCTION-IMMUTABLE-GIVENS\",\"operation\":\"LOOKUP\"},{\"compiled_instruction\":\"INSTRUCTION-CONTRADICTION-DETECTION\",\"operation\":\"LOOKUP\"},{\"compiled_instruction\":\"INSTRUCTION-CANDIDATE-ELIMINATION\",\"operation\":\"LOOKUP\"},{\"compiled_instruction\":\"INSTRUCTION-MINIMUM-DOMAIN-SELECTION\",\"operation\":\"LOOKUP\"},{\"compiled_instruction\":\"INSTRUCTION-BRANCHING\",\"operation\":\"LOOKUP\"},{\"compiled_instruction\":\"INSTRUCTION-CONTRADICTION-REJECTION\",\"operation\":\"LOOKUP\"},{\"compiled_instruction\":\"INSTRUCTION-RESTORATION\",\"operation\":\"LOOKUP\"},{\"compiled_instruction\":\"INSTRUCTION-COMPLETION\",\"operation\":\"LOOKUP\"},{\"compiled_instruction\":\"INSTRUCTION-UNIQUENESS-CHECKING\",\"operation\":\"LOOKUP\"},{\"compiled_instruction\":\"INSTRUCTION-DETERMINISTIC-RENDERING\",\"operation\":\"LOOKUP\"}]".
Alias "granular instructions compiled into the field" denotes Program "sudoku-granular-program".
Output schema "sudoku-grid" selects kernel schema "ANSWER_WITH_PROOF".
Instruction "solve-sudoku" selects operation "sudoku-instruction-sequence" accepts "Solve this Sudoku using only the {PROGRAM}: {BINDINGS}".
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
Cell "R1C1" has candidate domain "DOMAIN-R1C1".
Domain "DOMAIN-R1C1" allows digit "1".
Domain "DOMAIN-R1C1" allows digit "2".
Domain "DOMAIN-R1C1" allows digit "3".
Domain "DOMAIN-R1C1" allows digit "4".
Domain "DOMAIN-R1C1" allows digit "5".
Domain "DOMAIN-R1C1" allows digit "6".
Domain "DOMAIN-R1C1" allows digit "7".
Domain "DOMAIN-R1C1" allows digit "8".
Domain "DOMAIN-R1C1" allows digit "9".
Cell "R1C2" has candidate domain "DOMAIN-R1C2".
Domain "DOMAIN-R1C2" allows digit "1".
Domain "DOMAIN-R1C2" allows digit "2".
Domain "DOMAIN-R1C2" allows digit "3".
Domain "DOMAIN-R1C2" allows digit "4".
Domain "DOMAIN-R1C2" allows digit "5".
Domain "DOMAIN-R1C2" allows digit "6".
Domain "DOMAIN-R1C2" allows digit "7".
Domain "DOMAIN-R1C2" allows digit "8".
Domain "DOMAIN-R1C2" allows digit "9".
Cell "R1C3" has candidate domain "DOMAIN-R1C3".
Domain "DOMAIN-R1C3" allows digit "1".
Domain "DOMAIN-R1C3" allows digit "2".
Domain "DOMAIN-R1C3" allows digit "3".
Domain "DOMAIN-R1C3" allows digit "4".
Domain "DOMAIN-R1C3" allows digit "5".
Domain "DOMAIN-R1C3" allows digit "6".
Domain "DOMAIN-R1C3" allows digit "7".
Domain "DOMAIN-R1C3" allows digit "8".
Domain "DOMAIN-R1C3" allows digit "9".
Cell "R1C4" has candidate domain "DOMAIN-R1C4".
Domain "DOMAIN-R1C4" allows digit "1".
Domain "DOMAIN-R1C4" allows digit "2".
Domain "DOMAIN-R1C4" allows digit "3".
Domain "DOMAIN-R1C4" allows digit "4".
Domain "DOMAIN-R1C4" allows digit "5".
Domain "DOMAIN-R1C4" allows digit "6".
Domain "DOMAIN-R1C4" allows digit "7".
Domain "DOMAIN-R1C4" allows digit "8".
Domain "DOMAIN-R1C4" allows digit "9".
Cell "R1C5" has candidate domain "DOMAIN-R1C5".
Domain "DOMAIN-R1C5" allows digit "1".
Domain "DOMAIN-R1C5" allows digit "2".
Domain "DOMAIN-R1C5" allows digit "3".
Domain "DOMAIN-R1C5" allows digit "4".
Domain "DOMAIN-R1C5" allows digit "5".
Domain "DOMAIN-R1C5" allows digit "6".
Domain "DOMAIN-R1C5" allows digit "7".
Domain "DOMAIN-R1C5" allows digit "8".
Domain "DOMAIN-R1C5" allows digit "9".
Cell "R1C6" has candidate domain "DOMAIN-R1C6".
Domain "DOMAIN-R1C6" allows digit "1".
Domain "DOMAIN-R1C6" allows digit "2".
Domain "DOMAIN-R1C6" allows digit "3".
Domain "DOMAIN-R1C6" allows digit "4".
Domain "DOMAIN-R1C6" allows digit "5".
Domain "DOMAIN-R1C6" allows digit "6".
Domain "DOMAIN-R1C6" allows digit "7".
Domain "DOMAIN-R1C6" allows digit "8".
Domain "DOMAIN-R1C6" allows digit "9".
Cell "R1C7" has candidate domain "DOMAIN-R1C7".
Domain "DOMAIN-R1C7" allows digit "1".
Domain "DOMAIN-R1C7" allows digit "2".
Domain "DOMAIN-R1C7" allows digit "3".
Domain "DOMAIN-R1C7" allows digit "4".
Domain "DOMAIN-R1C7" allows digit "5".
Domain "DOMAIN-R1C7" allows digit "6".
Domain "DOMAIN-R1C7" allows digit "7".
Domain "DOMAIN-R1C7" allows digit "8".
Domain "DOMAIN-R1C7" allows digit "9".
Cell "R1C8" has candidate domain "DOMAIN-R1C8".
Domain "DOMAIN-R1C8" allows digit "1".
Domain "DOMAIN-R1C8" allows digit "2".
Domain "DOMAIN-R1C8" allows digit "3".
Domain "DOMAIN-R1C8" allows digit "4".
Domain "DOMAIN-R1C8" allows digit "5".
Domain "DOMAIN-R1C8" allows digit "6".
Domain "DOMAIN-R1C8" allows digit "7".
Domain "DOMAIN-R1C8" allows digit "8".
Domain "DOMAIN-R1C8" allows digit "9".
Cell "R1C9" has candidate domain "DOMAIN-R1C9".
Domain "DOMAIN-R1C9" allows digit "1".
Domain "DOMAIN-R1C9" allows digit "2".
Domain "DOMAIN-R1C9" allows digit "3".
Domain "DOMAIN-R1C9" allows digit "4".
Domain "DOMAIN-R1C9" allows digit "5".
Domain "DOMAIN-R1C9" allows digit "6".
Domain "DOMAIN-R1C9" allows digit "7".
Domain "DOMAIN-R1C9" allows digit "8".
Domain "DOMAIN-R1C9" allows digit "9".
Cell "R2C1" has candidate domain "DOMAIN-R2C1".
Domain "DOMAIN-R2C1" allows digit "1".
Domain "DOMAIN-R2C1" allows digit "2".
Domain "DOMAIN-R2C1" allows digit "3".
Domain "DOMAIN-R2C1" allows digit "4".
Domain "DOMAIN-R2C1" allows digit "5".
Domain "DOMAIN-R2C1" allows digit "6".
Domain "DOMAIN-R2C1" allows digit "7".
Domain "DOMAIN-R2C1" allows digit "8".
Domain "DOMAIN-R2C1" allows digit "9".
Cell "R2C2" has candidate domain "DOMAIN-R2C2".
Domain "DOMAIN-R2C2" allows digit "1".
Domain "DOMAIN-R2C2" allows digit "2".
Domain "DOMAIN-R2C2" allows digit "3".
Domain "DOMAIN-R2C2" allows digit "4".
Domain "DOMAIN-R2C2" allows digit "5".
Domain "DOMAIN-R2C2" allows digit "6".
Domain "DOMAIN-R2C2" allows digit "7".
Domain "DOMAIN-R2C2" allows digit "8".
Domain "DOMAIN-R2C2" allows digit "9".
Cell "R2C3" has candidate domain "DOMAIN-R2C3".
Domain "DOMAIN-R2C3" allows digit "1".
Domain "DOMAIN-R2C3" allows digit "2".
Domain "DOMAIN-R2C3" allows digit "3".
Domain "DOMAIN-R2C3" allows digit "4".
Domain "DOMAIN-R2C3" allows digit "5".
Domain "DOMAIN-R2C3" allows digit "6".
Domain "DOMAIN-R2C3" allows digit "7".
Domain "DOMAIN-R2C3" allows digit "8".
Domain "DOMAIN-R2C3" allows digit "9".
Cell "R2C4" has candidate domain "DOMAIN-R2C4".
Domain "DOMAIN-R2C4" allows digit "1".
Domain "DOMAIN-R2C4" allows digit "2".
Domain "DOMAIN-R2C4" allows digit "3".
Domain "DOMAIN-R2C4" allows digit "4".
Domain "DOMAIN-R2C4" allows digit "5".
Domain "DOMAIN-R2C4" allows digit "6".
Domain "DOMAIN-R2C4" allows digit "7".
Domain "DOMAIN-R2C4" allows digit "8".
Domain "DOMAIN-R2C4" allows digit "9".
Cell "R2C5" has candidate domain "DOMAIN-R2C5".
Domain "DOMAIN-R2C5" allows digit "1".
Domain "DOMAIN-R2C5" allows digit "2".
Domain "DOMAIN-R2C5" allows digit "3".
Domain "DOMAIN-R2C5" allows digit "4".
Domain "DOMAIN-R2C5" allows digit "5".
Domain "DOMAIN-R2C5" allows digit "6".
Domain "DOMAIN-R2C5" allows digit "7".
Domain "DOMAIN-R2C5" allows digit "8".
Domain "DOMAIN-R2C5" allows digit "9".
Cell "R2C6" has candidate domain "DOMAIN-R2C6".
Domain "DOMAIN-R2C6" allows digit "1".
Domain "DOMAIN-R2C6" allows digit "2".
Domain "DOMAIN-R2C6" allows digit "3".
Domain "DOMAIN-R2C6" allows digit "4".
Domain "DOMAIN-R2C6" allows digit "5".
Domain "DOMAIN-R2C6" allows digit "6".
Domain "DOMAIN-R2C6" allows digit "7".
Domain "DOMAIN-R2C6" allows digit "8".
Domain "DOMAIN-R2C6" allows digit "9".
Cell "R2C7" has candidate domain "DOMAIN-R2C7".
Domain "DOMAIN-R2C7" allows digit "1".
Domain "DOMAIN-R2C7" allows digit "2".
Domain "DOMAIN-R2C7" allows digit "3".
Domain "DOMAIN-R2C7" allows digit "4".
Domain "DOMAIN-R2C7" allows digit "5".
Domain "DOMAIN-R2C7" allows digit "6".
Domain "DOMAIN-R2C7" allows digit "7".
Domain "DOMAIN-R2C7" allows digit "8".
Domain "DOMAIN-R2C7" allows digit "9".
Cell "R2C8" has candidate domain "DOMAIN-R2C8".
Domain "DOMAIN-R2C8" allows digit "1".
Domain "DOMAIN-R2C8" allows digit "2".
Domain "DOMAIN-R2C8" allows digit "3".
Domain "DOMAIN-R2C8" allows digit "4".
Domain "DOMAIN-R2C8" allows digit "5".
Domain "DOMAIN-R2C8" allows digit "6".
Domain "DOMAIN-R2C8" allows digit "7".
Domain "DOMAIN-R2C8" allows digit "8".
Domain "DOMAIN-R2C8" allows digit "9".
Cell "R2C9" has candidate domain "DOMAIN-R2C9".
Domain "DOMAIN-R2C9" allows digit "1".
Domain "DOMAIN-R2C9" allows digit "2".
Domain "DOMAIN-R2C9" allows digit "3".
Domain "DOMAIN-R2C9" allows digit "4".
Domain "DOMAIN-R2C9" allows digit "5".
Domain "DOMAIN-R2C9" allows digit "6".
Domain "DOMAIN-R2C9" allows digit "7".
Domain "DOMAIN-R2C9" allows digit "8".
Domain "DOMAIN-R2C9" allows digit "9".
Cell "R3C1" has candidate domain "DOMAIN-R3C1".
Domain "DOMAIN-R3C1" allows digit "1".
Domain "DOMAIN-R3C1" allows digit "2".
Domain "DOMAIN-R3C1" allows digit "3".
Domain "DOMAIN-R3C1" allows digit "4".
Domain "DOMAIN-R3C1" allows digit "5".
Domain "DOMAIN-R3C1" allows digit "6".
Domain "DOMAIN-R3C1" allows digit "7".
Domain "DOMAIN-R3C1" allows digit "8".
Domain "DOMAIN-R3C1" allows digit "9".
Cell "R3C2" has candidate domain "DOMAIN-R3C2".
Domain "DOMAIN-R3C2" allows digit "1".
Domain "DOMAIN-R3C2" allows digit "2".
Domain "DOMAIN-R3C2" allows digit "3".
Domain "DOMAIN-R3C2" allows digit "4".
Domain "DOMAIN-R3C2" allows digit "5".
Domain "DOMAIN-R3C2" allows digit "6".
Domain "DOMAIN-R3C2" allows digit "7".
Domain "DOMAIN-R3C2" allows digit "8".
Domain "DOMAIN-R3C2" allows digit "9".
Cell "R3C3" has candidate domain "DOMAIN-R3C3".
Domain "DOMAIN-R3C3" allows digit "1".
Domain "DOMAIN-R3C3" allows digit "2".
Domain "DOMAIN-R3C3" allows digit "3".
Domain "DOMAIN-R3C3" allows digit "4".
Domain "DOMAIN-R3C3" allows digit "5".
Domain "DOMAIN-R3C3" allows digit "6".
Domain "DOMAIN-R3C3" allows digit "7".
Domain "DOMAIN-R3C3" allows digit "8".
Domain "DOMAIN-R3C3" allows digit "9".
Cell "R3C4" has candidate domain "DOMAIN-R3C4".
Domain "DOMAIN-R3C4" allows digit "1".
Domain "DOMAIN-R3C4" allows digit "2".
Domain "DOMAIN-R3C4" allows digit "3".
Domain "DOMAIN-R3C4" allows digit "4".
Domain "DOMAIN-R3C4" allows digit "5".
Domain "DOMAIN-R3C4" allows digit "6".
Domain "DOMAIN-R3C4" allows digit "7".
Domain "DOMAIN-R3C4" allows digit "8".
Domain "DOMAIN-R3C4" allows digit "9".
Cell "R3C5" has candidate domain "DOMAIN-R3C5".
Domain "DOMAIN-R3C5" allows digit "1".
Domain "DOMAIN-R3C5" allows digit "2".
Domain "DOMAIN-R3C5" allows digit "3".
Domain "DOMAIN-R3C5" allows digit "4".
Domain "DOMAIN-R3C5" allows digit "5".
Domain "DOMAIN-R3C5" allows digit "6".
Domain "DOMAIN-R3C5" allows digit "7".
Domain "DOMAIN-R3C5" allows digit "8".
Domain "DOMAIN-R3C5" allows digit "9".
Cell "R3C6" has candidate domain "DOMAIN-R3C6".
Domain "DOMAIN-R3C6" allows digit "1".
Domain "DOMAIN-R3C6" allows digit "2".
Domain "DOMAIN-R3C6" allows digit "3".
Domain "DOMAIN-R3C6" allows digit "4".
Domain "DOMAIN-R3C6" allows digit "5".
Domain "DOMAIN-R3C6" allows digit "6".
Domain "DOMAIN-R3C6" allows digit "7".
Domain "DOMAIN-R3C6" allows digit "8".
Domain "DOMAIN-R3C6" allows digit "9".
Cell "R3C7" has candidate domain "DOMAIN-R3C7".
Domain "DOMAIN-R3C7" allows digit "1".
Domain "DOMAIN-R3C7" allows digit "2".
Domain "DOMAIN-R3C7" allows digit "3".
Domain "DOMAIN-R3C7" allows digit "4".
Domain "DOMAIN-R3C7" allows digit "5".
Domain "DOMAIN-R3C7" allows digit "6".
Domain "DOMAIN-R3C7" allows digit "7".
Domain "DOMAIN-R3C7" allows digit "8".
Domain "DOMAIN-R3C7" allows digit "9".
Cell "R3C8" has candidate domain "DOMAIN-R3C8".
Domain "DOMAIN-R3C8" allows digit "1".
Domain "DOMAIN-R3C8" allows digit "2".
Domain "DOMAIN-R3C8" allows digit "3".
Domain "DOMAIN-R3C8" allows digit "4".
Domain "DOMAIN-R3C8" allows digit "5".
Domain "DOMAIN-R3C8" allows digit "6".
Domain "DOMAIN-R3C8" allows digit "7".
Domain "DOMAIN-R3C8" allows digit "8".
Domain "DOMAIN-R3C8" allows digit "9".
Cell "R3C9" has candidate domain "DOMAIN-R3C9".
Domain "DOMAIN-R3C9" allows digit "1".
Domain "DOMAIN-R3C9" allows digit "2".
Domain "DOMAIN-R3C9" allows digit "3".
Domain "DOMAIN-R3C9" allows digit "4".
Domain "DOMAIN-R3C9" allows digit "5".
Domain "DOMAIN-R3C9" allows digit "6".
Domain "DOMAIN-R3C9" allows digit "7".
Domain "DOMAIN-R3C9" allows digit "8".
Domain "DOMAIN-R3C9" allows digit "9".
Cell "R4C1" has candidate domain "DOMAIN-R4C1".
Domain "DOMAIN-R4C1" allows digit "1".
Domain "DOMAIN-R4C1" allows digit "2".
Domain "DOMAIN-R4C1" allows digit "3".
Domain "DOMAIN-R4C1" allows digit "4".
Domain "DOMAIN-R4C1" allows digit "5".
Domain "DOMAIN-R4C1" allows digit "6".
Domain "DOMAIN-R4C1" allows digit "7".
Domain "DOMAIN-R4C1" allows digit "8".
Domain "DOMAIN-R4C1" allows digit "9".
Cell "R4C2" has candidate domain "DOMAIN-R4C2".
Domain "DOMAIN-R4C2" allows digit "1".
Domain "DOMAIN-R4C2" allows digit "2".
Domain "DOMAIN-R4C2" allows digit "3".
Domain "DOMAIN-R4C2" allows digit "4".
Domain "DOMAIN-R4C2" allows digit "5".
Domain "DOMAIN-R4C2" allows digit "6".
Domain "DOMAIN-R4C2" allows digit "7".
Domain "DOMAIN-R4C2" allows digit "8".
Domain "DOMAIN-R4C2" allows digit "9".
Cell "R4C3" has candidate domain "DOMAIN-R4C3".
Domain "DOMAIN-R4C3" allows digit "1".
Domain "DOMAIN-R4C3" allows digit "2".
Domain "DOMAIN-R4C3" allows digit "3".
Domain "DOMAIN-R4C3" allows digit "4".
Domain "DOMAIN-R4C3" allows digit "5".
Domain "DOMAIN-R4C3" allows digit "6".
Domain "DOMAIN-R4C3" allows digit "7".
Domain "DOMAIN-R4C3" allows digit "8".
Domain "DOMAIN-R4C3" allows digit "9".
Cell "R4C4" has candidate domain "DOMAIN-R4C4".
Domain "DOMAIN-R4C4" allows digit "1".
Domain "DOMAIN-R4C4" allows digit "2".
Domain "DOMAIN-R4C4" allows digit "3".
Domain "DOMAIN-R4C4" allows digit "4".
Domain "DOMAIN-R4C4" allows digit "5".
Domain "DOMAIN-R4C4" allows digit "6".
Domain "DOMAIN-R4C4" allows digit "7".
Domain "DOMAIN-R4C4" allows digit "8".
Domain "DOMAIN-R4C4" allows digit "9".
Cell "R4C5" has candidate domain "DOMAIN-R4C5".
Domain "DOMAIN-R4C5" allows digit "1".
Domain "DOMAIN-R4C5" allows digit "2".
Domain "DOMAIN-R4C5" allows digit "3".
Domain "DOMAIN-R4C5" allows digit "4".
Domain "DOMAIN-R4C5" allows digit "5".
Domain "DOMAIN-R4C5" allows digit "6".
Domain "DOMAIN-R4C5" allows digit "7".
Domain "DOMAIN-R4C5" allows digit "8".
Domain "DOMAIN-R4C5" allows digit "9".
Cell "R4C6" has candidate domain "DOMAIN-R4C6".
Domain "DOMAIN-R4C6" allows digit "1".
Domain "DOMAIN-R4C6" allows digit "2".
Domain "DOMAIN-R4C6" allows digit "3".
Domain "DOMAIN-R4C6" allows digit "4".
Domain "DOMAIN-R4C6" allows digit "5".
Domain "DOMAIN-R4C6" allows digit "6".
Domain "DOMAIN-R4C6" allows digit "7".
Domain "DOMAIN-R4C6" allows digit "8".
Domain "DOMAIN-R4C6" allows digit "9".
Cell "R4C7" has candidate domain "DOMAIN-R4C7".
Domain "DOMAIN-R4C7" allows digit "1".
Domain "DOMAIN-R4C7" allows digit "2".
Domain "DOMAIN-R4C7" allows digit "3".
Domain "DOMAIN-R4C7" allows digit "4".
Domain "DOMAIN-R4C7" allows digit "5".
Domain "DOMAIN-R4C7" allows digit "6".
Domain "DOMAIN-R4C7" allows digit "7".
Domain "DOMAIN-R4C7" allows digit "8".
Domain "DOMAIN-R4C7" allows digit "9".
Cell "R4C8" has candidate domain "DOMAIN-R4C8".
Domain "DOMAIN-R4C8" allows digit "1".
Domain "DOMAIN-R4C8" allows digit "2".
Domain "DOMAIN-R4C8" allows digit "3".
Domain "DOMAIN-R4C8" allows digit "4".
Domain "DOMAIN-R4C8" allows digit "5".
Domain "DOMAIN-R4C8" allows digit "6".
Domain "DOMAIN-R4C8" allows digit "7".
Domain "DOMAIN-R4C8" allows digit "8".
Domain "DOMAIN-R4C8" allows digit "9".
Cell "R4C9" has candidate domain "DOMAIN-R4C9".
Domain "DOMAIN-R4C9" allows digit "1".
Domain "DOMAIN-R4C9" allows digit "2".
Domain "DOMAIN-R4C9" allows digit "3".
Domain "DOMAIN-R4C9" allows digit "4".
Domain "DOMAIN-R4C9" allows digit "5".
Domain "DOMAIN-R4C9" allows digit "6".
Domain "DOMAIN-R4C9" allows digit "7".
Domain "DOMAIN-R4C9" allows digit "8".
Domain "DOMAIN-R4C9" allows digit "9".
Cell "R5C1" has candidate domain "DOMAIN-R5C1".
Domain "DOMAIN-R5C1" allows digit "1".
Domain "DOMAIN-R5C1" allows digit "2".
Domain "DOMAIN-R5C1" allows digit "3".
Domain "DOMAIN-R5C1" allows digit "4".
Domain "DOMAIN-R5C1" allows digit "5".
Domain "DOMAIN-R5C1" allows digit "6".
Domain "DOMAIN-R5C1" allows digit "7".
Domain "DOMAIN-R5C1" allows digit "8".
Domain "DOMAIN-R5C1" allows digit "9".
Cell "R5C2" has candidate domain "DOMAIN-R5C2".
Domain "DOMAIN-R5C2" allows digit "1".
Domain "DOMAIN-R5C2" allows digit "2".
Domain "DOMAIN-R5C2" allows digit "3".
Domain "DOMAIN-R5C2" allows digit "4".
Domain "DOMAIN-R5C2" allows digit "5".
Domain "DOMAIN-R5C2" allows digit "6".
Domain "DOMAIN-R5C2" allows digit "7".
Domain "DOMAIN-R5C2" allows digit "8".
Domain "DOMAIN-R5C2" allows digit "9".
Cell "R5C3" has candidate domain "DOMAIN-R5C3".
Domain "DOMAIN-R5C3" allows digit "1".
Domain "DOMAIN-R5C3" allows digit "2".
Domain "DOMAIN-R5C3" allows digit "3".
Domain "DOMAIN-R5C3" allows digit "4".
Domain "DOMAIN-R5C3" allows digit "5".
Domain "DOMAIN-R5C3" allows digit "6".
Domain "DOMAIN-R5C3" allows digit "7".
Domain "DOMAIN-R5C3" allows digit "8".
Domain "DOMAIN-R5C3" allows digit "9".
Cell "R5C4" has candidate domain "DOMAIN-R5C4".
Domain "DOMAIN-R5C4" allows digit "1".
Domain "DOMAIN-R5C4" allows digit "2".
Domain "DOMAIN-R5C4" allows digit "3".
Domain "DOMAIN-R5C4" allows digit "4".
Domain "DOMAIN-R5C4" allows digit "5".
Domain "DOMAIN-R5C4" allows digit "6".
Domain "DOMAIN-R5C4" allows digit "7".
Domain "DOMAIN-R5C4" allows digit "8".
Domain "DOMAIN-R5C4" allows digit "9".
Cell "R5C5" has candidate domain "DOMAIN-R5C5".
Domain "DOMAIN-R5C5" allows digit "1".
Domain "DOMAIN-R5C5" allows digit "2".
Domain "DOMAIN-R5C5" allows digit "3".
Domain "DOMAIN-R5C5" allows digit "4".
Domain "DOMAIN-R5C5" allows digit "5".
Domain "DOMAIN-R5C5" allows digit "6".
Domain "DOMAIN-R5C5" allows digit "7".
Domain "DOMAIN-R5C5" allows digit "8".
Domain "DOMAIN-R5C5" allows digit "9".
Cell "R5C6" has candidate domain "DOMAIN-R5C6".
Domain "DOMAIN-R5C6" allows digit "1".
Domain "DOMAIN-R5C6" allows digit "2".
Domain "DOMAIN-R5C6" allows digit "3".
Domain "DOMAIN-R5C6" allows digit "4".
Domain "DOMAIN-R5C6" allows digit "5".
Domain "DOMAIN-R5C6" allows digit "6".
Domain "DOMAIN-R5C6" allows digit "7".
Domain "DOMAIN-R5C6" allows digit "8".
Domain "DOMAIN-R5C6" allows digit "9".
Cell "R5C7" has candidate domain "DOMAIN-R5C7".
Domain "DOMAIN-R5C7" allows digit "1".
Domain "DOMAIN-R5C7" allows digit "2".
Domain "DOMAIN-R5C7" allows digit "3".
Domain "DOMAIN-R5C7" allows digit "4".
Domain "DOMAIN-R5C7" allows digit "5".
Domain "DOMAIN-R5C7" allows digit "6".
Domain "DOMAIN-R5C7" allows digit "7".
Domain "DOMAIN-R5C7" allows digit "8".
Domain "DOMAIN-R5C7" allows digit "9".
Cell "R5C8" has candidate domain "DOMAIN-R5C8".
Domain "DOMAIN-R5C8" allows digit "1".
Domain "DOMAIN-R5C8" allows digit "2".
Domain "DOMAIN-R5C8" allows digit "3".
Domain "DOMAIN-R5C8" allows digit "4".
Domain "DOMAIN-R5C8" allows digit "5".
Domain "DOMAIN-R5C8" allows digit "6".
Domain "DOMAIN-R5C8" allows digit "7".
Domain "DOMAIN-R5C8" allows digit "8".
Domain "DOMAIN-R5C8" allows digit "9".
Cell "R5C9" has candidate domain "DOMAIN-R5C9".
Domain "DOMAIN-R5C9" allows digit "1".
Domain "DOMAIN-R5C9" allows digit "2".
Domain "DOMAIN-R5C9" allows digit "3".
Domain "DOMAIN-R5C9" allows digit "4".
Domain "DOMAIN-R5C9" allows digit "5".
Domain "DOMAIN-R5C9" allows digit "6".
Domain "DOMAIN-R5C9" allows digit "7".
Domain "DOMAIN-R5C9" allows digit "8".
Domain "DOMAIN-R5C9" allows digit "9".
Cell "R6C1" has candidate domain "DOMAIN-R6C1".
Domain "DOMAIN-R6C1" allows digit "1".
Domain "DOMAIN-R6C1" allows digit "2".
Domain "DOMAIN-R6C1" allows digit "3".
Domain "DOMAIN-R6C1" allows digit "4".
Domain "DOMAIN-R6C1" allows digit "5".
Domain "DOMAIN-R6C1" allows digit "6".
Domain "DOMAIN-R6C1" allows digit "7".
Domain "DOMAIN-R6C1" allows digit "8".
Domain "DOMAIN-R6C1" allows digit "9".
Cell "R6C2" has candidate domain "DOMAIN-R6C2".
Domain "DOMAIN-R6C2" allows digit "1".
Domain "DOMAIN-R6C2" allows digit "2".
Domain "DOMAIN-R6C2" allows digit "3".
Domain "DOMAIN-R6C2" allows digit "4".
Domain "DOMAIN-R6C2" allows digit "5".
Domain "DOMAIN-R6C2" allows digit "6".
Domain "DOMAIN-R6C2" allows digit "7".
Domain "DOMAIN-R6C2" allows digit "8".
Domain "DOMAIN-R6C2" allows digit "9".
Cell "R6C3" has candidate domain "DOMAIN-R6C3".
Domain "DOMAIN-R6C3" allows digit "1".
Domain "DOMAIN-R6C3" allows digit "2".
Domain "DOMAIN-R6C3" allows digit "3".
Domain "DOMAIN-R6C3" allows digit "4".
Domain "DOMAIN-R6C3" allows digit "5".
Domain "DOMAIN-R6C3" allows digit "6".
Domain "DOMAIN-R6C3" allows digit "7".
Domain "DOMAIN-R6C3" allows digit "8".
Domain "DOMAIN-R6C3" allows digit "9".
Cell "R6C4" has candidate domain "DOMAIN-R6C4".
Domain "DOMAIN-R6C4" allows digit "1".
Domain "DOMAIN-R6C4" allows digit "2".
Domain "DOMAIN-R6C4" allows digit "3".
Domain "DOMAIN-R6C4" allows digit "4".
Domain "DOMAIN-R6C4" allows digit "5".
Domain "DOMAIN-R6C4" allows digit "6".
Domain "DOMAIN-R6C4" allows digit "7".
Domain "DOMAIN-R6C4" allows digit "8".
Domain "DOMAIN-R6C4" allows digit "9".
Cell "R6C5" has candidate domain "DOMAIN-R6C5".
Domain "DOMAIN-R6C5" allows digit "1".
Domain "DOMAIN-R6C5" allows digit "2".
Domain "DOMAIN-R6C5" allows digit "3".
Domain "DOMAIN-R6C5" allows digit "4".
Domain "DOMAIN-R6C5" allows digit "5".
Domain "DOMAIN-R6C5" allows digit "6".
Domain "DOMAIN-R6C5" allows digit "7".
Domain "DOMAIN-R6C5" allows digit "8".
Domain "DOMAIN-R6C5" allows digit "9".
Cell "R6C6" has candidate domain "DOMAIN-R6C6".
Domain "DOMAIN-R6C6" allows digit "1".
Domain "DOMAIN-R6C6" allows digit "2".
Domain "DOMAIN-R6C6" allows digit "3".
Domain "DOMAIN-R6C6" allows digit "4".
Domain "DOMAIN-R6C6" allows digit "5".
Domain "DOMAIN-R6C6" allows digit "6".
Domain "DOMAIN-R6C6" allows digit "7".
Domain "DOMAIN-R6C6" allows digit "8".
Domain "DOMAIN-R6C6" allows digit "9".
Cell "R6C7" has candidate domain "DOMAIN-R6C7".
Domain "DOMAIN-R6C7" allows digit "1".
Domain "DOMAIN-R6C7" allows digit "2".
Domain "DOMAIN-R6C7" allows digit "3".
Domain "DOMAIN-R6C7" allows digit "4".
Domain "DOMAIN-R6C7" allows digit "5".
Domain "DOMAIN-R6C7" allows digit "6".
Domain "DOMAIN-R6C7" allows digit "7".
Domain "DOMAIN-R6C7" allows digit "8".
Domain "DOMAIN-R6C7" allows digit "9".
Cell "R6C8" has candidate domain "DOMAIN-R6C8".
Domain "DOMAIN-R6C8" allows digit "1".
Domain "DOMAIN-R6C8" allows digit "2".
Domain "DOMAIN-R6C8" allows digit "3".
Domain "DOMAIN-R6C8" allows digit "4".
Domain "DOMAIN-R6C8" allows digit "5".
Domain "DOMAIN-R6C8" allows digit "6".
Domain "DOMAIN-R6C8" allows digit "7".
Domain "DOMAIN-R6C8" allows digit "8".
Domain "DOMAIN-R6C8" allows digit "9".
Cell "R6C9" has candidate domain "DOMAIN-R6C9".
Domain "DOMAIN-R6C9" allows digit "1".
Domain "DOMAIN-R6C9" allows digit "2".
Domain "DOMAIN-R6C9" allows digit "3".
Domain "DOMAIN-R6C9" allows digit "4".
Domain "DOMAIN-R6C9" allows digit "5".
Domain "DOMAIN-R6C9" allows digit "6".
Domain "DOMAIN-R6C9" allows digit "7".
Domain "DOMAIN-R6C9" allows digit "8".
Domain "DOMAIN-R6C9" allows digit "9".
Cell "R7C1" has candidate domain "DOMAIN-R7C1".
Domain "DOMAIN-R7C1" allows digit "1".
Domain "DOMAIN-R7C1" allows digit "2".
Domain "DOMAIN-R7C1" allows digit "3".
Domain "DOMAIN-R7C1" allows digit "4".
Domain "DOMAIN-R7C1" allows digit "5".
Domain "DOMAIN-R7C1" allows digit "6".
Domain "DOMAIN-R7C1" allows digit "7".
Domain "DOMAIN-R7C1" allows digit "8".
Domain "DOMAIN-R7C1" allows digit "9".
Cell "R7C2" has candidate domain "DOMAIN-R7C2".
Domain "DOMAIN-R7C2" allows digit "1".
Domain "DOMAIN-R7C2" allows digit "2".
Domain "DOMAIN-R7C2" allows digit "3".
Domain "DOMAIN-R7C2" allows digit "4".
Domain "DOMAIN-R7C2" allows digit "5".
Domain "DOMAIN-R7C2" allows digit "6".
Domain "DOMAIN-R7C2" allows digit "7".
Domain "DOMAIN-R7C2" allows digit "8".
Domain "DOMAIN-R7C2" allows digit "9".
Cell "R7C3" has candidate domain "DOMAIN-R7C3".
Domain "DOMAIN-R7C3" allows digit "1".
Domain "DOMAIN-R7C3" allows digit "2".
Domain "DOMAIN-R7C3" allows digit "3".
Domain "DOMAIN-R7C3" allows digit "4".
Domain "DOMAIN-R7C3" allows digit "5".
Domain "DOMAIN-R7C3" allows digit "6".
Domain "DOMAIN-R7C3" allows digit "7".
Domain "DOMAIN-R7C3" allows digit "8".
Domain "DOMAIN-R7C3" allows digit "9".
Cell "R7C4" has candidate domain "DOMAIN-R7C4".
Domain "DOMAIN-R7C4" allows digit "1".
Domain "DOMAIN-R7C4" allows digit "2".
Domain "DOMAIN-R7C4" allows digit "3".
Domain "DOMAIN-R7C4" allows digit "4".
Domain "DOMAIN-R7C4" allows digit "5".
Domain "DOMAIN-R7C4" allows digit "6".
Domain "DOMAIN-R7C4" allows digit "7".
Domain "DOMAIN-R7C4" allows digit "8".
Domain "DOMAIN-R7C4" allows digit "9".
Cell "R7C5" has candidate domain "DOMAIN-R7C5".
Domain "DOMAIN-R7C5" allows digit "1".
Domain "DOMAIN-R7C5" allows digit "2".
Domain "DOMAIN-R7C5" allows digit "3".
Domain "DOMAIN-R7C5" allows digit "4".
Domain "DOMAIN-R7C5" allows digit "5".
Domain "DOMAIN-R7C5" allows digit "6".
Domain "DOMAIN-R7C5" allows digit "7".
Domain "DOMAIN-R7C5" allows digit "8".
Domain "DOMAIN-R7C5" allows digit "9".
Cell "R7C6" has candidate domain "DOMAIN-R7C6".
Domain "DOMAIN-R7C6" allows digit "1".
Domain "DOMAIN-R7C6" allows digit "2".
Domain "DOMAIN-R7C6" allows digit "3".
Domain "DOMAIN-R7C6" allows digit "4".
Domain "DOMAIN-R7C6" allows digit "5".
Domain "DOMAIN-R7C6" allows digit "6".
Domain "DOMAIN-R7C6" allows digit "7".
Domain "DOMAIN-R7C6" allows digit "8".
Domain "DOMAIN-R7C6" allows digit "9".
Cell "R7C7" has candidate domain "DOMAIN-R7C7".
Domain "DOMAIN-R7C7" allows digit "1".
Domain "DOMAIN-R7C7" allows digit "2".
Domain "DOMAIN-R7C7" allows digit "3".
Domain "DOMAIN-R7C7" allows digit "4".
Domain "DOMAIN-R7C7" allows digit "5".
Domain "DOMAIN-R7C7" allows digit "6".
Domain "DOMAIN-R7C7" allows digit "7".
Domain "DOMAIN-R7C7" allows digit "8".
Domain "DOMAIN-R7C7" allows digit "9".
Cell "R7C8" has candidate domain "DOMAIN-R7C8".
Domain "DOMAIN-R7C8" allows digit "1".
Domain "DOMAIN-R7C8" allows digit "2".
Domain "DOMAIN-R7C8" allows digit "3".
Domain "DOMAIN-R7C8" allows digit "4".
Domain "DOMAIN-R7C8" allows digit "5".
Domain "DOMAIN-R7C8" allows digit "6".
Domain "DOMAIN-R7C8" allows digit "7".
Domain "DOMAIN-R7C8" allows digit "8".
Domain "DOMAIN-R7C8" allows digit "9".
Cell "R7C9" has candidate domain "DOMAIN-R7C9".
Domain "DOMAIN-R7C9" allows digit "1".
Domain "DOMAIN-R7C9" allows digit "2".
Domain "DOMAIN-R7C9" allows digit "3".
Domain "DOMAIN-R7C9" allows digit "4".
Domain "DOMAIN-R7C9" allows digit "5".
Domain "DOMAIN-R7C9" allows digit "6".
Domain "DOMAIN-R7C9" allows digit "7".
Domain "DOMAIN-R7C9" allows digit "8".
Domain "DOMAIN-R7C9" allows digit "9".
Cell "R8C1" has candidate domain "DOMAIN-R8C1".
Domain "DOMAIN-R8C1" allows digit "1".
Domain "DOMAIN-R8C1" allows digit "2".
Domain "DOMAIN-R8C1" allows digit "3".
Domain "DOMAIN-R8C1" allows digit "4".
Domain "DOMAIN-R8C1" allows digit "5".
Domain "DOMAIN-R8C1" allows digit "6".
Domain "DOMAIN-R8C1" allows digit "7".
Domain "DOMAIN-R8C1" allows digit "8".
Domain "DOMAIN-R8C1" allows digit "9".
Cell "R8C2" has candidate domain "DOMAIN-R8C2".
Domain "DOMAIN-R8C2" allows digit "1".
Domain "DOMAIN-R8C2" allows digit "2".
Domain "DOMAIN-R8C2" allows digit "3".
Domain "DOMAIN-R8C2" allows digit "4".
Domain "DOMAIN-R8C2" allows digit "5".
Domain "DOMAIN-R8C2" allows digit "6".
Domain "DOMAIN-R8C2" allows digit "7".
Domain "DOMAIN-R8C2" allows digit "8".
Domain "DOMAIN-R8C2" allows digit "9".
Cell "R8C3" has candidate domain "DOMAIN-R8C3".
Domain "DOMAIN-R8C3" allows digit "1".
Domain "DOMAIN-R8C3" allows digit "2".
Domain "DOMAIN-R8C3" allows digit "3".
Domain "DOMAIN-R8C3" allows digit "4".
Domain "DOMAIN-R8C3" allows digit "5".
Domain "DOMAIN-R8C3" allows digit "6".
Domain "DOMAIN-R8C3" allows digit "7".
Domain "DOMAIN-R8C3" allows digit "8".
Domain "DOMAIN-R8C3" allows digit "9".
Cell "R8C4" has candidate domain "DOMAIN-R8C4".
Domain "DOMAIN-R8C4" allows digit "1".
Domain "DOMAIN-R8C4" allows digit "2".
Domain "DOMAIN-R8C4" allows digit "3".
Domain "DOMAIN-R8C4" allows digit "4".
Domain "DOMAIN-R8C4" allows digit "5".
Domain "DOMAIN-R8C4" allows digit "6".
Domain "DOMAIN-R8C4" allows digit "7".
Domain "DOMAIN-R8C4" allows digit "8".
Domain "DOMAIN-R8C4" allows digit "9".
Cell "R8C5" has candidate domain "DOMAIN-R8C5".
Domain "DOMAIN-R8C5" allows digit "1".
Domain "DOMAIN-R8C5" allows digit "2".
Domain "DOMAIN-R8C5" allows digit "3".
Domain "DOMAIN-R8C5" allows digit "4".
Domain "DOMAIN-R8C5" allows digit "5".
Domain "DOMAIN-R8C5" allows digit "6".
Domain "DOMAIN-R8C5" allows digit "7".
Domain "DOMAIN-R8C5" allows digit "8".
Domain "DOMAIN-R8C5" allows digit "9".
Cell "R8C6" has candidate domain "DOMAIN-R8C6".
Domain "DOMAIN-R8C6" allows digit "1".
Domain "DOMAIN-R8C6" allows digit "2".
Domain "DOMAIN-R8C6" allows digit "3".
Domain "DOMAIN-R8C6" allows digit "4".
Domain "DOMAIN-R8C6" allows digit "5".
Domain "DOMAIN-R8C6" allows digit "6".
Domain "DOMAIN-R8C6" allows digit "7".
Domain "DOMAIN-R8C6" allows digit "8".
Domain "DOMAIN-R8C6" allows digit "9".
Cell "R8C7" has candidate domain "DOMAIN-R8C7".
Domain "DOMAIN-R8C7" allows digit "1".
Domain "DOMAIN-R8C7" allows digit "2".
Domain "DOMAIN-R8C7" allows digit "3".
Domain "DOMAIN-R8C7" allows digit "4".
Domain "DOMAIN-R8C7" allows digit "5".
Domain "DOMAIN-R8C7" allows digit "6".
Domain "DOMAIN-R8C7" allows digit "7".
Domain "DOMAIN-R8C7" allows digit "8".
Domain "DOMAIN-R8C7" allows digit "9".
Cell "R8C8" has candidate domain "DOMAIN-R8C8".
Domain "DOMAIN-R8C8" allows digit "1".
Domain "DOMAIN-R8C8" allows digit "2".
Domain "DOMAIN-R8C8" allows digit "3".
Domain "DOMAIN-R8C8" allows digit "4".
Domain "DOMAIN-R8C8" allows digit "5".
Domain "DOMAIN-R8C8" allows digit "6".
Domain "DOMAIN-R8C8" allows digit "7".
Domain "DOMAIN-R8C8" allows digit "8".
Domain "DOMAIN-R8C8" allows digit "9".
Cell "R8C9" has candidate domain "DOMAIN-R8C9".
Domain "DOMAIN-R8C9" allows digit "1".
Domain "DOMAIN-R8C9" allows digit "2".
Domain "DOMAIN-R8C9" allows digit "3".
Domain "DOMAIN-R8C9" allows digit "4".
Domain "DOMAIN-R8C9" allows digit "5".
Domain "DOMAIN-R8C9" allows digit "6".
Domain "DOMAIN-R8C9" allows digit "7".
Domain "DOMAIN-R8C9" allows digit "8".
Domain "DOMAIN-R8C9" allows digit "9".
Cell "R9C1" has candidate domain "DOMAIN-R9C1".
Domain "DOMAIN-R9C1" allows digit "1".
Domain "DOMAIN-R9C1" allows digit "2".
Domain "DOMAIN-R9C1" allows digit "3".
Domain "DOMAIN-R9C1" allows digit "4".
Domain "DOMAIN-R9C1" allows digit "5".
Domain "DOMAIN-R9C1" allows digit "6".
Domain "DOMAIN-R9C1" allows digit "7".
Domain "DOMAIN-R9C1" allows digit "8".
Domain "DOMAIN-R9C1" allows digit "9".
Cell "R9C2" has candidate domain "DOMAIN-R9C2".
Domain "DOMAIN-R9C2" allows digit "1".
Domain "DOMAIN-R9C2" allows digit "2".
Domain "DOMAIN-R9C2" allows digit "3".
Domain "DOMAIN-R9C2" allows digit "4".
Domain "DOMAIN-R9C2" allows digit "5".
Domain "DOMAIN-R9C2" allows digit "6".
Domain "DOMAIN-R9C2" allows digit "7".
Domain "DOMAIN-R9C2" allows digit "8".
Domain "DOMAIN-R9C2" allows digit "9".
Cell "R9C3" has candidate domain "DOMAIN-R9C3".
Domain "DOMAIN-R9C3" allows digit "1".
Domain "DOMAIN-R9C3" allows digit "2".
Domain "DOMAIN-R9C3" allows digit "3".
Domain "DOMAIN-R9C3" allows digit "4".
Domain "DOMAIN-R9C3" allows digit "5".
Domain "DOMAIN-R9C3" allows digit "6".
Domain "DOMAIN-R9C3" allows digit "7".
Domain "DOMAIN-R9C3" allows digit "8".
Domain "DOMAIN-R9C3" allows digit "9".
Cell "R9C4" has candidate domain "DOMAIN-R9C4".
Domain "DOMAIN-R9C4" allows digit "1".
Domain "DOMAIN-R9C4" allows digit "2".
Domain "DOMAIN-R9C4" allows digit "3".
Domain "DOMAIN-R9C4" allows digit "4".
Domain "DOMAIN-R9C4" allows digit "5".
Domain "DOMAIN-R9C4" allows digit "6".
Domain "DOMAIN-R9C4" allows digit "7".
Domain "DOMAIN-R9C4" allows digit "8".
Domain "DOMAIN-R9C4" allows digit "9".
Cell "R9C5" has candidate domain "DOMAIN-R9C5".
Domain "DOMAIN-R9C5" allows digit "1".
Domain "DOMAIN-R9C5" allows digit "2".
Domain "DOMAIN-R9C5" allows digit "3".
Domain "DOMAIN-R9C5" allows digit "4".
Domain "DOMAIN-R9C5" allows digit "5".
Domain "DOMAIN-R9C5" allows digit "6".
Domain "DOMAIN-R9C5" allows digit "7".
Domain "DOMAIN-R9C5" allows digit "8".
Domain "DOMAIN-R9C5" allows digit "9".
Cell "R9C6" has candidate domain "DOMAIN-R9C6".
Domain "DOMAIN-R9C6" allows digit "1".
Domain "DOMAIN-R9C6" allows digit "2".
Domain "DOMAIN-R9C6" allows digit "3".
Domain "DOMAIN-R9C6" allows digit "4".
Domain "DOMAIN-R9C6" allows digit "5".
Domain "DOMAIN-R9C6" allows digit "6".
Domain "DOMAIN-R9C6" allows digit "7".
Domain "DOMAIN-R9C6" allows digit "8".
Domain "DOMAIN-R9C6" allows digit "9".
Cell "R9C7" has candidate domain "DOMAIN-R9C7".
Domain "DOMAIN-R9C7" allows digit "1".
Domain "DOMAIN-R9C7" allows digit "2".
Domain "DOMAIN-R9C7" allows digit "3".
Domain "DOMAIN-R9C7" allows digit "4".
Domain "DOMAIN-R9C7" allows digit "5".
Domain "DOMAIN-R9C7" allows digit "6".
Domain "DOMAIN-R9C7" allows digit "7".
Domain "DOMAIN-R9C7" allows digit "8".
Domain "DOMAIN-R9C7" allows digit "9".
Cell "R9C8" has candidate domain "DOMAIN-R9C8".
Domain "DOMAIN-R9C8" allows digit "1".
Domain "DOMAIN-R9C8" allows digit "2".
Domain "DOMAIN-R9C8" allows digit "3".
Domain "DOMAIN-R9C8" allows digit "4".
Domain "DOMAIN-R9C8" allows digit "5".
Domain "DOMAIN-R9C8" allows digit "6".
Domain "DOMAIN-R9C8" allows digit "7".
Domain "DOMAIN-R9C8" allows digit "8".
Domain "DOMAIN-R9C8" allows digit "9".
Cell "R9C9" has candidate domain "DOMAIN-R9C9".
Domain "DOMAIN-R9C9" allows digit "1".
Domain "DOMAIN-R9C9" allows digit "2".
Domain "DOMAIN-R9C9" allows digit "3".
Domain "DOMAIN-R9C9" allows digit "4".
Domain "DOMAIN-R9C9" allows digit "5".
Domain "DOMAIN-R9C9" allows digit "6".
Domain "DOMAIN-R9C9" allows digit "7".
Domain "DOMAIN-R9C9" allows digit "8".
Domain "DOMAIN-R9C9" allows digit "9".
Digit "1" equals digit "1".
Digit "1" differs from digit "2".
Digit "1" differs from digit "3".
Digit "1" differs from digit "4".
Digit "1" differs from digit "5".
Digit "1" differs from digit "6".
Digit "1" differs from digit "7".
Digit "1" differs from digit "8".
Digit "1" differs from digit "9".
Digit "2" equals digit "2".
Digit "2" differs from digit "1".
Digit "2" differs from digit "3".
Digit "2" differs from digit "4".
Digit "2" differs from digit "5".
Digit "2" differs from digit "6".
Digit "2" differs from digit "7".
Digit "2" differs from digit "8".
Digit "2" differs from digit "9".
Digit "3" equals digit "3".
Digit "3" differs from digit "1".
Digit "3" differs from digit "2".
Digit "3" differs from digit "4".
Digit "3" differs from digit "5".
Digit "3" differs from digit "6".
Digit "3" differs from digit "7".
Digit "3" differs from digit "8".
Digit "3" differs from digit "9".
Digit "4" equals digit "4".
Digit "4" differs from digit "1".
Digit "4" differs from digit "2".
Digit "4" differs from digit "3".
Digit "4" differs from digit "5".
Digit "4" differs from digit "6".
Digit "4" differs from digit "7".
Digit "4" differs from digit "8".
Digit "4" differs from digit "9".
Digit "5" equals digit "5".
Digit "5" differs from digit "1".
Digit "5" differs from digit "2".
Digit "5" differs from digit "3".
Digit "5" differs from digit "4".
Digit "5" differs from digit "6".
Digit "5" differs from digit "7".
Digit "5" differs from digit "8".
Digit "5" differs from digit "9".
Digit "6" equals digit "6".
Digit "6" differs from digit "1".
Digit "6" differs from digit "2".
Digit "6" differs from digit "3".
Digit "6" differs from digit "4".
Digit "6" differs from digit "5".
Digit "6" differs from digit "7".
Digit "6" differs from digit "8".
Digit "6" differs from digit "9".
Digit "7" equals digit "7".
Digit "7" differs from digit "1".
Digit "7" differs from digit "2".
Digit "7" differs from digit "3".
Digit "7" differs from digit "4".
Digit "7" differs from digit "5".
Digit "7" differs from digit "6".
Digit "7" differs from digit "8".
Digit "7" differs from digit "9".
Digit "8" equals digit "8".
Digit "8" differs from digit "1".
Digit "8" differs from digit "2".
Digit "8" differs from digit "3".
Digit "8" differs from digit "4".
Digit "8" differs from digit "5".
Digit "8" differs from digit "6".
Digit "8" differs from digit "7".
Digit "8" differs from digit "9".
Digit "9" equals digit "9".
Digit "9" differs from digit "1".
Digit "9" differs from digit "2".
Digit "9" differs from digit "3".
Digit "9" differs from digit "4".
Digit "9" differs from digit "5".
Digit "9" differs from digit "6".
Digit "9" differs from digit "7".
Digit "9" differs from digit "8".
Program "SUDOKU-GRANULAR-PROGRAM" requires rule "INSTRUCTION-EXACTLY-ONE".
Rule "INSTRUCTION-EXACTLY-ONE" licenses semantic action "EXACTLY-ONE-VALUE-REQUIREMENT".
Program "SUDOKU-GRANULAR-PROGRAM" requires rule "INSTRUCTION-ROW-ALL-DIFFERENT".
Rule "INSTRUCTION-ROW-ALL-DIFFERENT" licenses semantic action "ALL-DIFFERENT-REQUIREMENT".
Program "SUDOKU-GRANULAR-PROGRAM" requires rule "INSTRUCTION-COLUMN-ALL-DIFFERENT".
Rule "INSTRUCTION-COLUMN-ALL-DIFFERENT" licenses semantic action "ALL-DIFFERENT-REQUIREMENT".
Program "SUDOKU-GRANULAR-PROGRAM" requires rule "INSTRUCTION-BOX-ALL-DIFFERENT".
Rule "INSTRUCTION-BOX-ALL-DIFFERENT" licenses semantic action "ALL-DIFFERENT-REQUIREMENT".
Program "SUDOKU-GRANULAR-PROGRAM" requires rule "INSTRUCTION-IMMUTABLE-GIVENS".
Rule "INSTRUCTION-IMMUTABLE-GIVENS" licenses semantic action "IMMUTABLE-GIVEN-REQUIREMENT".
Program "SUDOKU-GRANULAR-PROGRAM" requires rule "INSTRUCTION-CONTRADICTION-DETECTION".
Rule "INSTRUCTION-CONTRADICTION-DETECTION" licenses semantic action "CONTRADICTION".
Program "SUDOKU-GRANULAR-PROGRAM" requires rule "INSTRUCTION-CANDIDATE-ELIMINATION".
Rule "INSTRUCTION-CANDIDATE-ELIMINATION" licenses semantic action "EXCLUSION".
Program "SUDOKU-GRANULAR-PROGRAM" requires rule "INSTRUCTION-MINIMUM-DOMAIN-SELECTION".
Rule "INSTRUCTION-MINIMUM-DOMAIN-SELECTION" licenses semantic action "ASSIGNMENT".
Program "SUDOKU-GRANULAR-PROGRAM" requires rule "INSTRUCTION-BRANCHING".
Rule "INSTRUCTION-BRANCHING" licenses semantic action "ASSIGNMENT".
Program "SUDOKU-GRANULAR-PROGRAM" requires rule "INSTRUCTION-CONTRADICTION-REJECTION".
Rule "INSTRUCTION-CONTRADICTION-REJECTION" licenses semantic action "CONTRADICTION".
Program "SUDOKU-GRANULAR-PROGRAM" requires rule "INSTRUCTION-RESTORATION".
Rule "INSTRUCTION-RESTORATION" licenses semantic action "ASSIGNMENT".
Program "SUDOKU-GRANULAR-PROGRAM" requires rule "INSTRUCTION-COMPLETION".
Rule "INSTRUCTION-COMPLETION" licenses semantic action "COMPLETE-ASSIGNMENT".
Program "SUDOKU-GRANULAR-PROGRAM" requires rule "INSTRUCTION-UNIQUENESS-CHECKING".
Rule "INSTRUCTION-UNIQUENESS-CHECKING" licenses semantic action "UNIQUE-ASSIGNMENT".
Program "SUDOKU-GRANULAR-PROGRAM" requires rule "INSTRUCTION-DETERMINISTIC-RENDERING".
Rule "INSTRUCTION-DETERMINISTIC-RENDERING" licenses semantic action "COMPLETE-ASSIGNMENT".
Rule "INSTRUCTION-EXACTLY-ONE" precedes rule "INSTRUCTION-ROW-ALL-DIFFERENT".
Rule "INSTRUCTION-ROW-ALL-DIFFERENT" precedes rule "INSTRUCTION-COLUMN-ALL-DIFFERENT".
Rule "INSTRUCTION-COLUMN-ALL-DIFFERENT" precedes rule "INSTRUCTION-BOX-ALL-DIFFERENT".
Rule "INSTRUCTION-BOX-ALL-DIFFERENT" precedes rule "INSTRUCTION-IMMUTABLE-GIVENS".
Rule "INSTRUCTION-IMMUTABLE-GIVENS" precedes rule "INSTRUCTION-CONTRADICTION-DETECTION".
Rule "INSTRUCTION-CONTRADICTION-DETECTION" precedes rule "INSTRUCTION-CANDIDATE-ELIMINATION".
Rule "INSTRUCTION-CANDIDATE-ELIMINATION" precedes rule "INSTRUCTION-MINIMUM-DOMAIN-SELECTION".
Rule "INSTRUCTION-MINIMUM-DOMAIN-SELECTION" precedes rule "INSTRUCTION-BRANCHING".
Rule "INSTRUCTION-BRANCHING" precedes rule "INSTRUCTION-CONTRADICTION-REJECTION".
Rule "INSTRUCTION-CONTRADICTION-REJECTION" precedes rule "INSTRUCTION-RESTORATION".
Rule "INSTRUCTION-RESTORATION" precedes rule "INSTRUCTION-COMPLETION".
Rule "INSTRUCTION-COMPLETION" precedes rule "INSTRUCTION-UNIQUENESS-CHECKING".
Rule "INSTRUCTION-UNIQUENESS-CHECKING" precedes rule "INSTRUCTION-DETERMINISTIC-RENDERING".
```

## Exact Surface World source

```text
Operation "realize-semantic-result" selects kernel primitive "REALIZE_SEMANTIC_RESULT".
Instruction "realize-semantic-result" selects operation "realize-semantic-result" accepts "Realize the verified semantic result.".
```

## Exact required prompt

```text
Solve this Sudoku using only the granular instructions compiled into the field:
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

## Exact response

```text
UNSUPPORTED_ARGUMENT: bindings require field = value syntax
```

## Settlement and causal evidence

```json
{
  "baseline": {
    "handoff_count": 0,
    "refusal_code": "UNSUPPORTED_ARGUMENT",
    "refusal_message": "bindings require field = value syntax",
    "result_hash": "d3c1109f6bd2ac6276b5cf6c2cc50ff94c4153eb475c53e9b107a29436771086",
    "returned_grid": false,
    "settled_roles": [],
    "settlement_count": 0,
    "stage": "GROUNDING",
    "status": "REFUSAL"
  },
  "baseline_replay_byte_exact": true,
  "baseline_source_sha256": "05240e42a2cda0c021c25a186726e6fa861af1f4e19e2bde470169434b33c909",
  "bundle_hash": "d7c1dbd0ed9306f0f764d6c47b75698937f4dc54a633ef7df148897dd0a1c57f",
  "bundle_id": "536a3ff22d39bd4a1627b3f3c7820fcb9202539416f654efae98c3bca49969d3",
  "causal_controls": [
    {
      "control": "remove-exactly-one",
      "handoff_count": 0,
      "input_generation_id": "c78f74946af686989fe357e0996eb966f2de0ad14dc813f1cd777ab43d854efa",
      "main_generation_id": "16e0642d7183140edda656863d68dc38ca3174fc3a56ce8f75452fc2f17c8c23",
      "refusal_code": "UNSUPPORTED_ARGUMENT",
      "refusal_message": "bindings require field = value syntax",
      "replay_byte_exact": true,
      "result_hash": "8e40e337266a9c9e9b0078902b8ba4b54082c5c89b714351b77abb7424a77d69",
      "returned_grid": false,
      "settled_roles": [],
      "settlement_count": 0,
      "source_sha256": "4b034777058a44f077d359cf22c1caf050f86626805c22366c06f7c2b306876b",
      "stage": "GROUNDING",
      "status": "REFUSAL"
    },
    {
      "control": "remove-row-all-different",
      "handoff_count": 0,
      "input_generation_id": "1444aaa4e2965b69ebea7f6edc08d0e0c54913e1db26aa92ec89faf7d8d2abb8",
      "main_generation_id": "dac9c41f61155f8651f994b879ba6fb9483e2843eeda0e254fff94accda711e8",
      "refusal_code": "UNSUPPORTED_ARGUMENT",
      "refusal_message": "bindings require field = value syntax",
      "replay_byte_exact": true,
      "result_hash": "052bc820dc60c273af4e538adadd5d70e02a488fb814f0af040ba7649f5aba50",
      "returned_grid": false,
      "settled_roles": [],
      "settlement_count": 0,
      "source_sha256": "257eda0e816fecf7f10adcecc712f14822183f09b734c61264555c00f39179ff",
      "stage": "GROUNDING",
      "status": "REFUSAL"
    },
    {
      "control": "remove-column-all-different",
      "handoff_count": 0,
      "input_generation_id": "e72099959d22431f71eb59f3d42fc7b9ecb76f27957258900219d8c4e6839997",
      "main_generation_id": "70f328d6b61b5b2508b76f1a32917aa98631486f8c81569a992551c3bd60ea75",
      "refusal_code": "UNSUPPORTED_ARGUMENT",
      "refusal_message": "bindings require field = value syntax",
      "replay_byte_exact": true,
      "result_hash": "bc80e8df29e5c59dc38c2668e3f5d0807a82e92530ac64246f6dc005e63569ab",
      "returned_grid": false,
      "settled_roles": [],
      "settlement_count": 0,
      "source_sha256": "e798c3b7a3a9c11919b564f360adbb78fa59cc8f319c8e38066481169cf3138f",
      "stage": "GROUNDING",
      "status": "REFUSAL"
    },
    {
      "control": "remove-box-all-different",
      "handoff_count": 0,
      "input_generation_id": "aec460885b7161b459a5f217677e9642f96a7a95ca2081e1b2eb576081e27348",
      "main_generation_id": "4554d727974ebb6f2213e4b855ca13c4179531c213c145adb274c3238e96db41",
      "refusal_code": "UNSUPPORTED_ARGUMENT",
      "refusal_message": "bindings require field = value syntax",
      "replay_byte_exact": true,
      "result_hash": "f6b4e2c14ef08515f31e55f0507d6be469b7e8ced14f29ab8274701f936c134b",
      "returned_grid": false,
      "settled_roles": [],
      "settlement_count": 0,
      "source_sha256": "f74fbb6354116068390284ec294441e7e7c9c180f30e299bc0a8f1250b02b2b3",
      "stage": "GROUNDING",
      "status": "REFUSAL"
    },
    {
      "control": "remove-immutable-givens",
      "handoff_count": 0,
      "input_generation_id": "eed531441075e37b1b08281b16f81de9f4bcebcef474d3c59f80059298c05433",
      "main_generation_id": "5240159658fb255dd2ad12546975b5682aaea2eb091eb3e037589e95bcc24bcf",
      "refusal_code": "UNSUPPORTED_ARGUMENT",
      "refusal_message": "bindings require field = value syntax",
      "replay_byte_exact": true,
      "result_hash": "5b8061df457651c19b337aef8fefc556248cc997500cf42ecca8f6030ef353b8",
      "returned_grid": false,
      "settled_roles": [],
      "settlement_count": 0,
      "source_sha256": "a108a32d009603c40673e5b2d15f6d19aa2681cb3d60486a01a2b899a4c42326",
      "stage": "GROUNDING",
      "status": "REFUSAL"
    },
    {
      "control": "remove-candidate-elimination",
      "handoff_count": 0,
      "input_generation_id": "0c4e640c7b00a73289a1ff25bbd9ada96541007c9805200e5bd7d6b889ae760f",
      "main_generation_id": "0c0a91b93fcf7a31b8a01dd638ee59d54bfd60cd07a32321eb3c5a53714c32d5",
      "refusal_code": "UNSUPPORTED_ARGUMENT",
      "refusal_message": "bindings require field = value syntax",
      "replay_byte_exact": true,
      "result_hash": "2849f01fc9401c028a822a1418ff8f95f7a3db20aebe9d0cff3d8acab4d637a3",
      "returned_grid": false,
      "settled_roles": [],
      "settlement_count": 0,
      "source_sha256": "6ad2c46dbe0378fb7b549449c53cbc5e61c7b4bc650d494f87d45ca7d7925ae9",
      "stage": "GROUNDING",
      "status": "REFUSAL"
    },
    {
      "control": "remove-contradiction-rejection",
      "handoff_count": 0,
      "input_generation_id": "b2fb0ca9adb8904c2b53ed5dab5299f4e24305888da0fe609094cad855a95c57",
      "main_generation_id": "8c0d345f251fec97143d63ccb3dcfb134f081713e133e466cb426d2bb974fb69",
      "refusal_code": "UNSUPPORTED_ARGUMENT",
      "refusal_message": "bindings require field = value syntax",
      "replay_byte_exact": true,
      "result_hash": "6095afaa101ffa7f6c47afd46804dd0e2afc8b86f21033313d53aea4a6388733",
      "returned_grid": false,
      "settled_roles": [],
      "settlement_count": 0,
      "source_sha256": "a1d862448053820284b0f48b928ebbe9bb8292f3eae95bc4dee3b932a5e694fd",
      "stage": "GROUNDING",
      "status": "REFUSAL"
    },
    {
      "control": "remove-branching",
      "handoff_count": 0,
      "input_generation_id": "e35df66a31c1e421bdff7faf7adba5ee33ea4c86a5d7a06ff3191799996240f3",
      "main_generation_id": "71a3de6a458d8eacf94076c183a5e90c6cac03d70e582a68791a694bd06d965d",
      "refusal_code": "UNSUPPORTED_ARGUMENT",
      "refusal_message": "bindings require field = value syntax",
      "replay_byte_exact": true,
      "result_hash": "4be259a829dbf9cd5da7113e105b7ac54870781ad74a2883a00d2024aeebc17f",
      "returned_grid": false,
      "settled_roles": [],
      "settlement_count": 0,
      "source_sha256": "5cc9a73dc44e59300e6f6afa7652d57867d677717dbce890a2bdb70d6ff0bc18",
      "stage": "GROUNDING",
      "status": "REFUSAL"
    },
    {
      "control": "remove-restoration",
      "handoff_count": 0,
      "input_generation_id": "cee6e5facd3d51e1bdfae1bf3d90fb5aa7c981ce71b30d7f428dae634a7ba7b2",
      "main_generation_id": "0ff1c78be42358085736ef95f0af9cc1482a2eee7705baabeaee49c910a9b78a",
      "refusal_code": "UNSUPPORTED_ARGUMENT",
      "refusal_message": "bindings require field = value syntax",
      "replay_byte_exact": true,
      "result_hash": "1fd44fc7dffa7fb10cd596d9460e73391e5e08ad6feb3cf061dea762269cdaf5",
      "returned_grid": false,
      "settled_roles": [],
      "settlement_count": 0,
      "source_sha256": "ff586c1995642c5da585dc5997083e67e52e85c88d050ba92f2c11704c89fbb1",
      "stage": "GROUNDING",
      "status": "REFUSAL"
    },
    {
      "control": "remove-completion",
      "handoff_count": 0,
      "input_generation_id": "ad8c65dd937f53ca8b6659a3fa37e21cf5778075c513fbabe55ba77d365beb7b",
      "main_generation_id": "1754b02c17cc3a26e68f630a10203d659b69d27fd17cbdd2d820e336fdc76b95",
      "refusal_code": "UNSUPPORTED_ARGUMENT",
      "refusal_message": "bindings require field = value syntax",
      "replay_byte_exact": true,
      "result_hash": "f0d82ec009db34b5b25bc330f795816e06f306c53d03a225ad9bd8ba33800f02",
      "returned_grid": false,
      "settled_roles": [],
      "settlement_count": 0,
      "source_sha256": "fb1a792f8380db10453eca4bb00d66947f49c57069475d42c3c9632afba866a5",
      "stage": "GROUNDING",
      "status": "REFUSAL"
    },
    {
      "control": "remove-uniqueness-checking",
      "handoff_count": 0,
      "input_generation_id": "08c148e8dd039133dd6328b7211b88274a1829bff63ba75fd29097e17bf3bd99",
      "main_generation_id": "1a669efc3e8374f3b86d166bac17df16db4ea8ebf5ef56b5b2a844b1e058332c",
      "refusal_code": "UNSUPPORTED_ARGUMENT",
      "refusal_message": "bindings require field = value syntax",
      "replay_byte_exact": true,
      "result_hash": "a4ef67e51f28730f6663113d2b47bd6c8ce78b2c774713ec2d194dcf0d1aa369",
      "returned_grid": false,
      "settled_roles": [],
      "settlement_count": 0,
      "source_sha256": "8c6cad1feffd50069086abdfb955b30d9f956cc012da2a5a42aa2ee0ce6b8d6e",
      "stage": "GROUNDING",
      "status": "REFUSAL"
    },
    {
      "control": "reverse-selected-unit-memberships",
      "handoff_count": 0,
      "input_generation_id": "b50a5b835f629021e26426e89734c04f6cf00ef930096e1d23c7bf40eb7d3483",
      "main_generation_id": "9ea237be44b904dc03685cb23f12f873c72456c2fff538c24c044250197f1fd9",
      "refusal_code": "UNSUPPORTED_ARGUMENT",
      "refusal_message": "bindings require field = value syntax",
      "replay_byte_exact": true,
      "result_hash": "8121657c1ecfa38b540b28d370b2e724cc02ef2ad4b252ba6e42ef0bdbc23248",
      "returned_grid": false,
      "settled_roles": [],
      "settlement_count": 0,
      "source_sha256": "5bf308759fdeccc3ddf0f4b04d1f376e253fccde395202effc8ecd6c6559a472",
      "stage": "GROUNDING",
      "status": "REFUSAL"
    },
    {
      "control": "shuffle-selected-unit-memberships",
      "handoff_count": 0,
      "input_generation_id": "3dbc3a2c3c18d2824680bb560942842d75efb8eb9f2b2bc50881c92450d38139",
      "main_generation_id": "c741284ef23f8f7975d84d0d3f9d3ba1eab35c54042bc168b5f040535cce2e41",
      "refusal_code": "UNSUPPORTED_ARGUMENT",
      "refusal_message": "bindings require field = value syntax",
      "replay_byte_exact": true,
      "result_hash": "b55a20fcc44464a750a0ae09d41a2055a7e124f55bb4a7b8677cdefb89df89f2",
      "returned_grid": false,
      "settled_roles": [],
      "settlement_count": 0,
      "source_sha256": "da01a5c0b5ae3899bc3c4eb0567510f94192c13e660905e679c5be74c9abb567",
      "stage": "GROUNDING",
      "status": "REFUSAL"
    }
  ],
  "causal_summary": {
    "causal_sensitivity_established": false,
    "returned_any_grid": 0,
    "same_grounding_refusal": 13,
    "total": 13
  },
  "compiled_counts": {
    "cell_domain_links": 81,
    "cell_domains": 81,
    "cells": 81,
    "digit_equality_links": 9,
    "digit_inequality_links": 72,
    "digits_and_blanks": 11,
    "directional_edges_per_input_main_world": 1175,
    "domain_candidate_links": 729,
    "instruction_meanings": 14,
    "meanings_per_input_main_world": 344,
    "program_steps": 14,
    "unit_memberships": 243,
    "vectors_per_input_main_world": 321
  },
  "diagnostic_replay_byte_exact": true,
  "dispatch_count": 0,
  "elapsed_seconds": 15.44,
  "encoder": "DETERMINISTIC-TEST-ENCODER-64",
  "exact_response": "UNSUPPORTED_ARGUMENT: bindings require field = value syntax",
  "execution_performed": false,
  "final_verdict": "NO_GO_INSTRUCTION_EXECUTION",
  "independent_verifier_invoked": false,
  "network_attempts": 0,
  "prequery_leakage": {
    "assets_checked": 6,
    "findings": {
      "exact_prompt": false,
      "prompt_hash": false,
      "puzzle_hash": false,
      "puzzle_rows": false
    },
    "forbidden_values_checked": 4,
    "prompt_and_puzzle_absent": true,
    "target_solution_hash_constructed": false,
    "target_solution_or_state_constructed_by_harness": false,
    "target_solution_or_state_passed_to_compiler": false
  },
  "preservation": {
    "production_stores_and_preexisting_report_byte_identical": true,
    "protected_sha256": {
      "data/store-4.7.sqlite3": "4bda69217d0e64b398508e206a670dd99f3e64976dc9e7a0aadb5f22e55cd3da",
      "data/store-4.8.sqlite3": "b8695b7c59e8830b184f4d23eb76ea00273e272c573af309e141200bf4872334",
      "reports/SUDOKU-4.8-DISPOSABLE-001.md": "302438aa41a536ffe8d055f8b31b638673a72eb05142c519c4a3f05750a5af66"
    },
    "runtime_source_byte_identical": true,
    "tracked_files_byte_identical": true
  },
  "runtime": "4.8",
  "runtime_commit": "68835899d6416c9aa061858ec8390a33ecd8feab",
  "runtime_or_harness_sudoku_state_transitions": 0,
  "same_puzzle_binding_diagnostic": {
    "handoff_count": 1,
    "refusal_code": "UNSUPPORTED_PROGRAM",
    "refusal_message": "lookup target is missing",
    "result_hash": "eeed64416f9cc7eb416cfba3afb23d84d85b7a0fe0642ccce0ed42e040317e6e",
    "returned_grid": false,
    "settled_roles": [
      "INPUT"
    ],
    "settlement_count": 1,
    "stage": "MAIN",
    "status": "REFUSAL"
  },
  "store_schema": "proof-energy-world-store/4.8",
  "surface_source_sha256": "75aec1ef7589f3b502fe73e6950258449d3538221a34787f34a060d981f3f12c",
  "verifier_reason": "Settlement returned no grid; the verifier was forbidden to generate one.",
  "worlds": {
    "INPUT": {
      "generation_id": "19b5cce1e9527b4b12ac615ed6bd2f281fbe366cf537c44be1b59a991f29a1e8",
      "world_hash": "6d32b3cf786d67a657ed562d6db14ee00f574309e5d532696a760f9a270949f2"
    },
    "MAIN": {
      "generation_id": "7dcfdc445ec99d6e6db87752ba05d3f14bca0ec130e1976cb52e0ab1fd2f49d6",
      "world_hash": "5e63e7bfb464d52e93cc68dec786a108e603d312ba8fe34eaf8f86e79b7e908e"
    },
    "SURFACE": {
      "generation_id": "dec9241a67e5913768d445a99b243dea9f00bf1590e9c1ca63cf6a6946cee6d7",
      "world_hash": "d1dce1d45186126df32c4dc30278f217d698e106e7c9567076df9df8722f67af"
    }
  }
}
```

## Where computation occurred

- Compilation created content-addressed meanings, vectors, 1,175 directional edges, and complete source provenance.
- Stock grounding matched the instruction and Program alias but could not turn the literal grid into typed bindings.
- In the binding-format diagnostic only, stock Input settlement and verification produced one ID-only handoff.
- Stock Main settlement invoked the compiled `LINEAR_PIPELINE`; its first existing `LOOKUP` operation had no entity slot and refused. No Main semantic state or Surface response was produced.
- The independent Sudoku verifier was not invoked because settlement returned no grid. It generated, repaired, guided, and scored nothing.
- All eleven rule removals and both membership corruptions preserved the same pre-settlement refusal. This is not causal success; it confirms that the compiled Sudoku rules never entered settlement computation.

## Exact missing architecture

Runtime 4.8 has no executable 81-variable state, domain-valued variables, exactly-one/all-different factors, candidate-update transition, branch/restoration operator, Sudoku constraint energy, or uniqueness proof count over assignments. Its scalar energy verifies only outputs produced by the frozen primitive registry. Declaring granular instruction names and relations does not create new settlement dynamics.

## Isolation

All disposable bundles, SQLite stores, fixtures, caches, and raw results were deleted. Canonical Runtime 4.8 source/configuration, production stores, tests, tracked files, and the pre-existing local report remained byte-identical. This report is local and uncommitted.
