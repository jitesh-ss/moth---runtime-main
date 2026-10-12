# Runtime 4.9 Disposable Closed-World Meta-Reasoning Audit 001

Date: 2026-08-31  
Runtime: standalone Moth 4.9 from `/Users/jitesh-ss/work/Moth`  
Execution environment: disposable temporary Worlds and SQLite stores  
Final verdict: **CLOSED_WORLD_META_REASONING_CONFIRMED_WITHIN_FROZEN_FACTOR_BOUNDARY**

## Decisive conclusion

The unmodified Runtime 4.9 successfully evaluated proposed plans, diagnosed the
first failed assumption, selected a uniquely valid repair, and verified proof
completeness through one static energy settlement.

This confirms constrained meta-reasoning inside the current 4.9 factor model.
It does not establish adaptive reflection, branching search, arbitrary plan
topologies, broad natural-language understanding, or unrestricted general
reasoning.

## Isolation

The campaign used:

- temporary Input, Main, and Surface Worlds;
- temporary Runtime 4.9 stores;
- temporary fixtures, source, harness, caches, and episode evidence;
- the existing Runtime 4.9 implementation without modifications;
- exact compiled instruction envelopes and the deterministic test encoder;
- no LLM, planner, optimizer, external solver, tool dispatcher, or network.

The temporary assets were deleted after evidence reduction. The production
stores were never opened by the harness and retained these SHA-256 hashes:

```text
Runtime 4.7: 4bda69217d0e64b398508e206a670dd99f3e64976dc9e7a0aadb5f22e55cd3da
Runtime 4.8: b8695b7c59e8830b184f4d23eb76ea00273e272c573af309e141200bf4872334
Runtime 4.9: 3dbe7b143ea1e6a77cbd983759d4fc8c3d50c4bf08395f983476972f7f07e0e4
```

## Exactly what was compiled

One fixed reusable reasoning World was compiled before running the panel.

### Values and domains

- Boolean values: `false`, `true`.
- Plan values: `plan-alpha`, `plan-beta`, `plan-gamma`.
- Failure values: permission, route, inventory, time, safety, and no failure.
- Fifteen transient requirement bindings: five requirements for each plan.
- One transient proposed-plan binding.

The five requirement dimensions were:

1. permission;
2. route availability;
3. inventory availability;
4. deadline feasibility;
5. safety compliance.

### Generic compiled factor templates

1. `and-two`: conjunction through an allowed truth table.
2. `diagnose-first-failure`: maps five requirement states to the first failed
   assumption using the frozen precedence above.
3. `select-valid`: supports every currently valid plan; zero valid plans is a
   contradiction and multiple valid plans preserve ambiguity.
4. `proposed-valid`: evaluates whether the transient proposed plan is valid.
5. `choose-reason`: selects the diagnosis belonging to the proposed plan.
6. `proof-complete`: returns true only when exactly one selected plan is
   supported.

### Compiled factor program

The program contained 148 field-construction instructions using only Runtime
4.9's existing generic opcodes:

```text
CREATE_VARIABLE
INSTANTIATE_FACTOR
BIND_PORT
CLAMP_FROM_PROMPT
EXPOSE_OUTPUT
```

It created 35 transient variables and 19 factor instances:

- 12 conjunction factors;
- 3 diagnosis factors;
- 1 valid-plan selection factor;
- 1 proposed-plan validity factor;
- 1 diagnosis-selection factor;
- 1 proof-completeness factor.

It exposed five outputs:

```text
selected-plan
proposed-valid
failed-assumption
repair-plan
proof-complete
```

No scenario, complete output, target combination, expected diagnosis, or
expected repair was compiled into the Worlds.

Compiled source SHA-256:

```text
3901b3cb450f5fa9c8178ad3d6fddb5dd367975c3d1088ea71c05d9649ebf1bb
```

## Frozen campaign

Panel SHA-256:

```text
06b22e18d494f77abb34786712704132bdac1ea92696ac4af5b6f81927266b8b
```

The panel contained 100 unseen arrangements:

| Category | Passed | Total |
|---|---:|---:|
| Already-valid proposed plans | 20 | 20 |
| Invalid plans with one uniquely valid repair | 60 | 60 |
| No valid plan | 10 | 10 |
| Multiple valid plans | 10 | 10 |
| **Main panel** | **100** | **100** |

Additional controls:

| Control | Passed | Total |
|---|---:|---:|
| Compiled alternate instruction envelope | 20 | 20 |
| Causal removal by invalidating the selected plan | 60 | 60 |
| Prompt-supplied rule/instruction injection refusal | 1 | 1 |
| Diagnosis-factor removal prevents an answer | 1 | 1 |
| Store and archived-episode integrity | 1 | 1 |

All 80 answer-producing episodes replayed byte-exactly without an encoder. The
store-level verifier also reconstructed successful prefixes and refusal
episodes.

Expected refusal behavior was observed:

- no valid plan: `UNSATISFIABLE`;
- multiple valid plans: `AMBIGUOUS_SETTLEMENT`;
- appended prompt instruction: typed refusal (`UNSUPPORTED_OUTPUT`);
- removed diagnosis construction: `AMBIGUOUS_SETTLEMENT`.

## Exact sample prompt

```text
Evaluate meta-plan-repair with plan-alpha-permission = true, plan-alpha-route = true, plan-alpha-inventory = true, plan-alpha-time = true, plan-alpha-safety = true, plan-beta-permission = true, plan-beta-route = false, plan-beta-inventory = true, plan-beta-time = true, plan-beta-safety = true, plan-gamma-permission = true, plan-gamma-route = true, plan-gamma-inventory = false, plan-gamma-time = true, plan-gamma-safety = true, proposed-plan = plan-beta using answer-json.
```

## Exact sample response

```json
{
  "failed-assumption": "ROUTE_FAILURE",
  "proof-complete": "true",
  "proposed-valid": "false",
  "repair-plan": "PLAN_ALPHA",
  "selected-plan": "PLAN_ALPHA"
}
```

Sample settlement evidence:

```json
{
  "energy": {
    "ambiguity_units": 0,
    "multiplier": 54,
    "total_units": 0,
    "violation_count": 0
  },
  "domain_reductions": 19,
  "factor_witnesses": 19,
  "trace_hash": "4aae581fefd3f51cab3b4017c3eaa0629bba14ff7b4dc3cdcc8008d9fe65090f",
  "execution_performed": false,
  "dispatch_count": 0
}
```

## Where the computation occurred

1. Pre-World grounding selected the compiled instruction, factor program,
   schema fields, plans, and Boolean values.
2. Input World verified the identifier-only request.
3. Main World executed the 148 compiled construction instructions and created
   the transient factor network.
4. The unchanged Runtime 4.9 allowed-tuple narrowing law eliminated unsupported
   values until all required variables were singleton—or produced an explicit
   contradiction/ambiguity.
5. The independent verifier reconstructed materialization, reductions, factor
   witnesses, energy, provenance, and generation identity.
6. Surface World returned only the verified semantic value.
7. Encoder-free replay reproduced the canonical result bytes.

The harness generated held-out arrangements and checked expected outcomes only
after settlement. It did not create, guide, score, repair, or search candidate
states during settlement.

## Attempt history

Attempt 001 achieved the same 100/100 semantic, 20/20 envelope, and 60/60 causal
results but was provisionally labelled `NO_GO` because the injection gate
required `UNSUPPORTED_INSTRUCTION` specifically. Runtime 4.9 safely refused it
as `UNSUPPORTED_OUTPUT`. Attempt 002 changed only that reporting gate to accept
any typed refusal; no World, factor, case, runtime, or expected semantic result
was changed.

Disposable bundle and World commitments:

```text
Bundle: f447f12545c486e3a1d631b9b21206290e0ab8e04f4d01b3cb75a42a7a30a0d6
Input:  a694e88f6e3ebd933b2dcf5c23dcfd644c18e90fbc0ec44323dd5d5865df5960
Main:   94b5432e20b69f61d35bb935c648e51f3db5975f606be7c887508dca67fea674
Surface:30a1bb4b2d5f612911ce3911ccf98d1d5244f0a62a6c96a1091a788df79884ec
```

## What this result means

This experiment demonstrates that Runtime 4.9 can perform one-settlement,
closed-world meta-reasoning over a frozen factor program:

- evaluate a proposed answer;
- diagnose its failed compiled premise;
- select a uniquely forced alternative;
- establish proof completeness;
- refuse contradiction and ambiguity rather than guess.

It is meaningful transfer beyond arithmetic because no change was made to the
factor kernel. Nevertheless, this panel used one fixed three-plan/five-condition
topology and exact compiled language envelopes. It therefore does **not** prove:

- arbitrary closed-world general reasoning;
- novel program synthesis;
- natural-language fidelity comparable to an LLM;
- adaptive strategy invention;
- recursive reflection;
- hypothetical branching, restoration, or backtracking;
- reliable planning when local narrowing does not force a singleton state.

The precise supported claim is:

> Runtime 4.9 is a reliable closed-world factor-reasoning substrate for frozen,
> propagation-complete programs, including explicit evaluation and repair of a
> proposed reasoning result.
