from __future__ import annotations

from types import SimpleNamespace

import pytest

from moth_launcher_v5_1 import cli


@pytest.mark.parametrize("version,module", [
    ("4.7", "moth_runtime.cli"),
    ("4.8", "moth_runtime_v4_8.cli"),
    ("4.9", "moth_runtime_v4_9.cli"),
    ("5.0", "moth_runtime_v5_0.cli"),
    ("5.1", "moth_runtime_v5_1.cli"),
])
def test_launcher_selects_every_preserved_runtime(monkeypatch, version, module):
    imported = []
    monkeypatch.setattr(cli, "import_module", lambda name: (
        imported.append(name) or SimpleNamespace(main=lambda arguments: 19)
    ))
    assert cli.main(["--runtime", version, "status"]) == 19
    assert imported == [module]


def test_launcher_rejects_unknown_runtime_without_import(monkeypatch, capsys):
    imported = []
    monkeypatch.setattr(cli, "import_module", lambda name: imported.append(name))
    assert cli.main(["--runtime", "9.9", "status"]) == 2
    assert imported == []
    assert "choose one of: 4.7, 4.8, 4.9, 5.0, 5.1" in capsys.readouterr().err


def test_launcher_preserves_runtime_arguments():
    assert cli.select_runtime([
        "--store", "runtime.sqlite3", "--runtime=5.1", "--json", "status",
    ]) == ("5.1", ["--store", "runtime.sqlite3", "--json", "status"])
