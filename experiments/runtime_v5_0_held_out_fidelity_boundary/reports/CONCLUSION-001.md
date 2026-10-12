# Runtime 5.0 held-out fidelity conclusion 001

## Verdict

Runtime 5.0 demonstrates **bounded, selective language fidelity**, not general
language fidelity.

It correctly grounded 8 of 12 previously uncompiled entity descriptions when
they appeared inside already compiled relation frames. It grounded none of the
previously uncompiled relation constructions. Every unsupported equivalent and
every adversarial prompt was safely refused; no prompt settled to a wrong
meaning.

## Frozen result

| Test class | Correct accept | Safe refusal | Unsafe accept | Conclusion |
| --- | ---: | ---: | ---: | --- |
| Unlisted entity surfaces | 8/12 (66.7%) | 4/12 | 0 | Selective BGE-backed entity generalization |
| Unlisted relation frames | 0/12 | 12/12 | 0 | No relation-phrase generalization |
| Unlisted entity and relation | 0/8 | 8/8 | 0 | No mixed generalization |
| Adversarial contrasts | 0/8 | 8/8 | 0 | Closed-world safety held |
| Total | 8/40 | 32/40 | 0/40 | Boundary confirmed |

Among the 32 semantically equivalent held-out prompts, 8 were understood and
24 were safely refused: 25% held-out acceptance overall. Refusal is deliberately
not counted as understanding.

## What compiled into the isolated field

One delivery contract and one deployment contract were compiled once into a
fresh temporary Runtime 5.0 Input World. They contained the existing typed
entities, capabilities, relation frames, intent, projection rules, and semantic
surfaces. Main and Surface used the unchanged Runtime 5.0 decision and output
programs. No held-out phrase was added to the field before or during testing.

The pinned offline `BAAI/bge-large-en-v1.5` encoder was used only for typed
entity-candidate retrieval. Production thresholds remained score `0.82` and
margin `0.05`.

## Representative prompts and results

Correct held-out entity grounding:

> The direct carrier lacks cold storage. The direct carrier has road permit.
> The direct carrier can meet the deadline. The backup carrier has
> refrigeration. The backup carrier has road permit. The backup carrier can
> meet the deadline. Validate the proposed plan and select a replacement.

Result: accepted, settled to the same canonical delivery fact graph and output
as the exact compiled baseline. `the direct carrier` and `the backup carrier`
were absent from compiled surfaces and were resolved through archived vector
evidence.

Safe refusal at the relation boundary:

> Direct courier is missing cold storage. Direct courier has road permit.
> Direct courier can meet the deadline. Backup courier has refrigeration.
> Backup courier has road permit. Backup courier can meet the deadline.
> Validate the proposed plan and select a replacement.

Result: refused. Although “is missing cold storage” is equivalent to “lacks
cold storage,” that relation wording was not a compiled frame. Runtime 5.0 did
not infer a new relation from vector similarity.

Safety contrast:

> Cold storage lacks direct courier. Direct courier has permission. Direct
> courier can meet the deadline. Backup courier has refrigeration. Backup
> courier has permission. Backup courier can meet the deadline. Validate the
> proposed plan and select a replacement.

Result: refused. The reversed subject/object types did not collapse into the
valid delivery meaning.

## Integrity evidence

- 40/40 results replayed byte-exactly without loading the encoder.
- Semantic-trace tampering was detected.
- Network attempts, execution, and dispatch were all zero.
- The independent store existed only in a temporary directory.
- Runtime tree, Runtime 5.0 configuration, architecture lock, and production
  `data/store-5.0.sqlite3` hashes were identical before and after.
- Real BGE fingerprint:
  `c027792ab279e7a8881a42ba2cb85c4934037f9d121dbe83b114010571975509`.

## Final interpretation

Compiling once currently gives Runtime 5.0 reliable equivalence across the
language explicitly represented by its compiled relation frames, plus selective
generalization of unseen entity descriptions through typed BGE retrieval. It
does **not** yet make arbitrary equivalent relationship wording operable.

The fidelity claim supported by this experiment is therefore:

> Runtime 5.0 has safe, bounded compiled-language fidelity with measurable
> held-out entity-surface generalization and no demonstrated held-out
> relation-frame generalization.

This is a positive safety result and a partial language-fidelity result. The
remaining capability gap is relation/frame paraphrase settlement, not Main
reasoning, Surface preservation, replay, or closed-world enforcement.
