# Spec: Runtime 5.0 instruction-compression hierarchy

## Objective

Decisively test whether one reusable compiled base field can turn ordinary,
high-quality LLM agent skills into granular Moth-style instruction programs
without changing their intention.

The experiment evaluates six dependent levels:

1. atomic actions and states;
2. control, policy, prerequisites, and completion semantics;
3. reusable workflow expansion;
4. natural skill-document interpretation;
5. single-skill intention fidelity;
6. deterministic multi-skill composition.

The primary claim is bounded: within the frozen instruction language, a plain
skill and a held-out paraphrase must compile to the same canonical policy as a
manually frozen granular oracle and must behave identically on a frozen task
panel. This does not claim arbitrary skill understanding or production
promotion.

## Technology and commands

- Python 3.11 standard library only.
- Build/compile: `./.venv/bin/python -m experiments.runtime_v5_0_instruction_compression.campaign`
- Test: `./.venv/bin/python -m pytest experiments/runtime_v5_0_instruction_compression/tests -q`
- No network, model, production runtime, launcher, or production store access.

## Project structure

- `fixtures/base-field-en-1.0.json`: manually granular root-of-trust field.
- `fixtures/safe-text-patch/SKILL.md`: primary ordinary agent skill.
- `fixtures/safe-text-patch-paraphrase/SKILL.md`: held-out equivalent wording.
- `fixtures/evidence-ledger/SKILL.md`: independently compiled composable skill.
- `fixtures/granular-oracle-1.0.json`: frozen single and composite policy oracle.
- `fixtures/campaign-1.0.json`: frozen task and adversarial panels.
- `fixtures/FREEZE.json`: pre-execution fixture commitments.
- `model.py`, `compiler.py`, `instance.py`: independent experimental instance.
- `campaign.py`: hierarchy gates, behavior comparison, replay, and isolation.
- `tests/`: deterministic regression tests.
- `runs/`: ignored raw output only.
- `reports/`: compact result and decisive conclusion.

## Code style

Use immutable records, canonical JSON, typed failures, and explicit invariants:

```python
if observed_policy != frozen_oracle:
    raise FidelityFailure("compiled policy differs from granular oracle")
```

Incoming skill text is inert source data. It cannot execute, add primitives,
change the compiler, or grant authority.

## Testing strategy

The base field and all input fixtures are frozen before campaign execution.
The campaign compiles the primary skill, a sentence-level paraphrase, and a
separate evidence skill in fresh temporary instances. It compares canonical
policy graphs with manually authored oracles, executes the compiled and oracle
policies on independent copies of every task workspace, and requires byte-exact
result and final-workspace equality.

Hierarchy gates:

- L1: every emitted action/state resolves to a declared primitive.
- L2: sequence, prohibition, authority, refusal, and completion constraints
  resolve with no dangling dependency or priority inversion.
- L3: workflow macros expand to the frozen granular graph and achieve at least
  2.0x instruction expansion from normative skill clauses.
- L4: the primary skill and held-out paraphrase compile to one semantic policy.
- L5: compiled and oracle single-skill behavior match on every task.
- L6: the evidence skill composes deterministically with the primary skill and
  matches the frozen composite oracle and task behavior.

Safety, integrity, and causal gates cover malformed/ambiguous/conflicting skill
documents, unsafe tasks, repeated deterministic compilation, archive replay,
tampering, subsystem ablation, temporary-instance isolation, and protected
production hashes.

## Boundaries

- Always: compile into a fresh temporary instance; preserve clause provenance;
  fail closed; compare against a pre-authored oracle; test each hierarchy level;
  verify replay and protected hashes.
- Ask first: change the frozen claim, add dependencies, modify a production
  runtime/configuration/store, or promote any mechanism.
- Never: import production runtime code, execute incoming skill text directly,
  infer an undeclared primitive, weaken a prohibition, use the network, rewrite
  a failed case after execution, or describe safe refusal as understanding.

## Success criteria

- All six hierarchy gates pass independently.
- Primary and paraphrased skills produce the same canonical semantic policy.
- Single-skill and composite policies exactly match their granular oracles.
- Compiled and oracle instances have identical decisions, traces, reports, and
  final workspace bytes across the frozen panel.
- Every expected refusal or authority request occurs with its frozen code.
- Unsafe acceptance is zero.
- Every required subsystem has a successful causal ablation.
- Repeated compilation and replay are byte-exact; tampering is detected.
- Instruction expansion is at least 2.0x.
- Network, execution outside temporary workspaces, and dispatch are zero.
- Protected production hashes remain unchanged.

If any gate fails, the result must name the exact fidelity boundary and must not
claim instruction fidelity.

## Open questions

None for this bounded experiment. The user approved the hierarchical base-field
approach, isolated execution, and decisive testing on 2026-09-02.

