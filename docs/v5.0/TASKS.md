# Runtime 5.0 implementation tasks

- [x] Freeze spec and baseline hashes.
  - Acceptance: product, architecture, spec, tasks, and baseline manifest exist.
  - Verify: inspect files and manifest digest.
- [x] Create independent 5.0 baseline.
  - Acceptance: no 5.0 import references 4.9; all identity domains are 5.0.
  - Verify: namespace scan and parity tests.
- [x] Compile semantic contracts.
  - Acceptance: typed references, frames, limits, surfaces, intents, and projections validate atomically.
  - Verify: compiler and archive tests.
- [x] Settle language in Input.
  - Acceptance: legacy precedence plus unique, typed semantic interpretation and safe refusals.
  - Verify: semantic success, contrast, ambiguity, and ablation tests.
- [x] Integrate receipts, replay, store, launcher, and docs.
  - Acceptance: semantic commitment reaches Main and exact encoder-free replay succeeds.
  - Verify: persistence, tampering, CLI, and cross-runtime tests.
- [x] Qualify and seal.
  - Acceptance: all focused gates pass and protected baselines are unchanged.
  - Verify: qualification commands and final manifest.
