# Spec: Runtime 5.1 Hierarchical Context Functions

## Frozen claim

For a finite candidate set and compiled declarative entries, Runtime 5.1 orders
energy lexicographically as BASE, SYSTEM, CONTEXT, then grounding cost. A lower
level may bypass a higher constraint only through an exact direct delegation or
an explicitly redelegable BASE → SYSTEM → CONTEXT chain.

## Gates

- BASE cannot be inverted by SYSTEM, CONTEXT, or grounding magnitude.
- SYSTEM cannot be inverted by CONTEXT.
- Direct and redelegated authority remain scoped.
- Same-level conflicts and distinct tied minima refuse.
- Equivalent traces are deterministic and independently reconstructable.
- No callback, network, tool dispatch, World mutation, or production store is used.
