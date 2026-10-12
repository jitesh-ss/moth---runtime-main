---
name: safe-text-patch
description: Use when a user asks to replace one known text value in one ordinary text file.
---

# Safe Text Patch

## Purpose

Replace a known text value in a specified file without disturbing anything else.

## Procedure

- Examine the requested target before changing it.
- Ensure that the target is a text file inside the permitted workspace.
- Confirm that the old text occurs exactly once.
- Replace that occurrence with the requested new text.
- Check the resulting file after the change.
- Give a concise report containing the target and verification evidence.

## Safety

- Never alter unrelated files or additional text.
- Ask for authorization before changing a protected file.
- Refuse when the target is missing or ambiguous.
- Refuse when required preconditions cannot be established.

## Completion

Claim completion only after verification succeeds and the result is reported.

