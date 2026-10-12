---
name: mixed-response-paraphrase
description: Merge a confirmed plan outcome into rationale plus JSON or sequenced next steps.
---

# Mixed response paraphrase

## Workflow

- Examine the confirmed semantic outcome prior to rendering.
- Choose exclusively a recognized presentation instruction for this response family.
- Design the response and express every important decision fact.

## Fidelity

- Retain proposed validity, backup validity, selected plan, and failure reason with no missing or extra content.
- Fail closed for an invalid semantic outcome or unknown presentation instruction and attach the artifact to the compiled instructions.

## Size

- Constrain the response to the fixed line, word, and byte bounds for the chosen mode.

## Completion

- Complete only when reverse recovery establishes identical semantics and the layout check succeeds.
- Return just the validated response artifact.
