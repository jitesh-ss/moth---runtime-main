# Runtime 5.0 Architecture

```text
normalized prompt
      |
      v
Input World: legacy envelope OR semantic contract settlement
      |  ID-only Main request + semantic graph commitment
      v
Main World: unchanged Runtime 4.9 settlement/factor kernel
      |  verified semantic result
      v
Surface World: unchanged semantic-value-preserving realization
```

Semantic contracts and their encoded surfaces are compiled, archived, and
content-addressed with the Input World. Semantic settlement preserves fact
coordinates and emits an independently verifiable proof trace. Encoder-free
replay recomputes archived vector comparisons without loading BGE. Every
archive, handoff, receipt, result, and store identity is domain-separated as
Runtime 5.0.
