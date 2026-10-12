# Runtime 5.3 architecture

Natural message → compiled clause grounding → revisioned knowledge projection → typed reasoning request → bounded composition → independent checking → deterministic conversational surface → atomic commit.

The package owns its compatibility kernel under `legacy/`; no old runtime package is imported. Kernel53.solve is a public pure finite-domain interface. The old compiled world schemas remain versioned 5.0 internally as a documented data compatibility convention, not a runtime dependency.

Immutable Safetensors objects contain language frames, entity aliases, actions, defaults, and knowledge snapshots. SQLite binds exact conversation, SYSTEM, CONTEXT, and knowledge revisions. Numeric typed trees contain opcodes, parent indexes, string pools and integer operands; no pickled objects or JSON blobs are compiled objects.

Knowledge separates user assertions, foundation defaults and derivation dependencies from instruction authority. Explicit corrections supersede facts; unmarked conflicts and unresolved references ask for clarification. Proposed plans never change observed locations. Prior answers are historical references, not automatically true current-state facts.

The initial language domain contains one robot, six rooms and two packages. Initial locations, keys, carrying state, door state and battery defaults are explicit artifact data. A user assertion can replace a foundation default; conflicting user assertions require correction or confirmation. This is a bounded conversational domain, not unrestricted English. Unknown material clauses cannot be silently discarded.

Uniform-cost search composes declared actions with hard admissibility checks and deterministic budgets. Independent action replay certifies plans. A closed reachable-state certificate certifies impossibility; an unfinished search reports budget exhaustion. Ordered goals track progress as part of state.

Compatibility queries use the owned original reasoning path. New chat supports facts, negation, corrections, retractions, location questions, delivery goals, conjunctions, ordering, references, clarifications and historical follow-ups. The pure request API also accepts explicit forbidden-action constraints. There is no claim that arbitrary new natural-language policies compile.

Preparation reads snapshots and publishes immutable CAS objects; only commit advances state. The kernel itself performs no storage I/O. Head comparisons and all message/result/knowledge writes share one SQLite transaction. Failed preparation can leave unreferenced immutable objects, which do not change conversational state.

Replay returns saved bytes. Reexecute reconstructs the chat request and result from historical knowledge, source messages and policy revisions. Compatibility reexecution uses a disposable copied store and compares canonical results. Neither operation changes original conversation heads. Timing metrics are outside deterministic receipts.
