# Runtime 4.9 compositional-language cascade

Status: **ATTEMPT 001 PASS — compositional language cascade confirmed within the frozen boundary**

This isolated Attempt 002 tests whether multi-clause English can settle into a
complete canonical fact graph and intent, cross a typed handoff, drive an
unmodified disposable Runtime 4.9 factor World, and produce a deterministic
Surface result. Runtime 4.9 and the prior semantic-equivalence experiment are
protected inputs, not development locations.

See [SPEC.md](SPEC.md) for the frozen gates.

Attempt 001 passed all 13 frozen prompts with zero unsafe acceptances. Eight
multi-clause prompts settled complete fact graphs and drove one generic
unmodified Runtime 4.9 Main factor World across two domains; five ambiguity,
integrity, completeness, and capability-boundary controls refused safely. See
[reports/CONCLUSION-001.md](reports/CONCLUSION-001.md).

```sh
.venv/bin/python -m pytest -q experiments/runtime_v4_9_compositional_language/tests
.venv/bin/python -m experiments.runtime_v4_9_compositional_language.campaign
```
