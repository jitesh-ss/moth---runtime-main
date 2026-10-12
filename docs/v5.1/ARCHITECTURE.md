# Runtime 5.1 architecture

The frozen Runtime 5.0 Input → Main → Surface kernel is loaded from a verified,
immutable foundation. A foundation contains one or more BASE HCF fields and
exactly three compiled World archives: Input, Main, and Surface. Runtime 5.1
surrounds it with an append-only
conversation log, active-context projection, three-level HCF settlement, bounded
Surface rendering, operational metrics, and conversation-level replay.

HCF energy is the tuple `(base violations, system violations, context violations,
grounding cost)`. Tuple comparison is lexicographic. Lower levels may override a
higher constraint only through an exact typed delegation. Entries within one
level have equal authority; unresolved same-level conflicts refuse.

BASE fields and compiled Worlds are fixed by `runtime-foundation.json`. Their
identities, entry hashes, World hashes, bundle hash, and encoder identity form a
single content-derived foundation hash. The store and every turn bind that hash.
Changing any member therefore requires a new store. The foundation format has no
weight descriptor and the runtime has no weight-loading path.

BASE entries are fixed by the loaded foundation, SYSTEM entries are compiled once
when a conversation is created, and CONTEXT entries are compiled from every
message. Every message remains archived. The active projection includes the
current message, exact referenced turns, then the newest whole messages that fit.

Deterministic evidence is content-addressed. Variable timing and process-resource
observations are stored separately and never participate in result identity.

## Compiled model artifact

The optional artifact layer wraps the foundation without changing the preserved
kernel. It contains five distinct field kinds. Their L1 atomic meanings, L2
operators, L3 macros, L4 interpretations, L5 skill profiles, and optional L6
composition describe capability compilation; they do not change HCF authority.

The capability index maps each Surface mode to exactly one field and canonical
policy. HCF settles that finite candidate before realization. The generated text,
JSON, inert Python literal, or Python function source is parsed back into a value
and compared byte-canonically with the Main result. Python ASTs are inspected but
never executed.

Skill compilation treats Markdown as bounded declarative input, retains
clause-level provenance, and produces an immutable policy and trace. Planning is
a pure function of that policy and an embedded task snapshot. It returns an
exact proposed replacement and hashes, an authority request, or a refusal; it
has no filesystem, subprocess, network, tool, or code-execution path.
