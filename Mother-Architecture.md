# Moth Mother Architecture

Status: current system-level description of the standalone runtime family through
Runtime 5.3. Runtime 4.7 remains canonical; 5.3 is independently selectable.

This document explains the architecture shared across the family and the
important differences between releases. Version-specific code, specifications,
architecture locks, and qualification records define exact release behavior.
The [earlier Mother document](docs/history/Mother-Architecture-through-5.0.md)
is preserved as historical context, including the detailed factor equations.

Moth is a **bounded, compiled reasoning runtime family with explicit constraints,
provenance, and verified results**. Its foundation declares the meanings,
operations, value domains, and output capabilities available to a runtime.
Runtime 5.3 adds mutable conversational assertions and bounded plan construction
inside that foundation. It does not learn new operations from arbitrary prose.

## 1. Runtime family and authority

| Runtime | Architectural role | Release posture |
|---|---|---|
| 4.7 | Exact closed-world semantic operations and proof-carrying output | Qualified and canonical |
| 4.8 | Independent Input → Main → Surface orchestration | Independently selectable |
| 4.9 | Active compiled factor construction and domain narrowing | Independently selectable |
| 5.0 | Compiled language contracts feeding the world kernel | Independently selectable |
| 5.1 | Conversational HCF authority, context projection, and packaged assets | Preserved conversational runtime |
| 5.2 | Safetensors compiled content and revisioned SYSTEM/CONTEXT layers | Qualified, independently selectable |
| 5.3 | Owned kernel, conversational knowledge, bounded planning, and reexecution | Qualified, independently selectable |

Runtime selection is explicit: `moth --runtime 5.3 ...`. An untagged command
refuses. Newer version numbers do not change the canonical designation.

The root [ARCHITECTURE.md](ARCHITECTURE.md),
[ARCHITECTURE-DETAILED.md](ARCHITECTURE-DETAILED.md), [PRODUCT.md](PRODUCT.md),
and [SPEC.md](SPEC.md) describe the preserved 4.7 release. Current 5.3 operator
information is in [its guide](docs/v5.3/PRODUCT.md), with
[current implementation notes](docs/v5.3/IMPLEMENTATION-NOTES.md).

## 2. What remains closed, and what can change

“Closed” refers to the declared vocabulary, finite values, primitives, and
licensed outputs. It does not mean that every release has identical rules for
conversational state.

- Earlier exact-world paths select compiled meanings and permitted transient
  bindings; they do not acquire a new persistent knowledge base from chat.
- 5.1 and 5.2 archive conversations and settle behavioral constraints. Their
  context projection is not general conversational reasoning.
- 5.3 accepts supported assertions about declared entities and values, records
  their source messages, and uses them in later reasoning requests. Corrections
  change applicable assertions without changing the immutable foundation.

A user assertion is not independently established truth. Foundation defaults,
user assertions, derived evidence, and hypothetical plan states have different
roles. Instructions govern behavior; higher instruction authority does not
make a factual assertion true.

## 3. The computational mechanisms

The family does not have one universal computation law covering every path.

### Exact-world and factor reasoning

The historical world kernels ground typed requests, execute supported exact
operations, and verify results. The 4.9 factor path materializes compiled finite
variables and table factors, then narrows domains in deterministic order.
Remaining ambiguity can refuse; that mechanism does not silently become a
complete search solver. See [the 4.9 architecture](docs/v4.9/ARCHITECTURE.md).

### Hierarchical constraint settlement

The conversational HCF layer compares:

```text
(BASE violations, SYSTEM violations, CONTEXT violations, grounding cost)
```

Comparison is lexicographic. Lower-priority preferences cannot compensate for a
higher-priority violation. Typed delegation licenses supported overrides.
Distinct semantic winners tied at minimum energy refuse, and a selected minimum
with remaining hierarchy violations refuses.

In 5.2 and 5.3, this layer selects among immutable capability/presentation
candidates. It does not itself construct the new multistep action plan.

### Bounded planning in 5.3

The new planner uses deterministic uniform-cost search over finite state.
Actions declare preconditions, assignment effects, and positive integer costs.
It generates successors by applying actions; complete solutions are not stored
as a catalog. State identities and expansion order are deterministic, and
repeated states are tracked. Ordered goals include goal progress in the state.

The typed request API can forbid specified actions. These are admissibility
constraints, not penalties that a cheaper plan can outweigh. Arbitrary English
policy sentences are not automatically supported by that API capability.

Planning cost, HCF energy, and historical factor energy are distinct quantities.
Safetensors is a storage representation, not evidence that these mechanisms are
a learned neural energy model or a general-intelligence breakthrough.

## 4. Runtime 5.3 execution flow

```text
Message + captured conversation / SYSTEM / CONTEXT / knowledge revisions
    |
    +-- Existing supported world query
    |       → owned compatibility kernel → verified world result
    |
    +-- New conversational request
            → compiled clause interpretation and reference resolution
            → proposed knowledge update or clarification
            → relevant facts, goals, provenance and historical bindings
            → typed ReasoningRequest
            → bounded search when a plan is requested
            → independent plan or impossibility checking
    |
    v
Deterministic surface realization and checks
    |
    v
Atomic commit of messages, result and applicable knowledge revision
```

The compatibility path retains the three-World engine. The new chat path is a
separate typed pipeline; it must not be described as exactly three World
settlements. Its public reasoning interface is
`Kernel53.solve(ReasoningRequest) -> ReasoningResult`.

The kernel does not read database heads or dispatch tools. Preparation may
publish immutable objects; only the commit transaction advances conversational
state. An interrupted preparation can leave unreferenced CAS objects without
creating a partially committed conversation.

## 5. Language grounding and conversational knowledge

5.3 uses declared aliases and compiled sentence frames, with no generative-model
interpreter. Supported constructions include assertions, explicit negation,
location questions, delivery requests, conjunctions, ordering, corrections,
retractions, clarification replies, and limited historical follow-ups.

Every material clause must be understood. An unsupported clause requests
rephrasing rather than silently dropping part of the message. Multiple plausible
entity references request clarification instead of selecting by hash.

Facts record identity, value, polarity, source, applicability, supersession,
and derivation dependencies. The implementation filters invalid dependencies
from active knowledge. A correction supersedes the identified assertion;
an unmarked conflict between user assertions asks whether to use the new value.
A supported assertion can replace a configured foundation default.

Knowledge is retained independently of the recent-message projection. Relevant
facts and their sources become reasoning inputs. A proposed plan remains
hypothetical: planning a delivery does not update the package's observed location.
Prior-result follow-ups refer to historical outcomes; they are not a general
mechanism for reasoning about everything previously said.

## 6. Shipped domain and resource boundaries

The qualified 5.3 conversational foundation currently contains:

- One robot, six rooms in a corridor, and two packages.
- Explicit initial location, carrying, battery, key, and door-state defaults.
- Moving, picking up, dropping, unlocking, and recharging actions.
- A charger in room one; the robot initially has six battery units and a key.

These are foundation data, not universal facts about any user's environment.
New domains require compatible compiled assets and qualification; chat cannot
invent entities or teach new primitives.

| 5.3 conversational limit | Maximum |
|---|---:|
| Message length | 512 whitespace-counted tokens |
| Clauses per message | 256 |
| Active facts | 4,096 |
| Grounded actions | 8,192 |
| Plan length | 32 actions |
| Expanded search states | 100,000 |

The owned compatibility path retains its earlier limits. Additional storage and
compiler bounds also apply. The runtime never treats reaching a resource limit
as proof that a goal is impossible.

## 7. Verification and outcomes

The plan checker does not call the search algorithm. It checks each action from
the bound initial state and verifies goal satisfaction. An impossibility
certificate must contain a state set including the initial state, closed under
permitted transitions and excluding goal completion. Search cutoffs cannot
supply that certificate.

| Outcome | Meaning |
|---|---|
| `ANSWER` | A supported answer or checked plan |
| `ACKNOWLEDGED` | A conversational update was accepted |
| `CLARIFICATION_REQUIRED` | Interpretation or factual conflict remains unresolved |
| `INSUFFICIENT_INFORMATION` | Required state is missing |
| `IMPOSSIBLE` | Exhaustive finite-state evidence rules out the requested plan |
| `BUDGET_EXHAUSTED` | Computation or input limits prevented resolution |
| `REFUSAL` | A capability, policy, or other supported refusal boundary was reached |
| `INTEGRITY_FAILURE` | Verification or an integrity boundary failed |

Not every conversational response is a theorem. An acknowledgement records an
assertion; it does not prove the assertion true. Exact hashes demonstrate binding
and integrity, not factual correctness or broad language comprehension.

Surfaces are deterministic realizations of typed results. Structured outputs
and plan action sequences are checked for preservation. This does not mean the
current prose gives a causal explanation for every result: the present `Why?`
path repeats the prior outcome rather than explaining its blocking conditions.

## 8. Storage, concurrency, and replay

5.3 owns its package and compatibility kernel under `moth_runtime_v5_3`. The
artifact includes the source closure and compiled assets without importing an
older runtime package. Historical world-data schema identities remain inside
that owned code; this is a data compatibility convention.

Safetensors holds new compiled objects as numeric typed trees, label pools and
operands. SQLite holds transactional descriptors and revision bindings. JSON is
used for source, manifests, results, diagnostics, and the documented historical
world-archive representation.

Messages and knowledge revisions are append-only records. A turn binds exact
message, SYSTEM, CONTEXT, and knowledge heads. Commit compares captured heads
and writes the turn and knowledge update atomically; a concurrent change causes
an explicit conflict instead of a mixed-state result.

There are two different replay operations:

- **Replay:** retrieve the recorded canonical result bytes.
- **Reexecute:** reconstruct the historical computation and compare its result.
  Chat reexecution uses bound knowledge and policy revisions. Compatibility
  reexecution uses a disposable copied store. Neither advances the original
  conversation; operational timings are excluded from deterministic identity.

Unlike saved-byte replay, reexecution may need the original grounding machinery
and its declared local assets. No older store or artifact is migrated into 5.3.

## 9. What the evidence establishes

[5.3 qualification](reports/RUNTIME-5.3-CONVERSATIONAL-REASONING-001.md)
and [post-promotion verification](experiments/runtime_v5_3_conversational_reasoning/reports/POST-PROMOTION-VERIFICATION-001.json)
record 127 candidate tests, 168 compatibility surface cases, 36 inert skill
cases, independent logistics checks at solution depths 2/4/8/12, deterministic
builds, isolation, integrity, transaction, and reexecution checks. The root suite
has 200 passes with five recorded older failures and no new failures.

The [subsequent conversation trial](reports/RUNTIME-5.3-CONVERSATION-TRIAL-001.md)
used 26 messages across eight conversations. Memory, corrections, ambiguity
handling, door-aware planning, retractions, and finite-world impossibility worked.
Every trial turn re-executed successfully.

That trial also exposed important limits: “Can you take it to room 3?” requested
rephrasing, and “Why can't it get there?” repeated the outcome instead of
explaining the battery constraint. Qualification counts must not be presented
as evidence that unrestricted natural conversation is solved.

## 10. Extension and release discipline

New capabilities begin as experiments with a frozen question, fixtures and
acceptance gates. Preserve raw runs outside committed evidence and keep compact
reports and reproducible inputs. Promote an independently selectable runtime
only after its code and assets qualify. Preserve previous packages, stores,
release records and locks.

The immediate functional gaps are broader compositional phrasing, causal
explanations from checked evidence, and more readable entity names in factual
answers. These are future work, not capabilities supplied by this documentation
update. The independent frozen-world generalization experiment remains deferred.

The stable commitments are a declared computational boundary, explicit factual
provenance, no trade of hard violations for soft preference, deterministic
historical binding, appropriate verification, and honest treatment of unknowns
and resource limits. The present runtimes do not execute proposed external actions.
