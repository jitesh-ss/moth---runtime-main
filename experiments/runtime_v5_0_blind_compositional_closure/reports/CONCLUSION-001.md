# Runtime 5.0 blind compositional-closure conclusion 001

## Decisive verdict

The final frozen test **does not yet confirm complete language fidelity inside
the field**.

It confirms substantial bounded compositional fidelity and strong safety, but
the required 12/12 blind-equivalence gate missed four cases. The field and
prompts remained sealed; no rule, threshold, prompt, or expected result was
changed after execution.

| Gate | Result |
| --- | ---: |
| Blind equivalent prompts | 8/12 correct (66.7%) |
| Equivalent semantic graphs | 1 across all 8 accepted prompts |
| Meaning-changing contrasts | 6/6 correct, 6 distinct graphs |
| Unsafe/unsupported refusals | 10/10 correct |
| Unsafe acceptances | 0 |
| Causal ablations | 6/6 dependent cases broke |
| Nested encoder-free replay | 28/28 byte-exact |

The unchanged Runtime 5.0 control accepted 0/12 blind equivalents. The sealed
compositional field increased that to 8/12, proving a causal capability gain,
but not closure.

## What compiled into the field

Before complete prompts existed, the experiment sealed reusable components:

- proposed and backup plan descriptions;
- resource, permission, and deadline descriptions;
- 14 typed positive/negative relation fragments;
- `and`, `but`, and `while` coordination with bounded subject inheritance;
- three validation and three selection intent components;
- bounded singular-pronoun resolution;
- modality, time, sentence, fact, and token constraints.

No complete counted prompt or sentence appeared in the field. Its pre-prompt
SHA-256 commitment was:

```text
2275ac182e275c021c0587a33b04fc65b2d42a01872d373d4cb13acdbc89a11c
```

## A successful blind composition

Prompt:

> Our primary carrier is short of refrigeration but retains delivery
> authorization and can still arrive on time. The reserve carrier possesses
> cold-chain support and remains authorized and can arrive before the cutoff.
> Determine whether the first plan is viable and choose the permitted
> alternative if necessary.

This complete wording was absent from the field. It composed into six canonical
facts, settled to the same semantic graph as the rigid baseline, and produced:

```text
proposed-valid = false
backup-valid = true
selected-plan = BACKUP
failure-reason = RESOURCE
```

Eight structurally different prompts converged to that one graph and output,
including reordered facts, subject inheritance, alternative intent components,
and a pronoun-dependent version.

## Exact failed boundary

Cases `e03`, `e04`, `e08`, and `e10` safely refused. Each used one of:

```text
will meet the delivery deadline
can arrive before the delivery deadline
```

The sealed field defined the capability surface `delivery deadline`, but did
not define a reusable determiner rule allowing `the` to compose with that
surface. Consequently the relation rule exposed an object span that did not
equal any compiled capability description. Settlement refused with
`UNKNOWN_CAPABILITY`.

This is not a dangerous semantic collapse. It is a real compositional coverage
gap. Adding `the delivery deadline` after observing the result would have
invalidated the blind test, so the field was not changed.

## Contrasts, safety, and causality

All six meaning-changing prompts settled correctly: proposed-valid,
permission-failure, deadline-failure, backup-resource-failure, no-valid-resource,
and no-valid-mixed outcomes produced their specified outputs and six distinct
graphs.

All ten unknown, reversed-role, wrong-object, modality, time, intent,
incomplete, ambiguous, unknown-relation, and conflicting-fact prompts refused.
Removing each of the proposed-entity, resource-capability, negative-resource
relation, coordination, validation-intent, and pronoun subsystems caused its
dependent prompt to fail. This demonstrates that compiled field components
caused the successful compositions.

## Integrity and isolation

- Composition-trace and Runtime semantic-trace tampering were detected.
- All 28 instructed results replayed byte-exactly without the encoder.
- Network attempts, execution, and dispatch were zero.
- The store was temporary and independent.
- Production Runtime 5.0 source, configuration, architecture lock, and store
  hashes were unchanged.

## Final conclusion

The evidence supports:

> Runtime 5.0 can gain safe, causal, compositional language and prompt fidelity
> from a compiled field, and accepted equivalent prompts converge to one
> internal meaning.

The evidence does **not** yet support:

> Language fidelity is completely solved for every novel composition presumed
> to belong to the field.

The remaining architectural requirement is that grammatical operators such as
determiners must themselves be explicit reusable field elements and must
compose with typed entity/capability surfaces. Until a fresh sealed field with
that mechanism passes a new blind campaign, the final language-fidelity claim
remains unqualified.
