---
name: safe-text-patch-paraphrase
description: Apply a requested change to a known value in a single text artifact.
---

# Controlled Value Substitution

## Purpose

Substitute one known value in an identified text artifact while preserving all other material.

## Procedure

- First review the requested artifact prior to modification.
- Check that it is a text artifact within the allowed workspace.
- Establish that the existing value has a single occurrence.
- Change the existing value to the requested replacement.
- Verify the updated artifact after the change.
- Tell the user which file changed and include the verification result as evidence.

## Safety

- Do not modify unrelated files or additional content.
- Request approval before modifying a restricted file.
- Stop if you cannot uniquely identify the target.
- Stop when the required conditions are not proven.

## Completion

Report success only after verification passes and the outcome is reported.

