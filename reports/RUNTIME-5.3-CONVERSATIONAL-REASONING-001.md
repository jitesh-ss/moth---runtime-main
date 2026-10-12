# Runtime 5.3 conversational reasoning qualification 001

Verdict: `QUALIFIED_CONVERSATIONAL_REASONING_5_3`.

The promoted package owns all runtime code, including its compatibility kernel. It has no older-runtime import dependency. It is independently selectable; Runtime 4.7 remains canonical.

## Frozen evidence

- Artifact: `354eb41918e2ba98d0b20564642c6f711d5086ce0dee94bcac017dc1e86788b8`.
- Three clean artifact builds: identical; promoted rebuild matches the candidate.
- 80 conversational fixtures, eight separately frozen paraphrase cases, independent logistics oracle at depths 2/4/8/12.
- Candidate regression panel: 127 tests (including final edge cases); see replay commands below.
- Compatibility surface outputs: 168/168; inert skill cases: 36/36; dispatches and task writes: zero.
- Isolated artifact execution, tamper rejection, historical reexecution, concurrent layer/turn rejection, and injected transaction rollback covered.
- Protected earlier-runtime/source/test/document hashes: unchanged.
- Baseline root suite: 186 passes and five existing failures, detailed in the experiment baseline record. These failures remain outside 5.3.
- Legacy settlement median time ratio: 1.027545 (gate <=1.10).
- Incremental peak RSS ratio: 0.816583 (gate <=1.10). Absolute RSS and post-import baselines are retained; this is not a total-process-memory improvement claim.
- Median new chat planning turn: 10.547 ms on the qualification machine, including transactional work measured by the caller.

Raw repeated runs are not required for qualification. Committed measurements are in [qualification-measurements-002.json](../experiments/runtime_v5_3_conversational_reasoning/reports/qualification-measurements-002.json). Earlier candidate measurements remain as historical development evidence, not the release artifact identity.

## Boundaries

The shipped chat world has one robot, six rooms and two packages. Language coverage is compiled and bounded. Foundations supply explicit initial defaults; user claims are assertions, not independently verified facts. Plans are hypothetical. This release provides no external tool execution, store migration, generative interpreter, or evidence for a general-intelligence breakthrough.

The checker independently replays plans and checks closed-state impossibility certificates. Generic forbidden-action constraints are supported by the typed kernel API; arbitrary English action-policy interpretation is not claimed. Legacy compiled-world data retains its schema identities inside the owned kernel.

## Replay

```sh
.venv/bin/python -B -m pytest tests -q
PYTHONPATH=experiments/runtime_v5_3_conversational_reasoning/candidate:src .venv/bin/python -B -m pytest experiments/runtime_v5_3_conversational_reasoning/tests -q
PYTHONPATH=experiments/runtime_v5_3_conversational_reasoning/candidate:src .venv/bin/python -B -m experiments.runtime_v5_3_conversational_reasoning.campaign
.venv/bin/moth --runtime 5.3 artifact verify config/v5.3/model/model-5.3
```

The campaign writes raw output to ignored runs/. The installed neutral launcher remains outside the isolated artifact closure. Use the version-specific module with `python -B` for isolated execution.
