from __future__ import annotations

import builtins
import json

import pytest

from moth_runtime import cli


def answer(value, *, kind: str = "ENTITY") -> dict:
    return {
        "status": "ANSWER",
        "output": {"kind": kind, "value": value},
        "proof": {"semantic_edge_ids": ["edge-1"]},
        "energy": {"violation_count": 0},
        "episode_id": "episode-1",
    }


def refusal() -> dict:
    return {
        "status": "REFUSAL",
        "refusal": {"code": "MISSING_PREMISE", "message": "No compiled proof reaches the result."},
        "episode_id": "episode-2",
    }


def install_query_result(monkeypatch: pytest.MonkeyPatch, result: dict) -> None:
    class FakeRuntime:
        def query(self, prompt: str) -> dict:
            return result

    monkeypatch.setattr(cli, "LocalBGEEncoder", lambda: object())
    monkeypatch.setattr(cli, "CapabilityStore", lambda path: object())
    monkeypatch.setattr(
        cli,
        "CapabilityRuntime",
        lambda store, *, encoder, generation_id: FakeRuntime(),
    )


def test_default_query_prints_only_identity_name(monkeypatch, capsys):
    result = answer({"meaning_id": "entity-1", "canonical_name": "Node-08"})
    install_query_result(monkeypatch, result)

    assert cli.main(["--store", "unused.sqlite3", "query", "compiled prompt"]) == 0
    assert capsys.readouterr().out == "Node-08\n"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ({"message": "alpha", "count": 1}, '{"count":1,"message":"alpha"}\n'),
        ([3, 2, 1], "[3,2,1]\n"),
        (7, "7\n"),
        (True, "true\n"),
        (None, "null\n"),
        ("compiled text", "compiled text\n"),
    ],
)
def test_default_query_prints_only_canonical_value(monkeypatch, capsys, value, expected):
    install_query_result(monkeypatch, answer(value, kind="COMPILED_JSON"))

    assert cli.main(["--store", "unused.sqlite3", "query", "compiled prompt"]) == 0
    assert capsys.readouterr().out == expected


def test_structured_canonical_name_field_is_not_collapsed(monkeypatch, capsys):
    value = {"canonical_name": "user data", "extra": True}
    install_query_result(monkeypatch, answer(value, kind="COMPILED_JSON"))

    assert cli.main(["--store", "unused.sqlite3", "query", "compiled prompt"]) == 0
    assert capsys.readouterr().out == '{"canonical_name":"user data","extra":true}\n'


def test_default_query_prints_concise_refusal(monkeypatch, capsys):
    install_query_result(monkeypatch, refusal())

    assert cli.main(["--store", "unused.sqlite3", "query", "compiled prompt"]) == 0
    assert capsys.readouterr().out == "MISSING_PREMISE: No compiled proof reaches the result.\n"


def test_json_query_preserves_complete_result(monkeypatch, capsys):
    result = answer({"meaning_id": "entity-1", "canonical_name": "Node-08"})
    install_query_result(monkeypatch, result)

    assert cli.main(["--json", "--store", "unused.sqlite3", "query", "compiled prompt"]) == 0
    assert json.loads(capsys.readouterr().out) == result


def test_quiet_query_emits_nothing(monkeypatch, capsys):
    install_query_result(monkeypatch, answer("hidden"))

    assert cli.main(["--quiet", "--store", "unused.sqlite3", "query", "compiled prompt"]) == 0
    assert capsys.readouterr().out == ""


def test_malformed_query_result_fails_closed(monkeypatch, capsys):
    install_query_result(monkeypatch, {"status": "ANSWER", "output": {}})

    assert cli.main(["--store", "unused.sqlite3", "query", "compiled prompt"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "ValueError: malformed answer result\n"


def test_default_repl_is_concise(monkeypatch, capsys):
    result = answer({"meaning_id": "entity-1", "canonical_name": "Node-08"})
    install_query_result(monkeypatch, result)
    prompts = iter(["compiled prompt"])

    def fake_input(prompt: str) -> str:
        try:
            return next(prompts)
        except StopIteration as exc:
            raise EOFError from exc

    monkeypatch.setattr(builtins, "input", fake_input)
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)

    assert cli.main(["--store", "unused.sqlite3", "repl"]) == 0
    assert capsys.readouterr().out == "Node-08\n\n"


def test_json_repl_preserves_complete_result(monkeypatch, capsys):
    result = answer({"meaning_id": "entity-1", "canonical_name": "Node-08"})
    install_query_result(monkeypatch, result)
    prompts = iter(["compiled prompt"])

    def fake_input(prompt: str) -> str:
        try:
            return next(prompts)
        except StopIteration as exc:
            raise EOFError from exc

    monkeypatch.setattr(builtins, "input", fake_input)
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)

    assert cli.main(["--json", "--store", "unused.sqlite3", "repl"]) == 0
    assert json.loads(capsys.readouterr().out) == result


def test_quiet_repl_emits_nothing(monkeypatch, capsys):
    install_query_result(monkeypatch, answer("hidden"))

    def fake_input(prompt: str) -> str:
        raise EOFError

    monkeypatch.setattr(builtins, "input", fake_input)
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)

    assert cli.main(["--quiet", "--store", "unused.sqlite3", "repl"]) == 0
    assert capsys.readouterr().out == ""
