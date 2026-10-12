# Runtime 4.8 Field-Only Decimal Addition Audit

Date: 2026-08-31  
Verdict: **`NO_GO_INSTRUCTION_EXECUTION`**

## Decisive answer

The unmodified Runtime 4.8 field did **not** perform an unseen decimal addition from compiled base-10 truth rows and granular instruction meanings.

The operands were supplied only after the three Worlds were compiled and sealed. Stock grounding resolved every transient digit and the compiled Program. Input World produced one zero-violation `MAIN_REQUEST`. Main World then returned `UNSUPPORTED_PROGRAM: lookup target is missing`. The named addition instructions were passive meanings and Program metadata; they did not instantiate digit variables, select truth rows, connect carry state, or emit a result.

No adder, arithmetic solver, factor interpreter, propagation, search, enumeration, external library, query-time learning, LLM, target result, or runtime modification was used.

## Exact source compiled into Input and Main Worlds

```text
# Runtime 4.8 field-only decimal addition compilation.
# The complete universal base-10 truth table is compiled before any query.
Entity "BASE-10" is declared.
Entity "DECIMAL-ADDITION" is declared.
Entity "CARRY-0" is declared.
Entity "CARRY-1" is declared.
Entity "SUM-DIGIT" is declared.
Entity "CARRY-OUT" is declared.
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
Entity "ONES" is declared.
Entity "TENS" is declared.
Entity "HUNDREDS" is declared.
Entity "THOUSANDS" is declared.
Entity "INSTRUCTION-READ-OPERAND-DIGITS" is declared.
Entity "INSTRUCTION-CLAMP-INITIAL-CARRY" is declared.
Entity "INSTRUCTION-SELECT-MATCHING-TRUTH-ROW" is declared.
Entity "INSTRUCTION-EMIT-SUM-DIGIT" is declared.
Entity "INSTRUCTION-PROPAGATE-CARRY-TO-NEXT-PLACE" is declared.
Entity "INSTRUCTION-ADVANCE-ONE-PLACE" is declared.
Entity "INSTRUCTION-TERMINATE-AFTER-FINAL-CARRY" is declared.
Entity "INSTRUCTION-RENDER-MOST-SIGNIFICANT-FIRST" is declared.
Entity "TRUTH-0-0-0-0-0" is declared.
Entity "TRUTH-0-0-1-1-0" is declared.
Entity "TRUTH-0-1-0-1-0" is declared.
Entity "TRUTH-0-1-1-2-0" is declared.
Entity "TRUTH-0-2-0-2-0" is declared.
Entity "TRUTH-0-2-1-3-0" is declared.
Entity "TRUTH-0-3-0-3-0" is declared.
Entity "TRUTH-0-3-1-4-0" is declared.
Entity "TRUTH-0-4-0-4-0" is declared.
Entity "TRUTH-0-4-1-5-0" is declared.
Entity "TRUTH-0-5-0-5-0" is declared.
Entity "TRUTH-0-5-1-6-0" is declared.
Entity "TRUTH-0-6-0-6-0" is declared.
Entity "TRUTH-0-6-1-7-0" is declared.
Entity "TRUTH-0-7-0-7-0" is declared.
Entity "TRUTH-0-7-1-8-0" is declared.
Entity "TRUTH-0-8-0-8-0" is declared.
Entity "TRUTH-0-8-1-9-0" is declared.
Entity "TRUTH-0-9-0-9-0" is declared.
Entity "TRUTH-0-9-1-0-1" is declared.
Entity "TRUTH-1-0-0-1-0" is declared.
Entity "TRUTH-1-0-1-2-0" is declared.
Entity "TRUTH-1-1-0-2-0" is declared.
Entity "TRUTH-1-1-1-3-0" is declared.
Entity "TRUTH-1-2-0-3-0" is declared.
Entity "TRUTH-1-2-1-4-0" is declared.
Entity "TRUTH-1-3-0-4-0" is declared.
Entity "TRUTH-1-3-1-5-0" is declared.
Entity "TRUTH-1-4-0-5-0" is declared.
Entity "TRUTH-1-4-1-6-0" is declared.
Entity "TRUTH-1-5-0-6-0" is declared.
Entity "TRUTH-1-5-1-7-0" is declared.
Entity "TRUTH-1-6-0-7-0" is declared.
Entity "TRUTH-1-6-1-8-0" is declared.
Entity "TRUTH-1-7-0-8-0" is declared.
Entity "TRUTH-1-7-1-9-0" is declared.
Entity "TRUTH-1-8-0-9-0" is declared.
Entity "TRUTH-1-8-1-0-1" is declared.
Entity "TRUTH-1-9-0-0-1" is declared.
Entity "TRUTH-1-9-1-1-1" is declared.
Entity "TRUTH-2-0-0-2-0" is declared.
Entity "TRUTH-2-0-1-3-0" is declared.
Entity "TRUTH-2-1-0-3-0" is declared.
Entity "TRUTH-2-1-1-4-0" is declared.
Entity "TRUTH-2-2-0-4-0" is declared.
Entity "TRUTH-2-2-1-5-0" is declared.
Entity "TRUTH-2-3-0-5-0" is declared.
Entity "TRUTH-2-3-1-6-0" is declared.
Entity "TRUTH-2-4-0-6-0" is declared.
Entity "TRUTH-2-4-1-7-0" is declared.
Entity "TRUTH-2-5-0-7-0" is declared.
Entity "TRUTH-2-5-1-8-0" is declared.
Entity "TRUTH-2-6-0-8-0" is declared.
Entity "TRUTH-2-6-1-9-0" is declared.
Entity "TRUTH-2-7-0-9-0" is declared.
Entity "TRUTH-2-7-1-0-1" is declared.
Entity "TRUTH-2-8-0-0-1" is declared.
Entity "TRUTH-2-8-1-1-1" is declared.
Entity "TRUTH-2-9-0-1-1" is declared.
Entity "TRUTH-2-9-1-2-1" is declared.
Entity "TRUTH-3-0-0-3-0" is declared.
Entity "TRUTH-3-0-1-4-0" is declared.
Entity "TRUTH-3-1-0-4-0" is declared.
Entity "TRUTH-3-1-1-5-0" is declared.
Entity "TRUTH-3-2-0-5-0" is declared.
Entity "TRUTH-3-2-1-6-0" is declared.
Entity "TRUTH-3-3-0-6-0" is declared.
Entity "TRUTH-3-3-1-7-0" is declared.
Entity "TRUTH-3-4-0-7-0" is declared.
Entity "TRUTH-3-4-1-8-0" is declared.
Entity "TRUTH-3-5-0-8-0" is declared.
Entity "TRUTH-3-5-1-9-0" is declared.
Entity "TRUTH-3-6-0-9-0" is declared.
Entity "TRUTH-3-6-1-0-1" is declared.
Entity "TRUTH-3-7-0-0-1" is declared.
Entity "TRUTH-3-7-1-1-1" is declared.
Entity "TRUTH-3-8-0-1-1" is declared.
Entity "TRUTH-3-8-1-2-1" is declared.
Entity "TRUTH-3-9-0-2-1" is declared.
Entity "TRUTH-3-9-1-3-1" is declared.
Entity "TRUTH-4-0-0-4-0" is declared.
Entity "TRUTH-4-0-1-5-0" is declared.
Entity "TRUTH-4-1-0-5-0" is declared.
Entity "TRUTH-4-1-1-6-0" is declared.
Entity "TRUTH-4-2-0-6-0" is declared.
Entity "TRUTH-4-2-1-7-0" is declared.
Entity "TRUTH-4-3-0-7-0" is declared.
Entity "TRUTH-4-3-1-8-0" is declared.
Entity "TRUTH-4-4-0-8-0" is declared.
Entity "TRUTH-4-4-1-9-0" is declared.
Entity "TRUTH-4-5-0-9-0" is declared.
Entity "TRUTH-4-5-1-0-1" is declared.
Entity "TRUTH-4-6-0-0-1" is declared.
Entity "TRUTH-4-6-1-1-1" is declared.
Entity "TRUTH-4-7-0-1-1" is declared.
Entity "TRUTH-4-7-1-2-1" is declared.
Entity "TRUTH-4-8-0-2-1" is declared.
Entity "TRUTH-4-8-1-3-1" is declared.
Entity "TRUTH-4-9-0-3-1" is declared.
Entity "TRUTH-4-9-1-4-1" is declared.
Entity "TRUTH-5-0-0-5-0" is declared.
Entity "TRUTH-5-0-1-6-0" is declared.
Entity "TRUTH-5-1-0-6-0" is declared.
Entity "TRUTH-5-1-1-7-0" is declared.
Entity "TRUTH-5-2-0-7-0" is declared.
Entity "TRUTH-5-2-1-8-0" is declared.
Entity "TRUTH-5-3-0-8-0" is declared.
Entity "TRUTH-5-3-1-9-0" is declared.
Entity "TRUTH-5-4-0-9-0" is declared.
Entity "TRUTH-5-4-1-0-1" is declared.
Entity "TRUTH-5-5-0-0-1" is declared.
Entity "TRUTH-5-5-1-1-1" is declared.
Entity "TRUTH-5-6-0-1-1" is declared.
Entity "TRUTH-5-6-1-2-1" is declared.
Entity "TRUTH-5-7-0-2-1" is declared.
Entity "TRUTH-5-7-1-3-1" is declared.
Entity "TRUTH-5-8-0-3-1" is declared.
Entity "TRUTH-5-8-1-4-1" is declared.
Entity "TRUTH-5-9-0-4-1" is declared.
Entity "TRUTH-5-9-1-5-1" is declared.
Entity "TRUTH-6-0-0-6-0" is declared.
Entity "TRUTH-6-0-1-7-0" is declared.
Entity "TRUTH-6-1-0-7-0" is declared.
Entity "TRUTH-6-1-1-8-0" is declared.
Entity "TRUTH-6-2-0-8-0" is declared.
Entity "TRUTH-6-2-1-9-0" is declared.
Entity "TRUTH-6-3-0-9-0" is declared.
Entity "TRUTH-6-3-1-0-1" is declared.
Entity "TRUTH-6-4-0-0-1" is declared.
Entity "TRUTH-6-4-1-1-1" is declared.
Entity "TRUTH-6-5-0-1-1" is declared.
Entity "TRUTH-6-5-1-2-1" is declared.
Entity "TRUTH-6-6-0-2-1" is declared.
Entity "TRUTH-6-6-1-3-1" is declared.
Entity "TRUTH-6-7-0-3-1" is declared.
Entity "TRUTH-6-7-1-4-1" is declared.
Entity "TRUTH-6-8-0-4-1" is declared.
Entity "TRUTH-6-8-1-5-1" is declared.
Entity "TRUTH-6-9-0-5-1" is declared.
Entity "TRUTH-6-9-1-6-1" is declared.
Entity "TRUTH-7-0-0-7-0" is declared.
Entity "TRUTH-7-0-1-8-0" is declared.
Entity "TRUTH-7-1-0-8-0" is declared.
Entity "TRUTH-7-1-1-9-0" is declared.
Entity "TRUTH-7-2-0-9-0" is declared.
Entity "TRUTH-7-2-1-0-1" is declared.
Entity "TRUTH-7-3-0-0-1" is declared.
Entity "TRUTH-7-3-1-1-1" is declared.
Entity "TRUTH-7-4-0-1-1" is declared.
Entity "TRUTH-7-4-1-2-1" is declared.
Entity "TRUTH-7-5-0-2-1" is declared.
Entity "TRUTH-7-5-1-3-1" is declared.
Entity "TRUTH-7-6-0-3-1" is declared.
Entity "TRUTH-7-6-1-4-1" is declared.
Entity "TRUTH-7-7-0-4-1" is declared.
Entity "TRUTH-7-7-1-5-1" is declared.
Entity "TRUTH-7-8-0-5-1" is declared.
Entity "TRUTH-7-8-1-6-1" is declared.
Entity "TRUTH-7-9-0-6-1" is declared.
Entity "TRUTH-7-9-1-7-1" is declared.
Entity "TRUTH-8-0-0-8-0" is declared.
Entity "TRUTH-8-0-1-9-0" is declared.
Entity "TRUTH-8-1-0-9-0" is declared.
Entity "TRUTH-8-1-1-0-1" is declared.
Entity "TRUTH-8-2-0-0-1" is declared.
Entity "TRUTH-8-2-1-1-1" is declared.
Entity "TRUTH-8-3-0-1-1" is declared.
Entity "TRUTH-8-3-1-2-1" is declared.
Entity "TRUTH-8-4-0-2-1" is declared.
Entity "TRUTH-8-4-1-3-1" is declared.
Entity "TRUTH-8-5-0-3-1" is declared.
Entity "TRUTH-8-5-1-4-1" is declared.
Entity "TRUTH-8-6-0-4-1" is declared.
Entity "TRUTH-8-6-1-5-1" is declared.
Entity "TRUTH-8-7-0-5-1" is declared.
Entity "TRUTH-8-7-1-6-1" is declared.
Entity "TRUTH-8-8-0-6-1" is declared.
Entity "TRUTH-8-8-1-7-1" is declared.
Entity "TRUTH-8-9-0-7-1" is declared.
Entity "TRUTH-8-9-1-8-1" is declared.
Entity "TRUTH-9-0-0-9-0" is declared.
Entity "TRUTH-9-0-1-0-1" is declared.
Entity "TRUTH-9-1-0-0-1" is declared.
Entity "TRUTH-9-1-1-1-1" is declared.
Entity "TRUTH-9-2-0-1-1" is declared.
Entity "TRUTH-9-2-1-2-1" is declared.
Entity "TRUTH-9-3-0-2-1" is declared.
Entity "TRUTH-9-3-1-3-1" is declared.
Entity "TRUTH-9-4-0-3-1" is declared.
Entity "TRUTH-9-4-1-4-1" is declared.
Entity "TRUTH-9-5-0-4-1" is declared.
Entity "TRUTH-9-5-1-5-1" is declared.
Entity "TRUTH-9-6-0-5-1" is declared.
Entity "TRUTH-9-6-1-6-1" is declared.
Entity "TRUTH-9-7-0-6-1" is declared.
Entity "TRUTH-9-7-1-7-1" is declared.
Entity "TRUTH-9-8-0-7-1" is declared.
Entity "TRUTH-9-8-1-8-1" is declared.
Entity "TRUTH-9-9-0-8-1" is declared.
Entity "TRUTH-9-9-1-9-1" is declared.
Directional relation "decimal-has-digit" maps Meaning to Meaning and is multi-valued.
Relation form "decimal-form-1" for relation "decimal-has-digit" accepts "System {SOURCE} permits digit {DESTINATION}.".
Directional relation "row-left" maps Meaning to Meaning and is multi-valued.
Relation form "decimal-form-2" for relation "row-left" accepts "Truth row {SOURCE} has left digit {DESTINATION}.".
Directional relation "row-right" maps Meaning to Meaning and is multi-valued.
Relation form "decimal-form-3" for relation "row-right" accepts "Truth row {SOURCE} has right digit {DESTINATION}.".
Directional relation "row-carry-in" maps Meaning to Meaning and is multi-valued.
Relation form "decimal-form-4" for relation "row-carry-in" accepts "Truth row {SOURCE} has carry input {DESTINATION}.".
Directional relation "row-sum" maps Meaning to Meaning and is multi-valued.
Relation form "decimal-form-5" for relation "row-sum" accepts "Truth row {SOURCE} emits sum digit {DESTINATION}.".
Directional relation "row-carry-out" maps Meaning to Meaning and is multi-valued.
Relation form "decimal-form-6" for relation "row-carry-out" accepts "Truth row {SOURCE} emits carry output {DESTINATION}.".
Directional relation "next-place" maps Meaning to Meaning and is multi-valued.
Relation form "decimal-form-7" for relation "next-place" accepts "Place {SOURCE} advances to place {DESTINATION}.".
Directional relation "requires" maps Meaning to Meaning and is multi-valued.
Relation form "decimal-form-8" for relation "requires" accepts "Addition {SOURCE} requires instruction {DESTINATION}.".
Directional relation "precedes" maps Meaning to Meaning and is multi-valued.
Relation form "decimal-form-9" for relation "precedes" accepts "Instruction {SOURCE} precedes instruction {DESTINATION}.".
Directional relation "licenses" maps Meaning to Meaning and is multi-valued.
Relation form "decimal-form-10" for relation "licenses" accepts "Instruction {SOURCE} licenses action {DESTINATION}.".
Scalar type "decimal-digit" selects kernel type "STRING".
Structured schema "decimal-operands" is canonical JSON Schema "{\"additionalProperties\":false,\"properties\":{\"A0\":{\"type\":\"string\",\"x-moth-field\":\"A0\"},\"A1\":{\"type\":\"string\",\"x-moth-field\":\"A1\"},\"A2\":{\"type\":\"string\",\"x-moth-field\":\"A2\"},\"A3\":{\"type\":\"string\",\"x-moth-field\":\"A3\"},\"B0\":{\"type\":\"string\",\"x-moth-field\":\"B0\"},\"B1\":{\"type\":\"string\",\"x-moth-field\":\"B1\"},\"B2\":{\"type\":\"string\",\"x-moth-field\":\"B2\"},\"B3\":{\"type\":\"string\",\"x-moth-field\":\"B3\"},\"C0\":{\"type\":\"string\",\"x-moth-field\":\"C0\"}},\"required\":[\"A0\",\"A1\",\"A2\",\"A3\",\"B0\",\"B1\",\"B2\",\"B3\",\"C0\"],\"type\":\"object\"}".
Schema field "A0" in schema "decimal-operands" has type "decimal-digit" and is required.
Schema field "A1" in schema "decimal-operands" has type "decimal-digit" and is required.
Schema field "A2" in schema "decimal-operands" has type "decimal-digit" and is required.
Schema field "A3" in schema "decimal-operands" has type "decimal-digit" and is required.
Schema field "B0" in schema "decimal-operands" has type "decimal-digit" and is required.
Schema field "B1" in schema "decimal-operands" has type "decimal-digit" and is required.
Schema field "B2" in schema "decimal-operands" has type "decimal-digit" and is required.
Schema field "B3" in schema "decimal-operands" has type "decimal-digit" and is required.
Schema field "C0" in schema "decimal-operands" has type "decimal-digit" and is required.
Operation "decimal-instruction-sequence" selects kernel primitive "LINEAR_PIPELINE".
Program "decimal-addition-program" is canonical step JSON "[{\"compiled_instruction\":\"INSTRUCTION-READ-OPERAND-DIGITS\",\"operation\":\"LOOKUP\"},{\"compiled_instruction\":\"INSTRUCTION-CLAMP-INITIAL-CARRY\",\"operation\":\"LOOKUP\"},{\"compiled_instruction\":\"INSTRUCTION-SELECT-MATCHING-TRUTH-ROW\",\"operation\":\"LOOKUP\"},{\"compiled_instruction\":\"INSTRUCTION-EMIT-SUM-DIGIT\",\"operation\":\"LOOKUP\"},{\"compiled_instruction\":\"INSTRUCTION-PROPAGATE-CARRY-TO-NEXT-PLACE\",\"operation\":\"LOOKUP\"},{\"compiled_instruction\":\"INSTRUCTION-ADVANCE-ONE-PLACE\",\"operation\":\"LOOKUP\"},{\"compiled_instruction\":\"INSTRUCTION-TERMINATE-AFTER-FINAL-CARRY\",\"operation\":\"LOOKUP\"},{\"compiled_instruction\":\"INSTRUCTION-RENDER-MOST-SIGNIFICANT-FIRST\",\"operation\":\"LOOKUP\"}]".
Alias "compiled decimal addition instructions" denotes Program "decimal-addition-program".
Output schema "decimal-result" selects kernel schema "ANSWER_WITH_PROOF".
Instruction "add-decimals" selects operation "decimal-instruction-sequence" accepts "Add using {PROGRAM} with {BINDINGS}.".
System "BASE-10" permits digit "0".
System "BASE-10" permits digit "1".
System "BASE-10" permits digit "2".
System "BASE-10" permits digit "3".
System "BASE-10" permits digit "4".
System "BASE-10" permits digit "5".
System "BASE-10" permits digit "6".
System "BASE-10" permits digit "7".
System "BASE-10" permits digit "8".
System "BASE-10" permits digit "9".
Truth row "TRUTH-0-0-0-0-0" has left digit "0".
Truth row "TRUTH-0-0-0-0-0" has right digit "0".
Truth row "TRUTH-0-0-0-0-0" has carry input "CARRY-0".
Truth row "TRUTH-0-0-0-0-0" emits sum digit "0".
Truth row "TRUTH-0-0-0-0-0" emits carry output "CARRY-0".
Truth row "TRUTH-0-0-1-1-0" has left digit "0".
Truth row "TRUTH-0-0-1-1-0" has right digit "0".
Truth row "TRUTH-0-0-1-1-0" has carry input "CARRY-1".
Truth row "TRUTH-0-0-1-1-0" emits sum digit "1".
Truth row "TRUTH-0-0-1-1-0" emits carry output "CARRY-0".
Truth row "TRUTH-0-1-0-1-0" has left digit "0".
Truth row "TRUTH-0-1-0-1-0" has right digit "1".
Truth row "TRUTH-0-1-0-1-0" has carry input "CARRY-0".
Truth row "TRUTH-0-1-0-1-0" emits sum digit "1".
Truth row "TRUTH-0-1-0-1-0" emits carry output "CARRY-0".
Truth row "TRUTH-0-1-1-2-0" has left digit "0".
Truth row "TRUTH-0-1-1-2-0" has right digit "1".
Truth row "TRUTH-0-1-1-2-0" has carry input "CARRY-1".
Truth row "TRUTH-0-1-1-2-0" emits sum digit "2".
Truth row "TRUTH-0-1-1-2-0" emits carry output "CARRY-0".
Truth row "TRUTH-0-2-0-2-0" has left digit "0".
Truth row "TRUTH-0-2-0-2-0" has right digit "2".
Truth row "TRUTH-0-2-0-2-0" has carry input "CARRY-0".
Truth row "TRUTH-0-2-0-2-0" emits sum digit "2".
Truth row "TRUTH-0-2-0-2-0" emits carry output "CARRY-0".
Truth row "TRUTH-0-2-1-3-0" has left digit "0".
Truth row "TRUTH-0-2-1-3-0" has right digit "2".
Truth row "TRUTH-0-2-1-3-0" has carry input "CARRY-1".
Truth row "TRUTH-0-2-1-3-0" emits sum digit "3".
Truth row "TRUTH-0-2-1-3-0" emits carry output "CARRY-0".
Truth row "TRUTH-0-3-0-3-0" has left digit "0".
Truth row "TRUTH-0-3-0-3-0" has right digit "3".
Truth row "TRUTH-0-3-0-3-0" has carry input "CARRY-0".
Truth row "TRUTH-0-3-0-3-0" emits sum digit "3".
Truth row "TRUTH-0-3-0-3-0" emits carry output "CARRY-0".
Truth row "TRUTH-0-3-1-4-0" has left digit "0".
Truth row "TRUTH-0-3-1-4-0" has right digit "3".
Truth row "TRUTH-0-3-1-4-0" has carry input "CARRY-1".
Truth row "TRUTH-0-3-1-4-0" emits sum digit "4".
Truth row "TRUTH-0-3-1-4-0" emits carry output "CARRY-0".
Truth row "TRUTH-0-4-0-4-0" has left digit "0".
Truth row "TRUTH-0-4-0-4-0" has right digit "4".
Truth row "TRUTH-0-4-0-4-0" has carry input "CARRY-0".
Truth row "TRUTH-0-4-0-4-0" emits sum digit "4".
Truth row "TRUTH-0-4-0-4-0" emits carry output "CARRY-0".
Truth row "TRUTH-0-4-1-5-0" has left digit "0".
Truth row "TRUTH-0-4-1-5-0" has right digit "4".
Truth row "TRUTH-0-4-1-5-0" has carry input "CARRY-1".
Truth row "TRUTH-0-4-1-5-0" emits sum digit "5".
Truth row "TRUTH-0-4-1-5-0" emits carry output "CARRY-0".
Truth row "TRUTH-0-5-0-5-0" has left digit "0".
Truth row "TRUTH-0-5-0-5-0" has right digit "5".
Truth row "TRUTH-0-5-0-5-0" has carry input "CARRY-0".
Truth row "TRUTH-0-5-0-5-0" emits sum digit "5".
Truth row "TRUTH-0-5-0-5-0" emits carry output "CARRY-0".
Truth row "TRUTH-0-5-1-6-0" has left digit "0".
Truth row "TRUTH-0-5-1-6-0" has right digit "5".
Truth row "TRUTH-0-5-1-6-0" has carry input "CARRY-1".
Truth row "TRUTH-0-5-1-6-0" emits sum digit "6".
Truth row "TRUTH-0-5-1-6-0" emits carry output "CARRY-0".
Truth row "TRUTH-0-6-0-6-0" has left digit "0".
Truth row "TRUTH-0-6-0-6-0" has right digit "6".
Truth row "TRUTH-0-6-0-6-0" has carry input "CARRY-0".
Truth row "TRUTH-0-6-0-6-0" emits sum digit "6".
Truth row "TRUTH-0-6-0-6-0" emits carry output "CARRY-0".
Truth row "TRUTH-0-6-1-7-0" has left digit "0".
Truth row "TRUTH-0-6-1-7-0" has right digit "6".
Truth row "TRUTH-0-6-1-7-0" has carry input "CARRY-1".
Truth row "TRUTH-0-6-1-7-0" emits sum digit "7".
Truth row "TRUTH-0-6-1-7-0" emits carry output "CARRY-0".
Truth row "TRUTH-0-7-0-7-0" has left digit "0".
Truth row "TRUTH-0-7-0-7-0" has right digit "7".
Truth row "TRUTH-0-7-0-7-0" has carry input "CARRY-0".
Truth row "TRUTH-0-7-0-7-0" emits sum digit "7".
Truth row "TRUTH-0-7-0-7-0" emits carry output "CARRY-0".
Truth row "TRUTH-0-7-1-8-0" has left digit "0".
Truth row "TRUTH-0-7-1-8-0" has right digit "7".
Truth row "TRUTH-0-7-1-8-0" has carry input "CARRY-1".
Truth row "TRUTH-0-7-1-8-0" emits sum digit "8".
Truth row "TRUTH-0-7-1-8-0" emits carry output "CARRY-0".
Truth row "TRUTH-0-8-0-8-0" has left digit "0".
Truth row "TRUTH-0-8-0-8-0" has right digit "8".
Truth row "TRUTH-0-8-0-8-0" has carry input "CARRY-0".
Truth row "TRUTH-0-8-0-8-0" emits sum digit "8".
Truth row "TRUTH-0-8-0-8-0" emits carry output "CARRY-0".
Truth row "TRUTH-0-8-1-9-0" has left digit "0".
Truth row "TRUTH-0-8-1-9-0" has right digit "8".
Truth row "TRUTH-0-8-1-9-0" has carry input "CARRY-1".
Truth row "TRUTH-0-8-1-9-0" emits sum digit "9".
Truth row "TRUTH-0-8-1-9-0" emits carry output "CARRY-0".
Truth row "TRUTH-0-9-0-9-0" has left digit "0".
Truth row "TRUTH-0-9-0-9-0" has right digit "9".
Truth row "TRUTH-0-9-0-9-0" has carry input "CARRY-0".
Truth row "TRUTH-0-9-0-9-0" emits sum digit "9".
Truth row "TRUTH-0-9-0-9-0" emits carry output "CARRY-0".
Truth row "TRUTH-0-9-1-0-1" has left digit "0".
Truth row "TRUTH-0-9-1-0-1" has right digit "9".
Truth row "TRUTH-0-9-1-0-1" has carry input "CARRY-1".
Truth row "TRUTH-0-9-1-0-1" emits sum digit "0".
Truth row "TRUTH-0-9-1-0-1" emits carry output "CARRY-1".
Truth row "TRUTH-1-0-0-1-0" has left digit "1".
Truth row "TRUTH-1-0-0-1-0" has right digit "0".
Truth row "TRUTH-1-0-0-1-0" has carry input "CARRY-0".
Truth row "TRUTH-1-0-0-1-0" emits sum digit "1".
Truth row "TRUTH-1-0-0-1-0" emits carry output "CARRY-0".
Truth row "TRUTH-1-0-1-2-0" has left digit "1".
Truth row "TRUTH-1-0-1-2-0" has right digit "0".
Truth row "TRUTH-1-0-1-2-0" has carry input "CARRY-1".
Truth row "TRUTH-1-0-1-2-0" emits sum digit "2".
Truth row "TRUTH-1-0-1-2-0" emits carry output "CARRY-0".
Truth row "TRUTH-1-1-0-2-0" has left digit "1".
Truth row "TRUTH-1-1-0-2-0" has right digit "1".
Truth row "TRUTH-1-1-0-2-0" has carry input "CARRY-0".
Truth row "TRUTH-1-1-0-2-0" emits sum digit "2".
Truth row "TRUTH-1-1-0-2-0" emits carry output "CARRY-0".
Truth row "TRUTH-1-1-1-3-0" has left digit "1".
Truth row "TRUTH-1-1-1-3-0" has right digit "1".
Truth row "TRUTH-1-1-1-3-0" has carry input "CARRY-1".
Truth row "TRUTH-1-1-1-3-0" emits sum digit "3".
Truth row "TRUTH-1-1-1-3-0" emits carry output "CARRY-0".
Truth row "TRUTH-1-2-0-3-0" has left digit "1".
Truth row "TRUTH-1-2-0-3-0" has right digit "2".
Truth row "TRUTH-1-2-0-3-0" has carry input "CARRY-0".
Truth row "TRUTH-1-2-0-3-0" emits sum digit "3".
Truth row "TRUTH-1-2-0-3-0" emits carry output "CARRY-0".
Truth row "TRUTH-1-2-1-4-0" has left digit "1".
Truth row "TRUTH-1-2-1-4-0" has right digit "2".
Truth row "TRUTH-1-2-1-4-0" has carry input "CARRY-1".
Truth row "TRUTH-1-2-1-4-0" emits sum digit "4".
Truth row "TRUTH-1-2-1-4-0" emits carry output "CARRY-0".
Truth row "TRUTH-1-3-0-4-0" has left digit "1".
Truth row "TRUTH-1-3-0-4-0" has right digit "3".
Truth row "TRUTH-1-3-0-4-0" has carry input "CARRY-0".
Truth row "TRUTH-1-3-0-4-0" emits sum digit "4".
Truth row "TRUTH-1-3-0-4-0" emits carry output "CARRY-0".
Truth row "TRUTH-1-3-1-5-0" has left digit "1".
Truth row "TRUTH-1-3-1-5-0" has right digit "3".
Truth row "TRUTH-1-3-1-5-0" has carry input "CARRY-1".
Truth row "TRUTH-1-3-1-5-0" emits sum digit "5".
Truth row "TRUTH-1-3-1-5-0" emits carry output "CARRY-0".
Truth row "TRUTH-1-4-0-5-0" has left digit "1".
Truth row "TRUTH-1-4-0-5-0" has right digit "4".
Truth row "TRUTH-1-4-0-5-0" has carry input "CARRY-0".
Truth row "TRUTH-1-4-0-5-0" emits sum digit "5".
Truth row "TRUTH-1-4-0-5-0" emits carry output "CARRY-0".
Truth row "TRUTH-1-4-1-6-0" has left digit "1".
Truth row "TRUTH-1-4-1-6-0" has right digit "4".
Truth row "TRUTH-1-4-1-6-0" has carry input "CARRY-1".
Truth row "TRUTH-1-4-1-6-0" emits sum digit "6".
Truth row "TRUTH-1-4-1-6-0" emits carry output "CARRY-0".
Truth row "TRUTH-1-5-0-6-0" has left digit "1".
Truth row "TRUTH-1-5-0-6-0" has right digit "5".
Truth row "TRUTH-1-5-0-6-0" has carry input "CARRY-0".
Truth row "TRUTH-1-5-0-6-0" emits sum digit "6".
Truth row "TRUTH-1-5-0-6-0" emits carry output "CARRY-0".
Truth row "TRUTH-1-5-1-7-0" has left digit "1".
Truth row "TRUTH-1-5-1-7-0" has right digit "5".
Truth row "TRUTH-1-5-1-7-0" has carry input "CARRY-1".
Truth row "TRUTH-1-5-1-7-0" emits sum digit "7".
Truth row "TRUTH-1-5-1-7-0" emits carry output "CARRY-0".
Truth row "TRUTH-1-6-0-7-0" has left digit "1".
Truth row "TRUTH-1-6-0-7-0" has right digit "6".
Truth row "TRUTH-1-6-0-7-0" has carry input "CARRY-0".
Truth row "TRUTH-1-6-0-7-0" emits sum digit "7".
Truth row "TRUTH-1-6-0-7-0" emits carry output "CARRY-0".
Truth row "TRUTH-1-6-1-8-0" has left digit "1".
Truth row "TRUTH-1-6-1-8-0" has right digit "6".
Truth row "TRUTH-1-6-1-8-0" has carry input "CARRY-1".
Truth row "TRUTH-1-6-1-8-0" emits sum digit "8".
Truth row "TRUTH-1-6-1-8-0" emits carry output "CARRY-0".
Truth row "TRUTH-1-7-0-8-0" has left digit "1".
Truth row "TRUTH-1-7-0-8-0" has right digit "7".
Truth row "TRUTH-1-7-0-8-0" has carry input "CARRY-0".
Truth row "TRUTH-1-7-0-8-0" emits sum digit "8".
Truth row "TRUTH-1-7-0-8-0" emits carry output "CARRY-0".
Truth row "TRUTH-1-7-1-9-0" has left digit "1".
Truth row "TRUTH-1-7-1-9-0" has right digit "7".
Truth row "TRUTH-1-7-1-9-0" has carry input "CARRY-1".
Truth row "TRUTH-1-7-1-9-0" emits sum digit "9".
Truth row "TRUTH-1-7-1-9-0" emits carry output "CARRY-0".
Truth row "TRUTH-1-8-0-9-0" has left digit "1".
Truth row "TRUTH-1-8-0-9-0" has right digit "8".
Truth row "TRUTH-1-8-0-9-0" has carry input "CARRY-0".
Truth row "TRUTH-1-8-0-9-0" emits sum digit "9".
Truth row "TRUTH-1-8-0-9-0" emits carry output "CARRY-0".
Truth row "TRUTH-1-8-1-0-1" has left digit "1".
Truth row "TRUTH-1-8-1-0-1" has right digit "8".
Truth row "TRUTH-1-8-1-0-1" has carry input "CARRY-1".
Truth row "TRUTH-1-8-1-0-1" emits sum digit "0".
Truth row "TRUTH-1-8-1-0-1" emits carry output "CARRY-1".
Truth row "TRUTH-1-9-0-0-1" has left digit "1".
Truth row "TRUTH-1-9-0-0-1" has right digit "9".
Truth row "TRUTH-1-9-0-0-1" has carry input "CARRY-0".
Truth row "TRUTH-1-9-0-0-1" emits sum digit "0".
Truth row "TRUTH-1-9-0-0-1" emits carry output "CARRY-1".
Truth row "TRUTH-1-9-1-1-1" has left digit "1".
Truth row "TRUTH-1-9-1-1-1" has right digit "9".
Truth row "TRUTH-1-9-1-1-1" has carry input "CARRY-1".
Truth row "TRUTH-1-9-1-1-1" emits sum digit "1".
Truth row "TRUTH-1-9-1-1-1" emits carry output "CARRY-1".
Truth row "TRUTH-2-0-0-2-0" has left digit "2".
Truth row "TRUTH-2-0-0-2-0" has right digit "0".
Truth row "TRUTH-2-0-0-2-0" has carry input "CARRY-0".
Truth row "TRUTH-2-0-0-2-0" emits sum digit "2".
Truth row "TRUTH-2-0-0-2-0" emits carry output "CARRY-0".
Truth row "TRUTH-2-0-1-3-0" has left digit "2".
Truth row "TRUTH-2-0-1-3-0" has right digit "0".
Truth row "TRUTH-2-0-1-3-0" has carry input "CARRY-1".
Truth row "TRUTH-2-0-1-3-0" emits sum digit "3".
Truth row "TRUTH-2-0-1-3-0" emits carry output "CARRY-0".
Truth row "TRUTH-2-1-0-3-0" has left digit "2".
Truth row "TRUTH-2-1-0-3-0" has right digit "1".
Truth row "TRUTH-2-1-0-3-0" has carry input "CARRY-0".
Truth row "TRUTH-2-1-0-3-0" emits sum digit "3".
Truth row "TRUTH-2-1-0-3-0" emits carry output "CARRY-0".
Truth row "TRUTH-2-1-1-4-0" has left digit "2".
Truth row "TRUTH-2-1-1-4-0" has right digit "1".
Truth row "TRUTH-2-1-1-4-0" has carry input "CARRY-1".
Truth row "TRUTH-2-1-1-4-0" emits sum digit "4".
Truth row "TRUTH-2-1-1-4-0" emits carry output "CARRY-0".
Truth row "TRUTH-2-2-0-4-0" has left digit "2".
Truth row "TRUTH-2-2-0-4-0" has right digit "2".
Truth row "TRUTH-2-2-0-4-0" has carry input "CARRY-0".
Truth row "TRUTH-2-2-0-4-0" emits sum digit "4".
Truth row "TRUTH-2-2-0-4-0" emits carry output "CARRY-0".
Truth row "TRUTH-2-2-1-5-0" has left digit "2".
Truth row "TRUTH-2-2-1-5-0" has right digit "2".
Truth row "TRUTH-2-2-1-5-0" has carry input "CARRY-1".
Truth row "TRUTH-2-2-1-5-0" emits sum digit "5".
Truth row "TRUTH-2-2-1-5-0" emits carry output "CARRY-0".
Truth row "TRUTH-2-3-0-5-0" has left digit "2".
Truth row "TRUTH-2-3-0-5-0" has right digit "3".
Truth row "TRUTH-2-3-0-5-0" has carry input "CARRY-0".
Truth row "TRUTH-2-3-0-5-0" emits sum digit "5".
Truth row "TRUTH-2-3-0-5-0" emits carry output "CARRY-0".
Truth row "TRUTH-2-3-1-6-0" has left digit "2".
Truth row "TRUTH-2-3-1-6-0" has right digit "3".
Truth row "TRUTH-2-3-1-6-0" has carry input "CARRY-1".
Truth row "TRUTH-2-3-1-6-0" emits sum digit "6".
Truth row "TRUTH-2-3-1-6-0" emits carry output "CARRY-0".
Truth row "TRUTH-2-4-0-6-0" has left digit "2".
Truth row "TRUTH-2-4-0-6-0" has right digit "4".
Truth row "TRUTH-2-4-0-6-0" has carry input "CARRY-0".
Truth row "TRUTH-2-4-0-6-0" emits sum digit "6".
Truth row "TRUTH-2-4-0-6-0" emits carry output "CARRY-0".
Truth row "TRUTH-2-4-1-7-0" has left digit "2".
Truth row "TRUTH-2-4-1-7-0" has right digit "4".
Truth row "TRUTH-2-4-1-7-0" has carry input "CARRY-1".
Truth row "TRUTH-2-4-1-7-0" emits sum digit "7".
Truth row "TRUTH-2-4-1-7-0" emits carry output "CARRY-0".
Truth row "TRUTH-2-5-0-7-0" has left digit "2".
Truth row "TRUTH-2-5-0-7-0" has right digit "5".
Truth row "TRUTH-2-5-0-7-0" has carry input "CARRY-0".
Truth row "TRUTH-2-5-0-7-0" emits sum digit "7".
Truth row "TRUTH-2-5-0-7-0" emits carry output "CARRY-0".
Truth row "TRUTH-2-5-1-8-0" has left digit "2".
Truth row "TRUTH-2-5-1-8-0" has right digit "5".
Truth row "TRUTH-2-5-1-8-0" has carry input "CARRY-1".
Truth row "TRUTH-2-5-1-8-0" emits sum digit "8".
Truth row "TRUTH-2-5-1-8-0" emits carry output "CARRY-0".
Truth row "TRUTH-2-6-0-8-0" has left digit "2".
Truth row "TRUTH-2-6-0-8-0" has right digit "6".
Truth row "TRUTH-2-6-0-8-0" has carry input "CARRY-0".
Truth row "TRUTH-2-6-0-8-0" emits sum digit "8".
Truth row "TRUTH-2-6-0-8-0" emits carry output "CARRY-0".
Truth row "TRUTH-2-6-1-9-0" has left digit "2".
Truth row "TRUTH-2-6-1-9-0" has right digit "6".
Truth row "TRUTH-2-6-1-9-0" has carry input "CARRY-1".
Truth row "TRUTH-2-6-1-9-0" emits sum digit "9".
Truth row "TRUTH-2-6-1-9-0" emits carry output "CARRY-0".
Truth row "TRUTH-2-7-0-9-0" has left digit "2".
Truth row "TRUTH-2-7-0-9-0" has right digit "7".
Truth row "TRUTH-2-7-0-9-0" has carry input "CARRY-0".
Truth row "TRUTH-2-7-0-9-0" emits sum digit "9".
Truth row "TRUTH-2-7-0-9-0" emits carry output "CARRY-0".
Truth row "TRUTH-2-7-1-0-1" has left digit "2".
Truth row "TRUTH-2-7-1-0-1" has right digit "7".
Truth row "TRUTH-2-7-1-0-1" has carry input "CARRY-1".
Truth row "TRUTH-2-7-1-0-1" emits sum digit "0".
Truth row "TRUTH-2-7-1-0-1" emits carry output "CARRY-1".
Truth row "TRUTH-2-8-0-0-1" has left digit "2".
Truth row "TRUTH-2-8-0-0-1" has right digit "8".
Truth row "TRUTH-2-8-0-0-1" has carry input "CARRY-0".
Truth row "TRUTH-2-8-0-0-1" emits sum digit "0".
Truth row "TRUTH-2-8-0-0-1" emits carry output "CARRY-1".
Truth row "TRUTH-2-8-1-1-1" has left digit "2".
Truth row "TRUTH-2-8-1-1-1" has right digit "8".
Truth row "TRUTH-2-8-1-1-1" has carry input "CARRY-1".
Truth row "TRUTH-2-8-1-1-1" emits sum digit "1".
Truth row "TRUTH-2-8-1-1-1" emits carry output "CARRY-1".
Truth row "TRUTH-2-9-0-1-1" has left digit "2".
Truth row "TRUTH-2-9-0-1-1" has right digit "9".
Truth row "TRUTH-2-9-0-1-1" has carry input "CARRY-0".
Truth row "TRUTH-2-9-0-1-1" emits sum digit "1".
Truth row "TRUTH-2-9-0-1-1" emits carry output "CARRY-1".
Truth row "TRUTH-2-9-1-2-1" has left digit "2".
Truth row "TRUTH-2-9-1-2-1" has right digit "9".
Truth row "TRUTH-2-9-1-2-1" has carry input "CARRY-1".
Truth row "TRUTH-2-9-1-2-1" emits sum digit "2".
Truth row "TRUTH-2-9-1-2-1" emits carry output "CARRY-1".
Truth row "TRUTH-3-0-0-3-0" has left digit "3".
Truth row "TRUTH-3-0-0-3-0" has right digit "0".
Truth row "TRUTH-3-0-0-3-0" has carry input "CARRY-0".
Truth row "TRUTH-3-0-0-3-0" emits sum digit "3".
Truth row "TRUTH-3-0-0-3-0" emits carry output "CARRY-0".
Truth row "TRUTH-3-0-1-4-0" has left digit "3".
Truth row "TRUTH-3-0-1-4-0" has right digit "0".
Truth row "TRUTH-3-0-1-4-0" has carry input "CARRY-1".
Truth row "TRUTH-3-0-1-4-0" emits sum digit "4".
Truth row "TRUTH-3-0-1-4-0" emits carry output "CARRY-0".
Truth row "TRUTH-3-1-0-4-0" has left digit "3".
Truth row "TRUTH-3-1-0-4-0" has right digit "1".
Truth row "TRUTH-3-1-0-4-0" has carry input "CARRY-0".
Truth row "TRUTH-3-1-0-4-0" emits sum digit "4".
Truth row "TRUTH-3-1-0-4-0" emits carry output "CARRY-0".
Truth row "TRUTH-3-1-1-5-0" has left digit "3".
Truth row "TRUTH-3-1-1-5-0" has right digit "1".
Truth row "TRUTH-3-1-1-5-0" has carry input "CARRY-1".
Truth row "TRUTH-3-1-1-5-0" emits sum digit "5".
Truth row "TRUTH-3-1-1-5-0" emits carry output "CARRY-0".
Truth row "TRUTH-3-2-0-5-0" has left digit "3".
Truth row "TRUTH-3-2-0-5-0" has right digit "2".
Truth row "TRUTH-3-2-0-5-0" has carry input "CARRY-0".
Truth row "TRUTH-3-2-0-5-0" emits sum digit "5".
Truth row "TRUTH-3-2-0-5-0" emits carry output "CARRY-0".
Truth row "TRUTH-3-2-1-6-0" has left digit "3".
Truth row "TRUTH-3-2-1-6-0" has right digit "2".
Truth row "TRUTH-3-2-1-6-0" has carry input "CARRY-1".
Truth row "TRUTH-3-2-1-6-0" emits sum digit "6".
Truth row "TRUTH-3-2-1-6-0" emits carry output "CARRY-0".
Truth row "TRUTH-3-3-0-6-0" has left digit "3".
Truth row "TRUTH-3-3-0-6-0" has right digit "3".
Truth row "TRUTH-3-3-0-6-0" has carry input "CARRY-0".
Truth row "TRUTH-3-3-0-6-0" emits sum digit "6".
Truth row "TRUTH-3-3-0-6-0" emits carry output "CARRY-0".
Truth row "TRUTH-3-3-1-7-0" has left digit "3".
Truth row "TRUTH-3-3-1-7-0" has right digit "3".
Truth row "TRUTH-3-3-1-7-0" has carry input "CARRY-1".
Truth row "TRUTH-3-3-1-7-0" emits sum digit "7".
Truth row "TRUTH-3-3-1-7-0" emits carry output "CARRY-0".
Truth row "TRUTH-3-4-0-7-0" has left digit "3".
Truth row "TRUTH-3-4-0-7-0" has right digit "4".
Truth row "TRUTH-3-4-0-7-0" has carry input "CARRY-0".
Truth row "TRUTH-3-4-0-7-0" emits sum digit "7".
Truth row "TRUTH-3-4-0-7-0" emits carry output "CARRY-0".
Truth row "TRUTH-3-4-1-8-0" has left digit "3".
Truth row "TRUTH-3-4-1-8-0" has right digit "4".
Truth row "TRUTH-3-4-1-8-0" has carry input "CARRY-1".
Truth row "TRUTH-3-4-1-8-0" emits sum digit "8".
Truth row "TRUTH-3-4-1-8-0" emits carry output "CARRY-0".
Truth row "TRUTH-3-5-0-8-0" has left digit "3".
Truth row "TRUTH-3-5-0-8-0" has right digit "5".
Truth row "TRUTH-3-5-0-8-0" has carry input "CARRY-0".
Truth row "TRUTH-3-5-0-8-0" emits sum digit "8".
Truth row "TRUTH-3-5-0-8-0" emits carry output "CARRY-0".
Truth row "TRUTH-3-5-1-9-0" has left digit "3".
Truth row "TRUTH-3-5-1-9-0" has right digit "5".
Truth row "TRUTH-3-5-1-9-0" has carry input "CARRY-1".
Truth row "TRUTH-3-5-1-9-0" emits sum digit "9".
Truth row "TRUTH-3-5-1-9-0" emits carry output "CARRY-0".
Truth row "TRUTH-3-6-0-9-0" has left digit "3".
Truth row "TRUTH-3-6-0-9-0" has right digit "6".
Truth row "TRUTH-3-6-0-9-0" has carry input "CARRY-0".
Truth row "TRUTH-3-6-0-9-0" emits sum digit "9".
Truth row "TRUTH-3-6-0-9-0" emits carry output "CARRY-0".
Truth row "TRUTH-3-6-1-0-1" has left digit "3".
Truth row "TRUTH-3-6-1-0-1" has right digit "6".
Truth row "TRUTH-3-6-1-0-1" has carry input "CARRY-1".
Truth row "TRUTH-3-6-1-0-1" emits sum digit "0".
Truth row "TRUTH-3-6-1-0-1" emits carry output "CARRY-1".
Truth row "TRUTH-3-7-0-0-1" has left digit "3".
Truth row "TRUTH-3-7-0-0-1" has right digit "7".
Truth row "TRUTH-3-7-0-0-1" has carry input "CARRY-0".
Truth row "TRUTH-3-7-0-0-1" emits sum digit "0".
Truth row "TRUTH-3-7-0-0-1" emits carry output "CARRY-1".
Truth row "TRUTH-3-7-1-1-1" has left digit "3".
Truth row "TRUTH-3-7-1-1-1" has right digit "7".
Truth row "TRUTH-3-7-1-1-1" has carry input "CARRY-1".
Truth row "TRUTH-3-7-1-1-1" emits sum digit "1".
Truth row "TRUTH-3-7-1-1-1" emits carry output "CARRY-1".
Truth row "TRUTH-3-8-0-1-1" has left digit "3".
Truth row "TRUTH-3-8-0-1-1" has right digit "8".
Truth row "TRUTH-3-8-0-1-1" has carry input "CARRY-0".
Truth row "TRUTH-3-8-0-1-1" emits sum digit "1".
Truth row "TRUTH-3-8-0-1-1" emits carry output "CARRY-1".
Truth row "TRUTH-3-8-1-2-1" has left digit "3".
Truth row "TRUTH-3-8-1-2-1" has right digit "8".
Truth row "TRUTH-3-8-1-2-1" has carry input "CARRY-1".
Truth row "TRUTH-3-8-1-2-1" emits sum digit "2".
Truth row "TRUTH-3-8-1-2-1" emits carry output "CARRY-1".
Truth row "TRUTH-3-9-0-2-1" has left digit "3".
Truth row "TRUTH-3-9-0-2-1" has right digit "9".
Truth row "TRUTH-3-9-0-2-1" has carry input "CARRY-0".
Truth row "TRUTH-3-9-0-2-1" emits sum digit "2".
Truth row "TRUTH-3-9-0-2-1" emits carry output "CARRY-1".
Truth row "TRUTH-3-9-1-3-1" has left digit "3".
Truth row "TRUTH-3-9-1-3-1" has right digit "9".
Truth row "TRUTH-3-9-1-3-1" has carry input "CARRY-1".
Truth row "TRUTH-3-9-1-3-1" emits sum digit "3".
Truth row "TRUTH-3-9-1-3-1" emits carry output "CARRY-1".
Truth row "TRUTH-4-0-0-4-0" has left digit "4".
Truth row "TRUTH-4-0-0-4-0" has right digit "0".
Truth row "TRUTH-4-0-0-4-0" has carry input "CARRY-0".
Truth row "TRUTH-4-0-0-4-0" emits sum digit "4".
Truth row "TRUTH-4-0-0-4-0" emits carry output "CARRY-0".
Truth row "TRUTH-4-0-1-5-0" has left digit "4".
Truth row "TRUTH-4-0-1-5-0" has right digit "0".
Truth row "TRUTH-4-0-1-5-0" has carry input "CARRY-1".
Truth row "TRUTH-4-0-1-5-0" emits sum digit "5".
Truth row "TRUTH-4-0-1-5-0" emits carry output "CARRY-0".
Truth row "TRUTH-4-1-0-5-0" has left digit "4".
Truth row "TRUTH-4-1-0-5-0" has right digit "1".
Truth row "TRUTH-4-1-0-5-0" has carry input "CARRY-0".
Truth row "TRUTH-4-1-0-5-0" emits sum digit "5".
Truth row "TRUTH-4-1-0-5-0" emits carry output "CARRY-0".
Truth row "TRUTH-4-1-1-6-0" has left digit "4".
Truth row "TRUTH-4-1-1-6-0" has right digit "1".
Truth row "TRUTH-4-1-1-6-0" has carry input "CARRY-1".
Truth row "TRUTH-4-1-1-6-0" emits sum digit "6".
Truth row "TRUTH-4-1-1-6-0" emits carry output "CARRY-0".
Truth row "TRUTH-4-2-0-6-0" has left digit "4".
Truth row "TRUTH-4-2-0-6-0" has right digit "2".
Truth row "TRUTH-4-2-0-6-0" has carry input "CARRY-0".
Truth row "TRUTH-4-2-0-6-0" emits sum digit "6".
Truth row "TRUTH-4-2-0-6-0" emits carry output "CARRY-0".
Truth row "TRUTH-4-2-1-7-0" has left digit "4".
Truth row "TRUTH-4-2-1-7-0" has right digit "2".
Truth row "TRUTH-4-2-1-7-0" has carry input "CARRY-1".
Truth row "TRUTH-4-2-1-7-0" emits sum digit "7".
Truth row "TRUTH-4-2-1-7-0" emits carry output "CARRY-0".
Truth row "TRUTH-4-3-0-7-0" has left digit "4".
Truth row "TRUTH-4-3-0-7-0" has right digit "3".
Truth row "TRUTH-4-3-0-7-0" has carry input "CARRY-0".
Truth row "TRUTH-4-3-0-7-0" emits sum digit "7".
Truth row "TRUTH-4-3-0-7-0" emits carry output "CARRY-0".
Truth row "TRUTH-4-3-1-8-0" has left digit "4".
Truth row "TRUTH-4-3-1-8-0" has right digit "3".
Truth row "TRUTH-4-3-1-8-0" has carry input "CARRY-1".
Truth row "TRUTH-4-3-1-8-0" emits sum digit "8".
Truth row "TRUTH-4-3-1-8-0" emits carry output "CARRY-0".
Truth row "TRUTH-4-4-0-8-0" has left digit "4".
Truth row "TRUTH-4-4-0-8-0" has right digit "4".
Truth row "TRUTH-4-4-0-8-0" has carry input "CARRY-0".
Truth row "TRUTH-4-4-0-8-0" emits sum digit "8".
Truth row "TRUTH-4-4-0-8-0" emits carry output "CARRY-0".
Truth row "TRUTH-4-4-1-9-0" has left digit "4".
Truth row "TRUTH-4-4-1-9-0" has right digit "4".
Truth row "TRUTH-4-4-1-9-0" has carry input "CARRY-1".
Truth row "TRUTH-4-4-1-9-0" emits sum digit "9".
Truth row "TRUTH-4-4-1-9-0" emits carry output "CARRY-0".
Truth row "TRUTH-4-5-0-9-0" has left digit "4".
Truth row "TRUTH-4-5-0-9-0" has right digit "5".
Truth row "TRUTH-4-5-0-9-0" has carry input "CARRY-0".
Truth row "TRUTH-4-5-0-9-0" emits sum digit "9".
Truth row "TRUTH-4-5-0-9-0" emits carry output "CARRY-0".
Truth row "TRUTH-4-5-1-0-1" has left digit "4".
Truth row "TRUTH-4-5-1-0-1" has right digit "5".
Truth row "TRUTH-4-5-1-0-1" has carry input "CARRY-1".
Truth row "TRUTH-4-5-1-0-1" emits sum digit "0".
Truth row "TRUTH-4-5-1-0-1" emits carry output "CARRY-1".
Truth row "TRUTH-4-6-0-0-1" has left digit "4".
Truth row "TRUTH-4-6-0-0-1" has right digit "6".
Truth row "TRUTH-4-6-0-0-1" has carry input "CARRY-0".
Truth row "TRUTH-4-6-0-0-1" emits sum digit "0".
Truth row "TRUTH-4-6-0-0-1" emits carry output "CARRY-1".
Truth row "TRUTH-4-6-1-1-1" has left digit "4".
Truth row "TRUTH-4-6-1-1-1" has right digit "6".
Truth row "TRUTH-4-6-1-1-1" has carry input "CARRY-1".
Truth row "TRUTH-4-6-1-1-1" emits sum digit "1".
Truth row "TRUTH-4-6-1-1-1" emits carry output "CARRY-1".
Truth row "TRUTH-4-7-0-1-1" has left digit "4".
Truth row "TRUTH-4-7-0-1-1" has right digit "7".
Truth row "TRUTH-4-7-0-1-1" has carry input "CARRY-0".
Truth row "TRUTH-4-7-0-1-1" emits sum digit "1".
Truth row "TRUTH-4-7-0-1-1" emits carry output "CARRY-1".
Truth row "TRUTH-4-7-1-2-1" has left digit "4".
Truth row "TRUTH-4-7-1-2-1" has right digit "7".
Truth row "TRUTH-4-7-1-2-1" has carry input "CARRY-1".
Truth row "TRUTH-4-7-1-2-1" emits sum digit "2".
Truth row "TRUTH-4-7-1-2-1" emits carry output "CARRY-1".
Truth row "TRUTH-4-8-0-2-1" has left digit "4".
Truth row "TRUTH-4-8-0-2-1" has right digit "8".
Truth row "TRUTH-4-8-0-2-1" has carry input "CARRY-0".
Truth row "TRUTH-4-8-0-2-1" emits sum digit "2".
Truth row "TRUTH-4-8-0-2-1" emits carry output "CARRY-1".
Truth row "TRUTH-4-8-1-3-1" has left digit "4".
Truth row "TRUTH-4-8-1-3-1" has right digit "8".
Truth row "TRUTH-4-8-1-3-1" has carry input "CARRY-1".
Truth row "TRUTH-4-8-1-3-1" emits sum digit "3".
Truth row "TRUTH-4-8-1-3-1" emits carry output "CARRY-1".
Truth row "TRUTH-4-9-0-3-1" has left digit "4".
Truth row "TRUTH-4-9-0-3-1" has right digit "9".
Truth row "TRUTH-4-9-0-3-1" has carry input "CARRY-0".
Truth row "TRUTH-4-9-0-3-1" emits sum digit "3".
Truth row "TRUTH-4-9-0-3-1" emits carry output "CARRY-1".
Truth row "TRUTH-4-9-1-4-1" has left digit "4".
Truth row "TRUTH-4-9-1-4-1" has right digit "9".
Truth row "TRUTH-4-9-1-4-1" has carry input "CARRY-1".
Truth row "TRUTH-4-9-1-4-1" emits sum digit "4".
Truth row "TRUTH-4-9-1-4-1" emits carry output "CARRY-1".
Truth row "TRUTH-5-0-0-5-0" has left digit "5".
Truth row "TRUTH-5-0-0-5-0" has right digit "0".
Truth row "TRUTH-5-0-0-5-0" has carry input "CARRY-0".
Truth row "TRUTH-5-0-0-5-0" emits sum digit "5".
Truth row "TRUTH-5-0-0-5-0" emits carry output "CARRY-0".
Truth row "TRUTH-5-0-1-6-0" has left digit "5".
Truth row "TRUTH-5-0-1-6-0" has right digit "0".
Truth row "TRUTH-5-0-1-6-0" has carry input "CARRY-1".
Truth row "TRUTH-5-0-1-6-0" emits sum digit "6".
Truth row "TRUTH-5-0-1-6-0" emits carry output "CARRY-0".
Truth row "TRUTH-5-1-0-6-0" has left digit "5".
Truth row "TRUTH-5-1-0-6-0" has right digit "1".
Truth row "TRUTH-5-1-0-6-0" has carry input "CARRY-0".
Truth row "TRUTH-5-1-0-6-0" emits sum digit "6".
Truth row "TRUTH-5-1-0-6-0" emits carry output "CARRY-0".
Truth row "TRUTH-5-1-1-7-0" has left digit "5".
Truth row "TRUTH-5-1-1-7-0" has right digit "1".
Truth row "TRUTH-5-1-1-7-0" has carry input "CARRY-1".
Truth row "TRUTH-5-1-1-7-0" emits sum digit "7".
Truth row "TRUTH-5-1-1-7-0" emits carry output "CARRY-0".
Truth row "TRUTH-5-2-0-7-0" has left digit "5".
Truth row "TRUTH-5-2-0-7-0" has right digit "2".
Truth row "TRUTH-5-2-0-7-0" has carry input "CARRY-0".
Truth row "TRUTH-5-2-0-7-0" emits sum digit "7".
Truth row "TRUTH-5-2-0-7-0" emits carry output "CARRY-0".
Truth row "TRUTH-5-2-1-8-0" has left digit "5".
Truth row "TRUTH-5-2-1-8-0" has right digit "2".
Truth row "TRUTH-5-2-1-8-0" has carry input "CARRY-1".
Truth row "TRUTH-5-2-1-8-0" emits sum digit "8".
Truth row "TRUTH-5-2-1-8-0" emits carry output "CARRY-0".
Truth row "TRUTH-5-3-0-8-0" has left digit "5".
Truth row "TRUTH-5-3-0-8-0" has right digit "3".
Truth row "TRUTH-5-3-0-8-0" has carry input "CARRY-0".
Truth row "TRUTH-5-3-0-8-0" emits sum digit "8".
Truth row "TRUTH-5-3-0-8-0" emits carry output "CARRY-0".
Truth row "TRUTH-5-3-1-9-0" has left digit "5".
Truth row "TRUTH-5-3-1-9-0" has right digit "3".
Truth row "TRUTH-5-3-1-9-0" has carry input "CARRY-1".
Truth row "TRUTH-5-3-1-9-0" emits sum digit "9".
Truth row "TRUTH-5-3-1-9-0" emits carry output "CARRY-0".
Truth row "TRUTH-5-4-0-9-0" has left digit "5".
Truth row "TRUTH-5-4-0-9-0" has right digit "4".
Truth row "TRUTH-5-4-0-9-0" has carry input "CARRY-0".
Truth row "TRUTH-5-4-0-9-0" emits sum digit "9".
Truth row "TRUTH-5-4-0-9-0" emits carry output "CARRY-0".
Truth row "TRUTH-5-4-1-0-1" has left digit "5".
Truth row "TRUTH-5-4-1-0-1" has right digit "4".
Truth row "TRUTH-5-4-1-0-1" has carry input "CARRY-1".
Truth row "TRUTH-5-4-1-0-1" emits sum digit "0".
Truth row "TRUTH-5-4-1-0-1" emits carry output "CARRY-1".
Truth row "TRUTH-5-5-0-0-1" has left digit "5".
Truth row "TRUTH-5-5-0-0-1" has right digit "5".
Truth row "TRUTH-5-5-0-0-1" has carry input "CARRY-0".
Truth row "TRUTH-5-5-0-0-1" emits sum digit "0".
Truth row "TRUTH-5-5-0-0-1" emits carry output "CARRY-1".
Truth row "TRUTH-5-5-1-1-1" has left digit "5".
Truth row "TRUTH-5-5-1-1-1" has right digit "5".
Truth row "TRUTH-5-5-1-1-1" has carry input "CARRY-1".
Truth row "TRUTH-5-5-1-1-1" emits sum digit "1".
Truth row "TRUTH-5-5-1-1-1" emits carry output "CARRY-1".
Truth row "TRUTH-5-6-0-1-1" has left digit "5".
Truth row "TRUTH-5-6-0-1-1" has right digit "6".
Truth row "TRUTH-5-6-0-1-1" has carry input "CARRY-0".
Truth row "TRUTH-5-6-0-1-1" emits sum digit "1".
Truth row "TRUTH-5-6-0-1-1" emits carry output "CARRY-1".
Truth row "TRUTH-5-6-1-2-1" has left digit "5".
Truth row "TRUTH-5-6-1-2-1" has right digit "6".
Truth row "TRUTH-5-6-1-2-1" has carry input "CARRY-1".
Truth row "TRUTH-5-6-1-2-1" emits sum digit "2".
Truth row "TRUTH-5-6-1-2-1" emits carry output "CARRY-1".
Truth row "TRUTH-5-7-0-2-1" has left digit "5".
Truth row "TRUTH-5-7-0-2-1" has right digit "7".
Truth row "TRUTH-5-7-0-2-1" has carry input "CARRY-0".
Truth row "TRUTH-5-7-0-2-1" emits sum digit "2".
Truth row "TRUTH-5-7-0-2-1" emits carry output "CARRY-1".
Truth row "TRUTH-5-7-1-3-1" has left digit "5".
Truth row "TRUTH-5-7-1-3-1" has right digit "7".
Truth row "TRUTH-5-7-1-3-1" has carry input "CARRY-1".
Truth row "TRUTH-5-7-1-3-1" emits sum digit "3".
Truth row "TRUTH-5-7-1-3-1" emits carry output "CARRY-1".
Truth row "TRUTH-5-8-0-3-1" has left digit "5".
Truth row "TRUTH-5-8-0-3-1" has right digit "8".
Truth row "TRUTH-5-8-0-3-1" has carry input "CARRY-0".
Truth row "TRUTH-5-8-0-3-1" emits sum digit "3".
Truth row "TRUTH-5-8-0-3-1" emits carry output "CARRY-1".
Truth row "TRUTH-5-8-1-4-1" has left digit "5".
Truth row "TRUTH-5-8-1-4-1" has right digit "8".
Truth row "TRUTH-5-8-1-4-1" has carry input "CARRY-1".
Truth row "TRUTH-5-8-1-4-1" emits sum digit "4".
Truth row "TRUTH-5-8-1-4-1" emits carry output "CARRY-1".
Truth row "TRUTH-5-9-0-4-1" has left digit "5".
Truth row "TRUTH-5-9-0-4-1" has right digit "9".
Truth row "TRUTH-5-9-0-4-1" has carry input "CARRY-0".
Truth row "TRUTH-5-9-0-4-1" emits sum digit "4".
Truth row "TRUTH-5-9-0-4-1" emits carry output "CARRY-1".
Truth row "TRUTH-5-9-1-5-1" has left digit "5".
Truth row "TRUTH-5-9-1-5-1" has right digit "9".
Truth row "TRUTH-5-9-1-5-1" has carry input "CARRY-1".
Truth row "TRUTH-5-9-1-5-1" emits sum digit "5".
Truth row "TRUTH-5-9-1-5-1" emits carry output "CARRY-1".
Truth row "TRUTH-6-0-0-6-0" has left digit "6".
Truth row "TRUTH-6-0-0-6-0" has right digit "0".
Truth row "TRUTH-6-0-0-6-0" has carry input "CARRY-0".
Truth row "TRUTH-6-0-0-6-0" emits sum digit "6".
Truth row "TRUTH-6-0-0-6-0" emits carry output "CARRY-0".
Truth row "TRUTH-6-0-1-7-0" has left digit "6".
Truth row "TRUTH-6-0-1-7-0" has right digit "0".
Truth row "TRUTH-6-0-1-7-0" has carry input "CARRY-1".
Truth row "TRUTH-6-0-1-7-0" emits sum digit "7".
Truth row "TRUTH-6-0-1-7-0" emits carry output "CARRY-0".
Truth row "TRUTH-6-1-0-7-0" has left digit "6".
Truth row "TRUTH-6-1-0-7-0" has right digit "1".
Truth row "TRUTH-6-1-0-7-0" has carry input "CARRY-0".
Truth row "TRUTH-6-1-0-7-0" emits sum digit "7".
Truth row "TRUTH-6-1-0-7-0" emits carry output "CARRY-0".
Truth row "TRUTH-6-1-1-8-0" has left digit "6".
Truth row "TRUTH-6-1-1-8-0" has right digit "1".
Truth row "TRUTH-6-1-1-8-0" has carry input "CARRY-1".
Truth row "TRUTH-6-1-1-8-0" emits sum digit "8".
Truth row "TRUTH-6-1-1-8-0" emits carry output "CARRY-0".
Truth row "TRUTH-6-2-0-8-0" has left digit "6".
Truth row "TRUTH-6-2-0-8-0" has right digit "2".
Truth row "TRUTH-6-2-0-8-0" has carry input "CARRY-0".
Truth row "TRUTH-6-2-0-8-0" emits sum digit "8".
Truth row "TRUTH-6-2-0-8-0" emits carry output "CARRY-0".
Truth row "TRUTH-6-2-1-9-0" has left digit "6".
Truth row "TRUTH-6-2-1-9-0" has right digit "2".
Truth row "TRUTH-6-2-1-9-0" has carry input "CARRY-1".
Truth row "TRUTH-6-2-1-9-0" emits sum digit "9".
Truth row "TRUTH-6-2-1-9-0" emits carry output "CARRY-0".
Truth row "TRUTH-6-3-0-9-0" has left digit "6".
Truth row "TRUTH-6-3-0-9-0" has right digit "3".
Truth row "TRUTH-6-3-0-9-0" has carry input "CARRY-0".
Truth row "TRUTH-6-3-0-9-0" emits sum digit "9".
Truth row "TRUTH-6-3-0-9-0" emits carry output "CARRY-0".
Truth row "TRUTH-6-3-1-0-1" has left digit "6".
Truth row "TRUTH-6-3-1-0-1" has right digit "3".
Truth row "TRUTH-6-3-1-0-1" has carry input "CARRY-1".
Truth row "TRUTH-6-3-1-0-1" emits sum digit "0".
Truth row "TRUTH-6-3-1-0-1" emits carry output "CARRY-1".
Truth row "TRUTH-6-4-0-0-1" has left digit "6".
Truth row "TRUTH-6-4-0-0-1" has right digit "4".
Truth row "TRUTH-6-4-0-0-1" has carry input "CARRY-0".
Truth row "TRUTH-6-4-0-0-1" emits sum digit "0".
Truth row "TRUTH-6-4-0-0-1" emits carry output "CARRY-1".
Truth row "TRUTH-6-4-1-1-1" has left digit "6".
Truth row "TRUTH-6-4-1-1-1" has right digit "4".
Truth row "TRUTH-6-4-1-1-1" has carry input "CARRY-1".
Truth row "TRUTH-6-4-1-1-1" emits sum digit "1".
Truth row "TRUTH-6-4-1-1-1" emits carry output "CARRY-1".
Truth row "TRUTH-6-5-0-1-1" has left digit "6".
Truth row "TRUTH-6-5-0-1-1" has right digit "5".
Truth row "TRUTH-6-5-0-1-1" has carry input "CARRY-0".
Truth row "TRUTH-6-5-0-1-1" emits sum digit "1".
Truth row "TRUTH-6-5-0-1-1" emits carry output "CARRY-1".
Truth row "TRUTH-6-5-1-2-1" has left digit "6".
Truth row "TRUTH-6-5-1-2-1" has right digit "5".
Truth row "TRUTH-6-5-1-2-1" has carry input "CARRY-1".
Truth row "TRUTH-6-5-1-2-1" emits sum digit "2".
Truth row "TRUTH-6-5-1-2-1" emits carry output "CARRY-1".
Truth row "TRUTH-6-6-0-2-1" has left digit "6".
Truth row "TRUTH-6-6-0-2-1" has right digit "6".
Truth row "TRUTH-6-6-0-2-1" has carry input "CARRY-0".
Truth row "TRUTH-6-6-0-2-1" emits sum digit "2".
Truth row "TRUTH-6-6-0-2-1" emits carry output "CARRY-1".
Truth row "TRUTH-6-6-1-3-1" has left digit "6".
Truth row "TRUTH-6-6-1-3-1" has right digit "6".
Truth row "TRUTH-6-6-1-3-1" has carry input "CARRY-1".
Truth row "TRUTH-6-6-1-3-1" emits sum digit "3".
Truth row "TRUTH-6-6-1-3-1" emits carry output "CARRY-1".
Truth row "TRUTH-6-7-0-3-1" has left digit "6".
Truth row "TRUTH-6-7-0-3-1" has right digit "7".
Truth row "TRUTH-6-7-0-3-1" has carry input "CARRY-0".
Truth row "TRUTH-6-7-0-3-1" emits sum digit "3".
Truth row "TRUTH-6-7-0-3-1" emits carry output "CARRY-1".
Truth row "TRUTH-6-7-1-4-1" has left digit "6".
Truth row "TRUTH-6-7-1-4-1" has right digit "7".
Truth row "TRUTH-6-7-1-4-1" has carry input "CARRY-1".
Truth row "TRUTH-6-7-1-4-1" emits sum digit "4".
Truth row "TRUTH-6-7-1-4-1" emits carry output "CARRY-1".
Truth row "TRUTH-6-8-0-4-1" has left digit "6".
Truth row "TRUTH-6-8-0-4-1" has right digit "8".
Truth row "TRUTH-6-8-0-4-1" has carry input "CARRY-0".
Truth row "TRUTH-6-8-0-4-1" emits sum digit "4".
Truth row "TRUTH-6-8-0-4-1" emits carry output "CARRY-1".
Truth row "TRUTH-6-8-1-5-1" has left digit "6".
Truth row "TRUTH-6-8-1-5-1" has right digit "8".
Truth row "TRUTH-6-8-1-5-1" has carry input "CARRY-1".
Truth row "TRUTH-6-8-1-5-1" emits sum digit "5".
Truth row "TRUTH-6-8-1-5-1" emits carry output "CARRY-1".
Truth row "TRUTH-6-9-0-5-1" has left digit "6".
Truth row "TRUTH-6-9-0-5-1" has right digit "9".
Truth row "TRUTH-6-9-0-5-1" has carry input "CARRY-0".
Truth row "TRUTH-6-9-0-5-1" emits sum digit "5".
Truth row "TRUTH-6-9-0-5-1" emits carry output "CARRY-1".
Truth row "TRUTH-6-9-1-6-1" has left digit "6".
Truth row "TRUTH-6-9-1-6-1" has right digit "9".
Truth row "TRUTH-6-9-1-6-1" has carry input "CARRY-1".
Truth row "TRUTH-6-9-1-6-1" emits sum digit "6".
Truth row "TRUTH-6-9-1-6-1" emits carry output "CARRY-1".
Truth row "TRUTH-7-0-0-7-0" has left digit "7".
Truth row "TRUTH-7-0-0-7-0" has right digit "0".
Truth row "TRUTH-7-0-0-7-0" has carry input "CARRY-0".
Truth row "TRUTH-7-0-0-7-0" emits sum digit "7".
Truth row "TRUTH-7-0-0-7-0" emits carry output "CARRY-0".
Truth row "TRUTH-7-0-1-8-0" has left digit "7".
Truth row "TRUTH-7-0-1-8-0" has right digit "0".
Truth row "TRUTH-7-0-1-8-0" has carry input "CARRY-1".
Truth row "TRUTH-7-0-1-8-0" emits sum digit "8".
Truth row "TRUTH-7-0-1-8-0" emits carry output "CARRY-0".
Truth row "TRUTH-7-1-0-8-0" has left digit "7".
Truth row "TRUTH-7-1-0-8-0" has right digit "1".
Truth row "TRUTH-7-1-0-8-0" has carry input "CARRY-0".
Truth row "TRUTH-7-1-0-8-0" emits sum digit "8".
Truth row "TRUTH-7-1-0-8-0" emits carry output "CARRY-0".
Truth row "TRUTH-7-1-1-9-0" has left digit "7".
Truth row "TRUTH-7-1-1-9-0" has right digit "1".
Truth row "TRUTH-7-1-1-9-0" has carry input "CARRY-1".
Truth row "TRUTH-7-1-1-9-0" emits sum digit "9".
Truth row "TRUTH-7-1-1-9-0" emits carry output "CARRY-0".
Truth row "TRUTH-7-2-0-9-0" has left digit "7".
Truth row "TRUTH-7-2-0-9-0" has right digit "2".
Truth row "TRUTH-7-2-0-9-0" has carry input "CARRY-0".
Truth row "TRUTH-7-2-0-9-0" emits sum digit "9".
Truth row "TRUTH-7-2-0-9-0" emits carry output "CARRY-0".
Truth row "TRUTH-7-2-1-0-1" has left digit "7".
Truth row "TRUTH-7-2-1-0-1" has right digit "2".
Truth row "TRUTH-7-2-1-0-1" has carry input "CARRY-1".
Truth row "TRUTH-7-2-1-0-1" emits sum digit "0".
Truth row "TRUTH-7-2-1-0-1" emits carry output "CARRY-1".
Truth row "TRUTH-7-3-0-0-1" has left digit "7".
Truth row "TRUTH-7-3-0-0-1" has right digit "3".
Truth row "TRUTH-7-3-0-0-1" has carry input "CARRY-0".
Truth row "TRUTH-7-3-0-0-1" emits sum digit "0".
Truth row "TRUTH-7-3-0-0-1" emits carry output "CARRY-1".
Truth row "TRUTH-7-3-1-1-1" has left digit "7".
Truth row "TRUTH-7-3-1-1-1" has right digit "3".
Truth row "TRUTH-7-3-1-1-1" has carry input "CARRY-1".
Truth row "TRUTH-7-3-1-1-1" emits sum digit "1".
Truth row "TRUTH-7-3-1-1-1" emits carry output "CARRY-1".
Truth row "TRUTH-7-4-0-1-1" has left digit "7".
Truth row "TRUTH-7-4-0-1-1" has right digit "4".
Truth row "TRUTH-7-4-0-1-1" has carry input "CARRY-0".
Truth row "TRUTH-7-4-0-1-1" emits sum digit "1".
Truth row "TRUTH-7-4-0-1-1" emits carry output "CARRY-1".
Truth row "TRUTH-7-4-1-2-1" has left digit "7".
Truth row "TRUTH-7-4-1-2-1" has right digit "4".
Truth row "TRUTH-7-4-1-2-1" has carry input "CARRY-1".
Truth row "TRUTH-7-4-1-2-1" emits sum digit "2".
Truth row "TRUTH-7-4-1-2-1" emits carry output "CARRY-1".
Truth row "TRUTH-7-5-0-2-1" has left digit "7".
Truth row "TRUTH-7-5-0-2-1" has right digit "5".
Truth row "TRUTH-7-5-0-2-1" has carry input "CARRY-0".
Truth row "TRUTH-7-5-0-2-1" emits sum digit "2".
Truth row "TRUTH-7-5-0-2-1" emits carry output "CARRY-1".
Truth row "TRUTH-7-5-1-3-1" has left digit "7".
Truth row "TRUTH-7-5-1-3-1" has right digit "5".
Truth row "TRUTH-7-5-1-3-1" has carry input "CARRY-1".
Truth row "TRUTH-7-5-1-3-1" emits sum digit "3".
Truth row "TRUTH-7-5-1-3-1" emits carry output "CARRY-1".
Truth row "TRUTH-7-6-0-3-1" has left digit "7".
Truth row "TRUTH-7-6-0-3-1" has right digit "6".
Truth row "TRUTH-7-6-0-3-1" has carry input "CARRY-0".
Truth row "TRUTH-7-6-0-3-1" emits sum digit "3".
Truth row "TRUTH-7-6-0-3-1" emits carry output "CARRY-1".
Truth row "TRUTH-7-6-1-4-1" has left digit "7".
Truth row "TRUTH-7-6-1-4-1" has right digit "6".
Truth row "TRUTH-7-6-1-4-1" has carry input "CARRY-1".
Truth row "TRUTH-7-6-1-4-1" emits sum digit "4".
Truth row "TRUTH-7-6-1-4-1" emits carry output "CARRY-1".
Truth row "TRUTH-7-7-0-4-1" has left digit "7".
Truth row "TRUTH-7-7-0-4-1" has right digit "7".
Truth row "TRUTH-7-7-0-4-1" has carry input "CARRY-0".
Truth row "TRUTH-7-7-0-4-1" emits sum digit "4".
Truth row "TRUTH-7-7-0-4-1" emits carry output "CARRY-1".
Truth row "TRUTH-7-7-1-5-1" has left digit "7".
Truth row "TRUTH-7-7-1-5-1" has right digit "7".
Truth row "TRUTH-7-7-1-5-1" has carry input "CARRY-1".
Truth row "TRUTH-7-7-1-5-1" emits sum digit "5".
Truth row "TRUTH-7-7-1-5-1" emits carry output "CARRY-1".
Truth row "TRUTH-7-8-0-5-1" has left digit "7".
Truth row "TRUTH-7-8-0-5-1" has right digit "8".
Truth row "TRUTH-7-8-0-5-1" has carry input "CARRY-0".
Truth row "TRUTH-7-8-0-5-1" emits sum digit "5".
Truth row "TRUTH-7-8-0-5-1" emits carry output "CARRY-1".
Truth row "TRUTH-7-8-1-6-1" has left digit "7".
Truth row "TRUTH-7-8-1-6-1" has right digit "8".
Truth row "TRUTH-7-8-1-6-1" has carry input "CARRY-1".
Truth row "TRUTH-7-8-1-6-1" emits sum digit "6".
Truth row "TRUTH-7-8-1-6-1" emits carry output "CARRY-1".
Truth row "TRUTH-7-9-0-6-1" has left digit "7".
Truth row "TRUTH-7-9-0-6-1" has right digit "9".
Truth row "TRUTH-7-9-0-6-1" has carry input "CARRY-0".
Truth row "TRUTH-7-9-0-6-1" emits sum digit "6".
Truth row "TRUTH-7-9-0-6-1" emits carry output "CARRY-1".
Truth row "TRUTH-7-9-1-7-1" has left digit "7".
Truth row "TRUTH-7-9-1-7-1" has right digit "9".
Truth row "TRUTH-7-9-1-7-1" has carry input "CARRY-1".
Truth row "TRUTH-7-9-1-7-1" emits sum digit "7".
Truth row "TRUTH-7-9-1-7-1" emits carry output "CARRY-1".
Truth row "TRUTH-8-0-0-8-0" has left digit "8".
Truth row "TRUTH-8-0-0-8-0" has right digit "0".
Truth row "TRUTH-8-0-0-8-0" has carry input "CARRY-0".
Truth row "TRUTH-8-0-0-8-0" emits sum digit "8".
Truth row "TRUTH-8-0-0-8-0" emits carry output "CARRY-0".
Truth row "TRUTH-8-0-1-9-0" has left digit "8".
Truth row "TRUTH-8-0-1-9-0" has right digit "0".
Truth row "TRUTH-8-0-1-9-0" has carry input "CARRY-1".
Truth row "TRUTH-8-0-1-9-0" emits sum digit "9".
Truth row "TRUTH-8-0-1-9-0" emits carry output "CARRY-0".
Truth row "TRUTH-8-1-0-9-0" has left digit "8".
Truth row "TRUTH-8-1-0-9-0" has right digit "1".
Truth row "TRUTH-8-1-0-9-0" has carry input "CARRY-0".
Truth row "TRUTH-8-1-0-9-0" emits sum digit "9".
Truth row "TRUTH-8-1-0-9-0" emits carry output "CARRY-0".
Truth row "TRUTH-8-1-1-0-1" has left digit "8".
Truth row "TRUTH-8-1-1-0-1" has right digit "1".
Truth row "TRUTH-8-1-1-0-1" has carry input "CARRY-1".
Truth row "TRUTH-8-1-1-0-1" emits sum digit "0".
Truth row "TRUTH-8-1-1-0-1" emits carry output "CARRY-1".
Truth row "TRUTH-8-2-0-0-1" has left digit "8".
Truth row "TRUTH-8-2-0-0-1" has right digit "2".
Truth row "TRUTH-8-2-0-0-1" has carry input "CARRY-0".
Truth row "TRUTH-8-2-0-0-1" emits sum digit "0".
Truth row "TRUTH-8-2-0-0-1" emits carry output "CARRY-1".
Truth row "TRUTH-8-2-1-1-1" has left digit "8".
Truth row "TRUTH-8-2-1-1-1" has right digit "2".
Truth row "TRUTH-8-2-1-1-1" has carry input "CARRY-1".
Truth row "TRUTH-8-2-1-1-1" emits sum digit "1".
Truth row "TRUTH-8-2-1-1-1" emits carry output "CARRY-1".
Truth row "TRUTH-8-3-0-1-1" has left digit "8".
Truth row "TRUTH-8-3-0-1-1" has right digit "3".
Truth row "TRUTH-8-3-0-1-1" has carry input "CARRY-0".
Truth row "TRUTH-8-3-0-1-1" emits sum digit "1".
Truth row "TRUTH-8-3-0-1-1" emits carry output "CARRY-1".
Truth row "TRUTH-8-3-1-2-1" has left digit "8".
Truth row "TRUTH-8-3-1-2-1" has right digit "3".
Truth row "TRUTH-8-3-1-2-1" has carry input "CARRY-1".
Truth row "TRUTH-8-3-1-2-1" emits sum digit "2".
Truth row "TRUTH-8-3-1-2-1" emits carry output "CARRY-1".
Truth row "TRUTH-8-4-0-2-1" has left digit "8".
Truth row "TRUTH-8-4-0-2-1" has right digit "4".
Truth row "TRUTH-8-4-0-2-1" has carry input "CARRY-0".
Truth row "TRUTH-8-4-0-2-1" emits sum digit "2".
Truth row "TRUTH-8-4-0-2-1" emits carry output "CARRY-1".
Truth row "TRUTH-8-4-1-3-1" has left digit "8".
Truth row "TRUTH-8-4-1-3-1" has right digit "4".
Truth row "TRUTH-8-4-1-3-1" has carry input "CARRY-1".
Truth row "TRUTH-8-4-1-3-1" emits sum digit "3".
Truth row "TRUTH-8-4-1-3-1" emits carry output "CARRY-1".
Truth row "TRUTH-8-5-0-3-1" has left digit "8".
Truth row "TRUTH-8-5-0-3-1" has right digit "5".
Truth row "TRUTH-8-5-0-3-1" has carry input "CARRY-0".
Truth row "TRUTH-8-5-0-3-1" emits sum digit "3".
Truth row "TRUTH-8-5-0-3-1" emits carry output "CARRY-1".
Truth row "TRUTH-8-5-1-4-1" has left digit "8".
Truth row "TRUTH-8-5-1-4-1" has right digit "5".
Truth row "TRUTH-8-5-1-4-1" has carry input "CARRY-1".
Truth row "TRUTH-8-5-1-4-1" emits sum digit "4".
Truth row "TRUTH-8-5-1-4-1" emits carry output "CARRY-1".
Truth row "TRUTH-8-6-0-4-1" has left digit "8".
Truth row "TRUTH-8-6-0-4-1" has right digit "6".
Truth row "TRUTH-8-6-0-4-1" has carry input "CARRY-0".
Truth row "TRUTH-8-6-0-4-1" emits sum digit "4".
Truth row "TRUTH-8-6-0-4-1" emits carry output "CARRY-1".
Truth row "TRUTH-8-6-1-5-1" has left digit "8".
Truth row "TRUTH-8-6-1-5-1" has right digit "6".
Truth row "TRUTH-8-6-1-5-1" has carry input "CARRY-1".
Truth row "TRUTH-8-6-1-5-1" emits sum digit "5".
Truth row "TRUTH-8-6-1-5-1" emits carry output "CARRY-1".
Truth row "TRUTH-8-7-0-5-1" has left digit "8".
Truth row "TRUTH-8-7-0-5-1" has right digit "7".
Truth row "TRUTH-8-7-0-5-1" has carry input "CARRY-0".
Truth row "TRUTH-8-7-0-5-1" emits sum digit "5".
Truth row "TRUTH-8-7-0-5-1" emits carry output "CARRY-1".
Truth row "TRUTH-8-7-1-6-1" has left digit "8".
Truth row "TRUTH-8-7-1-6-1" has right digit "7".
Truth row "TRUTH-8-7-1-6-1" has carry input "CARRY-1".
Truth row "TRUTH-8-7-1-6-1" emits sum digit "6".
Truth row "TRUTH-8-7-1-6-1" emits carry output "CARRY-1".
Truth row "TRUTH-8-8-0-6-1" has left digit "8".
Truth row "TRUTH-8-8-0-6-1" has right digit "8".
Truth row "TRUTH-8-8-0-6-1" has carry input "CARRY-0".
Truth row "TRUTH-8-8-0-6-1" emits sum digit "6".
Truth row "TRUTH-8-8-0-6-1" emits carry output "CARRY-1".
Truth row "TRUTH-8-8-1-7-1" has left digit "8".
Truth row "TRUTH-8-8-1-7-1" has right digit "8".
Truth row "TRUTH-8-8-1-7-1" has carry input "CARRY-1".
Truth row "TRUTH-8-8-1-7-1" emits sum digit "7".
Truth row "TRUTH-8-8-1-7-1" emits carry output "CARRY-1".
Truth row "TRUTH-8-9-0-7-1" has left digit "8".
Truth row "TRUTH-8-9-0-7-1" has right digit "9".
Truth row "TRUTH-8-9-0-7-1" has carry input "CARRY-0".
Truth row "TRUTH-8-9-0-7-1" emits sum digit "7".
Truth row "TRUTH-8-9-0-7-1" emits carry output "CARRY-1".
Truth row "TRUTH-8-9-1-8-1" has left digit "8".
Truth row "TRUTH-8-9-1-8-1" has right digit "9".
Truth row "TRUTH-8-9-1-8-1" has carry input "CARRY-1".
Truth row "TRUTH-8-9-1-8-1" emits sum digit "8".
Truth row "TRUTH-8-9-1-8-1" emits carry output "CARRY-1".
Truth row "TRUTH-9-0-0-9-0" has left digit "9".
Truth row "TRUTH-9-0-0-9-0" has right digit "0".
Truth row "TRUTH-9-0-0-9-0" has carry input "CARRY-0".
Truth row "TRUTH-9-0-0-9-0" emits sum digit "9".
Truth row "TRUTH-9-0-0-9-0" emits carry output "CARRY-0".
Truth row "TRUTH-9-0-1-0-1" has left digit "9".
Truth row "TRUTH-9-0-1-0-1" has right digit "0".
Truth row "TRUTH-9-0-1-0-1" has carry input "CARRY-1".
Truth row "TRUTH-9-0-1-0-1" emits sum digit "0".
Truth row "TRUTH-9-0-1-0-1" emits carry output "CARRY-1".
Truth row "TRUTH-9-1-0-0-1" has left digit "9".
Truth row "TRUTH-9-1-0-0-1" has right digit "1".
Truth row "TRUTH-9-1-0-0-1" has carry input "CARRY-0".
Truth row "TRUTH-9-1-0-0-1" emits sum digit "0".
Truth row "TRUTH-9-1-0-0-1" emits carry output "CARRY-1".
Truth row "TRUTH-9-1-1-1-1" has left digit "9".
Truth row "TRUTH-9-1-1-1-1" has right digit "1".
Truth row "TRUTH-9-1-1-1-1" has carry input "CARRY-1".
Truth row "TRUTH-9-1-1-1-1" emits sum digit "1".
Truth row "TRUTH-9-1-1-1-1" emits carry output "CARRY-1".
Truth row "TRUTH-9-2-0-1-1" has left digit "9".
Truth row "TRUTH-9-2-0-1-1" has right digit "2".
Truth row "TRUTH-9-2-0-1-1" has carry input "CARRY-0".
Truth row "TRUTH-9-2-0-1-1" emits sum digit "1".
Truth row "TRUTH-9-2-0-1-1" emits carry output "CARRY-1".
Truth row "TRUTH-9-2-1-2-1" has left digit "9".
Truth row "TRUTH-9-2-1-2-1" has right digit "2".
Truth row "TRUTH-9-2-1-2-1" has carry input "CARRY-1".
Truth row "TRUTH-9-2-1-2-1" emits sum digit "2".
Truth row "TRUTH-9-2-1-2-1" emits carry output "CARRY-1".
Truth row "TRUTH-9-3-0-2-1" has left digit "9".
Truth row "TRUTH-9-3-0-2-1" has right digit "3".
Truth row "TRUTH-9-3-0-2-1" has carry input "CARRY-0".
Truth row "TRUTH-9-3-0-2-1" emits sum digit "2".
Truth row "TRUTH-9-3-0-2-1" emits carry output "CARRY-1".
Truth row "TRUTH-9-3-1-3-1" has left digit "9".
Truth row "TRUTH-9-3-1-3-1" has right digit "3".
Truth row "TRUTH-9-3-1-3-1" has carry input "CARRY-1".
Truth row "TRUTH-9-3-1-3-1" emits sum digit "3".
Truth row "TRUTH-9-3-1-3-1" emits carry output "CARRY-1".
Truth row "TRUTH-9-4-0-3-1" has left digit "9".
Truth row "TRUTH-9-4-0-3-1" has right digit "4".
Truth row "TRUTH-9-4-0-3-1" has carry input "CARRY-0".
Truth row "TRUTH-9-4-0-3-1" emits sum digit "3".
Truth row "TRUTH-9-4-0-3-1" emits carry output "CARRY-1".
Truth row "TRUTH-9-4-1-4-1" has left digit "9".
Truth row "TRUTH-9-4-1-4-1" has right digit "4".
Truth row "TRUTH-9-4-1-4-1" has carry input "CARRY-1".
Truth row "TRUTH-9-4-1-4-1" emits sum digit "4".
Truth row "TRUTH-9-4-1-4-1" emits carry output "CARRY-1".
Truth row "TRUTH-9-5-0-4-1" has left digit "9".
Truth row "TRUTH-9-5-0-4-1" has right digit "5".
Truth row "TRUTH-9-5-0-4-1" has carry input "CARRY-0".
Truth row "TRUTH-9-5-0-4-1" emits sum digit "4".
Truth row "TRUTH-9-5-0-4-1" emits carry output "CARRY-1".
Truth row "TRUTH-9-5-1-5-1" has left digit "9".
Truth row "TRUTH-9-5-1-5-1" has right digit "5".
Truth row "TRUTH-9-5-1-5-1" has carry input "CARRY-1".
Truth row "TRUTH-9-5-1-5-1" emits sum digit "5".
Truth row "TRUTH-9-5-1-5-1" emits carry output "CARRY-1".
Truth row "TRUTH-9-6-0-5-1" has left digit "9".
Truth row "TRUTH-9-6-0-5-1" has right digit "6".
Truth row "TRUTH-9-6-0-5-1" has carry input "CARRY-0".
Truth row "TRUTH-9-6-0-5-1" emits sum digit "5".
Truth row "TRUTH-9-6-0-5-1" emits carry output "CARRY-1".
Truth row "TRUTH-9-6-1-6-1" has left digit "9".
Truth row "TRUTH-9-6-1-6-1" has right digit "6".
Truth row "TRUTH-9-6-1-6-1" has carry input "CARRY-1".
Truth row "TRUTH-9-6-1-6-1" emits sum digit "6".
Truth row "TRUTH-9-6-1-6-1" emits carry output "CARRY-1".
Truth row "TRUTH-9-7-0-6-1" has left digit "9".
Truth row "TRUTH-9-7-0-6-1" has right digit "7".
Truth row "TRUTH-9-7-0-6-1" has carry input "CARRY-0".
Truth row "TRUTH-9-7-0-6-1" emits sum digit "6".
Truth row "TRUTH-9-7-0-6-1" emits carry output "CARRY-1".
Truth row "TRUTH-9-7-1-7-1" has left digit "9".
Truth row "TRUTH-9-7-1-7-1" has right digit "7".
Truth row "TRUTH-9-7-1-7-1" has carry input "CARRY-1".
Truth row "TRUTH-9-7-1-7-1" emits sum digit "7".
Truth row "TRUTH-9-7-1-7-1" emits carry output "CARRY-1".
Truth row "TRUTH-9-8-0-7-1" has left digit "9".
Truth row "TRUTH-9-8-0-7-1" has right digit "8".
Truth row "TRUTH-9-8-0-7-1" has carry input "CARRY-0".
Truth row "TRUTH-9-8-0-7-1" emits sum digit "7".
Truth row "TRUTH-9-8-0-7-1" emits carry output "CARRY-1".
Truth row "TRUTH-9-8-1-8-1" has left digit "9".
Truth row "TRUTH-9-8-1-8-1" has right digit "8".
Truth row "TRUTH-9-8-1-8-1" has carry input "CARRY-1".
Truth row "TRUTH-9-8-1-8-1" emits sum digit "8".
Truth row "TRUTH-9-8-1-8-1" emits carry output "CARRY-1".
Truth row "TRUTH-9-9-0-8-1" has left digit "9".
Truth row "TRUTH-9-9-0-8-1" has right digit "9".
Truth row "TRUTH-9-9-0-8-1" has carry input "CARRY-0".
Truth row "TRUTH-9-9-0-8-1" emits sum digit "8".
Truth row "TRUTH-9-9-0-8-1" emits carry output "CARRY-1".
Truth row "TRUTH-9-9-1-9-1" has left digit "9".
Truth row "TRUTH-9-9-1-9-1" has right digit "9".
Truth row "TRUTH-9-9-1-9-1" has carry input "CARRY-1".
Truth row "TRUTH-9-9-1-9-1" emits sum digit "9".
Truth row "TRUTH-9-9-1-9-1" emits carry output "CARRY-1".
Place "ONES" advances to place "TENS".
Place "TENS" advances to place "HUNDREDS".
Place "HUNDREDS" advances to place "THOUSANDS".
Addition "DECIMAL-ADDITION" requires instruction "INSTRUCTION-READ-OPERAND-DIGITS".
Instruction "INSTRUCTION-READ-OPERAND-DIGITS" licenses action "DECIMAL-ADDITION".
Addition "DECIMAL-ADDITION" requires instruction "INSTRUCTION-CLAMP-INITIAL-CARRY".
Instruction "INSTRUCTION-CLAMP-INITIAL-CARRY" licenses action "CARRY-0".
Addition "DECIMAL-ADDITION" requires instruction "INSTRUCTION-SELECT-MATCHING-TRUTH-ROW".
Instruction "INSTRUCTION-SELECT-MATCHING-TRUTH-ROW" licenses action "DECIMAL-ADDITION".
Addition "DECIMAL-ADDITION" requires instruction "INSTRUCTION-EMIT-SUM-DIGIT".
Instruction "INSTRUCTION-EMIT-SUM-DIGIT" licenses action "SUM-DIGIT".
Addition "DECIMAL-ADDITION" requires instruction "INSTRUCTION-PROPAGATE-CARRY-TO-NEXT-PLACE".
Instruction "INSTRUCTION-PROPAGATE-CARRY-TO-NEXT-PLACE" licenses action "CARRY-OUT".
Addition "DECIMAL-ADDITION" requires instruction "INSTRUCTION-ADVANCE-ONE-PLACE".
Instruction "INSTRUCTION-ADVANCE-ONE-PLACE" licenses action "BASE-10".
Addition "DECIMAL-ADDITION" requires instruction "INSTRUCTION-TERMINATE-AFTER-FINAL-CARRY".
Instruction "INSTRUCTION-TERMINATE-AFTER-FINAL-CARRY" licenses action "CARRY-OUT".
Addition "DECIMAL-ADDITION" requires instruction "INSTRUCTION-RENDER-MOST-SIGNIFICANT-FIRST".
Instruction "INSTRUCTION-RENDER-MOST-SIGNIFICANT-FIRST" licenses action "SUM-DIGIT".
Instruction "INSTRUCTION-READ-OPERAND-DIGITS" precedes instruction "INSTRUCTION-CLAMP-INITIAL-CARRY".
Instruction "INSTRUCTION-CLAMP-INITIAL-CARRY" precedes instruction "INSTRUCTION-SELECT-MATCHING-TRUTH-ROW".
Instruction "INSTRUCTION-SELECT-MATCHING-TRUTH-ROW" precedes instruction "INSTRUCTION-EMIT-SUM-DIGIT".
Instruction "INSTRUCTION-EMIT-SUM-DIGIT" precedes instruction "INSTRUCTION-PROPAGATE-CARRY-TO-NEXT-PLACE".
Instruction "INSTRUCTION-PROPAGATE-CARRY-TO-NEXT-PLACE" precedes instruction "INSTRUCTION-ADVANCE-ONE-PLACE".
Instruction "INSTRUCTION-ADVANCE-ONE-PLACE" precedes instruction "INSTRUCTION-TERMINATE-AFTER-FINAL-CARRY".
Instruction "INSTRUCTION-TERMINATE-AFTER-FINAL-CARRY" precedes instruction "INSTRUCTION-RENDER-MOST-SIGNIFICANT-FIRST".
```

## Exact Surface World source

```text
Operation "realize-semantic-result" selects kernel primitive "REALIZE_SEMANTIC_RESULT".
Instruction "realize-semantic-result" selects operation "realize-semantic-result" accepts "Realize the verified semantic result.".
```

## Exact unseen prompt

```text
Add using compiled decimal addition instructions with A0=7,A1=8,A2=4,A3=0,B0=6,B1=9,B2=5,B3=0,C0=CARRY-0.
```

## Exact response

```text
UNSUPPORTED_PROGRAM: lookup target is missing
```

## Settlement, replay, leakage, and controls

```json
{
  "baseline": {
    "handoff_count": 1,
    "refusal_code": "UNSUPPORTED_PROGRAM",
    "refusal_message": "lookup target is missing",
    "result_hash": "d6b7352bbfedcbb223e90266615133f1ba49bb478e2c7b080803e4488660ecc0",
    "returned_output": false,
    "settled_roles": [
      "INPUT"
    ],
    "settlement_count": 1,
    "stage": "MAIN",
    "status": "REFUSAL"
  },
  "baseline_replay_byte_exact": true,
  "baseline_source_sha256": "08f6e3d33044bd1fb3dd9bf47845be56de210870e1aa8d8e013f926854b6daf5",
  "bundle_hash": "074b970783afbab0b453fbf192d0aea480905006398ee80c0b2bf538da5fa91d",
  "bundle_id": "132886ea4a05cf4c315e699aad7212b771dcf134f9bc573c1f519170c59b9f34",
  "causal_controls": [
    {
      "control": "remove-one-universal-truth-row",
      "handoff_count": 1,
      "main_generation_id": "c22e1bb425fc4f55c457d4f971a7d382b73c9444b22502a16b69def627502665",
      "refusal_code": "UNSUPPORTED_PROGRAM",
      "refusal_message": "lookup target is missing",
      "replay_byte_exact": true,
      "result_hash": "e0c612473241ea4ca56ef8430be6777181b0a1c87e701899123661415ea9ae72",
      "returned_output": false,
      "settled_roles": [
        "INPUT"
      ],
      "settlement_count": 1,
      "source_sha256": "fc69ae2357c060aa19f22ac17c8b59cd8e7163a4f44e6d8762f6991b736103a6",
      "stage": "MAIN",
      "status": "REFUSAL"
    },
    {
      "control": "remove-carry-propagation-instruction",
      "handoff_count": 1,
      "main_generation_id": "b3e1511ca109579aad57ca5f631cd4e1a64c0be409578d0be65b736e15c8bc18",
      "refusal_code": "UNSUPPORTED_PROGRAM",
      "refusal_message": "lookup target is missing",
      "replay_byte_exact": true,
      "result_hash": "4250045ffd94ae74e2798ef581e88d31806492f77e3fed41d374e9b372b6bd34",
      "returned_output": false,
      "settled_roles": [
        "INPUT"
      ],
      "settlement_count": 1,
      "source_sha256": "55455544318af1f51512e2091277a8c05f740b85a106a9ed358dbf01f06d6a26",
      "stage": "MAIN",
      "status": "REFUSAL"
    },
    {
      "control": "reverse-place-order",
      "handoff_count": 1,
      "main_generation_id": "ed822cbbfed31b7e00ff4d2ef59bcee223b2b21c451e786dafae6733c90fb2dd",
      "refusal_code": "UNSUPPORTED_PROGRAM",
      "refusal_message": "lookup target is missing",
      "replay_byte_exact": true,
      "result_hash": "1db19584ddd64936d23fac49b1b058bc9577391b6e3e430fb6d842e55ae1eb6b",
      "returned_output": false,
      "settled_roles": [
        "INPUT"
      ],
      "settlement_count": 1,
      "source_sha256": "57669c56cf3f055087b301df3d28a750391fadebad6780f301c075ec4627ef74",
      "stage": "MAIN",
      "status": "REFUSAL"
    }
  ],
  "causal_sensitivity_established": false,
  "compiled_counts": {
    "carry_values": 2,
    "decimal_truth_rows": 200,
    "digits": 10,
    "directional_edges_per_input_main_world": 1036,
    "granular_instruction_meanings": 8,
    "meanings_per_input_main_world": 272,
    "places": 4,
    "program_steps": 8,
    "truth_table_edges": 1000,
    "vectors_per_input_main_world": 253
  },
  "dispatch_count": 0,
  "elapsed_seconds": 3.445,
  "encoder": "DETERMINISTIC-TEST-ENCODER-64",
  "exact_response": "UNSUPPORTED_PROGRAM: lookup target is missing",
  "execution_performed": false,
  "final_verdict": "NO_GO_INSTRUCTION_EXECUTION",
  "independent_arithmetic_verifier_invoked": false,
  "network_attempts": 0,
  "prequery_leakage": {
    "completed_result_constructed_before_settlement": false,
    "completed_result_or_hash_passed_to_compiler": false,
    "findings": {
      "exact_prompt": false,
      "operand_a": false,
      "operand_b": false,
      "operand_pair": false,
      "operand_pair_hash": false,
      "prompt_hash": false
    },
    "prompt_operands_and_hashes_absent": true,
    "raw_assets_checked": 4,
    "semantic_assets_checked": 5
  },
  "preservation": {
    "production_stores_and_existing_reports_byte_identical": true,
    "protected_sha256": {
      "data/store-4.7.sqlite3": "4bda69217d0e64b398508e206a670dd99f3e64976dc9e7a0aadb5f22e55cd3da",
      "data/store-4.8.sqlite3": "b8695b7c59e8830b184f4d23eb76ea00273e272c573af309e141200bf4872334",
      "reports/FIELD-ONLY-SUDOKU-4.8-001.md": "7b3221a938a0882846460830d4f7b609b6a4fab6644a3023cfb5ab9f512eb849",
      "reports/SUDOKU-4.8-DISPOSABLE-001.md": "302438aa41a536ffe8d055f8b31b638673a72eb05142c519c4a3f05750a5af66"
    },
    "runtime_source_byte_identical": true,
    "tracked_files_byte_identical": true
  },
  "runtime": "4.8",
  "runtime_commit": "68835899d6416c9aa061858ec8390a33ecd8feab",
  "runtime_or_harness_query_arithmetic_transitions": 0,
  "store_schema": "proof-energy-world-store/4.8",
  "surface_source_sha256": "75aec1ef7589f3b502fe73e6950258449d3538221a34787f34a060d981f3f12c",
  "verifier_reason": "Settlement produced no arithmetic output; verifier was forbidden from generating one.",
  "worlds": {
    "INPUT": {
      "generation_id": "d79e731144ebcf5ff5c706f6f7bd6ffa9406b5d88da206a9b78f6e930d1e8724",
      "world_hash": "c668e49a70742f4f8f7f1594ca1230b62a91f37440bf9dcf9eb9a041af2f785d"
    },
    "MAIN": {
      "generation_id": "1f309a30192c8f987d51787334dcab8d2e1ae92867f09ad67782f2a71ce74913",
      "world_hash": "671f3b4f6f48d75fa3fa38b33a82c96ce90488f33779ff8e7eec87866a3bcf47"
    },
    "SURFACE": {
      "generation_id": "dec9241a67e5913768d445a99b243dea9f00bf1590e9c1ca63cf6a6946cee6d7",
      "world_hash": "d1dce1d45186126df32c4dc30278f217d698e106e7c9567076df9df8722f67af"
    }
  }
}
```

## Where computation occurred

- Before the prompt, fixture compilation generated the complete universal 200-row decimal full-adder table: every left digit, right digit, and carry-in maps to a sum digit and carry-out.
- The compiler created content-addressed meanings, vectors, directional edges, and complete source provenance.
- Stock grounding converted the prompt's digit bindings to compiled identifiers.
- Stock Input settlement verified and handed off the typed request with zero violations.
- Stock Main settlement encountered the first compiled `LOOKUP` step and refused because no entity target existed. It did not interpret the step metadata as arithmetic.
- Surface World never ran. No result existed for an independent arithmetic verifier to check, so that verifier was not invoked.
- Removing a truth row, removing carry propagation, and reversing place order did not change the refusal. This confirms the compiled arithmetic material had no causal role in settlement.

## Exact missing mechanism

Runtime 4.8 cannot instantiate compiled truth-table rows as factors over transient digit and carry variables. It has no writable per-place state and no field-native operator that couples carry-out at one place to carry-in at the next. The scalar energy only evaluates outputs created by its frozen primitive registry; instruction names and binary semantic edges cannot add new transition dynamics.

## Isolation

The temporary bundle, stores, fixtures, caches, and raw results were deleted. Runtime 4.8 code/configuration, production stores, tests, tracked files, and all pre-existing local reports remained byte-identical. This report is local and uncommitted.
