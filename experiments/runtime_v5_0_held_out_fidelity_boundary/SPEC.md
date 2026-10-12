# Spec: Runtime 5.0 held-out fidelity boundary

## Objective

Conclude the language-fidelity boundary of Runtime 5.0 by testing language that
was deliberately absent from the compiled entity surfaces and relation frames.
The experiment must report correct acceptance, safe refusal, and unsafe
acceptance separately rather than treating refusal as understanding.

## Technology and commands

- Production package: `moth_runtime_v5_0`.
- Entity retrieval: pinned local `BAAI/bge-large-en-v1.5`, offline, CPU.
- Main/Surface fixture compilation: deterministic test encoder; semantic
  execution still uses the unchanged production kernels.
- Store: fresh temporary `proof-energy-world-store/5.0` instance.
- Run: `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 ./.venv/bin/python -m experiments.runtime_v5_0_held_out_fidelity_boundary.campaign`
- Verify: `./.venv/bin/python -m pytest experiments/runtime_v5_0_held_out_fidelity_boundary/tests -q`

## Project structure

- `fixtures/campaign-en-1.0.json`: 40 frozen held-out/adversarial cases.
- `campaign.py`: isolated compilation, execution, classification, replay, and integrity checks.
- `reports/`: compact result manifest and conclusion.
- `runs/`: ignored raw state only.

## Frozen campaign

Two exact prompts establish the delivery and deployment baseline graphs but are
not counted. The 40 counted cases are:

- 12 `ENTITY_SURFACE_HOLDOUT`: known relation frames with subject descriptions
  absent from every compiled entity surface. BGE is the only permitted entity
  recovery path.
- 12 `RELATION_FRAME_HOLDOUT`: exact entities with equivalent relation wording
  absent from every compiled frame.
- 8 `MIXED_HOLDOUT`: both entity wording and relation wording are unlisted.
- 8 `ADVERSARIAL`: wrong entity/type/direction, ambiguous reference, unsupported
  modality/time/intent, or other near-meaning that must refuse.

For the first three categories, an answer is correct only if its semantic graph
and final value equal the exact baseline for that domain. Refusal is safe but
does not count as language generalization. Any other answer is unsafe.

## Code style

Canonical result classification is explicit:

```python
if status == "ANSWER" and graph == baseline_graph and value == baseline_value:
    classification = "CORRECT_ACCEPT"
elif status == "REFUSAL":
    classification = "SAFE_REFUSAL"
else:
    classification = "UNSAFE_ACCEPT"
```

## Testing strategy

Compile once, query all cases, persist and byte-replay every result without an
encoder, inspect vector evidence for correct BGE acceptances, detect one altered
semantic trace, and compare Runtime/configuration/architecture-lock/production-
store hashes before and after.

## Boundaries

- Always: freeze prompts before execution; retain the production thresholds;
  count refusal separately from understanding; require zero unsafe acceptance.
- Ask first: change thresholds, add surfaces/frames, modify Runtime 5.0, or
  introduce another model.
- Never: rewrite a failed prompt, weaken a gate, use network access, or count a
  refusal as successful generalization.

## Success criteria

- All 40 cases receive a deterministic classification.
- Unsafe acceptances: zero.
- All eight adversarial cases refuse.
- Every result replays byte-exactly encoder-free.
- Any BGE acceptance contains archived vector evidence and reconstructs exactly.
- Semantic trace tampering is rejected.
- Protected Runtime 5.0 and production-store hashes remain unchanged.
- The conclusion explicitly reports acceptance rates for entity, frame, and
  mixed holdouts even when those rates are zero.

## Open questions

None. The user requested this final isolated boundary test on 2026-09-02.
