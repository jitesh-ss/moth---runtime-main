# Plan: autonomous JSON skill experiment

Approved by the owner's instruction to execute the frozen specification and
return only with decisive results.

## Components

1. Define and compile a generic JSON field using the existing Runtime 5.1
   layered field compiler.
2. Compile one detailed Markdown skill through the existing Runtime 5.1 skill
   compiler and verify ten byte-identical rebuilds.
3. Build an experiment-local, hash-bound autonomous router and realizer. It
   receives only a natural prompt, extracts embedded strict JSON, resolves one
   supported formatting intent, applies the compiled policy, verifies parse-back
   semantics and requested layout, and returns a deterministic receipt.
4. Persist conversations and turns in a fresh experiment-local SQLite store.
5. Generate and freeze independent positive, negative, and metamorphic panels
   before the scored attempt.
6. Run causal ablations, repeated executions, a fresh-store replay, oracle-leak
   scan, and the existing Runtime 5.1 preservation suites.
7. Preserve raw attempt data under ignored `runs/` and compact evidence under
   `reports/`.

## Implementation order

Field and skill fixtures must exist before the candidate compiler. The compiler
must be verified before the router is exercised. Panels are generated and
hashed before campaign execution. The scored campaign runs only after unit and
integration tests pass. Preservation tests run after the campaign.

## Risks and controls

- **Hidden templates:** the router may contain generic operations only; static
  scans reject case ids and expected documents.
- **Skill is decorative:** no-skill, unrelated-skill, trigger, workflow, and
  router ablations must remove or invalidate the capability.
- **Oracle coupling:** fixture generation and runtime realization use separate
  implementations and modules.
- **Broad false activation:** 96 typed negative cases and injection controls.
- **Layout-only success:** value, shape, and requested bytes are checked
  independently.
- **Existing 5.1 contamination:** no existing source is edited; hashes and
  focused tests are checked afterward.

## Verification checkpoints

1. Field loads and the skill compiles deterministically.
2. Small development examples pass through natural routing.
3. Frozen fixture manifest is written once.
4. All experiment tests pass.
5. Attempt 001 executes once without overwrite.
6. Existing 5.1 focused tests pass and qualified artifact hash is unchanged.

