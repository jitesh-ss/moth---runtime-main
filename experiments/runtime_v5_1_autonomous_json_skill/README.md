# Runtime 5.1 autonomous JSON skill experiment

Status: `SPECIFICATION_DRAFT — OWNER_REVIEW_REQUIRED`

This isolated experiment asks whether one detailed, normally written JSON
formatting skill can be compiled once over a fixed Runtime 5.1 candidate field
and then autonomously handle a broad held-out panel of natural-language JSON
format requests. No case may receive an explicit skill id, presentation mode,
template selection, manual correction, or retry hint.

The frozen experiment contract is in [SPEC.md](SPEC.md). Implementation, fixture
generation, execution, and conclusions must not begin until the specification
has been reviewed. Nothing in this directory changes or promotes the qualified
Runtime 5.1 artifact.

Planned layout:

- `fixtures/` — candidate field, single skill, frozen panels, and source hashes.
- `runs/` — ignored raw artifacts, stores, predictions, and repeated rows.
- `reports/` — compact manifests, aggregate results, failures, and replay data.
- `tests/` — experiment-local unit, causal, integrity, and campaign tests.

