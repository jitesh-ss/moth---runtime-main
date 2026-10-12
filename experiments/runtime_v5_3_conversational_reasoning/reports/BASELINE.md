# Baseline before 5.3

186 passed, five pre-existing failures. Four cases in `tests/test_cli_entrypoints_v4_8.py` hard-code the old neutral-launcher usage string. `tests/test_runtime_v4_8.py::test_runtime_4_8_architecture_lock_matches_frozen_assets` reports the existing old documentation hash mismatch. No older test or lock was edited.
