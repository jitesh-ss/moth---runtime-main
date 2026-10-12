# Moth Evidence Reports

This directory contains compact surviving evidence from disposable experiments
and runtime qualification campaigns. Raw stores, fixtures, datasets, caches,
and row-level traces are intentionally not retained here.

Reports describe the exact boundary tested at the time. A passing disposable
extension does not automatically become a capability of a production runtime.

## Report index

| Report | Runtime | Verdict | What it established |
|---|---|---|---|
| [CAPABILITY-LAB-001.md](CAPABILITY-LAB-001.md) | 4.7 | `GO_CAPABILITY_LAB` | The frozen cumulative closed-world capability ladder and held-out campaign passed without tool execution or prime-field mutation. |
| [REAL-MULTIHOP-LAB-001.md](REAL-MULTIHOP-LAB-001.md) | 4.7 | `BOUNDARY_CONFIRMED` | Projected positive linear ProofWriter chains worked; native ProofWriter rule QA remained unsupported. |
| [SUDOKU-LAB-001.md](SUDOKU-LAB-001.md) | Disposable 4.7 extension | `COMPILED_SUDOKU_CONFIRMED` | Structured Sudoku constraints worked only with a disposable generic CSP primitive; prose-only instructions remained unsupported. |
| [SUDOKU-4.8-DISPOSABLE-001.md](SUDOKU-4.8-DISPOSABLE-001.md) | Disposable 4.8 extension | `COMPILED_SUDOKU_CONFIRMED` | Preserved the exact compiled Worlds, prompt, and result for the disposable CSP-backed Sudoku test. |
| [FIELD-ONLY-SUDOKU-4.8-001.md](FIELD-ONLY-SUDOKU-4.8-001.md) | Unmodified 4.8 | `NO_GO_INSTRUCTION_EXECUTION` | Granular instruction meanings remained passive and could not solve Sudoku through field settlement alone. |
| [FIELD-ONLY-DECIMAL-ADDITION-4.8-001.md](FIELD-ONLY-DECIMAL-ADDITION-4.8-001.md) | Unmodified 4.8 | `NO_GO_INSTRUCTION_EXECUTION` | Base-10 truth rows and instruction meanings did not execute addition without an active computation substrate. |
| [RUNTIME-4.9-FACTOR-QUALIFICATION-001.md](RUNTIME-4.9-FACTOR-QUALIFICATION-001.md) | 4.9 | `FACTOR_SETTLEMENT_CONFIRMED` | Generic compiled table factors settled unseen addition, graph-color, and scheduling cases with proof traces and exact replay. |
| [CLOSED-WORLD-META-REASONING-4.9-001.md](CLOSED-WORLD-META-REASONING-4.9-001.md) | 4.9 | `CLOSED_WORLD_META_REASONING_CONFIRMED_WITHIN_FROZEN_FACTOR_BOUNDARY` | Compiled factor programs evaluated and repaired plans inside a frozen closed-world boundary. |
| [REAL-WORLD-PROMPT-BOUNDARY-4.9-001.md](REAL-WORLD-PROMPT-BOUNDARY-4.9-001.md) | 4.9 | `NO_GO_REAL_WORLD_LANGUAGE_GROUNDING` | Controlled factor reasoning remained sound, while ordinary narrative prompts could not yet supply the required typed transient facts. |
| [RUNTIME-5.0-LANGUAGE-FIDELITY-QUALIFICATION-001.md](RUNTIME-5.0-LANGUAGE-FIDELITY-QUALIFICATION-001.md) | 5.0 | `BOUNDED_COMPILED_LANGUAGE_FIDELITY_CONFIRMED` | Compiled paraphrases and multi-clause facts settled through Input to unchanged factor reasoning with safe refusals and exact replay. |
| [Runtime 5.1 HCF conclusion](../experiments/runtime_v5_1_hcf/reports/CONCLUSION-001.md) | 5.1 experiment | `THREE_LEVEL_HCF_SETTLEMENT_CONFIRMED` | Fixed BASE, SYSTEM, CONTEXT precedence, typed delegation, equal same-level authority, and exact HCF trace reconstruction passed a frozen six-case campaign. |
| [RUNTIME-5.1-HCF-QUALIFICATION-001.md](RUNTIME-5.1-HCF-QUALIFICATION-001.md) | 5.1 | `BOUNDED_CONVERSATIONAL_HCF_RUNTIME_CONFIRMED` | The standalone console runtime preserved the 5.0 kernel and added verified HCF, conversations, active context, asset loading, replay, and operational inspection. |
| [Runtime 5.1 compiled artifact qualification](../experiments/runtime_v5_1_compiled_artifact/reports/QUALIFICATION-001.md) | 5.1 artifact | `WEIGHT_FREE_COMPILED_MODEL_ARTIFACT_5_1_CONFIRMED` | The isolated weight-free image passed deterministic build, field/skill fidelity, 168 Surface outputs, 36 inert plans, conversation replay, isolation, and tamper gates. |
| [RUNTIME-5.2-ENERGY-NATIVE-QUALIFICATION-001.md](RUNTIME-5.2-ENERGY-NATIVE-QUALIFICATION-001.md) | 5.2 | `ENERGY_NATIVE_MUTABLE_RUNTIME_5_2_CONFIRMED` | Safetensors-native compiled content, direct-array energy settlement, revisioned mutable SYSTEM/CONTEXT layers, independent packaging, deterministic builds, parity, replay, storage, performance, and tamper gates passed. |
| [RUNTIME-5.3-CONVERSATIONAL-REASONING-001.md](RUNTIME-5.3-CONVERSATIONAL-REASONING-001.md) | 5.3 | `QUALIFIED_CONVERSATIONAL_REASONING_5_3` | Independent package, conversational knowledge, bounded planning, verification, and historical reexecution qualified. |
| [RUNTIME-5.3-CONVERSATION-TRIAL-001.md](RUNTIME-5.3-CONVERSATION-TRIAL-001.md) | Installed base 5.3 | Functional observation | 26 messages across eight conversations demonstrated memory/planning and exposed ordinary-language and causal-explanation gaps. |

## Interpretation order

For the current architecture, read the evidence in this order:

1. Runtime 4.8 field-only failures establish that passive instruction storage
   is insufficient.
2. Runtime 4.9 factor qualification establishes active structured instruction
   execution.
3. The 4.9 meta-reasoning audit establishes transfer within the frozen factor
   model.
4. The real-world prompt audit establishes the remaining language-grounding
   boundary.
5. Runtime 5.0 closes that boundary only for frozen compiled semantic
   contracts; it does not establish unrestricted English understanding.
6. Runtime 5.1 and 5.2 establish conversational authority, compiled packaging,
   and revisioned mutable layers; storing context does not itself establish
   general conversational reasoning.
7. Runtime 5.3 adds persistent assertions and independently checked bounded
   planning. Its post-promotion trial distinguishes these working mechanisms
   from incomplete language coverage and explanation behavior.

The system-wide interpretation and capability claim are defined in
[Mother-Architecture.md](../Mother-Architecture.md).
