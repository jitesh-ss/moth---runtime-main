from __future__ import annotations

from types import SimpleNamespace

import pytest

from moth_launcher_v5_2 import cli


@pytest.mark.parametrize("version,module", [
    ("4.7", "moth_runtime.cli"),
    ("4.8", "moth_runtime_v4_8.cli"),
    ("4.9", "moth_runtime_v4_9.cli"),
    ("5.0", "moth_runtime_v5_0.cli"),
    ("5.1", "moth_runtime_v5_1.cli"),
    ("5.2", "moth_runtime_v5_2.cli"),
])
def test_launcher_selects_preserved_and_new_runtimes(monkeypatch, version, module):
    imported = []
    monkeypatch.setattr(cli, "import_module", lambda name: (
        imported.append(name) or SimpleNamespace(main=lambda arguments: 23)
    ))
    assert cli.main(["--runtime", version, "status"]) == 23
    assert imported == [module]


def test_launcher_rejects_unknown_runtime(monkeypatch, capsys):
    imported = []
    monkeypatch.setattr(cli, "import_module", lambda name: imported.append(name))
    assert cli.main(["--runtime", "9.9", "status"]) == 2
    assert imported == []
    assert "4.7, 4.8, 4.9, 5.0, 5.1, 5.2" in capsys.readouterr().err


def test_launcher_preserves_runtime_arguments():
    assert cli.select_runtime([
        "--store", "store-5.2", "--runtime=5.2", "--json", "status",
    ]) == ("5.2", ["--store", "store-5.2", "--json", "status"])
