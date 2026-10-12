---
name: Autonomous JSON formatting
description: Format and organize strict JSON from a natural user request while preserving its exact data.
---

# Autonomous JSON formatting

This skill converts embedded source JSON into a user-requested JSON structure.
The source data remains authoritative. Formatting and structural instructions
may reorganize that data but may not silently change its scalar values or types.

## Workflow

- First parse the source JSON before attempting to format or transform it.
- Recognize the natural request and select exactly one supported output shape.
- Select or project requested fields and rename fields only when explicitly requested.
- Build flat or nested objects, scalar or record arrays, keyed maps, envelopes, unions, sparse records, and grouped collections using the requested structure.
- Preserve source order when requested, or apply canonical key order when requested.
- Format JSON as compact output or pretty output with two-space or four-space indentation as requested.
- Parse the emitted JSON and verify both the requested shape and the preserved data.

## Fidelity

- Preserve every selected scalar value and exact JSON type, including strings, numbers, booleans, nulls, arrays, and objects.
- Never invent a field or fabricate a value that is absent from the source data.
- Refuse ambiguous fields, missing fields, duplicate output keys, unauthorized lossy changes, and unsupported transformations.
- Never use the network, invoke a tool, write a file, or execute generated code.

## Size

- Enforce explicit limits on source bytes, nesting depth, and record count.

## Completion

- Success is complete only after valid JSON parses, exact data is preserved, the requested shape is verified, and integrity hashes are bound.

