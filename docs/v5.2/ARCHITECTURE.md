# Runtime 5.2 architecture

Runtime 5.2 separates readable authoring, immutable compiled content, and
transactional conversational state.

```text
config/v5.2/sources/*.json|*.md
             │ compile and validate
             ▼
Safetensors CAS ──► read-only candidate/HCF/skill arrays ──► lexicographic settlement
             │                                             │
             │ immutable object hashes                     ▼
             └────────────── SQLite revision bindings ──► Runtime 5.0 kernel
                                                           │
                                                           ▼
                                                   verified surface result
```

Safetensors is the canonical and only compiled-content format. The immutable
energy foundation owns all candidates and BASE entries. Mutable fields can
constrain or activate those candidates but cannot add candidates, executable
payloads, worlds, or callbacks.

SQLite stores object descriptors, conversations, two layer revision chains,
append-only messages, turns, result chains, and metrics. A mutation creates a
new complete membership snapshot and atomically advances one layer head. A turn
binds the exact SYSTEM/CONTEXT revisions it observed; replay never follows the
current heads.

The settlement engine indexes dense candidate properties using compiled scope
indexes. It never reconstructs candidate dictionaries or HCF entry objects.
Only after selection does it construct a transparent JSON trace.

`moth_runtime_v5_2.kernel` is the sole path to the frozen 5.0 world engine.
The 5.2 package has no import dependency on 5.1, and its artifact contains the
required 5.0 and 5.2 source closure.
