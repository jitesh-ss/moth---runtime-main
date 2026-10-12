# Runtime 5.0 compiled relation-identification conclusion 001

## Decisive verdict

Compiling instructions for identifying relationships **causally and safely
improved Runtime 5.0 language fidelity**, but the frozen 12/12 capability target
was not fully met.

The unchanged control field refused all 12 relation holdouts. The instructed
field correctly settled 11 of those 12 prompts to the exact baseline meaning
and output. It also settled 5 of 8 mixed entity-and-relation holdouts. All eight
adversarial prompts refused and there were zero unsafe acceptances.

| Frozen class | Control correct accept | Instructed correct accept | Safe refusal | Unsafe accept |
| --- | ---: | ---: | ---: | ---: |
| Relation holdouts | 0/12 | 11/12 (91.7%) | 1/12 | 0 |
| Mixed entity + relation | not scored | 5/8 (62.5%) | 3/8 | 0 |
| Adversarial controls | not scored | 0/8 | 8/8 | 0 |

Across the 20 equivalent prompts, the instructed field understood 16 (80%).
Refusals are not counted as understanding.

## What compiled into the field

Six declarative identification instructions compiled into anchored frames for
the already-existing typed `satisfies` predicate:

```text
{SUBJECT} is missing {OBJECT}
{SUBJECT} does not possess {OBJECT}
{SUBJECT} is deficient in {OBJECT}
{SUBJECT} cannot provide {OBJECT}
{SUBJECT} is short of {OBJECT}
{SUBJECT} operates without access to {OBJECT}
```

Every instruction emitted the fixed coordinates:

```text
polarity = NEGATIVE
modality = ASSERTED
time = PRESENT
quantity = SINGULAR
subject role = PROPOSED | BACKUP
object role = RESOURCE | PERMISSION | DEADLINE
```

The compiler could not add meanings, entities, relations, roles, capabilities,
operations, or coordinates. Reversing the placeholders, changing modality, or
changing role types failed compilation atomically.

## Representative causal result

Prompt, unchanged from the failed boundary campaign:

> Direct courier is missing cold storage. Direct courier has road permit.
> Direct courier can meet the deadline. Backup courier has refrigeration.
> Backup courier has road permit. Backup courier can meet the deadline.
> Validate the proposed plan and select a replacement.

Control result: refusal because the first clause selected no compiled frame.

Instructed result: accepted. `is missing` was identified as the compiled
negative `satisfies` relationship, producing the same canonical fact graph and
Main output as `Direct courier lacks cold storage`.

All five other construction families produced the same causal result in both
delivery and deployment, except `f12`.

## The one relation-category miss

Prompt:

> Deployment engineer operates without access to the production system. ...

The new relation instruction successfully exposed `{SUBJECT}` and `{OBJECT}`,
but `the production system` was not a compiled entity surface and did not pass
the unchanged typed BGE entity boundary. The runtime safely refused with
`UNKNOWN_ENTITY`.

Therefore this case revealed a second independent fidelity boundary: relation
identification does not guarantee that every novel argument phrase will ground.
The frozen case was not rewritten or reclassified after this observation.

## Safety and integrity

- Unknown candidate, reversed types, wrong object type, ambiguous pronoun,
  unsupported modality, unsupported time, unsupported intent, and unknown
  domain all refused.
- Unsafe semantic acceptances: zero.
- 28/28 instructed results replayed byte-exactly without the encoder.
- Semantic-trace tampering was detected.
- Main and Surface World hashes were byte-identical between control and instructed instances.
- Network attempts, execution, and dispatch were zero.
- Both stores were temporary and independent.
- Runtime source, Runtime 5.0 configuration, architecture lock, and production
  store hashes were unchanged.

## Final interpretation

The hypothesis is supported: **instructions describing how to identify a
relationship can be compiled into the field and make previously inoperable
equivalent relationship language settle internally**. The A/B change from
0/12 to 11/12 demonstrates causality, not merely correlation with BGE.

The exact supported claim is bounded:

> Runtime 5.0 can acquire safe relation-level language fidelity from compiled,
> typed identification instructions. Successful full-prompt settlement still
> requires every entity argument and semantic coordinate to cross its own
> compiled boundary.

This experiment validates the architectural direction. It does not establish
arbitrary English relation understanding, and it does not qualify the
experiment-local rule compiler for production promotion.
