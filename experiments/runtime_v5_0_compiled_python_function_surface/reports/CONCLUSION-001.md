# Conclusion 001: actual Python functions and variables

Verdict: **`BOUNDED_COMPILED_PYTHON_FUNCTION_SURFACE_CONFIRMED`**.

The compiled Surface skill generated real Python source containing three input
variables, three functions, local variables, branching, a final function call,
and a printed dictionary. `selected-plan` was computed by `select_plan`; it was
not embedded from the Runtime answer.

## Decisive evidence

- 8 Runtime 5.0 semantic cases × 2 equivalent Python requests = 16 programs.
- 16/16 programs parsed under the strict AST allowlist.
- 16/16 programs executed and produced the exact Runtime semantic value.
- 16/16 candidate Runtime results were byte-identical to isolated controls.
- 16/16 archives replayed; generation and replay verification performed 48
  successful positive executions.
- 2/2 Runtime refusals remained byte-identical and produced no program.
- 10/10 compilations produced one policy hash; the paraphrased skill and frozen
  granular oracle produced the same policy.
- 5/5 unsafe-program probes, 4/4 invalid-skill probes, 7/7 causal ablations, and
  6/6 tamper probes failed closed.
- Programs were 30 lines, 745–752 bytes, and 107 AST nodes.
- Temporary Runtime instances and execution directories were removed. Protected
  Runtime 5.0 code, config, store, docs, and earlier experiments were unchanged.

## Representative generated program

```python
proposed_valid = False
backup_valid = True
failure_reason = 'RESOURCE'

def boolean_text(value):
    if value:
        return "true"
    return "false"

def select_plan(proposed, backup):
    if proposed:
        return "PROPOSED"
    if backup:
        return "BACKUP"
    return "NONE"

def build_decision(proposed, backup, reason):
    selected_plan = select_plan(proposed, backup)
    proposed_text = boolean_text(proposed)
    backup_text = boolean_text(backup)
    decision = {
        "proposed-valid": proposed_text,
        "backup-valid": backup_text,
        "selected-plan": selected_plan,
        "failure-reason": reason,
    }
    return decision

decision = build_decision(proposed_valid, backup_valid, failure_reason)
print(decision)
```

This establishes the bounded mechanism, not general Python generation. The
execution boundary is a constrained local subprocess with isolated flags,
minimal environment, resource limits, timeout, AST capability exclusion, and
temporary-directory cleanup. It is explicitly not a hardened container sandbox.
Docker was unavailable during the run and no sandbox dependency was installed.
