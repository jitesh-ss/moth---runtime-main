# Runtime 4.9 Product Description

Runtime 4.9 is an independent, opt-in Moth runtime that adds active structured
instruction settlement to Runtime 4.8's closed-world three-World architecture.
Runtime 4.8 remains unchanged and Runtime 4.7 remains canonical.

The product claim is deliberately narrow:

> Structured compiled instructions can construct transient finite-domain factor
> fields whose values settle deterministically through compiled table constraints.

The prompt can select a compiled factor program and bind compiled values. It
cannot add a value, factor, rule, operation, schema, or output meaning. The
Input World validates that selection. The Main World executes six generic
field-construction opcodes, narrows variable domains using allowed tuples, and
answers only at a zero-violation singleton fixed point. The Surface World
realizes the already-verified result without changing its meaning.

Runtime 4.9 adds no addition function, domain solver, search procedure, LLM,
tool dispatcher, or query-time learner. Arithmetic, coloring, scheduling, and
other domains differ only in compiled values, finite domains, factor tables,
and programs. Cyclic or underconstrained fields that arc consistency cannot
resolve return `AMBIGUOUS_SETTLEMENT`; contradictions return `UNSATISFIABLE`.

Every answer retains the complete three-World evidence plus the transient
materialization trace, domain-reduction trace, factor witnesses, scalar energy,
generation identity, and source provenance. Replay is encoder-free and exact.
Default terminal output remains concise; `--json` exposes the full record.

Use Runtime 4.9 explicitly:

```sh
moth --runtime 4.9 status
moth --runtime 4.9 query "..."
```

The delivered production store is initialized with empty Input, Main, and
Surface World heads and no active bundle. Runtime 4.9 is experimental and is
not the canonical runtime.
