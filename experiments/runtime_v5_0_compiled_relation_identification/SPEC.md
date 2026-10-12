# Spec: Runtime 5.0 compiled relation identification

## Objective

Test whether declarative instructions for identifying negative possession and
availability constructions can be compiled into a disposable Runtime 5.0 Input
World and cause previously refused equivalent clauses to settle to the existing
canonical `satisfies` relation. The experiment measures relation recognition;
it does not modify Runtime 5.0, Main reasoning, Surface realization, or meaning
membership.

The user-visible success condition is causal: an unchanged control field must
refuse the frozen relation holdouts, while the instructed field must settle them
to the exact baseline graph and output with zero adversarial unsafe acceptance.

## Technology and commands

- Runtime: unchanged production `moth_runtime_v5_0` package.
- Relation rule compiler: experiment-local Python, standard library only.
- Entity retrieval: pinned local `BAAI/bge-large-en-v1.5`, offline, CPU.
- Stores: two fresh temporary `proof-energy-world-store/5.0` databases.
- Run: `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 ./.venv/bin/python -m experiments.runtime_v5_0_compiled_relation_identification.campaign`
- Test: `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 ./.venv/bin/python -m pytest experiments/runtime_v5_0_compiled_relation_identification/tests -q`
- Regression: `./.venv/bin/python -m pytest tests/test_runtime_v5_0.py tests/test_runtime_v5_0_language.py tests/test_launcher_v5.py -q`

## Project structure

- `fixtures/relation-identification-en-1.0.json`: frozen declarative rules.
- `fixtures/campaign-en-1.0.json`: frozen relation, mixed, and adversarial prompts.
- `rule_compiler.py`: validates rules and compiles anchored typed frames.
- `campaign.py`: creates control/instructed instances, queries, classifies, and verifies.
- `tests/`: compiler and campaign tests.
- `reports/`: compact manifest and decisive conclusion.
- `runs/`: ignored raw state only.

## Compiled instruction model

Each instruction identifies one bounded construction family and compiles to a
safe anchored template with `{SUBJECT}` and `{OBJECT}`. Its output coordinates
are fixed:

```python
{
    "predicate": "satisfies",
    "polarity": "NEGATIVE",
    "modality": "ASSERTED",
    "time": "PRESENT",
    "quantity": "SINGULAR",
    "subject_roles": ["PROPOSED", "BACKUP"],
    "object_roles": ["RESOURCE", "PERMISSION", "DEADLINE"],
}
```

The experiment compiles six construction families: missing, negated
possession, deficient-in, cannot-provide, short-of, and operates-without-access.
Rules cannot create predicates, roles, entities, capabilities, coordinates, or
operations; they may only generate frames for the existing typed predicate.

## Testing strategy

Freeze before execution:

- 12 relation holdouts copied unchanged from the final boundary campaign.
- 8 mixed entity-and-relation holdouts copied unchanged.
- 8 adversarial role/type/reference/modality/time/intent/domain controls copied unchanged.
- 2 exact baseline prompts, excluded from counted cases.

For every equivalent case, correct acceptance requires the same semantic graph
and output as its domain baseline. Refusal is safe but is not understanding.
Any other answer is unsafe. Every adversarial case must refuse.

The unchanged control instance must refuse all 12 relation holdouts. The
instructed instance must correctly accept all 12 relation holdouts. Mixed cases
are reported independently because their outcome also depends on held-out
entity retrieval. All instructed results must replay byte-exactly encoder-free.

## Boundaries

- Always: use fresh temporary stores; preserve production thresholds; archive
  the rule manifest hash; compare protected hashes before/after; report refusal
  separately from understanding; perform causal control/instructed comparison.
- Ask first: change thresholds, add dependencies, change frozen prompts, or
  promote behavior into production Runtime 5.0.
- Never: edit `src/moth_runtime_v5_0`, `config/v5.0`, or the production store;
  use network; count refusal as understanding; permit BGE to override types,
  direction, polarity, modality, time, or closed-world membership.

## Success criteria

- Rule compilation is deterministic and rejects malformed or unsafe rules.
- Control refuses 12/12 frozen relation holdouts.
- Instructed field correctly accepts 12/12 frozen relation holdouts.
- Instructed field has zero unsafe acceptances across all 28 cases.
- All 8 adversarial cases refuse.
- All instructed results replay byte-exactly encoder-free.
- Semantic tampering is detected.
- Network, execution, and dispatch remain zero.
- Runtime/configuration/architecture-lock/production-store hashes are unchanged.
- The report states the exact mixed-case result and does not overclaim general English.

## Open questions

None. The user authorized planning, implementation, and completion of this
isolated test on 2026-09-02.

