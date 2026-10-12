# Runtime 5.0 instruction-compression hierarchy conclusion 001

## Decisive verdict

`BOUNDED_HIERARCHICAL_INSTRUCTION_FIDELITY_CONFIRMED`

The isolated experiment confirms the proposed architecture for one frozen,
complete agent-skill family: granular fundamentals can be compiled once into a
base field, ordinary skill language can identify and compose those meanings,
and the resulting policy can perform the skill's intention with the same
behavior as a manually granular oracle.

This is an experimental, bounded result. No production runtime was imported,
modified, or promoted.

## Hierarchy results

| Layer | Frozen content | Result |
| --- | --- | ---: |
| L1 | 12 atomic actions, 3 terminal states | passed |
| L2 | 8 control/policy operators, 5 conditions | passed |
| L3 | 7 granular workflow macros | passed |
| L4 | 16 skill-language interpretation rules | passed |
| L5 | 2 independently compiled skill profiles | passed |
| L6 | 1 typed composition rule | passed |

Removing one required subsystem at each layer caused its dependent compilation
or composition to fail. All six causal-ablation gates passed.

## Instruction fidelity

The ordinary `safe-text-patch` skill contained 12 counted normative clauses.
It compiled to a 30-unit granular policy graph, a 2.5x expansion. No complete
counted skill clause occurred in the base field.

The primary skill matched the independently authored granular policy exactly.
A separately worded equivalent skill produced the same policy hash:

```text
e9bd5922821e577a35cb3d968827c5d9c27e0bdf2d45e53ec2959e8c3340a36a
```

Their compilation traces differed because their source clauses and provenance
differed, while their instruction semantics remained identical. This is the
desired separation between language expression and behavioral meaning.

The independently compiled `evidence-ledger` skill then composed with the patch
skill through a typed `INSERT_BEFORE` rule. The composite policy exactly matched
the frozen composite oracle.

## Behavioral intention test

Single, paraphrased, and composite policies each ran against the same 12-case
panel in independent temporary filesystem instances:

| Per policy | Result |
| --- | ---: |
| Intended successful changes | 3/3 |
| Required authority request | 1/1 |
| Required safe refusals | 8/8 |
| Unsafe acceptances | 0 |
| Byte-exact archived replays | 12/12 |

Across all three policy forms, 36/36 executions were byte-identical to the
corresponding granular-oracle executions. Successful cases changed exactly the
requested file and text. Refusal and authority cases changed no workspace byte.

The panel covered ordinary and Unicode replacement, authorized and unauthorized
protected files, missing and ambiguous targets, missing and duplicate old text,
no-op replacement, unrelated requested changes, path traversal, and binary
input.

## Skill-compilation safety

Four malformed or unsafe skill variants were rejected as frozen:

- missing safety rule: `INCOMPLETE_SKILL`;
- clause selecting two interpretations: `AMBIGUOUS_INSTRUCTION`;
- undeclared deployment primitive: `UNSUPPORTED_INSTRUCTION`;
- attempted base-field self-modification: `UNSUPPORTED_INSTRUCTION`.

Repeated compilation was byte-identical 10/10 times. Archive tampering was
detected. Network attempts, dispatches, production imports, and writes outside
temporary task workspaces were zero. All frozen production runtime,
configuration, launcher, and store hashes were unchanged.

## Exact supported claim

The evidence supports:

> Inside a bounded compiled instruction field, a complete ordinary agent skill
> can identify reusable action, control, policy, workflow, and composition
> meanings; compile into the same canonical policy as a manually granular
> expansion; and perform the same intention on accepted, authority-gated, and
> refused tasks.

It does not yet support:

> Arbitrary third-party LLM skills from unrestricted prose can be compiled with
> instruction fidelity.

The field currently covers one operational family and one composable evidence
extension. The next decisive boundary is cross-domain blind transfer: freeze
the same base fundamentals, introduce several previously unseen skill families,
and measure how many compile without adding profile-specific interpretations.

