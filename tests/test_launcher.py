from __future__ import annotations

import re
from types import SimpleNamespace

import pytest

from moth_launcher import cli


@pytest.mark.parametrize(
    ("arguments", "version", "forwarded"),
    [
        (["--runtime", "4.7", "status"], "4.7", ["status"]),
        (["--runtime=4.7", "status"], "4.7", ["status"]),
        (["--runtime", "4.8", "query", "hello"], "4.8", ["query", "hello"]),
        (["--runtime=4.8", "--json", "status"], "4.8", ["--json", "status"]),
        (["--runtime=4.9", "status"], "4.9", ["status"]),
        (
            ["--store", "tmp.sqlite3", "--runtime", "4.8", "status"],
            "4.8",
            ["--store", "tmp.sqlite3", "status"],
        ),
    ],
)
def test_select_runtime_accepts_both_forms_and_preserves_arguments(
    arguments, version, forwarded
):
    assert cli.select_runtime(arguments) == (version, forwarded)


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        (["status"], "exactly one --runtime selector is required"),
        (["--runtime"], "--runtime requires a value"),
        (["--runtime", "--json", "status"], "--runtime requires a value"),
        (["--runtime="], "--runtime requires a value"),
        (
            ["--runtime", "4.7", "--runtime=4.7", "status"],
            "--runtime may be specified only once",
        ),
        (
            ["--runtime", "4.7", "--runtime=4.8", "status"],
            "conflicting runtime selectors: 4.7, 4.8",
        ),
        (
            ["--runtime", "9.9", "status"],
            "unsupported runtime '9.9'; choose one of: 4.7, 4.8, 4.9",
        ),
    ],
)
def test_select_runtime_rejects_missing_duplicate_conflicting_and_unsupported(
    arguments, message
):
    with pytest.raises(cli.LauncherUsageError, match="^" + re.escape(message) + "$"):
        cli.select_runtime(arguments)


def test_double_dash_ends_launcher_option_scanning():
    assert cli.select_runtime(["--runtime=4.8", "query", "--", "--runtime"]) == (
        "4.8",
        ["query", "--", "--runtime"],
    )


@pytest.mark.parametrize(
    ("version", "module_name"),
    [("4.7", "moth_runtime.cli"), ("4.8", "moth_runtime_v4_8.cli"),
     ("4.9", "moth_runtime_v4_9.cli")],
)
def test_main_lazy_loads_selected_runtime_and_forwards_exit_code(
    monkeypatch, version, module_name
):
    imported: list[str] = []
    received: list[list[str]] = []

    def runtime_main(arguments):
        received.append(arguments)
        return 17

    def fake_import(name):
        imported.append(name)
        return SimpleNamespace(main=runtime_main)

    monkeypatch.setattr(cli, "import_module", fake_import)

    assert cli.main(["--runtime", version, "--json", "status"]) == 17
    assert imported == [module_name]
    assert received == [["--json", "status"]]


def test_usage_failure_does_not_import_a_runtime(monkeypatch, capsys):
    imported: list[str] = []
    monkeypatch.setattr(cli, "import_module", lambda name: imported.append(name))

    assert cli.main(["status"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        "usage: moth --runtime {4.7,4.8,4.9} <runtime options and command>\n"
        "moth: error: exactly one --runtime selector is required\n"
    )
    assert imported == []


def test_runtime_without_callable_entrypoint_fails_closed(monkeypatch):
    monkeypatch.setattr(cli, "import_module", lambda name: SimpleNamespace())

    with pytest.raises(RuntimeError, match="runtime 4.8 has no callable CLI entry point"):
        cli.main(["--runtime=4.8", "status"])
