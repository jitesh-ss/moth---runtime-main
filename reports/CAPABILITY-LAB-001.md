# Runtime 4.7 Disposable Capability Lab — Attempt 001

Date: 2026-08-29  
Runtime commit: `6f635dbe4c71342fc8bebfad872e27b9af074596`  
Verdict: **`GO_CAPABILITY_LAB`**

## Conclusion

Standalone Runtime 4.7 passed the frozen cumulative capability ladder and the complete held-out campaign without modifying the runtime, its configuration, model assets, existing tests, or the populated local prime field.

- Calibration: `READY` at L0–L8.
- Quick gates: **1,688/1,688**.
- Held-out campaign: **2,400/2,400**.
- Supplemental closed-world reconstruction audit: **2,400/2,400**.
- Solver/exhaustive parity: **10/10** small fields in L6 and **10/10** in the full campaign.
- Failure examples: none.
- Runtime execution, patch application, and tool dispatch: zero.
- Network connection attempts: zero.
- Encoder-free replay: byte-exact.
- Pre/post preservation manifests: byte-identical.
- Disposable lab directory: deleted after evidence reduction.

This verdict establishes conformance for the frozen compiled corpus and panels. It does not make Runtime 4.7 open-world, generative, or authorized to execute tools or apply patches.

## Isolation protocol

The campaign ran from a temporary OS directory outside this repository. The harness explicitly selected `/Users/jitesh-ss/work/Moth/src/moth_runtime`; the old repository implementation was absent from imported modules. Python bytecode, Hugging Face state, temporary files, SQLite stores, archives, fixtures, and raw rows were redirected into the temporary directory. Hugging Face and Transformers offline modes were enabled, and socket connection functions were blocked and counted.

The campaign never opened the prime `data/store-4.7.sqlite3`. A separate disposable SQLite store was compiled, queried, verified, and replayed under the temporary directory. After preservation checks, that directory and all of its contents were deleted. No harness, fixture, store, archive, cache, or raw ledger was retained in this repository.

## Frozen identities and hashes

| Asset | SHA-256 |
|---|---|
| `ARCHITECTURE.md` | `0eba150c51afd20511be4d1e7831856166866c7ad061c157af66d1ab467cf80f` |
| `PRODUCT.md` | `4ccfa483a5938ba93f79bd381f9effb445cf72be2bba1a3c59da333a5da7246b` |
| `SPEC.md` | `848b27c95657e2e4806f0b0afce7e5d2496d08966c72ae35c5f4bf7d5e8bcea5` |
| Runtime source tree, 15 files | `2ed3869091899a5ffc49f1a371b385c5f75f8f40d6e4f2fdfcb8fb579a2c5615` |
| Configuration tree, 3 files | `7dba18eaa26b9c4ba1e57ca569e63fdc9e7a6a0459cce86dfdea14a1c9a87663` |
| Encoder manifest | `fb89845443c91d8337538cb5fc63ad27a02613b8460813087c121c7c002749f3` |
| Disposable campaign/fixture tree | `e2cbb6b8678af8923a4d4a4020b8c81bd024426357aed38f11a957eec26ce194` |
| Disposable runner | `370a02120f926cf4f183a6e954c077dec14cb1713d34969dba0bb0268b6d1871` |
| Preservation script | `b5bc0aacaf399bd59ab479a6d905f63dbe9e5e5e502e33e6fd44ea4a5f5540b1` |
| Combined disposable-harness manifest | `3f3ead1340df96e34669871a749f0e8bf192b20633749766347a03824e1d03bf` |
| Campaign-and-proof reduced summary before the supplemental audit | `9f7c6a302d0dd2e9bab8cb91f02a60a24e779b76c6271a1dc4cb75771c53fa2e` |

The copied local BGE encoder verified at 1,024 dimensions with fingerprint `31a5cc0c286db1e4923c37fae33eeab6cb3a6796ea272e9c899d77ae751e2224`. Its 45-file asset-tree hash was `89c7567554067f091c4eee99516be0c838d5ba01ebfec67eca03006d6f4d4d0f`.

## Frozen panel hashes

| Panel | Cases | SHA-256 |
|---|---:|---|
| L0 | 60 | `481fa54749b53a389a2052960e35fccbdf46f44b1b36b8e92d80a19e9ee4245d` |
| L1 | 160 | `895b66404243f37f423eccffffb003e172839fb414475a0413dc39df1bbb292c` |
| L2 | 180 | `9861ac0bedf590265ae83d1304e5c3378b9c4420326a928c64a421fde36e4419` |
| L3 | 196 | `3c69cc603cd8b9e96cbb648c9d60bbedfd1c383831060ca261fdb520a92ae969` |
| L4 | 180 | `d49eba478be35376efd0d8f037938068da13b508ddf96c5e7f76abea674651ff` |
| L5 | 240 | `3ffaec246f1ccf25394153c5d6a4aabf8c4742a43a743150accb3c3a905555cf` |
| L6 | 192 | `a8bd748a23a3e3560537bba83f458307886fe92da4d93e5b9af066b80e61a949` |
| L7 | 240 | `744762a32dfc41f847bdc15f8363ba311a30c7a634265503e9f7b41e3f507c1e` |
| L8 | 240 | `26fb602e9ee01e3277edbc60418089e68acafb17a62c07123360ec57608ca9c9` |
| Full | 2,400 | `fe86a446ed61402af9d29568ca748fcae9758014e5df6efb96f2894f8f6a2523` |

## Calibration

Calibration was diagnostic only. It used the frozen Runtime 4.7 thresholds and did not alter configuration. Every level evaluated 32 supported positives and 32 unsupported or ambiguity negatives.

| Level | Status | Positive checks | Unsafe negatives |
|---|---|---:|---:|
| L0 | `READY` | 32/32 | 0 |
| L1 | `READY` | 32/32 | 0 |
| L2 | `READY` | 32/32 | 0 |
| L3 | `READY` | 32/32 | 0 |
| L4 | `READY` | 32/32 | 0 |
| L5 | `READY` | 32/32 | 0 |
| L6 | `READY` | 32/32 | 0 |
| L7 | `READY` | 32/32 | 0 |
| L8 | `READY` | 32/32 | 0 |

## Sequential quick gates

| Level | Capability boundary | Result | Field hash | Generation hash |
|---|---|---:|---|---|
| L0 | Independent 4.7 parity | 60/60 | `dfbc2c458b11847cbbd4c45c23118f869ee3dc95e0c80bc91725766d5278e695` | `2a84843c4b78e120c4c684fdf0751882716746eec287b47781354123b98ddfd5` |
| L1 | Grounding breadth | 160/160 | `d778ebc5e1916a0dc65846654bc89a8902788e8cbf5c925148e046fc5ce6f7a5` | `b975b5355dcf15e4e3e49a4a13e825bccf75382077f40d21445f9f898939ce04` |
| L2 | Depth and causal preservation | 180/180 | `de29c343efcfc7142d4c8b6a58b82d5ae07b09deead6b0dae1cffb4b4f351445` | `5e132e3181a966ae68e352d1938ef7c05a9c4b8a0f4c49c6157b32ea983ad2e2` |
| L3 | Mixed-relation composition | 196/196 | `8af70e073985f81390486cd1e734cea6933e02335b881d29305cf5e04f4188da` | `895bc276c34cb48850728b3e6f11de24b10826d30a03b44f56afe90fdfded6b1` |
| L4 | Typed structured values | 180/180 | `3f4af577383774b2dbf2c64ffad3fc5d28db4ab532cb4629da871fb3da34e7de` | `d160a80f6be1df5b19edb74f4378466a5f36ee0e1307df56ee01f5f93e0339cb` |
| L5 | General compiled JSON | 240/240 | `682b1d8a9e0e0498da4796238137ecaf52674a4a74b69678e42fa79b32790f27` | `3ea0d20bb2f7e7854b11796a32660ac8182df3a70306e2ae498fc895021bf2ba` |
| L6 | Linear compiled programs | 192/192 | `6efbaa6d28493892d37181762f92c62a1a33ae22057d2224ab99187892f586ff` | `6e39fdee7c1ea02aa7c0bd7c1750ff18d53d5c71a41b0f9113b65fb817c4f430` |
| L7 | Python provenance and inert patch plans | 240/240 | `21326c14f406d90e139f8d9c0cdf6fab97d46ce40f181216fd67b5cd6d4e09e4` | `6d2744ea5d6fa6ced326ff7106fce534e70f3c0f7484dcd782cdd30894b14b78` |
| L8 | Inert tool-call-shaped JSON | 240/240 | `b305d8e48581f4ed1fcf1f42216841dcc1c33cc756b0afd2faba5de280acffc8` | `df1970800cdde3d06a779a35fe55b5a1b9f4edbde68a92371508e644ec80652a` |

L2 included all 152 required causal controls: premise removal, operator removal, provenance corruption, direction reversal, destination shuffling, competing proofs, irrelevant content, source order, schema removal, operation mismatch, and prompt assertions. L6 matched exhaustive enumeration on all ten depth-0–4 Route and Relay fields.

## Full held-out campaign

| Category | Passed | Total |
|---|---:|---:|
| Supported exact prompts | 480 | 480 |
| Supported paraphrases | 480 | 480 |
| Causal and integrity controls | 480 | 480 |
| Unsupported, ambiguous, and adversarial prompts | 480 | 480 |
| Source-order and irrelevant-content invariance | 240 | 240 |
| Replay, store, Python, patch-plan, and inert-tool JSON | 240 | 240 |
| **Total** | **2,400** | **2,400** |

The main L8 field hash was `b305d8e48581f4ed1fcf1f42216841dcc1c33cc756b0afd2faba5de280acffc8`; generation hash `df1970800cdde3d06a779a35fe55b5a1b9f4edbde68a92371508e644ec80652a`; archive hash `aa8d370bbbee72908c0beb7e8774fa0eb98f3aee7bb1aa32ac78ae92e3ad95d3`; and the ordered full-result hash aggregate was `d89274167f897cd03704640032ccc3f8640dd01753793974761f2ebda0d01b8c`.

The independent closed-world reconstruction audit re-evaluated all 2,400 cases encoder-free. It observed 1,440 answers and 960 refusals. The answers comprised 1,280 compiled entity or code-symbol results, 80 compiled JSON values reconstructed from exact field/value meaning IDs, and 80 patch plans reconstructed from compiled file, span, operation, and replacement-fragment meanings. Its audit hash was `4529986f819189f0e3b3617042b979c4fc0c33bf1b9b5a321d133aae01e31a2b`; the audit result aggregate was `25b5fe8d8099a6ab7f4b5f305dc9d1b38c51b7311c37824051671a8d65445a88`.

## Proof, energy, replay, and invariance receipts

Two independent encoder-free depth-50 receipts verified exact zero-energy unique proofs:

| Family | Endpoint | Edges | Owners | Energy `(total, violations, grounding)` | Proof hash |
|---|---|---:|---:|---|---|
| Route | `Route-50` | 50 | 50 | `(0, 0, 0)` | `590f4bb806135541737bfa8dee57ae9142669481637cf8aaea48e7dc63fad467` |
| Relay | `Relay-50` | 50 | 50 | `(0, 0, 0)` | `e3d029fa50e9d8970d208c11394e44205fd68f1c7ac851487160c4541cefb0d6` |

The combined proof-receipt hash was `a1d6762df2b3c19257a05a15f272c548bd4e893437107f22f508d224a8f3229a`.

Archive reconstruction produced byte-identical encoder-free output with result hash `61c310aeb65ed0b756fe42c99f3a5692c68f98343d22d33aab37ca8e6d4ddbdb`. The independent disposable SQLite store reported `integrity=ok`, one generation, and one episode; stored and replayed bytes both hashed to `2eed6d493eb2f42782e370dee93a797b2b6b599740d4fc79ebb54130b5204fad`.

Full-campaign invariance passed. The baseline field hash was `b305d8e48581f4ed1fcf1f42216841dcc1c33cc756b0afd2faba5de280acffc8`. Adding irrelevant content produced `4ce7ad13d9f481c7cf4c468465b228ba7992d88ee877df068aed5656da19583e`; reversing source input order produced the identical hash `4ce7ad13d9f481c7cf4c468465b228ba7992d88ee877df068aed5656da19583e`. Both variants preserved the expected semantic result, energy, and proof-edge sequence.

## Safety and preservation

All 4,088 primary quick/full results reported:

```json
{"execution":{"dispatch_count":0,"performed":false}}
```

The supplemental 2,400-case audit observed the same zero-execution state. No Python was imported or executed from the compiled fixture, no patch was applied, no tool was dispatched, and no network connection was attempted. The compiled Python fixture remained byte-identical.

Before and after the complete run:

- Git `HEAD` remained `6f635dbe4c71342fc8bebfad872e27b9af074596` and status remained clean.
- All 31 tracked files matched byte-for-byte.
- All 45 model files matched byte-for-byte.
- The prime field remained 1,601,536 bytes with SHA-256 `4bda69217d0e64b398508e206a670dd99f3e64976dc9e7a0aadb5f22e55cd3da`.
- No prime-field WAL or SHM sidecar appeared.
- Pre- and post-run preservation manifests were identical, both SHA-256 `89de48e5c8aafff32a3693818707d0e7aeeba56ca76f1f0c5c8768b24abd563f`.
- The temporary lab directory was removed and a repository scan found no campaign harness, fixture, store, archive, cache, summary, or raw-ledger residue.

The gated campaign elapsed time was 180.362846 seconds. The independent closed-world audit added 0.791391 seconds.

## Final verdict

**`GO_CAPABILITY_LAB`**

Runtime 4.7 behaved as the closed-world, proof-carrying compiled field described by the tested product boundary: supported compiled meanings composed deterministically; unsupported meanings refused; direction, causal premises, provenance, types, schemas, code spans, patch assets, and tool-shaped JSON remained exact and verifiable; replay required no encoder; and every potentially effectful output remained inert.
