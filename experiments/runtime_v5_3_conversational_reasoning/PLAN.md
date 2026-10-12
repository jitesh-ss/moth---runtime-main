# Implementation plan

1. Freeze contracts and protected hashes; record full baseline suite.
2. Own compatibility kernel, artifact builder and assets in candidate namespace.
3. Add pure typed request/search/checker contracts and compiled logistics domain.
4. Add language compilation and transactional knowledge revisions.
5. Integrate prepare/solve/verify/commit, surfaces and historical reexecution.
6. Add deterministic qualification corpus, independent oracle and preservation tests.
7. Optimize HCF without changing compatibility results.
8. Qualify; promote package/config, add launcher and documentation locks.

Commands (repository root): `.venv/bin/python -B -m pytest tests -q`; candidate checks use `PYTHONPATH=experiments/runtime_v5_3_conversational_reasoning/candidate:src .venv/bin/python -B -m pytest experiments/runtime_v5_3_conversational_reasoning/tests -q`.
