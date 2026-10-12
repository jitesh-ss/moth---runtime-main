# Runtime 4.9 Frozen Specification

## Scope

Runtime 4.9 is a separate package, configuration, store family, result domain,
and CLI target. All Runtime 4.8 behavior is copied and preserved. The only
semantic addition is the separately selected Main World primitive
`FACTOR_SETTLEMENT`.

Public identities:

- package: `src/moth_runtime_v4_9/`;
- runtime: `4.9`;
- store: `proof-energy-world-store/4.9`;
- result: `moth-world-result/4.9`;
- factor trace: `moth-factor-settlement/4.9`;
- default store: `data/store-4.9.sqlite3`.

## Compiled language additions

Two meaning types are added: `FINITE_DOMAIN` and `FACTOR_TEMPLATE`.

```text
Finite domain "bit" is canonical value JSON "[\"zero\",\"one\"]".
Factor template "xor" is canonical table JSON "{...}".
Factor program "one-bit" is canonical instruction JSON "[...]".
```

A finite domain contains 1–256 already compiled `VALUE` or `ENUM_MEMBER`
identifiers. A factor template contains 1–16 ordered ports and 1–4096 unique
allowed tuples. Every tuple value must belong to its port domain. Runtime 4.9
uses allowed tuples only.

A factor program has at most 16,384 canonical instructions. References must be
declared before use within the program. Every factor port must be bound exactly
once, bindings must have matching domains, and output ordinals must be unique
and contiguous. Compilation rejects the complete staged generation on error.

The only factor opcodes are:

1. `CREATE_VARIABLE(instance, domain)`;
2. `INSTANTIATE_FACTOR(instance, template)`;
3. `BIND_PORT(factor, port, variable)`;
4. `CLAMP_FROM_PROMPT(variable, field)`;
5. `CLAMP_LITERAL(variable, value)`;
6. `EXPOSE_OUTPUT(variable, ordinal, label)`.

## Settlement

Materialization starts with an empty transient field. It executes instructions
in canonical order and records the compiled `PROGRAM_STEP` that licensed each
effect. Prompt clamps can select only compiled values resolved before the Input
World settles. Transient state is never published into a World generation.

For every variable \(v\), initialize its current domain \(D_v\) from its
compiled finite domain, then apply clamps. For each factor in canonical order:

1. retain allowed tuples compatible with all connected current domains;
2. refuse `UNSATISFIABLE` if none remain;
3. collect supported values independently at every port;
4. intersect each connected variable domain with that support;
5. record every strict reduction and its factor/instruction provenance.

Repeat sweeps until no domain changes. No branching, guessing, backtracking,
enumeration, stochastic restart, or task-specific algorithm is permitted.

Let:

\[
A(D)=\sum_v(|D_v|-1),\qquad M=A_{max}+1,
\]

\[
V(D)=\#\{f:\text{factor }f\text{ has no compatible tuple}\},
\]

\[
E(D)=M V(D)+A(D).
\]

All created variables—not only outputs—must be singleton. Success requires
`V=0`, `A=0`, exactly one compatible tuple witness per factor, and complete
provenance. A non-singleton fixed point returns `AMBIGUOUS_SETTLEMENT`.

## Independent verification and replay

The verifier reconstructs variables, factors, bindings, clamps, and outputs
from the archived program. It replays every reported reduction, recomputes
compatible tuples, proves the final state is a fixed point, checks every
singleton and witness, recomputes energy and provenance, and verifies the trace
hash. Altered state, bindings, values, generation, provenance, energy, output,
or trace fails with `INTEGRITY_FAILURE`.

Encoder-free replay reconstructs the original bundle, both handoffs, all three
stage settlements, the complete factor evidence, and the canonical result
bytes.

## Frozen limits

- variables: 1,024;
- factor instances: 4,096;
- ports per factor: 16;
- tuples per template: 4,096;
- values per domain: 256;
- instructions: 16,384;
- aggregate tuple-port cells: 16,777,216;
- settlement sweeps: 1,024;
- factor trace: 64 MiB;
- prompt: 128 tokens.

## Qualification boundary

Focused qualification must cover all eight full-adder rows, unseen 4-, 8-,
and 16-bit carry chains, a graph-coloring field, a scheduling field, causal
removals/corruptions, forged evidence, three-World handoffs, and byte-exact
replay. Runtime code must remain identical across domains.

Passing establishes a programmable closed-world factor-settlement substrate.
It does not establish natural-language instruction compilation, search-complete
CSP solving, unrestricted reasoning, global optimization, Sudoku, chess, or
LLM-level generality.
