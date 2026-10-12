# Runtime 4.9 Factor Settlement — Qualification 001

Verdict: **FACTOR_SETTLEMENT_CONFIRMED**

Runtime 4.9 implements the frozen claim: structured compiled instructions can
materialize a transient finite-domain factor field and reach a deterministic,
search-free singleton fixed point through compiled allowed-tuple constraints.

## What changed

Only the independent Runtime 4.9 Main World gained the new
`FACTOR_SETTLEMENT` path. Runtime 4.8 code, configuration, documentation, and
stores were not edited. The factor kernel contains no arithmetic, coloring, or
scheduling functions.

Compiled programs use only `CREATE_VARIABLE`, `INSTANTIATE_FACTOR`,
`BIND_PORT`, `CLAMP_FROM_PROMPT`, `CLAMP_LITERAL`, and `EXPOSE_OUTPUT`.

## Decisive semantic evidence

| Panel | Result |
|---|---:|
| Full-adder truth-table input rows | 8/8 |
| Unseen multi-bit additions | 7/7 |
| Carry depths | 4, 8, and 16 bits |
| Graph-color propagation | 1/1 |
| Scheduling constraint field | 1/1 |
| Ambiguous fixed-point refusal | 1/1 |
| Unsatisfiable factor refusal | 1/1 |
| Forged factor-trace rejection | 1/1 |
| Three-World factor cascade | 1/1 |
| Encoder-free replay | byte-exact |

The seven frozen additions included overflow and long-carry cases. Every
successful state had zero factor violations, zero remaining ambiguity,
singleton domains for every transient variable, one allowed-tuple witness per
factor, complete instruction/factor provenance, and independently reconstructed
trace and energy.

The same runtime mechanism solved arithmetic, a two-color chain, and a small
ordering schedule by changing only compiled values, domains, factor tables, and
program steps.

## Real encoder smoke

The copied local BGE encoder was loaded offline. A disposable three-World
bundle compiled a four-bit full-adder field and answered the unseen query
`11 + 6 = 17`. All three Worlds settled, four factor witnesses were verified,
and encoder-free replay returned the original canonical result bytes. No
network, execution, dispatch, or persistent production-field mutation occurred.

Encoder fingerprint:

```text
7cbccf1d1a57c46cdfa496a688b8c8b152a0068aff64b248967b02adcf5ca48b
```

## Test results

- Focused Runtime 4.9, launcher, and terminal-routing checks: 49 passed.
- Complete standalone suite: 96 passed, 1 failed.
- The sole full-suite failure is a pre-existing Runtime 4.8 architecture-lock
  mismatch already present at base commit `6883589`; Runtime 4.8 files were
  left untouched rather than rewriting protected evidence.

## Integrity and preservation

- Runtime 4.7 production store SHA-256 remained
  `4bda69217d0e64b398508e206a670dd99f3e64976dc9e7a0aadb5f22e55cd3da`.
- Runtime 4.8 production store SHA-256 remained
  `b8695b7c59e8830b184f4d23eb76ea00273e272c573af309e141200bf4872334`.
- All three pre-existing untracked experiment reports remained byte-identical.
- Runtime 4.9 production store ends empty: null role heads, null active bundle,
  zero generations, zero bundles, and zero episodes.

## Claim boundary

This is evidence for a programmable closed-world factor-settlement substrate.
It is not evidence for natural-language instruction compilation, arbitrary
program execution, search-complete CSP solving, cyclic global optimization,
Sudoku, chess, open-world reasoning, or LLM-level generality. Problems that
allowed-tuple domain narrowing cannot uniquely resolve refuse with
`AMBIGUOUS_SETTLEMENT`; the runtime does not search for an answer.
