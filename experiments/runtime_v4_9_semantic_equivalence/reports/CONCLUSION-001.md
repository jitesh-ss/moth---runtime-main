# Runtime 4.9 semantic-equivalence field — Attempt 001

Date: 2026-09-01  
Base commit: `80471aa955a32751fd5a97a633759326654664fc`  
Verdict: **SEMANTIC_EQUIVALENCE_CONFIRMED_WITHIN_FROZEN_LANGUAGE_FIELD**

## Question

Can one compiled canonical meaning act as the attractor for previously unseen
equivalent text and alternate internal relation representations, while hard
semantic coordinates prevent unsafe collapse and the existing runtimes remain
unchanged?

## Mechanism tested

The experiment compiled typed entities, one typed predicate family, canonical
proposition rows, eight reusable English relation frames, and four reusable
internal relation transformations. Domain propositions were declared once;
the held-out prompts were not compiled as instruction prototypes.

Text frames produced transient predicate, subject, object, polarity, modality,
and time observations. Exact surfaces cost zero. The pinned offline BGE encoder
could propose compiled entities for unseen role surfaces, but could not assert a
meaning. Settlement considered only compiled proposition rows. Type, role,
predicate, polarity, modality, time, and closed-world compatibility were hard;
quantized vector distance only ranked compatible rows. Insufficient margin
returned `AMBIGUOUS_SEMANTICS`.

Alternate internal relations such as `LACKS`, `CAPABILITY_UNAVAILABLE_TO`, and
`HAS_CAPABILITY_NEGATIVE` passed through compiled typed transformations and
then the identical canonical selector.

## Frozen campaign result

| Gate | Result |
|---|---:|
| Frozen text and internal cases | 26/26 |
| Accepted compiled meanings | 19 |
| Expected safe refusals | 7/7 |
| Unsafe semantic collapses | 0 |
| Equivalent canonical convergence | PASS |
| Cross-domain frame reuse | 3/3 |
| Polarity contrasts | 2/2 |
| Wrong-entity contrasts | 2/2 |
| Role-reversal controls | 2/2 |
| Modality contrast | 1/1 |
| Temporal contrast | 1/1 |
| Ambiguity refusal | 1/1 |
| Closed-world refusals | 2/2 |
| Unsupported language/relation | 2/2 |

Four text forms—including the unseen vector-resolved expression
`primary delivery operator ... cold-chain equipment`—and three alternate
internal relation forms converged to canonical meaning ID:

```text
e83de7ad0cb6f1eccfdeef683e2f4f47ab03738cebac66ab612e6f95e0c7e76f
```

The same generic frames transferred to the software-deployment domain without
adding domain-specific sentence templates.

## Downstream Runtime 4.9 cascade

The experiment compiled a disposable in-memory factor World using the
unmodified Runtime 4.9 compiler and factor kernel. Every equivalent text and
internal form first settled to the same semantic meaning, then drove the same
`PLAN_INVALID` downstream result at zero factor energy. The positive-polarity
contrast settled to a distinct meaning and drove `PLAN_VALID`.

No Runtime 4.9 source, configuration, documentation, architecture lock, or
SQLite store was changed or used as mutable experiment state.

## Causal and integrity evidence

- Removing the semantic prior made the unseen entity surfaces fail while exact
  compiled surfaces continued to work.
- Altering the reusable frame polarity changed the selected canonical meaning.
- Reversing subject and object produced `TYPE_MISMATCH`.
- Removing internal transformations made internal equivalence unavailable.
- A modified trace with its original hash was rejected as `INTEGRITY_FAILURE`.
- Independent compiled-world checks agreed with every accepted result.
- Two full campaign executions, excluding wall-clock duration, were
  byte-identical. Row hash:
  `f2ba2c7347c39ad0c154406a8a5f0cf600142e7702c6937ee9f7afe9f4681dec`.

Pinned encoder fingerprint:

```text
7cbccf1d1a57c46cdfa496a688b8c8b152a0068aff64b248967b02adcf5ca48b
```

## Preservation and tests

Protected Runtime 4.7/4.8/4.9 source, configuration, and documentation aggregate
before and after:

```text
3ddad5a0f486179c3a9d56665bdbd1aeb1f770a660bcaf7828a490c7746beccb
```

- Experiment tests: **10 passed**.
- Focused Runtime 4.9 and launcher regressions: **40 passed**.
- Complete pre-existing suite: **96 passed, 1 failed**.

The sole complete-suite failure is the pre-existing Runtime 4.8 architecture-
lock mismatch already documented by Runtime 4.9 qualification at the same base
line. It was preserved rather than modifying Runtime 4.8 evidence.

## Decisive meaning

Attempt 001 confirms the architectural principle:

> A canonical meaning can be compiled once and recovered from multiple external
> and internal semantic forms through a shared constrained settlement field;
> prompt fidelity can therefore be a consequence of internal semantic
> canonicalization.

This is not yet unrestricted language fidelity. The frozen field covers one
binary predicate family, two domains, single-clause observations, eight generic
English frames, and four internal transformations. It does not cover arbitrary
syntax, pronouns, quantifiers, implicit facts, discourse, multi-clause
composition, or automatic induction of new relation frames. BGE remains a
candidate prior, not a semantic authority.

The result justifies a larger follow-on experiment in which the semantic field
is integrated as the Input World settlement contract and tested against held-
out relations, compositional paragraphs, and globally interacting ambiguities.
