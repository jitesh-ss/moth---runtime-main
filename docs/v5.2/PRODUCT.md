# Runtime 5.2 operator guide

Build and initialize a self-contained store:

```sh
.venv/bin/python -B -m experiments.runtime_v5_2_energy_native_fields.build_artifact /tmp/model-5.2
.venv/bin/moth --runtime 5.2 --store /tmp/store-5.2 init --artifact /tmp/model-5.2
.venv/bin/moth --runtime 5.2 --store /tmp/store-5.2 artifact verify
```

Create and use a conversation:

```sh
.venv/bin/moth --runtime 5.2 --store /tmp/store-5.2 session create
.venv/bin/moth --runtime 5.2 --store /tmp/store-5.2 turn CONVERSATION_ID "PROMPT"
```

Compile and attach a mutable field:

```sh
.venv/bin/moth --runtime 5.2 --store /tmp/store-5.2 field compile field.json --level CONTEXT
.venv/bin/moth --runtime 5.2 --store /tmp/store-5.2 layer upsert CONVERSATION_ID \
  --level CONTEXT --key response-policy --object OBJECT_HASH --expected-revision 0
```

Use `layer history`, `replay`, and `verify` to inspect exact historical
bindings. The original artifact path may be removed after initialization; the
store contains its verified artifact and object closure.

Runtime 5.2 deliberately provides no 5.1 migration. Pointing it at a 5.1 store
or artifact returns a version mismatch. Runtime 5.1 remains selectable with
`--runtime 5.1`.
