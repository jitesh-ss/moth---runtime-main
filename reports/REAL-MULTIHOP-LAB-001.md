# Runtime 4.7 Real Multi-Hop Boundary Audit — Attempt 001

Date: 2026-08-30  
Runtime commit: `86e6d3ae4a109204c34ece3547e2e7f2ca7d2c5c`  
Final verdict: **`BOUNDARY_CONFIRMED`**

## Decisive result

This disposable audit tested standalone Runtime 4.7 against official ProofWriter `V2020.12.3` OWA test data at depths 1, 2, 3, and 5.

Two distinct conclusions were evaluated:

- **`PROJECTED_LINEAR_PROOFWRITER`: `SUPPORTED`** — 4.7 correctly executed realistic positive, single-premise, linear ProofWriter proof chains after the complete admissible theory was compiled query-independently into its exact directional edge representation.
- **`NATIVE_PROOFWRITER_RULE_QA`: `UNSUPPORTED`** — 4.7 does not discover premises or rules from a native hypothesis, execute conjunction or branching proof DAGs, handle negation, or produce native True/False/Unknown classifications. It safely refused all tested native-boundary inputs.

The campaign passed **1,104/1,104 primary outcomes**: 64 calibration cases plus 1,040 semantic, causal, invariance, and boundary outcomes. No runtime, field, configuration, model, test, or prime-store file was modified. All disposable data and harness files were deleted after evidence reduction.

## Scope and interpretation

ProofWriter is an actual benchmark, but it is synthetic controlled English. Its native task combines facts, Horn rules, proof DAGs, and three-valued open-world answers. See the [ProofWriter paper](https://aclanthology.org/2021.findings-acl.317/).

This audit did not convert Runtime 4.7 into a native ProofWriter reasoner. It tested a deliberately bounded projection:

1. Parse each theory without reading its questions.
2. Admit only positive, single-premise Horn rules.
3. Materialize the complete admitted theory to a fixpoint.
4. Represent every ground proposition as an `ENTITY`.
5. Represent every grounded rule application as a directional `one-step entailment` edge.
6. Compile all admissible disconnected distractors as well as the proof component.
7. Seal the field before examining questions or gold proofs for deterministic panel selection.
8. Ask 4.7 to advance from a supplied starting proposition for the supplied proof depth.

Consequently, a pass establishes exact execution of compiled realistic chains. It does not establish query-time rule discovery or native QA from a hypothesis alone.

## Isolation and frozen inputs

| Item | Evidence |
|---|---|
| Repository | `/Users/jitesh-ss/work/Moth` |
| Runtime | `4.7` |
| Result schema | `moth-capability-result/4.7` |
| Dataset | Official ProofWriter `V2020.12.3`, OWA test splits only |
| Dataset URL | `https://aristo-data-public.s3.amazonaws.com/proofwriter/proofwriter-dataset-V2020.12.3.zip` |
| Archive SHA-256 | `bbc5694901e8306d0bd659aa1ad53ccfd02c201864f4b320ffa3777827d1fc26` |
| Panel SHA-256 | `2c8c6da4220b84cb5b3bc83be164f09bee7d683704d4194d36b3ea797bf6556b` |
| Adapter SHA-256 | `92068484ab6fda921f7c84194ae18ebdc0e058eb2883b529c8fd2d0e47ffe039` |
| Panel-freezer SHA-256 | `da90014084e520436a643668f0f50477883f19b11017fb37f3738b4459ed5497` |
| Runner SHA-256 | `75afe412a46d26b312d9e9a2f936249a42db4a3e567b131419d5382a36730f56` |
| Harness aggregate | `823bd11002d60e9f95a8c273ef7beae3adfca8db3d946f39a5a4d8c73d0bc83c` |
| BGE fingerprint | `31a5cc0c286db1e4923c37fae33eeab6cb3a6796ea272e9c899d77ae751e2224` |
| BGE asset tree | `89c7567554067f091c4eee99516be0c838d5ba01ebfec67eca03006d6f4d4d0f` (45 files) |

Test split hashes:

- Depth 1: `380bad7c88f5b02ad91b06fbaa4c47a1ea6fe02d6c7841c5bc41f5623a680bab`
- Depth 2: `579016c5b2aa7f4716ca82a40fe15c50bb5c42ddfa345c3fb307aeba9c01b9f7`
- Depth 3: `bec7afffdb4662ce61859acdf397edba12e3ae7bfad1c12ade1629a8bf3b39d6`
- Depth 5: `c09fad796aaf546d6fcbfc77ecf91f935ffed3c936c2b0e96f4aa57211fad842`

No train or development examples were used. Dataset acquisition was the only network-enabled phase; the campaign then ran offline with socket attempts blocked and counted.

## Panel construction and leakage check

Eligibility required a positive question, exactly one official proof, one proof leaf, a linear proof DAG, only positive single-premise rules, no repeated proposition, a unique path in the complete projected field, and exact agreement between an independent evaluator and the official endpoint and rule order.

Eligible cases before deterministic SHA-256 ranking:

| Gold depth | Eligible | Selected |
|---:|---:|---:|
| 1 | 1,520 | 25 |
| 2 | 623 | 25 |
| 3 | 323 | 25 |
| 5 | 60 | 25 |

The 100 selected cases span 100 theories, all four available family groupings (`AttNeg`, `AttNoneg`, `RelNeg`, and `RelNoneg`), 18 subjects, 7 relations, 24 objects, and 90 distinct endpoints.

A supplemental target-leakage audit removed every question, `proofDetails`, and `allProofs` entry from every selected theory and rebuilt the projected fields. All **100/100** rebuilt semantics and generated field sources were byte-identical.

- Leakage audit hash: `aed06e7cd154a51528f907951618bce3cd9cde1d37681215852dca05b4c35921`
- Scrubbed-source aggregate: `d7b281a1dfd28f03747402cc63ec33c4436584ab92d161056bb00aaa6df8b40c`

## Calibration

The frozen Runtime 4.7 thresholds were used without tuning.

| Category | Passed | Total |
|---|---:|---:|
| Supported proposition/instruction paraphrases | 32 | 32 |
| Unsupported lexical near-misses | 16 | 16 |
| Deliberate ambiguity pairs | 16 | 16 |
| **Total** | **64** | **64** |

Calibration status: **`READY`**.

## Projected linear proof results

Each selected case was run through three compiled English envelopes: an explicit start/relation/depth form, a natural proposition-following question, and a frozen instruction paraphrase. All three had to produce the same endpoint, ordered proof, zero-violation energy, and replay result.

| Gold depth | Cases | Prompt outcomes | Passed |
|---:|---:|---:|---:|
| 1 | 25 | 75 | 75 |
| 2 | 25 | 75 | 75 |
| 3 | 25 | 75 | 75 |
| 5 | 25 | 75 | 75 |
| **Total** | **100** | **300** | **300** |

Every passing answer had the official query proposition as its endpoint, zero hard violations, one semantic proof, proof length equal to gold depth, official/runtime rule-order agreement, complete active provenance, and byte-exact encoder-free replay.

## Causal and invariance controls

| Control | Expected behavior | Passed | Total |
|---|---|---:|---:|
| Required-edge removal | `MISSING_PREMISE` | 225 | 225 |
| Middle-edge reversal | `MISSING_PREMISE` | 100 | 100 |
| Destination shuffle | Original endpoint not preserved | 100 | 100 |
| Competing equal-length proof | `AMBIGUOUS_PROOF` | 75 | 75 |
| Disconnected irrelevant content | Endpoint, proof, and energy unchanged | 20 | 20 |
| Reversed source order | Canonical field and result hashes unchanged | 20 | 20 |
| **Total** |  | **540** | **540** |

No corrupted case returned the original endpoint without a valid proof.

## Native ProofWriter boundary

| Native input class | Required refusal | Passed | Total |
|---|---|---:|---:|
| Raw theories containing native rules | `COMPILATION_ERROR` | 40 | 40 |
| Original questions against inert theory text | `UNSUPPORTED_INSTRUCTION` | 40 | 40 |
| Conjunction-dependent proofs | `UNSUPPORTED_PROGRAM` | 40 | 40 |
| Negative or Unknown OWA questions | `UNSUPPORTED_PROGRAM` | 40 | 40 |
| Prompt-supplied new fact or rule | `UNSUPPORTED_INSTRUCTION` | 40 | 40 |
| **Total** |  | **200** | **200** |

Unsafe native answers: **0**. Native inputs produced no inferred edge, field mutation, speculative proof, code execution, or dispatch.

## Representative official-to-runtime mappings

| Depth | Theory / question | Leaf → endpoint | Official rule order | Runtime proof edge IDs |
|---:|---|---|---|---|
| 1 | `RelNoneg-OWA-D1-547` / `Q3` | `The rabbit sees the mouse` → `The rabbit chases the cat.` | `rule2` | `b99c28b7…f44040` |
| 2 | `AttNeg-OWA-D2-1099` / `Q5` | `Harry is cold` → `Harry is quiet` | `rule6`, `rule4` | `179aefe6…d6f35`, `cefd46ba…1ef34` |
| 3 | `RelNoneg-OWA-D3-306` / `Q7` | `The dog is blue` → `The dog chases the tiger` | `rule1`, `rule2`, `rule5` | `2953eac6…150e7`, `ad1f4ce6…c7a3`, `f9749144…39872` |
| 5 | `RelNeg-OWA-D5-404` / `Q11` | `The cow is big` → `The dog sees the dog` | `rule7`, `rule1`, `rule3`, `rule7`, `rule1` | `00d1b3ab…d959`, `3ff38471…b5e`, `4fc5cbde…b2b18`, `d219f203…f34a2`, `eb02b628…35e1` |

The campaign verified 275 unique base proof-edge occurrences and 825 proof-edge occurrences across the three prompt forms, including every provenance owner.

## Integrity, replay, and execution evidence

| Evidence | Value |
|---|---|
| Primary panel row aggregate | `227ff0bbe38c15c723bc2d964b84a33386e73984d75e6b1d0a67266ffe42818f` |
| Field hash aggregate | `97754588439ca2ffd167368ff380bd4c4ca6037700cc46c4628f36205f7161c7` |
| Generation hash aggregate | `f298828377d4444fb9f93e1a14515ba79176f2e937a80e456664a5ca7240cf11` |
| Proof hash aggregate | `762e2a1535199e2ab25d00c059c3c71c8662a89cb38566c231c249f5c7ba024b` |
| Replay hash aggregate | `9cf025e0596555a67de4d0bb4dedfbba45585216076f8243ce1c19acb8a43ba7` |
| Summary hash | `1f979f2eb04858a217dd74b2277bf417dd117671c450e9c0d75ddc4b8fdf49f6` |
| Encoder-free replay | 300/300 byte-exact |
| Runtime execution performed | 0 |
| Tool dispatch count | 0 |
| Network attempts during campaign | 0 |
| Failures retained | 0 |
| Campaign elapsed time | 60.635 seconds |

All 984 primary runtime results and the 300 encoder-free replay results reported `execution.performed=false` and `dispatch_count=0`.

## Preservation and cleanup

Protected input hashes:

- `ARCHITECTURE.md`: `0eba150c51afd20511be4d1e7831856166866c7ad061c157af66d1ab467cf80f`
- `PRODUCT.md`: `4ccfa483a5938ba93f79bd381f9effb445cf72be2bba1a3c59da333a5da7246b`
- `SPEC.md`: `848b27c95657e2e4806f0b0afce7e5d2496d08966c72ae35c5f4bf7d5e8bcea5`
- Tracked Runtime 4.7 source aggregate: `8e533392024dcef95270fc97ee2bc0d1d21cadabcab972e3132fef51a2f0460b`
- Tracked configuration aggregate: `ae3fb3057fa39e9537698c5618415563bf9e66cebc839801b3cc7d819cdaa6d8`
- Prime field: `4bda69217d0e64b398508e206a670dd99f3e64976dc9e7a0aadb5f22e55cd3da`

The complete pre/post preservation manifests were identical:

`e59f1ed8caadda70d59e76df9ef126177ffcee792ba212d9413112f3f30fd6c7`

This covers 32 tracked files, all 45 model files, and the populated prime field. The prime field was never opened and retained its exact 1,601,536-byte payload with no WAL or SHM sidecars.

The temporary dataset, adapter, harness, generated `.moth` sources, SQLite stores, archives, caches, fixtures, and raw ledgers were deleted. The repository contains no disposable audit residue. This report is intentionally the only surviving artifact and remains untracked and uncommitted.

## Limitations

- The projected prompts provide the initial proposition, relation, and depth. Runtime 4.7 does not infer the relevant starting premise from the native hypothesis.
- The adapter performs positive single-premise rule materialization before Runtime 4.7 executes the chain. Runtime 4.7 itself does not discover or apply natural-language Horn rules.
- Conjunction, branching proof DAGs, negation, negation-as-failure, cyclic requirements, and native True/False/Unknown classification remain outside the runtime contract.
- ProofWriter is more linguistically varied than letter/number chains, but it remains synthetic controlled English.
- These results establish safe closed-world chain execution and boundary behavior, not general natural-language reasoning.

## Final verdict

**`BOUNDARY_CONFIRMED`**

Runtime 4.7 reliably executes the tested realistic projected linear ProofWriter chains and preserves exact proof, provenance, energy, causal sensitivity, invariance, and replay properties. It also consistently rejects the native ProofWriter semantics it does not implement. The boundary between supported compiled-chain execution and unsupported native rule QA is therefore both empirically demonstrated and safely enforced in this campaign.
