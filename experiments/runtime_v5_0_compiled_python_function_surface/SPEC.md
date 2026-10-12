# Specification: compiled Python-function Surface

Status: **APPROVED AND FROZEN BEFORE CAMPAIGN EXECUTION** (2026-09-02).

## Question

Can an ordinary compact skill compile through the established Runtime 5.0
instruction hierarchy into deterministic, executable Python source with real
functions and variables, while preserving the verified Runtime result?

## Scope

The experiment supports one frozen `FACTOR_RESULT` schema. A successful Python
artifact must contain module input variables, three named functions, local
variables, a final `build_decision(...)` call, and `print(decision)`. The code
computes `selected-plan` rather than embedding it.

Execution is local and constrained, not a hardened container sandbox. Docker is
installed but its daemon was unavailable at experiment start, and the
Cloudflare Sandbox SDK was absent. Programs are deterministically generated,
AST-allowlisted before execution, run with isolated Python flags, a minimal
environment, resource limits, a timeout, and a disposable working directory.

## Required gates

1. The primary and paraphrased skills compile to the same frozen policy and the
   independently frozen granular oracle.
2. Ten repeated compilations produce one policy hash.
3. Every accepted artifact parses as Python and contains the exact required
   functions, variables, call graph, and only allowlisted AST nodes.
4. Every accepted artifact executes successfully in a fresh disposable
   directory and prints exactly the Runtime 5.0 semantic value.
5. Every Runtime answer is byte-identical between control and candidate stores.
6. Runtime refusals remain byte-identical and are never converted to programs.
7. Unsupported presentation requests, malformed results, unsafe skill variants,
   causal ablations, and program/archive tampering fail closed.
8. All experiment directories are removed after execution; protected Runtime
   5.0 and prior-experiment hashes remain unchanged.

## Non-goals

- General-purpose or user-authored code execution.
- Imports, filesystem or network access, subprocess creation, concurrency,
  classes, loops, comprehensions, exceptions, or metaprogramming.
- Promotion into `src/`, `config/`, `data/`, or the default runtime.
- A claim of hardened sandbox security.

## Decisive verdicts

- `BOUNDED_COMPILED_PYTHON_FUNCTION_SURFACE_CONFIRMED` only if every gate passes.
- Otherwise the campaign raises and emits no positive verdict.

