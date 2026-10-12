"""Operator surface for canonical Runtime 4.7."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from . import CapabilityRuntime
from .canonical import read_json
from .encoder import LocalBGEEncoder
from .store import CapabilityStore

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="moth-live-4.7", description="Moth canonical closed-world proof-energy runtime")
    root.add_argument("--store", default=str(PROJECT_ROOT / "data/store-4.7.sqlite3"))
    root.add_argument("--generation")
    root.add_argument(
        "--json", action="store_true",
        help="emit the complete proof-bearing result instead of concise query output",
    )
    root.add_argument("--quiet", action="store_true", help="suppress standard output")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("init")
    sync = commands.add_parser("sync")
    sync.add_argument("directory")
    add = commands.add_parser("add")
    add.add_argument("source_file")
    add.add_argument("--as", dest="source_id")
    remove = commands.add_parser("remove")
    remove.add_argument("source_id")
    query = commands.add_parser("query", help="query the field and print the concise answer")
    query.add_argument("prompt")
    replay = commands.add_parser("replay")
    replay.add_argument("episode_id")
    replay.add_argument("--encoder-free", action="store_true", required=True)
    commands.add_parser("sources")
    commands.add_parser("history")
    commands.add_parser("status")
    commands.add_parser("verify")
    export = commands.add_parser("export")
    export.add_argument("destination")
    commands.add_parser("doctor")
    commands.add_parser("repl", help="open an interactive concise-answer session")
    return root


def _thresholds() -> dict:
    path = PROJECT_ROOT / "config/grounding-en-1.0.json"
    return read_json(path)["thresholds"]


def _emit(value, *, as_json: bool, compact: bool = False) -> None:
    if as_json or not isinstance(value, str):
        print(json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":") if compact else None,
            indent=None if compact else 2,
        ))
    else:
        print(value)


def _query_response(result: dict) -> object:
    """Return only the user-facing value from a verified runtime result."""
    status = result.get("status")
    if status == "REFUSAL":
        refusal = result.get("refusal")
        if not isinstance(refusal, dict):
            raise ValueError("malformed refusal result")
        code = refusal.get("code")
        message = refusal.get("message")
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


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        encoder = LocalBGEEncoder()
        store = CapabilityStore(args.store)
        if args.command == "init":
            store.init()
            result = {"runtime": "4.7", "store": str(store.path.resolve()), "initialized": True}
        elif args.command == "doctor":
            result = {"runtime": "4.7", "encoder": encoder.verify_assets(), "thresholds": _thresholds()}
        elif args.command == "sync":
            field = store.sync(args.directory, encoder=encoder)
            result = {"generation_id": field.generation_id, "field_hash": field.field_hash}
        elif args.command == "add":
            path = Path(args.source_file)
            field = store.add(args.source_id or path.name, path.read_text(encoding="utf-8"), encoder=encoder)
            result = {"generation_id": field.generation_id, "field_hash": field.field_hash}
        elif args.command == "remove":
            field = store.remove(args.source_id, encoder=encoder)
            result = {"generation_id": field.generation_id, "field_hash": field.field_hash}
        elif args.command == "query":
            runtime = CapabilityRuntime(store, encoder=encoder, generation_id=args.generation)
            result = runtime.query(args.prompt)
        elif args.command == "replay":
            result = json.loads(store.replay(args.episode_id, encoder_free=True).decode("utf-8"))
        elif args.command == "sources":
            result = {key: {"bytes": len(value.encode("utf-8"))} for key, value in store.active_language_sources().items()}
        elif args.command == "history":
            result = store.history()
        elif args.command == "status":
            result = {"runtime": "4.7", "store": str(store.path.resolve()), "head": store.head_id()}
        elif args.command == "verify":
            result = store.verify()
        elif args.command == "export":
            result = store.export(args.destination)
        elif args.command == "repl":
            if not sys.stdin.isatty():
                raise ValueError("repl requires an interactive terminal")
            runtime = CapabilityRuntime(store, encoder=encoder, generation_id=args.generation)
            while True:
                try:
                    prompt = input("moth-4.7> ")
                except (EOFError, KeyboardInterrupt):
                    if not args.quiet:
                        print()
                    return 0
                repl_result = runtime.query(prompt)
                if not args.quiet:
                    _emit(
                        repl_result if args.json else _query_response(repl_result),
                        as_json=args.json,
                        compact=not args.json,
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
        print(json.dumps(payload, sort_keys=True) if args.json else f"{payload['error']}: {payload['message']}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
