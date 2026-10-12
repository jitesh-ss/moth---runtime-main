---
name: python-function-output-paraphrase
description: Produce restricted Python functions and variable bindings from a confirmed plan outcome.
---

# Python function output paraphrase

## Workflow

- Examine the confirmed semantic outcome prior to designing the source.
- Set proposed validity, backup validity, and failure reason in top-level bindings.
- Declare the named routines boolean_text, select_plan, and build_decision.
- Derive the chosen plan within select_plan instead of copying its final content.
- Introduce local string and decision bindings within build_decision.
- Invoke build_decision exactly once and display the resulting decision mapping.
- Parse and audit the whole Python abstract syntax tree before running it.

## Fidelity

- Allow exclusively the fixed bindings, routine declarations, branches, returns, mapping, local invocations, and display invocation.
- Forbid imports, member access, iteration, comprehensions, classes, exception handling, indirect invocation, filesystem access, networking, and child processes.
- Fail closed for an invalid semantic outcome, unknown presentation instruction, or disallowed syntax tree.
- Attach the source and computed outcome to the confirmed semantic result and compiled instructions.

## Size

- Produce one deterministic legible program inside the fixed line and byte ceilings.

## Completion

- Complete only when limited execution displays a mapping identical to the confirmed semantic value.
- Emit just the validated Python source artifact.

