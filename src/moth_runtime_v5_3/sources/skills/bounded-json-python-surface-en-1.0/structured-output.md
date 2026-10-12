---
name: structured-output
description: Serialize a verified structured decision as exact JSON or safe inert Python using the requested layout.
---

# Structured output

## Workflow

- Inspect the verified semantic result before creating an artifact.
- Select JSON or Python only from the supported format request.
- Use compact layout by default and readable layout only when requested.
- Serialize every material field with its exact key, value, and type.
- For JSON, emit one object accepted by the standard JSON parser.
- For Python, emit one literal assignment named decision that the AST parser can inspect without execution.

## Fidelity

- Preserve every key, value, and string type without adding or omitting a field.
- Never emit imports, calls, attributes, control flow, or executable behavior in Python.
- Refuse a malformed semantic result or unsupported format and layout request.
- Bind the artifact to the verified semantic result and compiled policy.

## Size

- Keep compact artifacts on one line and render readable artifacts with deterministic multiline indentation.

## Completion

- Finish only after parsing the artifact and confirming exact value equality and safe Python syntax.
- Emit only the verified JSON or Python artifact.

