"""Console and REPL for independent Runtime 5.3."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .artifact import ModelArtifact53
from .energy.schema import Level
from .runtime import Runtime53


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="moth --runtime 5.3",
        description="Moth independent energy-native HCF runtime",
    )
    root.add_argument(
        "--store", default=str(Path.cwd() / "data" / "store-5.3")
    )
    root.add_argument("--json", action="store_true")
    root.add_argument("--quiet", action="store_true")
    commands = root.add_subparsers(dest="command", required=True)

    reexecute = commands.add_parser('reexecute')
    reexecute.add_argument('conversation_id')
    reexecute.add_argument('turn_id')
    init = commands.add_parser("init")
    init.add_argument("--artifact", required=True)

    artifact = commands.add_parser("artifact")
    artifact_commands = artifact.add_subparsers(
        dest="artifact_command", required=True
    )
    build = artifact_commands.add_parser('build')
    build.add_argument('destination')
    for name in ("verify", "inspect"):
        child = artifact_commands.add_parser(name)
        child.add_argument("artifact_path", nargs="?")

    session = commands.add_parser("session")
    session_commands = session.add_subparsers(
        dest="session_command", required=True
    )
    create = session_commands.add_parser("create")
    create.add_argument("--system")
    create.add_argument("--skill", action="append", default=[], dest="skills")
    session_commands.add_parser("list")

    turn = commands.add_parser("turn")
    turn.add_argument("conversation_id")
    turn.add_argument("message")
    turn.add_argument("--presentation")

    repl = commands.add_parser("repl")
    repl.add_argument("--session", required=True, dest="conversation_id")

    inspect = commands.add_parser("inspect")
    inspect_commands = inspect.add_subparsers(
        dest="inspect_command", required=True
    )
    knowledge = inspect_commands.add_parser('knowledge')
    knowledge.add_argument('conversation_id')
    reasoning = inspect_commands.add_parser('reasoning')
    reasoning.add_argument('conversation_id')
    reasoning.add_argument('--turn', required=True)
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
    field_commands = field.add_subparsers(
        dest="field_command", required=True
    )
    field_commands.add_parser("list")
    field_inspect = field_commands.add_parser("inspect")
    field_inspect.add_argument("field_id")
    field_compile = field_commands.add_parser("compile")
    field_compile.add_argument("source")
    field_compile.add_argument(
        "--level", choices=("SYSTEM", "CONTEXT"), required=True
    )

    layer = commands.add_parser("layer")
    layer_commands = layer.add_subparsers(
        dest="layer_command", required=True
    )
    for name in ("list", "history"):
        child = layer_commands.add_parser(name)
        child.add_argument("conversation_id")
        child.add_argument(
            "--level", choices=("SYSTEM", "CONTEXT"), required=True
        )
    upsert = layer_commands.add_parser("upsert")
    upsert.add_argument("conversation_id")
    upsert.add_argument(
        "--level", choices=("SYSTEM", "CONTEXT"), required=True
    )
    upsert.add_argument("--key", required=True)
    upsert.add_argument("--object", required=True, dest="object_hash")
    upsert.add_argument(
        "--expected-revision", required=True, type=int
    )
    remove = layer_commands.add_parser("remove")
    remove.add_argument("conversation_id")
    remove.add_argument(
        "--level", choices=("SYSTEM", "CONTEXT"), required=True
    )
    remove.add_argument("--key", required=True)
    remove.add_argument(
        "--expected-revision", required=True, type=int
    )

    skill = commands.add_parser("skill")
    skill_commands = skill.add_subparsers(
        dest="skill_command", required=True
    )
    skill_compile = skill_commands.add_parser("compile")
    skill_compile.add_argument("field_id")
    skill_compile.add_argument("skill_source")
    skill_inspect = skill_commands.add_parser("inspect")
    skill_inspect.add_argument("compilation_id")
    skill_replay = skill_commands.add_parser("replay")
    skill_replay.add_argument("compilation_id")
    skill_plan = skill_commands.add_parser("plan")
    skill_plan.add_argument("compilation_id")
    skill_plan.add_argument("task_source")

    replay = commands.add_parser("replay")
    replay.add_argument("conversation_id")
    replay.add_argument("turn_id")
    verify = commands.add_parser("verify")
    verify.add_argument("--session", dest="conversation_id")
    commands.add_parser("status")
    commands.add_parser("doctor")
    query = commands.add_parser("query")
    query.add_argument("prompt")
    return root


def _emit(value: Any, *, as_json: bool) -> None:
    if isinstance(value, str) and not as_json:
        print(value)
    else:
        print(
            json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                indent=2 if as_json else None,
                separators=None if as_json else (",", ":"),
            )
        )


def _emit_bytes(value: bytes) -> None:
    binary = getattr(sys.stdout, "buffer", None)
    if binary is None:
        sys.stdout.write(value.decode("utf-8"))
        sys.stdout.flush()
    else:
        binary.write(value)
        binary.flush()


def _json_source(path: str) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("source root must be a JSON object")
    return value


def _repl(
    runtime: Runtime53,
    conversation_id: str,
    *,
    as_json: bool,
    quiet: bool,
) -> int:
    runtime.store.conversation(conversation_id)
    while True:
        try:
            message = input("moth-5.3> ")
        except (EOFError, KeyboardInterrupt):
            if not quiet:
                print()
            return 0
        command = message.strip()
        if command in {"/quit", "/exit"}:
            return 0
        if command == "/verify":
            value = runtime.verify_conversation(conversation_id)
        elif command.startswith("/"):
            value = {"error": "unknown REPL command", "command": command}
        else:
            result = runtime.turn(conversation_id, message)
            value = result if as_json else result["response"]
        if not quiet:
            _emit(value, as_json=as_json)


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == 'artifact' and args.artifact_command == 'build':
        from .build_artifact import build_artifact
        _emit(build_artifact(args.destination), as_json=args.json)
        return 0
    try:
        if args.command == "artifact" and args.artifact_path:
            artifact = ModelArtifact53.open(args.artifact_path)
            value = artifact.verify()
            if args.artifact_command == "inspect":
                value = {
                    **value,
                    "root": str(artifact.root),
                    "fields": sorted(artifact.fields),
                    "skills": sorted(artifact.skills),
                }
        elif args.command == "init":
            runtime = Runtime53.initialize(args.store, args.artifact)
            value = {
                **runtime.store.status(),
                "initialized": True,
                "foundation": runtime.inspect_foundation(),
                "artifact": runtime.inspect_artifact(),
            }
        else:
            runtime = Runtime53.open(args.store)
            if args.command == 'reexecute':
                value = runtime.reexecute(args.conversation_id,args.turn_id)
            elif args.command == 'inspect' and args.inspect_command == 'knowledge':
                value = runtime.inspect_knowledge(args.conversation_id)
            elif args.command == 'inspect' and args.inspect_command == 'reasoning':
                value = runtime.inspect_reasoning(args.conversation_id,args.turn)
            elif args.command == "artifact":
                value = runtime.inspect_artifact()
            elif (
                args.command == "session"
                and args.session_command == "create"
            ):
                conversation_id = runtime.create_conversation(
                    Path(args.system).read_text(encoding="utf-8") if args.system else "",
                    tuple(args.skills),
                )
                value = {
                    "runtime": "5.3",
                    "conversation_id": conversation_id,
                }
            elif (
                args.command == "session"
                and args.session_command == "list"
            ):
                value = runtime.store.list_conversations()
            elif args.command == "turn":
                result = runtime.turn(
                    args.conversation_id,
                    args.message,
                    args.presentation,
                )
                value = result if args.json else result["response"]
            elif args.command == "query":
                result = runtime.query(args.prompt)
                value = result if args.json else result["response"]
            elif args.command == "repl":
                return _repl(
                    runtime,
                    args.conversation_id,
                    as_json=args.json,
                    quiet=args.quiet,
                )
            elif (
                args.command == "inspect"
                and args.inspect_command == "foundation"
            ):
                value = runtime.inspect_foundation()
            elif (
                args.command == "inspect"
                and args.inspect_command == "artifact"
            ):
                value = runtime.inspect_artifact()
            elif (
                args.command == "inspect"
                and args.inspect_command == "context"
            ):
                value = runtime.inspect_context(
                    args.conversation_id, args.turn
                )
            elif (
                args.command == "inspect"
                and args.inspect_command == "hcf"
            ):
                value = runtime.inspect_hcf(
                    args.conversation_id, args.turn
                )
            elif (
                args.command == "inspect"
                and args.inspect_command == "metrics"
            ):
                runtime.store.turn(
                    args.conversation_id, turn_id=args.turn
                )
                value = runtime.store.metrics(args.turn)
            elif (
                args.command == "field"
                and args.field_command == "list"
            ):
                value = runtime.inspect_fields()
            elif (
                args.command == "field"
                and args.field_command == "inspect"
            ):
                value = runtime.inspect_field(args.field_id)
            elif (
                args.command == "field"
                and args.field_command == "compile"
            ):
                value = runtime.compile_hcf_field(
                    _json_source(args.source), Level[args.level]
                )
            elif args.command == "layer":
                level = Level[args.level]
                if args.layer_command == "list":
                    value = runtime.inspect_layer(
                        args.conversation_id, level
                    )
                elif args.layer_command == "history":
                    value = runtime.layer_history(
                        args.conversation_id, level
                    )
                elif args.layer_command == "upsert":
                    value = runtime.upsert_layer_field(
                        args.conversation_id,
                        level,
                        args.key,
                        args.object_hash,
                        args.expected_revision,
                    )
                else:
                    value = runtime.remove_layer_field(
                        args.conversation_id,
                        level,
                        args.key,
                        args.expected_revision,
                    )
            elif (
                args.command == "skill"
                and args.skill_command == "compile"
            ):
                value = runtime.compile_skill(
                    args.field_id,
                    Path(args.skill_source).read_text(encoding="utf-8"),
                )
            elif (
                args.command == "skill"
                and args.skill_command == "inspect"
            ):
                value = runtime.inspect_skill(args.compilation_id)
            elif (
                args.command == "skill"
                and args.skill_command == "replay"
            ):
                raw = runtime.replay_skill(args.compilation_id)
                if not args.quiet:
                    _emit_bytes(raw)
                return 0
            elif (
                args.command == "skill"
                and args.skill_command == "plan"
            ):
                value = runtime.plan_skill(
                    args.compilation_id,
                    _json_source(args.task_source),
                )
            elif args.command == "replay":
                raw = runtime.replay_turn(
                    args.conversation_id, args.turn_id
                )
                if not args.quiet:
                    _emit_bytes(raw)
                return 0
            elif args.command == "verify":
                value = (
                    runtime.verify_conversation(args.conversation_id)
                    if args.conversation_id
                    else runtime.store.verify_storage()
                )
            elif args.command == "status":
                value = runtime.store.status()
            elif args.command == "doctor":
                value = {
                    "runtime": "5.3",
                    "foundation": runtime.inspect_foundation(),
                    "context": {
                        "max_message_tokens": (
                            runtime.foundation.max_message_tokens
                        ),
                        "active_context_tokens": (
                            runtime.foundation.active_context_tokens
                        ),
                    },
                    "verified": True,
                }
            else:
                raise ValueError(f"unsupported command: {args.command}")
        if not args.quiet:
            _emit(value, as_json=args.json)
        return 0
    except Exception as exc:
        payload = {
            "error": type(exc).__name__,
            "code": getattr(exc, "code", None),
            "message": str(exc),
            "context": getattr(exc, "context", {}),
        }
        print(
            json.dumps(payload, sort_keys=True)
            if args.json
            else f"{payload['error']}: {payload['message']}",
            file=sys.stderr,
        )
        return 2
