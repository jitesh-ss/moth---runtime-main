from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from moth_runtime_v4_8 import cli as cli_v4_8
from moth_runtime_v4_8.encoder import DeterministicEncoder
from moth_runtime_v4_8.model import WorldRole
from moth_runtime_v4_8.store import WorldStore


ROOT = Path(__file__).resolve().parents[1]
BIN = Path(sys.executable).parent
MOTH = BIN / "moth"
MOTH_4_7 = BIN / "moth-4.7"
SURFACE_REALIZER = """\
Operation "realize-semantic-result" selects kernel primitive "REALIZE_SEMANTIC_RESULT".
Instruction "realize-semantic-result" selects operation "realize-semantic-result" accepts "Realize the verified semantic result.".
"""


def _environment(tmp_path: Path) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update({
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "HF_HOME": str(tmp_path / "hf"),
        "XDG_CACHE_HOME": str(tmp_path / "cache"),
        "PYTHONPYCACHEPREFIX": str(tmp_path / "pycache"),
        "PYTHONPATH": str(ROOT / "src"),
    })
    return environment


def _run(entrypoint: Path, tmp_path: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    assert entrypoint.is_file(), f"console entry point is not installed: {entrypoint}"
    return subprocess.run(
        [str(entrypoint), *arguments],
        cwd=tmp_path,
        env=_environment(tmp_path),
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )


def _run_bytes(
    entrypoint: Path, tmp_path: Path, *arguments: str
) -> subprocess.CompletedProcess[bytes]:
    assert entrypoint.is_file(), f"console entry point is not installed: {entrypoint}"
    return subprocess.run(
        [str(entrypoint), *arguments],
        cwd=tmp_path,
        env=_environment(tmp_path),
        capture_output=True,
        check=False,
        timeout=30,
    )


def _initialize(entrypoint: Path, tmp_path: Path, runtime: str | None, store: Path):
    selector = [] if runtime is None else ["--runtime", runtime]
    completed = _run(entrypoint, tmp_path, *selector, "--store", str(store), "init")
    assert completed.returncode == 0, completed.stderr
    return completed


def test_tagged_runtime_4_7_status_uses_only_temporary_store(tmp_path):
    store = tmp_path / "runtime-4.7.sqlite3"
    _initialize(MOTH, tmp_path, "4.7", store)

    completed = _run(MOTH, tmp_path, "--runtime=4.7", "--store", str(store), "status")

    assert completed.returncode == 0
    assert json.loads(completed.stdout) == {
        "runtime": "4.7", "store": str(store.resolve()), "head": None,
    }
    assert completed.stderr == ""


def test_tagged_runtime_4_8_status_and_query_use_only_temporary_store(tmp_path):
    store = tmp_path / "runtime-4.8.sqlite3"
    _initialize(MOTH, tmp_path, "4.8", store)

    status = _run(MOTH, tmp_path, "--runtime", "4.8", "--store", str(store), "status")
    assert status.returncode == 0
    status_value = json.loads(status.stdout)
    assert status_value["runtime"] == "4.8"
    assert status_value["store"] == str(store.resolve())
    assert status_value["heads"] == {"INPUT": None, "MAIN": None, "SURFACE": None}
    assert status_value["active_bundle"] is None

    query = _run(
        MOTH, tmp_path, "--runtime=4.8", "--store", str(store),
        "query", "anything",
    )
    assert query.returncode == 0
    assert query.stdout == (
        "WORLD_NOT_READY: Runtime 4.8 has no active three-world bundle.\n"
    )
    assert query.stderr == ""


def test_legacy_runtime_4_7_entrypoint_remains_operational(tmp_path):
    store = tmp_path / "legacy-4.7.sqlite3"
    _initialize(MOTH_4_7, tmp_path, None, store)

    completed = _run(MOTH_4_7, tmp_path, "--store", str(store), "status")

    assert completed.returncode == 0
    assert json.loads(completed.stdout)["runtime"] == "4.7"
    assert completed.stderr == ""


@pytest.mark.parametrize(
    ("arguments", "error"),
    [
        (["status"], "exactly one --runtime selector is required"),
        (["--runtime", "9.9", "status"], "unsupported runtime '9.9'"),
        (
            ["--runtime", "4.7", "--runtime=4.8", "status"],
            "conflicting runtime selectors: 4.7, 4.8",
        ),
        (
            ["--runtime=4.8", "--runtime", "4.8", "status"],
            "--runtime may be specified only once",
        ),
    ],
)
def test_neutral_entrypoint_rejects_invalid_runtime_selection(
    tmp_path, arguments, error
):
    completed = _run(MOTH, tmp_path, *arguments)

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert "usage: moth --runtime {4.7,4.8,4.9,5.0}" in completed.stderr
    assert error in completed.stderr


def test_runtime_4_8_replay_writes_exact_bytes_and_quiet_writes_nothing(
    monkeypatch, capsys, tmp_path
):
    archived = b'{"canonical":true,"nested":{"value":1}}'

    class FakeStore:
        def replay(self, episode_id: str, *, encoder_free: bool) -> bytes:
            assert episode_id == "episode-1"
            assert encoder_free is True
            return archived

    monkeypatch.setattr(cli_v4_8, "LocalBGEEncoder", lambda: object())
    monkeypatch.setattr(cli_v4_8, "WorldStore", lambda path: FakeStore())

    assert cli_v4_8.main([
        "--store", str(tmp_path / "unused.sqlite3"),
        "replay", "episode-1", "--encoder-free",
    ]) == 0
    assert capsys.readouterr().out.encode("utf-8") == archived

    assert cli_v4_8.main([
        "--quiet", "--store", str(tmp_path / "unused.sqlite3"),
        "replay", "episode-1", "--encoder-free",
    ]) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_tagged_runtime_4_8_replay_is_byte_exact_through_console_script(tmp_path):
    source = (ROOT / "tests/fixtures/world.moth").read_text(encoding="utf-8")
    store_path = tmp_path / "replay-4.8.sqlite3"
    store = WorldStore(store_path)
    encoder = DeterministicEncoder()
    store.publish(WorldRole.INPUT, {"input.moth": source}, encoder=encoder)
    store.publish(WorldRole.MAIN, {"main.moth": source}, encoder=encoder)
    store.publish(
        WorldRole.SURFACE,
        {"surface.moth": SURFACE_REALIZER},
        encoder=encoder,
    )
    store.activate()
    result = store.query(
        "Return Node-00 using answer-json.",
        encoder=encoder,
        thresholds={
            "default": {"score": 0.82, "margin": 0.05},
            "INSTRUCTION": {"score": 0.82, "margin": 0.08},
        },
    )
    archived = store.replay(result["episode_id"], encoder_free=True)

    replay = _run_bytes(
        MOTH, tmp_path, "--runtime", "4.8", "--store", str(store_path),
        "replay", result["episode_id"], "--encoder-free",
    )
    assert replay.returncode == 0
    assert replay.stdout == archived
    assert replay.stderr == b""

    quiet = _run_bytes(
        MOTH, tmp_path, "--runtime=4.8", "--quiet", "--store", str(store_path),
        "replay", result["episode_id"], "--encoder-free",
    )
    assert quiet.returncode == 0
    assert quiet.stdout == b""
    assert quiet.stderr == b""
