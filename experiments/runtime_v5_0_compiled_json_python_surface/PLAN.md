# Plan: Runtime 5.0 compiled JSON/Python Surface skill

1. Freeze format semantics, safe Python subset, compact/readable layouts,
   candidate skills, granular oracle, semantic cases, and protected hashes.
2. Compile the two skill wordings through the unchanged hierarchical Surface
   compiler and require exact oracle equivalence.
3. Implement JSON/Python serialization from the granular policy and verify
   output independently with `json`, `ast`, and `ast.literal_eval`.
4. Attach the candidate only to a disposable Runtime 5.0 overlay with a fresh
   store, preserving the unchanged Runtime result beside every artifact.
5. Run control parity, format/layout, refusal, malformed input, ablation,
   determinism, replay, tamper, and isolation gates.
6. Run focused and Runtime regressions and record the exact bounded verdict.

Semantic fidelity is evaluated before formatting quality. Python source is
never executed. No step promotes or edits an existing runtime or experiment.

