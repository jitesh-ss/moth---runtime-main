# Runtime 4.9 compositional-language cascade — Attempt 001

Date: 2026-09-01  
Base commit: `80471aa955a32751fd5a97a633759326654664fc`  
Verdict: **COMPOSITIONAL_LANGUAGE_CASCADE_CONFIRMED_WITHIN_FROZEN_BOUNDARY**

## Question

Can a separately compiled semantic Input stage interpret unseen multi-clause
prompts into a complete canonical fact graph and intent, pass only typed facts
to an unmodified Runtime 4.9 Main factor World, and produce the same verified
decision across paraphrase, clause order, pronouns, and two domains?

## Compiled mechanism

The experiment compiled one domain-independent decision coordinate system:

```text
candidates:   PROPOSED, BACKUP
requirements: RESOURCE, PERMISSION, DEADLINE
intent:       VALIDATE_AND_SELECT
```

Delivery and deployment supplied different entity and capability vocabularies
but projected into those same coordinates. Reusable language laws covered
possession, lack, authorization, deadline feasibility, entity aliases, and
singular reference to the most recent unambiguous candidate.

Input required one non-conflicting truth value for all six
candidate/requirement coordinates. It emitted a content-addressed handoff with
only domain, intent, canonical facts, and proof commitments. Raw prose did not
enter Main.

Main was one disposable in-memory World compiled by the unmodified Runtime 4.9
compiler. Its generic allowed-tuple factors calculated proposed validity,
backup validity, selection, and deterministic proposed-plan diagnosis. Surface
copied the verified semantic value without alteration.

## Frozen campaign result

| Gate | Result |
|---|---:|
| Total frozen prompts | 13/13 |
| Accepted end-to-end cascades | 8/8 |
| Expected safe refusals | 5/5 |
| Unsafe acceptances | 0 |
| Domains | delivery + deployment |
| Delivery paraphrase/order/pronoun equivalence | PASS |
| Deployment paraphrase/pronoun equivalence | PASS |
| Proposed-valid result | PASS |
| Backup-repair results | PASS |
| No-valid-plan result | PASS |
| Resource diagnosis | PASS |
| Permission diagnosis | PASS |
| Deadline diagnosis | PASS |

The three delivery resource-failure prompts had different wording, sentence
order, aliases, and pronoun use. All produced the same canonical six-fact hash:

```text
bec98b32287a02f49b0c6d49b173b5d73bf00e90c55a101b91734b3208d74c5b
```

Both deployment permission-failure prompts produced:

```text
6d98aa93bee28e43083fb93fa2a051163f923cdb514133da45058350f5f9d593
```

Their verified Surface result was respectively identical within each group.

## Generic Main World evidence

Every accepted case in both domains used the same compiled Main World:

```text
fcc00fa1cfc5c0296f04cce179c139e907860dd3b310a77323b6a56232f79bf2
```

All successful Main states had zero violations, zero ambiguity units, zero
total factor energy, singleton transient variables, verified factor witnesses,
and no execution or dispatch.

Representative resource-repair output:

```json
{
  "backup-valid": "true",
  "failure-reason": "RESOURCE",
  "proposed-valid": "false",
  "selected-plan": "BACKUP"
}
```

The same program also produced `PROPOSED`, `NONE`, `PERMISSION`, and `DEADLINE`
outcomes solely from different settled Input facts.

## Refusal and causal evidence

- A pronoun after a clause mentioning both candidates refused
  `AMBIGUOUS_REFERENCE`.
- A missing decision coordinate refused `INCOMPLETE_FACT_GRAPH`.
- Opposing assertions for one coordinate refused `CONFLICTING_FACTS`.
- An uncompiled candidate refused `UNKNOWN_ENTITY`.
- An uncompiled requested operation refused `UNSUPPORTED_INTENT`.
- Disabling anaphora broke the frozen pronoun panel.
- Removing the compiled intent surface broke intent settlement.
- Removing one fact family produced an incomplete graph.
- Altered handoff bindings were rejected.
- Altered Surface output with its original commitment was rejected.

Two complete campaigns were byte-identical after excluding wall-clock duration.
Frozen row hash:

```text
ab1ccde61c1d14dadbec7649dcbd860461e15c558a88fe4a32b6e0dd153af35a
```

## Preservation and regression evidence

Protected Runtime 4.7/4.8/4.9 aggregate before and after:

```text
3ddad5a0f486179c3a9d56665bdbd1aeb1f770a660bcaf7828a490c7746beccb
```

Attempt 001 semantic-equivalence experiment aggregate before and after:

```text
e1b92641fc6dddc642977e32b4278f19d3da986083647ee6ec911ba3930404a3
```

- Attempt 001 + Attempt 002 experiment tests: **18 passed**.
- Focused Runtime 4.9 and launcher tests: **40 passed**.
- Complete pre-existing suite: **96 passed, 1 failed**.

The sole full-suite failure remains the pre-existing Runtime 4.8 architecture-
lock mismatch documented before these experiments. It was preserved rather
than changing protected evidence.

No production SQLite store was opened or modified. No promoted runtime source,
configuration, documentation, architecture lock, or launcher was changed.

## Decisive meaning

Attempt 002 establishes:

> Bounded multi-clause language can settle into a complete canonical fact graph
> and intent, cross a typed proof-carrying boundary, and drive one generic
> compiled Runtime 4.9 reasoning program across multiple domains. Prompt
> paraphrase, sentence order, and bounded pronouns can therefore become Input
> settlement concerns rather than Main-domain templates.

This is stronger than Attempt 001 because complete paragraphs now drive actual
diagnosis and plan selection. It is still not unrestricted language fidelity.
The parser uses frozen reusable language laws, exact compiled vocabulary,
sentence segmentation, and most-recent singular anaphora. It does not yet
handle arbitrary grammar, multi-entity coreference, nested clauses,
quantifiers, implicit facts, ellipsis, conversational context, or learned
relation-frame induction.

The result justifies a larger candidate Input World that represents clauses,
references, facts, and intents as one globally settled semantic graph rather
than a deterministic bounded parser feeding the graph.
