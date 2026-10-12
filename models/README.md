# Local model assets

Model weights are intentionally not committed.

Place the complete pinned `BAAI/bge-large-en-v1.5` directory here:

```text
models/bge-large-en-v1.5/
```

The expected file hashes are sealed in
`config/encoder-text-en-1.0.json`. Run
`./.venv/bin/moth --runtime 4.7 doctor` from the project root to verify the
local assets. Runtime inference uses local files only and does not download
weights.
