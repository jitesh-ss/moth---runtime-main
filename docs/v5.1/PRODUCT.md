# Runtime 5.1 product contract

Runtime 5.1 is a standalone local conversational extension of Runtime 5.0. It
organizes compiled field content into `BASE`, `SYSTEM`, and `CONTEXT` levels and
settles candidates with lexicographic priority. It stores complete conversations,
projects a bounded active context, and exposes deterministic evidence through a
scriptable console and interactive REPL.

Runtime 5.1 starts from an immutable foundation attachment: one or more BASE HCF
fields plus exactly one compiled Input, Main, and Surface World. The attachment
is content-addressed, bound to the store, inspectable, and cannot be replaced in
an existing store.

Runtime 5.1 can also open a self-contained `moth-model-artifact/5.1` directory.
The artifact embeds the frozen Runtime 5.0 kernel dependency, Runtime 5.1,
three compiled Worlds, the foundation, five namespaced compiled field families,
canonical skill policies, and a field-driven capability index. Every declared
member is content-addressed and the complete image has an aggregate hash.

Artifact-backed conversations bind selected compiled skills into the immutable
SYSTEM level. CONTEXT can request an authorized presentation policy without
changing the semantic Input prompt. The selected policy realizes a pure Surface
answer and independently recovers its semantic value. Instruction skills can
only produce inert plans against request-embedded snapshots.

Runtime 5.1 does not call external models, execute tools, manage Worlds, expose a
provider API, deploy to cloud hardware, load weights, run generated Python, or
apply an inert plan. This is the complete weight-free compiled artifact, not the
later weighted production artifact. Language and Surface behavior remain
bounded by its qualified fields and fail closed outside them.
