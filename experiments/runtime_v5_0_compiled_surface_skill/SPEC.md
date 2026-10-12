# Spec: Runtime 5.0 compiled Surface skill

## Objective

Decisively test whether the proven instruction-compression architecture can
compile one ordinary natural-response skill into a policy that realizes
unchanged Runtime 5.0 semantic results as natural prose of an appropriate size.

The candidate must operate only in a disposable Runtime 5.0 instance. It may
select, order, lexicalize, connect, and compress verified facts, but it must not
change a decision, invent support, drop a material fact, weaken a refusal, or
write to any promoted runtime or production store.

The supported target is bounded compiled Surface fidelity over the frozen
four-field plan-decision result. It is not unrestricted language generation or
a claim that deterministic prose is generally equivalent to an LLM.

## Technology and commands

- Python 3.11 standard library plus the existing local Runtime 5.0 package.
- Compile/validate candidate skill:
  `./.venv/bin/python -m experiments.runtime_v5_0_compiled_surface_skill.campaign --compile-only`
- Focused tests:
  `./.venv/bin/python -m pytest experiments/runtime_v5_0_compiled_surface_skill/tests -q`
- Frozen campaign:
  `./.venv/bin/python -m experiments.runtime_v5_0_compiled_surface_skill.campaign`
- Runtime regression:
  `./.venv/bin/python -m pytest tests/test_runtime_v5_0.py tests/test_runtime_v5_0_language.py tests/test_launcher_v5.py -q`
- No network, external model, tool execution, or production-store access.

## Project structure

- `fixtures/surface-base-field-en-1.0.json`: reusable Surface instruction field.
- `fixtures/natural-response/SKILL.md`: ordinary candidate Surface skill.
- `fixtures/natural-response-paraphrase/SKILL.md`: independently worded equivalent skill.
- `fixtures/granular-surface-oracle-1.0.json`: pre-authored policy oracle.
- `fixtures/campaign-en-1.0.json`: semantic prompts, size requests, and hard expectations.
- `fixtures/FREEZE.json`: pre-execution commitments and protected hashes.
- `compiler.py`: bounded skill compiler derived from the proven hierarchy.
- `worlds.py`: reproducible disposable Runtime 5.0 World sources.
- `realizer.py`: policy executor and independent Surface verifier.
- `instance.py`: temporary Runtime 5.0 instance, archive, and replay boundary.
- `campaign.py`: control, instructed, fidelity, size, causal, replay, and isolation gates.
- `tests/`: focused deterministic verification.
- `runs/`: ignored raw output.
- `reports/`: compact result and decisive conclusion.

## Code style

Use immutable records, canonical JSON, typed failure codes, and explicit
semantic commitments:

```python
if realized.semantic_result_hash != expected_semantic_hash:
    raise SurfaceFidelityFailure("Surface response is detached from its result")
```

Skill text and presentation requests are inert data. Neither can introduce a
primitive, execute code, alter a World, grant authority, or rewrite a verified
semantic result.

## Testing strategy

Freeze the field, primary skill, paraphrased skill, granular oracle, complete
campaign panel, and protected hashes before executing the campaign.

The campaign compiles both skills in fresh compiler instances and requires one
canonical policy. It runs the unchanged Runtime 5.0 Surface as a control and
the compiled Surface policy as the instructed candidate over frozen delivery
and deployment prompts. Each accepted semantic result is realized at concise,
standard, and detailed sizes.

Hard fidelity gates:

- input paraphrases with one meaning produce the same structured result;
- every output preserves `proposed-valid`, `backup-valid`, `selected-plan`, and
  `failure-reason` through independently checked textual evidence;
- no output adds a plan, validity, or failure cause absent from the result;
- the semantic-result and compiled-policy hashes are bound into the archive;
- malformed results and unknown presentation requests fail closed;
- Runtime refusals remain refusals and are never converted into prose answers.

Size gates use inclusive word bands:

- concise: 8-24 words and one sentence;
- standard: 25-49 words and two or three sentences;
- detailed: 50-90 words and three to five sentences.

Natural-prose gates require outcome-first ordering, complete sentences,
sentence-final punctuation, no JSON/object syntax, no raw field identifiers,
no headings for these answer shapes, and no repeated sentence. These are
observable proxies for bounded LLM-like Surface quality, not a universal human
preference score.

Causal gates remove the size interpreter, discourse planner, lexicalizer,
semantic coverage verifier, and hash binder independently. Each ablation must
break its dependent case or be rejected. Repeated compilation and realization
must be byte-exact. Archive and response tampering must be detected.

## Boundaries

- Always: use fresh temporary stores and World bundles; compile skill text as
  inert source; preserve Runtime 5.0 results; verify all four semantic fields;
  compare against a pre-authored granular policy; measure size after rendering;
  hash protected paths before and after; retain failed gates honestly.
- Ask first: modify frozen fixtures after execution, change thresholds, add a
  dependency, edit a promoted runtime/configuration/store, or promote any asset.
- Never: edit `src/moth_runtime_v5_0`, `config/v5.0`, `data/store-5.0.sqlite3`,
  prior experiment evidence, or architecture locks; call the network; execute
  generated text; count refusal as understanding; use a quality score to excuse
  semantic drift or a size violation.

## Success criteria

- Primary and paraphrased skills compile to the same canonical policy and match
  the independently frozen granular oracle.
- All hierarchy, malformed-skill, deterministic-compilation, and causal gates pass.
- The unchanged control retains structured output; the candidate emits natural
  prose for every accepted case without modifying the Runtime result.
- All accepted semantic prompts pass at all three sizes with zero semantic
  omissions, zero unsupported additions, and zero size-band violations.
- Every expected Runtime refusal remains byte-identical to the control refusal.
- Candidate archives replay byte-exactly; semantic, policy, size, and response
  tampering are detected.
- Network calls, execution, dispatch, external writes, and production changes are zero.
- The conclusion names the exact supported boundary. Any failed hard gate yields
  a no-go or partial verdict rather than a natural-Surface fidelity claim.

## Open questions

None for this bounded experiment. The user approved the compiled-skill approach,
size as a first-class Surface property, decisive testing, and an isolated
Runtime 5.0 instance on 2026-09-02.

