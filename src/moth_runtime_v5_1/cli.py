"""Console and REPL for standalone Runtime 5.1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .artifact import ModelArtifact51
from .runtime import Runtime51


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="moth --runtime 5.1",
        description="Moth standalone conversational HCF runtime",
    )
    root.add_argument("--store", default=str(PROJECT_ROOT / "data/store-5.1.sqlite3"))
    root.add_argument("--json", action="store_true")
    root.add_argument("--quiet", action="store_true")
    commands = root.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init")
    init_source = init.add_mutually_exclusive_group(required=True)
    init_source.add_argument(
        "--foundation", "--assets", dest="foundation",
        help="directory containing runtime-foundation.json (--assets is a compatibility alias)",
    )
    init_source.add_argument("--artifact", help="directory containing model-artifact.json")

    artifact = commands.add_parser("artifact")
    artifact_commands = artifact.add_subparsers(dest="artifact_command", required=True)
    artifact_verify = artifact_commands.add_parser("verify")
    artifact_verify.add_argument("artifact_path")
    artifact_inspect = artifact_commands.add_parser("inspect")
    artifact_inspect.add_argument("artifact_path")

    session = commands.add_parser("session")
    session_commands = session.add_subparsers(dest="session_command", required=True)
    create = session_commands.add_parser("create")
    create.add_argument("--system", required=True)
    create.add_argument("--skill", action="append", default=[], dest="skills")
    session_commands.add_parser("list")

    turn = commands.add_parser("turn")
    turn.add_argument("conversation_id")
    turn.add_argument("message")
    turn.add_argument("--presentation")

    repl = commands.add_parser("repl")
    repl.add_argument("--session", required=True, dest="conversation_id")

    inspect = commands.add_parser("inspect")
    inspect_commands = inspect.add_subparsers(dest="inspect_command", required=True)
    inspect_commands.add_parser("foundation")
    inspect_commands.add_parser("artifact")
    context = inspect_commands.add_parser("context")
    context.add_argument("conversation_id")
    context.add_argument("--turn")
    hcf = inspect_commands.add_parser("hcf")
    hcf.add_argument("conversation_id")
    hcf.add_argument("--turn", required=True)
    metrics = inspect_commands.add_parser("metrics")
    metrics.add_argument("conversation_id")
    metrics.add_argument("--turn", required=True)

    field = commands.add_parser("field")
    field_commands = field.add_subparsers(dest="field_command", required=True)
    field_commands.add_parser("list")
    field_inspect = field_commands.add_parser("inspect")
    field_inspect.add_argument("field_id")

    skill = commands.add_parser("skill")
    skill_commands = skill.add_subparsers(dest="skill_command", required=True)
    skill_compile = skill_commands.add_parser("compile")
    skill_compile.add_argument("--field", required=True, dest="field_id")
    skill_compile.add_argument("--file", required=True, dest="skill_file")
    skill_inspect = skill_commands.add_parser("inspect")
    skill_inspect.add_argument("compilation_id")
    skill_replay = skill_commands.add_parser("replay")
    skill_replay.add_argument("compilation_id")
    skill_plan = skill_commands.add_parser("plan")
    skill_plan.add_argument("compilation_id")
    skill_plan.add_argument("--task", required=True, dest="task_file")

    replay = commands.add_parser("replay")
    replay.add_argument("conversation_id")
    replay.add_argument("--turn", required=True)

    verify = commands.add_parser("verify")
    verify.add_argument("--session", dest="conversation_id")
    commands.add_parser("status")
    commands.add_parser("doctor")
    query = commands.add_parser("query")
    query.add_argument("prompt")
    return root


def _emit(value, *, as_json: bool) -> None:
    if isinstance(value, str) and not as_json:
        print(value)
    else:
        print(json.dumps(value, ensure_ascii=False, sort_keys=True,
                         indent=2 if as_json else None,
                         separators=None if as_json else (",", ":")))


def _emit_bytes(value: bytes) -> None:
    binary = getattr(sys.stdout, "buffer", None)
    if binary is None:
        sys.stdout.write(value.decode("utf-8"))
        sys.stdout.flush()
    else:
        binary.write(value)
        binary.flush()


def _system_prompt(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _repl(runtime: Runtime51, conversation_id: str, *, as_json: bool,
          quiet: bool) -> int:
    runtime.store.conversation(conversation_id)
    last_turn: str | None = None
    while True:
        try:
            message = input("moth-5.1> ")
        except (EOFError, KeyboardInterrupt):
            if not quiet:
                print()
            return 0
        command = message.strip()
        if command in {"/quit", "/exit"}:
            return 0
        if command == "/artifact":
            value = runtime.inspect_artifact()
        elif command == "/foundation":
            value = runtime.inspect_foundation()
        elif command == "/fields":
            value = runtime.inspect_fields()
        elif command == "/skills":
            value = runtime.store.list_skill_compilations()
        elif command.startswith("/plan "):
            value = runtime.store.skill_plan(command.split(maxsplit=1)[1])
        elif command == "/context":
            value = runtime.inspect_context(conversation_id, last_turn)
        elif command == "/hcf":
            value = runtime.inspect_hcf(conversation_id, last_turn) if last_turn else {
                "error": "no completed turn"
            }
        elif command == "/metrics":
            value = runtime.store.metrics(last_turn) if last_turn else {
                "error": "no completed turn"
            }
        elif command == "/verify":
            value = runtime.verify_conversation(conversation_id)
        elif command.startswith("/"):
            value = {"error": "unknown REPL command", "command": command}
        else:
            result = runtime.turn(conversation_id, message)
            last_turn = result["turn_id"]
            value = result if as_json else result["response"]
        if not quiet:
            _emit(value, as_json=as_json)


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "artifact":
            artifact = ModelArtifact51.open(args.artifact_path)
            value = artifact.verify() if args.artifact_command == "verify" else {
                **artifact.verify(), "root": str(artifact.root),
                "fields": sorted(artifact.fields),
                "surface_modes": [item["mode"] for item in artifact.capability_index["surface_modes"]],
            }
        elif args.command == "init":
            runtime = (
                Runtime51.initialize_from_artifact(args.store, args.artifact)
                if args.artifact else Runtime51.initialize(args.store, args.foundation)
            )
            value = {
                **runtime.store.status(), "initialized": True,
                "foundation": runtime.inspect_foundation(),
            }
            if runtime.artifact is not None:
                value["artifact"] = runtime.inspect_artifact()
        else:
            runtime = Runtime51.open(args.store)
            if args.command == "session" and args.session_command == "create":
                conversation_id = runtime.create_conversation(
                    _system_prompt(args.system), tuple(args.skills),
                )
                value = {"runtime": "5.1", "conversation_id": conversation_id}
            elif args.command == "session" and args.session_command == "list":
                value = runtime.store.list_conversations()
            elif args.command == "turn":
                result = runtime.turn(args.conversation_id, args.message, args.presentation)
                value = result if args.json else result["response"]
            elif args.command == "query":
                result = runtime.query(args.prompt)
                value = result if args.json else result["response"]
            elif args.command == "repl":
                return _repl(runtime, args.conversation_id, as_json=args.json,
                             quiet=args.quiet)
            elif args.command == "inspect" and args.inspect_command == "foundation":
                value = runtime.inspect_foundation()
            elif args.command == "inspect" and args.inspect_command == "artifact":
                value = runtime.inspect_artifact()
            elif args.command == "inspect" and args.inspect_command == "context":
                value = runtime.inspect_context(args.conversation_id, args.turn)
            elif args.command == "inspect" and args.inspect_command == "hcf":
                value = runtime.inspect_hcf(args.conversation_id, args.turn)
            elif args.command == "inspect" and args.inspect_command == "metrics":
                runtime.store.turn(args.conversation_id, turn_id=args.turn)
                value = runtime.store.metrics(args.turn)
            elif args.command == "field" and args.field_command == "list":
                value = runtime.inspect_fields()
            elif args.command == "field" and args.field_command == "inspect":
                value = runtime.inspect_field(args.field_id)
            elif args.command == "skill" and args.skill_command == "compile":
                value = runtime.compile_skill(
                    args.field_id, Path(args.skill_file).read_text(encoding="utf-8"),
                )
            elif args.command == "skill" and args.skill_command == "inspect":
                value = runtime.inspect_skill(args.compilation_id)
            elif args.command == "skill" and args.skill_command == "replay":
                raw = runtime.replay_skill(args.compilation_id)
                if not args.quiet:
                    _emit_bytes(raw)
                return 0
            elif args.command == "skill" and args.skill_command == "plan":
                task = json.loads(Path(args.task_file).read_text(encoding="utf-8"))
                value = runtime.plan_skill(args.compilation_id, task)
            elif args.command == "replay":
                raw = runtime.replay_turn(args.conversation_id, args.turn)
                if not args.quiet:
                    _emit_bytes(raw)
                return 0
            elif args.command == "verify":
                value = (
                    runtime.verify_conversation(args.conversation_id)
                    if args.conversation_id else runtime.store.verify_storage()
                )
            elif args.command == "status":
                value = runtime.store.status()
            elif args.command == "doctor":
                value = {
                    "runtime": "5.1", "foundation": runtime.inspect_foundation(),
                    "context": {
                        "max_message_tokens": runtime.assets.max_message_tokens,
                        "active_context_tokens": runtime.assets.active_context_tokens,
                    },
                    "verified": True,
                }
            else:
                raise ValueError(f"unsupported command: {args.command}")
        if not args.quiet:
            _emit(value, as_json=args.json)
        return 0
    except Exception as exc:
        payload = {"error": type(exc).__name__, "message": str(exc)}
        print(json.dumps(payload, sort_keys=True) if args.json
              else f"{payload['error']}: {payload['message']}", file=sys.stderr)
        return 2
