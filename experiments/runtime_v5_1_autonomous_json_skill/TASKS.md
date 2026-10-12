# Tasks

- [x] Freeze the experiment specification.
  - Acceptance: objective, boundaries, panels, causal gates, and decisive
    thresholds are explicit.
  - Verify: review `SPEC.md`.

- [ ] Create the candidate field and single detailed skill.
  - Acceptance: existing Runtime 5.1 compilers produce one verified policy; ten
    compilations are byte-identical.
  - Verify: `test_compiler.py`.
  - Files: `fixtures/json-formatting-field-en-1.0.json`,
    `fixtures/json-formatting/SKILL.md`, `compiler.py`.

- [ ] Implement autonomous routing, realization, verification, and persistence.
  - Acceptance: a prompt-only turn produces a hash-bound JSON result or typed
    refusal without explicit skill or presentation input.
  - Verify: routing and realization tests.
  - Files: `candidate_runtime.py` and two test files.

- [ ] Freeze independent qualification fixtures.
  - Acceptance: at least 240 positive, 96 negative, and 64 metamorphic cases;
    source manifest covers all scored inputs.
  - Verify: fixture-count and manifest tests.
  - Files: `generate_fixtures.py`, generated JSON fixtures, manifest.

- [ ] Implement causal and campaign gates.
  - Acceptance: eight causal controls, repeats, fresh-store replay, and zero
    side effects are measured.
  - Verify: causal and campaign tests.
  - Files: `campaign.py`, two test files.

- [ ] Execute Attempt 001 and existing-runtime preservation tests.
  - Acceptance: non-overwritten raw rows and compact decisive report exist;
    existing Runtime 5.1 tests pass and artifact hash is unchanged.
  - Verify: commands frozen in `SPEC.md`.
  - Files: `runs/attempt-001/`, `reports/RESULT-001.json`, final report.

