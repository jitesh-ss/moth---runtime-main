---
name: structured-output-paraphrase
description: Convert a confirmed decision object into faithful JSON or non-executed Python source in the chosen presentation shape.
---

# Structured output paraphrase

## Workflow

- Examine the confirmed semantic outcome prior to building the output.
- Choose JSON or Python exclusively from a recognized output-language instruction.
- Fall back to a compact representation and expand to a readable representation only on request.
- Encode all important entries with unchanged names, contents, and data types.
- In JSON, return a single object that the built-in JSON decoder accepts.
- In Python, return one data-only binding called decision that can be checked through the syntax tree without running it.

## Fidelity

- Retain every name, content, and string data type with no extra or missing entry.
- Prohibit imports, function invocation, member access, branching, loops, and active Python behavior.
- Fail closed for an invalid semantic outcome or an unrecognized language or layout instruction.
- Attach the output to the confirmed semantic outcome and the compiled instructions.

## Size

- Produce compact output as one line and readable output as consistently indented multiple lines.

## Completion

- Complete only after decoding the output, proving identical data, and validating the inert Python tree.
- Return just the validated JSON or Python output.

