# Runtime 4.8 Product Description

Runtime 4.8 is an opt-in three-World form of Moth's closed-world,
proof-carrying energy runtime. Runtime 4.7 remains qualified and canonical.
The neutral terminal launcher has no implicit runtime default.

Runtime 4.8 processes a prompt through three independently settled and verified
compiled Worlds:

```text
prompt grounding -> Input World -> Main World -> Surface World -> response
```

- The **Input World** transforms an already-grounded request using compiled
  input-language knowledge. It does not perform prompt grounding.
- The **Main World** performs the same exact closed-world semantic reasoning
  model established by Runtime 4.7.
- The **Surface World** currently uses one compiled semantic-preserving
  realizer to verify and return the Main value. Compiled vocabulary, grammar,
  formatting, and output-length behavior remain later World contents.

Every World uses the same deterministic settlement kernel and an independent
verifier. The handoff between Worlds is typed, content-addressed, provenance
bound, and tied to one immutable three-World bundle. A World cannot introduce
knowledge, values, or language that was not compiled into its selected
generation. Any refusal or integrity failure stops the remaining cascade.

Users select Runtime 4.8 explicitly:

```sh
moth --runtime 4.8 status
moth --runtime 4.8 query "..."
```

The normal terminal response contains only the final verified Surface value;
`--json` returns complete grounding, per-World energy, proofs, provenance,
handoffs, and replay evidence.

Runtime 4.8 is delivered with empty Input, Main, and Surface Worlds and no
active bundle. It therefore returns `WORLD_NOT_READY` until compatible Worlds
are compiled and activated. The initial release establishes the architecture
and isolation only; it does not yet claim LLM-like input fidelity or controlled
surface realization.

Runtime 4.8 never executes Python, applies patches, dispatches tools, learns
from prompts, accesses the network, or migrates a Runtime 4.7 store.
