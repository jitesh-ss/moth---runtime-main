# Full report 001: Runtime 5.0 multi-phase output fidelity

Date: 2026-09-03  
Verdict: **`BOUNDED_MULTI_PHASE_LLM_LIKE_OUTPUT_FIDELITY_CONFIRMED`**  
Scope: **bounded closed-world Surface realization, not open-domain LLM equivalence**

## Executive conclusion

Runtime 5.0 successfully compiled ordinary-language output skills into granular
Surface policies and used those policies to produce natural prose, controlled
length, formal and conversational tone, Markdown structures, mixed prose and
JSON, action plans, strict JSON, inert Python, and executable Python containing
functions and variables.

Across the complete frozen campaign, **168 of 168 outputs** retained byte-exact
Runtime semantics. There were zero detected semantic omissions, unsupported
additions, semantic drift events, unsafe accepted Python programs, or Runtime
refusals converted into answers. All phase archives replayed successfully.

This is decisive evidence that the instruction-compression and language-fidelity
foundation can drive a broad bounded output Surface through compiled skills. It
does not yet establish open-domain generation, native multilingual fluency,
multi-turn conversational memory, or human-indistinguishability from a frontier
LLM.

## Isolation and protection

The campaign did not modify or run candidates against the production Runtime
store. Each phase created independent Runtime 5.0 stores under temporary
directories, compared candidate Runtime bytes with an isolated control, and
removed the temporary roots afterward.

The following were hashed before the campaign and verified afterward:

- `src/moth_runtime_v5_0`
- `src/moth_launcher_v5`
- `config/v5.0`
- `data/store-5.0.sqlite3`
- `docs/v5.0`
- the Runtime 5.0 language-fidelity qualification
- instruction-compression and all three predecessor Surface experiments

Every protected hash remained unchanged. Production-store access count was
zero. No network calls or model dispatches were performed.

## Skill architecture

The full campaign covered seven compiled skill families and fourteen independently
worded source-skill variants. Each primary/paraphrased pair reduced to the same
granular policy.

Existing frozen skill families:

1. Natural Surface realization with size control.
2. JSON and inert-Python serialization.
3. Executable Python functions and variables.

New skill families:

4. `prose-range`: compact and detailed natural prose.
5. `tone-adaptation`: formal and conversational prose.
6. `markdown-structure`: bullet lists and Markdown tables.
7. `mixed-response`: explanation-plus-JSON and action plans.

The four new families compiled through a field containing ten atomic actions,
eight policy conditions, six workflow macros, twelve interpretation rules, and
four skill profiles. Forty repeated new-family compilations were deterministic;
the full cross-phase total was seventy deterministic compilation trials.

## Phase results

| Phase | Modes | Outputs | Runtime parity | Semantic gate | Verdict |
|---|---:|---:|---:|---:|---|
| Natural prose and size | 3 effective size modes | 48 | 48/48 | 0 omissions/additions | Confirmed |
| Rich prose/structure/mixed | 8 modes | 64 | 64/64 | 64/64 inverse recovery | Confirmed |
| JSON and inert Python | 4 format/layout forms | 40 | 40/40 | 40/40 parsed exact | Confirmed |
| Executable Python | 1 bounded program form | 16 | 16/16 | 16/16 executed exact | Confirmed |
| **Total** | **16 modes** | **168** | **168/168** | **0 drift** | **Confirmed** |

### Phase 1: natural prose and size

The frozen natural-Surface campaign produced 48 responses over eight semantic
cases and six request phrasings. Concise responses contained 16–20 words,
standard responses 27–30 words, and detailed responses 55–64 words. All size
bands passed; no required claim disappeared and no unsupported claim appeared.

### Phase 2: new rich outputs

The new phase generated 64 outputs: eight semantic cases across eight modes.
Each semantic case produced eight distinct response texts. Every output was
inverted back into exactly one four-field Runtime decision before acceptance.

| Mode | Outputs | Lines | Word range | Byte range |
|---|---:|---:|---:|---:|
| Compact prose | 8 | 1 | 19–20 | 108–114 |
| Detailed prose | 8 | 11 | 32–33 | 212–227 |
| Formal tone | 8 | 1 | 26–27 | 158–164 |
| Conversational tone | 8 | 1 | 21–22 | 113–119 |
| Markdown bullets | 8 | 4 | 11 | 88–94 |
| Markdown table | 8 | 6 | 13 | 128–134 |
| Explanation plus JSON | 8 | 10 | 17–18 | 188–194 |
| Action plan | 8 | 4 | 26 | 145–151 |

The phase produced 56 distinct artifact hashes. The repeated delivery
paraphrase intentionally converged to the same semantic graph and therefore the
same outputs; this explains why the count is lower than 64 without indicating a
diversity failure.

### Phase 3: structured data

The structured phase produced 24 JSON artifacts and 16 inert-Python artifacts.
Compact and readable layouts were independently parsed. All 40 recovered exactly
the Runtime value, with no schema, layout, or Python-safety violation.

### Phase 4: executable Python

Sixteen generated programs contained three functions, four module variables,
local variables, branching, a final function call, and a printed decision. All
programs passed the 107-node AST contract and computed the exact Runtime value.
Generation and replay verification performed 48 successful positive executions.

Execution remained a constrained local subprocess using deterministic source,
AST capability exclusion, isolated Python flags, a minimal environment, resource
limits, a timeout, and disposable working directories. Docker was unavailable,
so this is not claimed as hardened container isolation.

## Refusal and language fidelity

- Natural phase: 2/2 refusal cases preserved byte-for-byte.
- Rich phase: 8/8 family-specific refusal checks preserved byte-for-byte.
- Structured phase: 2/2 refusals preserved.
- Executable phase: 2/2 refusals preserved.
- Equivalent input paraphrases converged to the same semantic graph.
- Unsupported presentation requests and malformed results failed closed in
  every applicable family.

## Adversarial and causal evidence

The complete campaign passed **92 adversarial gates**:

- Natural Surface: 3 invalid skills, 5 causal ablations, 5 tamper probes.
- Rich Surface: 16 invalid skills, 20 causal ablations, 6 tamper probes.
- Structured Surface: 3 invalid skills, 6 causal ablations, 6 tamper probes.
- Executable Python: 4 invalid skills, 5 unsafe-program probes, 7 causal
  ablations, and 6 tamper probes.

The new skills rejected fact invention, network research, self-modification, and
missing semantic-preservation instructions. Removing route selection, discourse
planning, fact realization, inverse recovery, or hash binding prevented output.

## Test results

- Mega-campaign suite: **8 passed, 0 failed**.
- Runtime 5.0 and launcher regressions: **54 passed, 0 failed**.
- Repository-wide baseline: **150 passed, 1 failed**.

The repository-wide failure is a pre-existing Runtime 4.8 architecture-lock
mismatch in `tests/test_runtime_v4_8.py`. Expected document hash
`1ed5fc85...` differs from actual `0b1b1531...`. Runtime 4.8 is outside this
experiment and was not changed.

## What is now established

Within the frozen Runtime 5.0 decision domain, compiled skills demonstrably
control:

- natural sentence construction;
- concise, standard, and detailed size bands;
- formal versus conversational tone;
- multi-section discourse;
- bullet lists and Markdown tables;
- mixed prose and machine-readable JSON;
- action-plan sequencing;
- strict JSON and inert Python serialization;
- bounded executable Python with functions and variables;
- semantic preservation, refusal preservation, replay, and tamper detection.

## What remains unestablished

The positive verdict must not be generalized beyond the evidence. This campaign
does not establish:

- open-domain generation from arbitrary knowledge;
- genuinely novel program architectures beyond the bounded Python contract;
- long-form documents spanning many pages;
- native-quality multilingual generation;
- persistent multi-turn conversation and correction;
- calibrated uncertainty over incomplete open-world knowledge;
- citation grounding against external sources;
- blind human indistinguishability from a general-purpose LLM;
- hardened execution of arbitrary untrusted code.

Those require separate frozen qualifications, not broader claims from this run.

## Final decision

The Runtime 5.0 Surface architecture is ready for the next research stage. The
mechanism is no longer limited to a single text template or data serializer:
multiple independently authored skills compile into stable policies and control
meaning-preserving output across prose, size, tone, structure, mixed formats,
and bounded code.

Promotion is not implied. The current evidence remains an isolated experimental
qualification until a separate promotion request creates a versioned
qualification record, architecture lock, regression contract, and canonical
field update.

