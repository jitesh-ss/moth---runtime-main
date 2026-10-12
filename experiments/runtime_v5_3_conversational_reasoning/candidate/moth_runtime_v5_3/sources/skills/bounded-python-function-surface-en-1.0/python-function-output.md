---
name: python-function-output
description: Render a verified plan decision as bounded Python with named functions and variables.
---

# Python function output

## Workflow

- Inspect the verified semantic result before planning the program.
- Bind proposed validity, backup validity, and failure reason as module variables.
- Define boolean_text, select_plan, and build_decision as named functions.
- Compute selected plan inside select_plan rather than embedding the selected value.
- Create local text and decision variables inside build_decision.
- Call build_decision once and print the resulting decision dictionary.
- Parse and inspect the complete Python syntax tree before execution.

## Fidelity

- Permit only the frozen assignments, function definitions, conditionals, returns, dictionary, local calls, and print call.
- Prohibit imports, attributes, loops, comprehensions, classes, exceptions, dynamic calls, file access, network access, and subprocesses.
- Refuse a malformed semantic result, unsupported presentation request, or unsafe syntax tree.
- Bind the program and execution result to the verified semantic result and compiled policy.

## Size

- Emit the deterministic readable program within the frozen line and byte limits.

## Completion

- Finish only after constrained execution prints a dictionary exactly equal to the verified semantic value.
- Return only the verified Python program artifact.

