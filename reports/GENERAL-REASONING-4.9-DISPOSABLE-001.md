# Runtime 4.9 Disposable General-Reasoning Audit 001

Date: 2026-09-01  
Runtime commit: `80471aa955a32751fd5a97a633759326654664fc`  
Final verdict: **NO_GO_GENERAL_COMPOSITION**

## Question

Can the unmodified Runtime 4.9 factor field combine reusable granular
instructions from several compiled domains and solve a new globally constrained
problem without task-specific runtime code?

## What was compiled

The disposable field contained only generic finite-domain meanings and
allowed-tuple factors for:

- exact finite values and typed domains;
- addition over units 0–30;
- less-than-or-equal comparison;
- candidate selection;
- credential-to-role authorization;
- start time, duration, and completion time;
- cost, budget, and remaining budget;
- logistics, laboratory, and deployment facts;
- one reusable single-stage selection program;
- one three-stage coordinated-mission program;
- three precompiled prompt envelopes and deterministic output instructions.

Runtime opcodes remained limited to `CREATE_VARIABLE`, `INSTANTIATE_FACTOR`,
`BIND_PORT`, `CLAMP_FROM_PROMPT`, `CLAMP_LITERAL`, and `EXPOSE_OUTPUT`.
No planner, search routine, branching implementation, learned reasoner, or
task-specific solver was added.

Compiled source SHA-256:
`499650cd5eb072a461da65523ede84b878c02633981275a8201cb4b6b6210317`

## Decisive prompt

```text
Settle coordinate-mission with context-0 = logistics, task-0 = deliver-sample, credential-0 = road-permit, context-1 = laboratory, task-1 = analyze-specimen, credential-1 = science-badge, context-2 = deployment, task-2 = release-service, credential-2 = deploy-token, mission-start = u00, mission-budget = u18, mission-deadline = u10 using answer-json.
```

An independent post-settlement check enumerated the eight authorized candidate
combinations and found exactly one valid global plan:

```json
{
  "logistics-option": "direct-route",
  "laboratory-option": "microscope-beta",
  "deployment-option": "green-lane",
  "completion": 10,
  "total-cost": 18
}
```

The checker did not generate, guide, repair, or score Runtime 4.9 settlement.

## What happened

- Reusable single-stage cases: **10/10 passed** across logistics, laboratory,
  deployment, arithmetic, deadlines, budgets, and credential selection.
- Coordinated three-domain case: **failed safely**.
- Runtime response: `AMBIGUOUS_SETTLEMENT: fixed point contains non-singleton variables`.
- Valid domain reductions before refusal: **37**.
- Variables still non-singleton: **14**.
- Independently established global solutions: **exactly 1**.
- Runtime execution, dispatch, learning, and network activity: **0**.
- Canonical repository, configurations, production stores, and model assets:
  unchanged during the disposable campaign.

Attempt 001 solved its supported cases but had invalid causal gates because two
supposedly required constraints were redundant and its irrelevant-content case
changed an active domain. It was preserved as a failed panel. Attempt 002
changed fixtures only and produced the decisive settlement result above.

## Meaning

Runtime 4.9 can execute reusable compiled constraints when local tuple-support
propagation is sufficient to force every variable to one value. That is real,
bounded, closed-world compositional computation.

It does **not** yet demonstrate closed-world general reasoning. In the decisive
case, every remaining value had local support in each neighboring factor, even
though only one complete assignment satisfied all factors simultaneously.
Search-free generalized arc consistency could not expose that global fact.

The smallest missing architectural capability is a compiled, proof-carrying
global decision mechanism—for example bounded branching with contradiction
rejection and restoration, stronger consistency, or exact variable
elimination. Merely compiling more instruction names will not fix this limit;
the settlement kernel must be able to execute such global decisions.

## Claim boundary

This result does not invalidate Runtime 4.9's factor-settlement qualification.
It narrows the claim precisely:

> Runtime 4.9 is a sound search-free compiled constraint-propagation runtime,
> but it is not yet a general closed-world reasoning system.
