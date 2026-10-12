# Runtime 5.3 frozen specification — attempt 001

Status: candidate. Fully owned independent runtime; preserve all previous runtimes.

## Objective
Natural supported English becomes typed facts, goals and references. Historical knowledge participates in reasoning. A generic finite action engine constructs plans and an independent checker verifies them. No external execution, network, generative interpreter, migration, or general-intelligence claim.

## Contracts
MessageInterpretation carries clauses, entities, source spans and grounding evidence. Parse all material clauses or clarify without applying changes. Exact aliases and typed discourse focus resolve references; distinct meanings never use hash tie-breaking. Facts have provenance, polarity, validity, supersession and derivation dependencies. Instructions do not establish truth. Explicit corrections supersede; unmarked conflicts clarify. Plans remain hypothetical.

Kernel53.solve(ReasoningRequest) is pure. Requests bind goal, selected facts, constraints, prior results, foundation/revision hashes and deterministic budgets. Preparation, solving, checking, rendering and atomic commit are separate. Capture message/SYSTEM/CONTEXT/knowledge heads and compare all at commit. Persist valid statements even if planning exhausts its budget; integrity failures and ambiguous interpretations apply no knowledge changes.

Generic finite-domain actions use typed grounded parameters, conjunctive equal/not-equal preconditions, assignments and positive integer costs. Deterministic uniform-cost search has duplicate detection and canonical action ordering. Relevant unknown state is insufficient information. Independent checker validates action replay and goal; impossibility requires a closed reachable-state certificate, not a cutoff.

Outcomes: ANSWER, ACKNOWLEDGED, CLARIFICATION_REQUIRED, INSUFFICIENT_INFORMATION, IMPOSSIBLE, BUDGET_EXHAUSTED, REFUSAL, INTEGRITY_FAILURE.

Limits: 512 whitespace tokens, 256 clauses, 4096 active facts, 8192 grounded actions, 32 plan actions, 100000 expanded states. Compatibility queries retain their historical limits.

Safetensors stores new compiled assets and knowledge. SQLite stores transactional bindings. Copied kernel world JSON is the explicit compatibility exception. Artifact owns all source/assets. No earlier runtime imports. Replay retrieves bytes; reexecute recomputes exact historical inputs without writing.

## Qualification
Three identical builds; isolated execution; import closure; tamper and cross-version rejection; protected file hashes. At least 80 conversation fixtures plus separate paraphrases. Independent planning oracle at depths 2/4/8/12, impossible, unknown and budget tests. Correction/retraction/dependency invalidation, restart, concurrency and rollback. Full suite with no new failures. Legacy settlement median time and incremental memory <=110% baseline. No promotion before passing gates.
