# Runtime 5.3 operator guide

Run from the repository root. All stores are separate from older versions; no migration is provided.

```sh
.venv/bin/moth --runtime 5.3 --store /tmp/moth-5.3 init --artifact config/v5.3/model/model-5.3
.venv/bin/moth --runtime 5.3 --store /tmp/moth-5.3 session create
.venv/bin/moth --runtime 5.3 --store /tmp/moth-5.3 repl --session CONVERSATION_ID
```

Try this conversation:

```text
Robot one is in room one. Package A is in room two.
Take it to room three.
Where is package A?
Actually, the package is in room four.
Where is it?
```

The proposed plan does not execute. The location question still reports room two until the correction is accepted. The foundation supplies explicit world defaults: a six-room corridor, one robot initially at room one with six battery units and a key, package A at room two, package B at room one, unlocked doors, and a charger at room one. Runtime rules support moving, pickup/drop, unlocking and recharging.

Supported follow-ups include `Why?`, `Show the plan again`, `Forget that package A is in room four`, and `yes` after a proposed factual correction. Ambiguous references request an entity name. Arbitrary English outside compiled constructions requests rephrasing.

```sh
.venv/bin/moth --runtime 5.3 --store /tmp/moth-5.3 inspect knowledge CONVERSATION_ID
.venv/bin/moth --runtime 5.3 --store /tmp/moth-5.3 inspect reasoning CONVERSATION_ID --turn TURN_ID
.venv/bin/moth --runtime 5.3 --store /tmp/moth-5.3 reexecute CONVERSATION_ID TURN_ID
.venv/bin/moth --runtime 5.3 --store /tmp/moth-5.3 replay CONVERSATION_ID TURN_ID
.venv/bin/moth --runtime 5.3 --store /tmp/moth-5.3 verify --session CONVERSATION_ID
.venv/bin/moth --runtime 5.3 artifact build /tmp/new-model-5.3
```

For isolated execution, point PYTHONPATH at the artifact's runtime directory and use `python -B -m moth_runtime_v5_3`. Keep the store outside the immutable artifact. Compiled system prompts and layer commands retain the previous supported syntax. Query and REPL messages are natural text; JSON is not required.

```sh
.venv/bin/python -B -m pytest tests -q
PYTHONPATH=experiments/runtime_v5_3_conversational_reasoning/candidate:src .venv/bin/python -B -m pytest experiments/runtime_v5_3_conversational_reasoning/tests -q
PYTHONPATH=experiments/runtime_v5_3_conversational_reasoning/candidate:src .venv/bin/python -B -m experiments.runtime_v5_3_conversational_reasoning.campaign
```

The campaign writes fresh raw measurements under ignored runs/. The committed qualification includes a frozen compact copy. The five known older-suite failures are recorded in the baseline report; none is a new 5.3 failure.
