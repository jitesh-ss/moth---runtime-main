"""Operator surface for opt-in Runtime 4.8."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from . import ThreeWorldRuntime
from .canonical import read_json
from .encoder import LocalBGEEncoder
from .model import WorldRole
from .store import WorldStore

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="moth --runtime 4.8",
        description="Moth opt-in empty three-World proof-energy runtime",
    )
    root.add_argument("--store", default=str(PROJECT_ROOT / "data/store-4.8.sqlite3"))
    root.add_argument(
        "--json", action="store_true",
        help="emit the complete proof-bearing result instead of concise query output",
    )
    root.add_argument("--quiet", action="store_true", help="suppress standard output")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("init")
    sync = commands.add_parser("sync")
    sync.add_argument("--world", choices=("input", "main", "surface"), required=True)
    sync.add_argument("directory")
    add = commands.add_parser("add")
    add.add_argument("--world", choices=("input", "main", "surface"), required=True)
    add.add_argument("source_file")
    add.add_argument("--as", dest="source_id")
    remove = commands.add_parser("remove")
    remove.add_argument("--world", choices=("input", "main", "surface"), required=True)
    remove.add_argument("source_id")
    commands.add_parser("activate")
    query = commands.add_parser(
        "query", help="run the active three-World bundle and print its concise Surface response",
    )
    query.add_argument("prompt")
    replay = commands.add_parser(
        "replay", help="write the exact archived canonical result bytes",
    )
    replay.add_argument("episode_id")
    replay.add_argument(
        "--encoder-free", action="store_true", required=True,
        help="verify and emit the archived episode without loading the encoder",
    )
    sources = commands.add_parser("sources")
    sources.add_argument("--world", choices=("input", "main", "surface"), required=True)
    history = commands.add_parser("history")
    history.add_argument("--world", choices=("input", "main", "surface"))
    commands.add_parser("status")
    commands.add_parser("verify")
    export = commands.add_parser("export")
    export.add_argument("destination")
    commands.add_parser("doctor")
    commands.add_parser("repl", help="open an interactive concise Surface-response session")
    return root


def _thresholds() -> dict:
    return read_json(PROJECT_ROOT / "config/v4.8/grounding-en-1.0.json")["thresholds"]


def _emit(value, *, as_json: bool, compact: bool = False) -> None:
    if as_json or not isinstance(value, str):
        print(json.dumps(
            value, ensure_ascii=False, sort_keys=True,
            separators=(",", ":") if compact else None,
            indent=None if compact else 2,
        ))
    else:
        print(value)


def _emit_canonical_bytes(value: bytes) -> None:
    """Write an archived canonical result without reserializing or adding bytes."""
    binary = getattr(sys.stdout, "buffer", None)
    if binary is not None:
        binary.write(value)
        binary.flush()
        return
    # StringIO-style streams used by focused tests do not expose ``buffer``.
    sys.stdout.write(value.decode("utf-8"))
    sys.stdout.flush()


def _query_response(result: dict) -> object:
    status = result.get("status")
    if status == "REFUSAL":
        refusal = result.get("refusal")
        if not isinstance(refusal, dict):
            raise ValueError("malformed refusal result")
        code, message = refusal.get("code"), refusal.get("message")
        if not isinstance(code, str) or not isinstance(message, str):
            raise ValueError("malformed refusal result")
        return f"{code}: {message}"
    if status != "ANSWER":
        raise ValueError("malformed query result")
    output = result.get("output")
    if not isinstance(output, dict) or "value" not in output:
        raise ValueError("malformed answer result")
    value = output["value"]
    if (
        isinstance(value, dict)
        and set(value) == {"canonical_name", "meaning_id"}
        and isinstance(value.get("canonical_name"), str)
        and isinstance(value.get("meaning_id"), str)
    ):
        return value["canonical_name"]
    return value


def _role(value: str) -> WorldRole:
    return WorldRole(value.upper())


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        encoder = LocalBGEEncoder()
        store = WorldStore(args.store)
        if args.command == "init":
            store.init()
            result = {**store.status(), "store": str(store.path.resolve()), "initialized": True}
        elif args.command == "doctor":
            result = {"runtime": "4.8", "encoder": encoder.verify_assets(), "thresholds": _thresholds()}
        elif args.command == "sync":
            world = store.sync(_role(args.world), args.directory, encoder=encoder)
            result = {
                "role": world.world_role.value, "generation_id": world.generation_id,
                "world_hash": world.world_hash,
            }
        elif args.command == "add":
            path = Path(args.source_file)
            world = store.add(
                _role(args.world), args.source_id or path.name,
                path.read_text(encoding="utf-8"), encoder=encoder,
            )
            result = {
                "role": world.world_role.value, "generation_id": world.generation_id,
                "world_hash": world.world_hash,
            }
        elif args.command == "remove":
            world = store.remove(_role(args.world), args.source_id, encoder=encoder)
            result = {
                "role": world.world_role.value, "generation_id": world.generation_id,
                "world_hash": world.world_hash,
            }
        elif args.command == "activate":
            result = store.activate().canonical()
        elif args.command == "query":
            result = ThreeWorldRuntime(store, encoder=encoder).query(args.prompt)
        elif args.command == "replay":
            replay_bytes = store.replay(args.episode_id, encoder_free=True)
            if not args.quiet:
                _emit_canonical_bytes(replay_bytes)
            return 0
        elif args.command == "sources":
            result = {
                key: {"bytes": len(value.encode("utf-8"))}
                for key, value in store.active_sources(_role(args.world)).items()
            }
        elif args.command == "history":
            result = store.history(None if args.world is None else _role(args.world))
        elif args.command == "status":
            result = {**store.status(), "store": str(store.path.resolve())}
        elif args.command == "verify":
            result = store.verify()
        elif args.command == "export":
            result = store.export(args.destination)
        elif args.command == "repl":
            if not sys.stdin.isatty():
                raise ValueError("repl requires an interactive terminal")
            runtime = ThreeWorldRuntime(store, encoder=encoder)
            while True:
                try:
                    prompt = input("moth-4.8> ")
                except (EOFError, KeyboardInterrupt):
                    if not args.quiet:
                        print()
                    return 0
                repl_result = runtime.query(prompt)
                if not args.quiet:
                    _emit(
                        repl_result if args.json else _query_response(repl_result),
                        as_json=args.json, compact=not args.json,
                    )
        else:
            raise ValueError(f"unsupported command: {args.command}")
        if not args.quiet:
            display = result
            compact = False
            if args.command == "query" and not args.json:
                display = _query_response(result)
                compact = True
            _emit(display, as_json=args.json, compact=compact)
        return 0
    except Exception as exc:
        payload = {"error": type(exc).__name__, "message": str(exc)}
        print(
            json.dumps(payload, sort_keys=True)
            if args.json else f"{payload['error']}: {payload['message']}",
            file=sys.stderr,
        )
        return 2
