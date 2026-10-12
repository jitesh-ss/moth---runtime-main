# Runtime 5.0 instruction-compression hierarchy

This isolated experiment tests whether a normal, well-authored LLM agent skill
can be compiled through a reusable instruction hierarchy into the same policy
and behavior as a frozen manually granular oracle.

The experiment is independent of every promoted Moth runtime. It imports no
`moth_runtime*` or launcher package, writes only to temporary instance
directories, and treats all production source, configuration, locks, and stores
as protected read-only evidence.

See [`SPEC.md`](SPEC.md), [`PLAN.md`](PLAN.md), and [`TASKS.md`](TASKS.md).

Status: `BOUNDED_HIERARCHICAL_INSTRUCTION_FIDELITY_CONFIRMED`.

The decisive result is in [`reports/CONCLUSION-001.md`](reports/CONCLUSION-001.md).
