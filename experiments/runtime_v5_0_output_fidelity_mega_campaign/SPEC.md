# Specification: Runtime 5.0 output-fidelity mega campaign

Status: **APPROVED BY USER DIRECTION; FREEZE BEFORE EXECUTION** (2026-09-03).

## Objective

Determine, with explicit phase-wise evidence, which bounded LLM-like output
capabilities Runtime 5.0 can realize from verified semantic results when each
output family is controlled by a compiled skill. Preserve failures as boundary
evidence and never alter a promoted runtime, canonical field, or production
store.

## Commands

```sh
PYTHONPATH=src .venv/bin/python -m experiments.runtime_v5_0_output_fidelity_mega_campaign.campaign --compile-only
PYTHONPATH=src .venv/bin/python -m pytest -q experiments/runtime_v5_0_output_fidelity_mega_campaign/tests
PYTHONPATH=src .venv/bin/python -m experiments.runtime_v5_0_output_fidelity_mega_campaign.campaign
PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_runtime_v5_0.py tests/test_runtime_v5_0_language.py tests/test_launcher_v5.py
```

## Project structure

- `fixtures/`: frozen panel, field, oracles, and output-specific skills.
- `runs/`: ignored raw candidate output only.
- `reports/`: compact result, phase report, and full conclusion.
- `tests/`: compiler, realizer, isolation, and campaign tests.
- Python modules beside this spec: candidate compiler integration, realizer,
  disposable instance, rich-output phase, and mega-campaign orchestrator.

## Phases and scale

1. **Foundation integrity** — freeze and verify Runtime 5.0, its production
   store, language qualification, instruction-compression foundation, and all
   predecessor Surface experiments.
2. **Natural prose** — replay 48 responses from the compiled natural Surface.
3. **Rich LLM-like output** — compile four new skill families (each with an
   independently worded equivalent) and realize 64 outputs across compact prose,
   detailed prose, formal tone, conversational tone, bullets, Markdown tables,
   explanation-plus-JSON, and action plans.
4. **Structured data** — replay 40 JSON and inert-Python artifacts.
5. **Executable Python** — replay 16 function-and-variable programs under the
   existing constrained local execution boundary.
6. **Cross-phase qualification** — aggregate 168 outputs, refusal preservation,
   deterministic compilation, tamper/ablation/unsafe gates, cleanup, protected
   hashes, and Runtime 5.0 regressions.

## Code style

All candidate realizers are deterministic and pure until an explicitly bounded
execution harness is reached. Errors use stable codes and fail closed.

```python
artifact = realize(runtime_output, request, compiled_skill)
assert recover(artifact["text"], artifact["mode"]) == runtime_output["value"]
```

## Testing strategy

- Every skill variant must validate and compile to its frozen granular oracle.
- Ten repeated compilations per new skill family must produce one policy hash.
- Every answer must preserve all four material decision fields under independent
  inverse recovery, match control Runtime bytes, archive, and replay.
- Equivalent input paraphrases must converge to one semantic graph.
- Refusals must remain byte-identical and must never become Surface artifacts.
- Unsupported requests, malformed semantics, incomplete policies, skill
  contamination, artifact tampering, and unsafe executable Python fail closed.
- Temporary store and execution paths must be removed; protected hashes must be
  identical before and after the full campaign.

## Boundaries

- **Always:** use fresh temporary stores and frozen fixtures; preserve exact raw
  verdicts; report scope and negative results.
- **Ask first:** promotion, canonical-field changes, new dependencies, networked
  judges, or a hardened external sandbox deployment.
- **Never:** open or migrate the production store for candidate execution; edit
  `src/moth_runtime_v5_0`, `src/moth_launcher_v5`, `config/v5.0`, `data/`, or
  predecessor experiment evidence; claim open-domain LLM equivalence.

## Success criteria

- All four phases return their phase-specific positive verdicts.
- 168/168 realized outputs preserve Runtime byte parity and semantic fidelity.
- 0 semantic omissions, unsupported additions, unsafe accepted programs, or
  converted refusals.
- All new skill equivalence, deterministic compilation, inverse recovery,
  replay, ablation, invalid-skill, and tamper gates pass.
- Protected hashes and production access count remain unchanged/zero.
- Runtime 5.0 and launcher regression suite passes completely.

The positive umbrella verdict is
`BOUNDED_MULTI_PHASE_LLM_LIKE_OUTPUT_FIDELITY_CONFIRMED`. Any failed required
gate aborts the campaign and prevents that verdict.

## Open questions

None for this run. Multilingual native-speaker scoring, multi-turn conversational
state, open-domain generation, and external blind human evaluation remain future
qualifications rather than being silently simulated here.

