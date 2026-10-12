# Runtime 5.0 compiled Python-function Surface experiment

Status: **BOUNDED COMPILED PYTHON-FUNCTION SURFACE CONFIRMED**.

This experiment tests whether a compact Surface skill can compile into a
bounded Runtime 5.0 realizer that emits real Python source containing named
variables, functions, local computation, a function call, and a final value.
The generated program is checked structurally before constrained local
execution. It does not alter the promoted runtime or production store.

See [SPEC.md](SPEC.md), [PLAN.md](PLAN.md), and [TASKS.md](TASKS.md).
The decisive record is [reports/CONCLUSION-001.md](reports/CONCLUSION-001.md).

Replay:

```sh
PYTHONPATH=src .venv/bin/python -m experiments.runtime_v5_0_compiled_python_function_surface.campaign
```
