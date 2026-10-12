# Spec: Runtime 5.0 blind compositional closure

## Objective

Decisively test bounded language fidelity inside a compiled field. Compile and
seal reusable rules for entity descriptions, capability descriptions, relation
fragments, coordination, subject inheritance, and intent composition before any
complete test prompt is frozen. Then require previously unseen combinations to
settle to the same Runtime 5.0 canonical graph and output as the rigid baseline.

Prompt fidelity is evaluated as a consequence: equivalent raw prompts must
produce one semantic graph and output, while semantic contrasts remain distinct
and unsupported language refuses.

## Technology and commands

- Production kernels: unchanged `moth_runtime_v5_0` Input/Main/Surface.
- Experimental layer: deterministic field compiler and compositional Input
  settlement wrapper under this experiment only.
- Entity vectors: pinned local `BAAI/bge-large-en-v1.5`, offline.
- Store: fresh temporary `proof-energy-world-store/5.0` database.
- Run: `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 ./.venv/bin/python -m experiments.runtime_v5_0_blind_compositional_closure.campaign`
- Test: `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 ./.venv/bin/python -m pytest experiments/runtime_v5_0_blind_compositional_closure/tests -q`
- Regression: `./.venv/bin/python -m pytest tests/test_runtime_v5_0.py tests/test_runtime_v5_0_language.py tests/test_launcher_v5.py -q`

## Project structure

- `fixtures/field-en-1.0.json`: field frozen and hashed before prompts.
- `fixtures/blind-campaign-en-1.0.json`: complete prompts frozen after field seal.
- `field.py`: validates and compiles reusable rules.
- `instance.py`: isolated compositional Input settlement and replay wrapper.
- `campaign.py`: control, closure, contrast, refusal, ablation, and integrity gates.
- `tests/`: compiler and end-to-end verification.
- `reports/`: compact result and decisive conclusion.

## Field design

The field defines components only:

- two typed plan entities and composable descriptions;
- resource, permission, and deadline capabilities;
- positive and negative relation fragments;
- `and`, `but`, and `while` coordination with bounded subject inheritance;
- a validation goal plus a selection goal composing one intent;
- forbidden modality/time markers and closed-world failure behavior.

No complete counted prompt or complete counted sentence may occur in the field
fixture. The field fixture hash is embedded in the subsequently frozen campaign.

## Code style

Settlement is data-driven and emits an explicit trace:

```python
canonical_clause = rule["emit"].format(
    SUBJECT=entity["canonical"],
    OBJECT=capability["canonical"],
)
trace.append({"rule_id": rule["id"], "input": fragment, "output": canonical_clause})
```

Rules are anchored; placeholders are typed; unknown residues refuse. No fuzzy
rule selection or global branching is permitted.

## Testing strategy

After sealing the field, freeze:

- 12 equivalent compositional prompts with no complete frame in the field;
- 6 valid semantic contrasts with specified different outputs;
- 10 unsafe/unsupported prompts that must refuse;
- 6 causal ablations, one per identification subsystem.

The unchanged Runtime 5.0 control receives the same raw equivalent prompts and
must not demonstrate compositional closure. The instructed instance must:

- settle all equivalent prompts to the rigid baseline graph and output;
- settle all valid contrasts to their expected different graph/output;
- refuse all unsafe/unsupported prompts;
- lose the dependent case when each required rule subsystem is ablated;
- replay every outer composition trace and inner Runtime result byte-exactly.

## Boundaries

- Always: seal field before prompts; preserve production thresholds; use fresh
  temporary state; distinguish correct acceptance, correct contrast, safe
  refusal, and unsafe acceptance; verify protected hashes.
- Ask first: alter the sealed field or prompts after execution, change
  thresholds, add dependencies, or promote behavior into Runtime 5.0.
- Never: compile complete test sentences, learn from test prompts, use network,
  let vectors override typed constraints, count refusal as understanding, or
  edit production runtime/configuration/store files.

## Success criteria

- Field compilation is deterministic and malformed fields fail atomically.
- Field hash is frozen into the campaign before complete prompts exist.
- No complete counted prompt or sentence appears in the field fixture.
- 12/12 equivalent prompts converge to one baseline semantic graph and output.
- 6/6 valid contrasts settle to their specified different outputs and graphs.
- 10/10 unsafe/unsupported prompts refuse; unsafe acceptances are zero.
- 6/6 causal ablations break their dependent case.
- All instructed results and traces replay byte-exactly encoder-free.
- Semantic and composition tampering are detected.
- Main and Surface remain unchanged; network/execution/dispatch remain zero.
- Protected Runtime 5.0 hashes remain unchanged.

## Open questions

None. The user authorized the plan and complete isolated test on 2026-09-02.

