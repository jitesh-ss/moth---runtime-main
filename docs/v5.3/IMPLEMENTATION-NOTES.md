# Runtime 5.3 current implementation notes

These notes supplement the sealed [architecture](ARCHITECTURE.md),
[operator guide](PRODUCT.md), and [qualification](../../reports/RUNTIME-5.3-CONVERSATIONAL-REASONING-001.md).
They record behavior observed after promotion without rewriting those release
records or their hashes. The [Mother architecture](../../Mother-Architecture.md)
provides the current family-wide description.

## Demonstrated behavior

The installed CLI remembers supported assertions, resolves references, applies
explicit corrections, asks about conflicting claims, and handles retractions.
Its finite planner adds an unlocking action when a door is locked and reports
verified impossibility when no permitted plan can succeed. A proposed delivery
does not change observed package locations.

A [26-message trial](../../reports/RUNTIME-5.3-CONVERSATION-TRIAL-001.md)
covered eight conversations. All turns re-executed and all conversations passed
verification. These integrity checks do not establish that every response is
useful or that arbitrary wording is understood.

## Known functional gaps

| Request or behavior | Current result | Implication |
|---|---|---|
| `Take it to room three.` after a clear package reference | Produces a plan | Supported reference resolution works |
| `Can you take it to room 3?` | Requests rephrasing | Common conversational framing is not supported by the current frames |
| `Where did I say the package was?` | Requests rephrasing | General questions about conversation history are not implemented |
| `Why can't it get there?` after an impossible task | Repeats the prior outcome | It does not yet explain the blocking battery/precondition evidence |
| Factual answers and clarifications | Can display `packagea`, `room5`, or `packagea.location` | Surface wording still exposes internal identifiers |

`Why?` and `Show the plan again` are limited historical-result references. Their
acceptance by the parser must not be confused with causal explanation or a
correctly interpreted premise in every question.

## Scope and architecture boundaries

The shipped chat foundation has one robot, six rooms and two packages with
explicit defaults. It does not provide unrestricted conversational knowledge.
Unsupported clauses are not silently accepted as facts.

HCF lexicographic settlement governs supported capability/presentation choices;
the new planner separately performs uniform-cost search. They are not a single
energy-minimization reasoning loop. The typed kernel API accepts forbidden-action
constraints; that does not establish support for arbitrary policy prose.

Independent plan verification establishes correctness relative to the supplied
world and assertions. It does not independently establish the truth of user
assertions. Generated plans remain hypothetical and are never dispatched.

## Next work

Expand and independently test language coverage, generate causal explanations
from verified evidence, and improve readable entity names. Keep these changes
in a new qualified attempt rather than silently changing the sealed 5.3 release.
The broader frozen-foundation intelligence experiment remains deferred.
