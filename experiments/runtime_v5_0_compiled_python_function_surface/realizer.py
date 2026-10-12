"""Compile-policy-driven generation and constrained execution of bounded Python."""

from __future__ import annotations

import ast
import os
from pathlib import Path
import resource
import subprocess
import sys
from tempfile import TemporaryDirectory
from typing import Any

from experiments.runtime_v5_0_compiled_surface_skill.compiler import validate_field, validate_policy
from experiments.runtime_v5_0_compiled_surface_skill.model import (
    COMPILATION_SCHEMA,
    digest as compiler_digest,
    normalize_text,
    policy_hash,
)

from .model import ARTIFACT_SCHEMA, ProgramFidelityFailure, digest, sha256_bytes


SEMANTIC_FIELDS = {
    "proposed-valid",
    "backup-valid",
    "selected-plan",
    "failure-reason",
}
REQUIRED_ACTIONS = {
    "VALIDATE_SEMANTIC_RESULT",
    "PLAN_PROGRAM",
    "BIND_INPUT_VARIABLES",
    "DEFINE_BOOLEAN_TEXT",
    "DEFINE_SELECT_PLAN",
    "DEFINE_BUILD_DECISION",
    "COMPUTE_SELECTED_PLAN",
    "BIND_LOCAL_VARIABLES",
    "CALL_BUILD_DECISION",
    "PRINT_DECISION",
    "PARSE_PROGRAM_AST",
    "VERIFY_AST_ALLOWLIST",
    "VERIFY_PROGRAM_SHAPE",
    "EXECUTE_CONSTRAINED",
    "PARSE_EXECUTION_OUTPUT",
    "VERIFY_EXACT_VALUE",
    "BIND_SEMANTIC_HASH",
    "BIND_POLICY_HASH",
    "EMIT_PROGRAM",
}
ALLOWED_AST_TYPES = (
    ast.Module,
    ast.Assign,
    ast.FunctionDef,
    ast.arguments,
    ast.arg,
    ast.If,
    ast.Return,
    ast.Expr,
    ast.Call,
    ast.Dict,
    ast.Name,
    ast.Load,
    ast.Store,
    ast.Constant,
)
FUNCTION_ARGUMENTS = {
    "boolean_text": ["value"],
    "select_plan": ["proposed", "backup"],
    "build_decision": ["proposed", "backup", "reason"],
}
MODULE_VARIABLES = ["proposed_valid", "backup_valid", "failure_reason", "decision"]
EXPECTED_CALL_COUNTS = {"boolean_text": 2, "select_plan": 1, "build_decision": 1, "print": 1}


def semantic_hash(runtime_output: dict[str, Any]) -> str:
    return digest("moth-runtime-v5-output/python-function-surface-1.0", runtime_output)


def _validate_semantic_result(runtime_output: dict[str, Any]) -> dict[str, str]:
    if not isinstance(runtime_output, dict) or set(runtime_output) != {"kind", "value"}:
        raise ProgramFidelityFailure("MALFORMED_SEMANTIC_RESULT", "Runtime output envelope is invalid")
    if runtime_output.get("kind") != "FACTOR_RESULT" or not isinstance(runtime_output.get("value"), dict):
        raise ProgramFidelityFailure("UNSUPPORTED_SEMANTIC_RESULT", "unsupported Runtime output kind")
    value = runtime_output["value"]
    if set(value) != SEMANTIC_FIELDS or any(not isinstance(item, str) for item in value.values()):
        raise ProgramFidelityFailure("MALFORMED_SEMANTIC_RESULT", "decision schema or types changed")
    proposed = value["proposed-valid"]
    backup = value["backup-valid"]
    selected = value["selected-plan"]
    reason = value["failure-reason"]
    if proposed not in {"true", "false"} or backup not in {"true", "false"}:
        raise ProgramFidelityFailure("MALFORMED_SEMANTIC_RESULT", "validity is outside the frozen domain")
    if selected not in {"PROPOSED", "BACKUP", "NONE"} or reason not in {"NONE", "RESOURCE", "PERMISSION", "DEADLINE"}:
        raise ProgramFidelityFailure("MALFORMED_SEMANTIC_RESULT", "decision is outside the frozen domain")
    expected = "PROPOSED" if proposed == "true" else "BACKUP" if backup == "true" else "NONE"
    if selected != expected or (reason == "NONE") != (proposed == "true"):
        raise ProgramFidelityFailure("INCONSISTENT_SEMANTIC_RESULT", "decision violates the factor contract")
    return dict(value)


def _validate_compilation(compilation: dict[str, Any], field: dict[str, Any]) -> dict[str, Any]:
    validate_field(field)
    if compilation.get("schema") != COMPILATION_SCHEMA:
        raise ProgramFidelityFailure("INVALID_SURFACE_POLICY", "compilation schema is invalid")
    if compilation.get("field_hash") != compiler_digest("moth-surface-instruction-field/1.0", field):
        raise ProgramFidelityFailure("HASH_BINDING_INVALID", "policy is detached from its field")
    policy = compilation.get("policy")
    if not isinstance(policy, dict):
        raise ProgramFidelityFailure("INVALID_SURFACE_POLICY", "compiled policy is absent")
    validate_policy(policy, field)
    if compilation.get("policy_hash") != policy_hash(policy):
        raise ProgramFidelityFailure("HASH_BINDING_INVALID", "compiled policy hash changed")
    missing = sorted(REQUIRED_ACTIONS - set(policy["workflow"]))
    if missing:
        raise ProgramFidelityFailure("INCOMPLETE_SURFACE_POLICY", "required action is absent", {"missing": missing})
    return policy


def _validate_request(request: str, field: dict[str, Any]) -> None:
    normalized = normalize_text(request).casefold().rstrip(".!?")
    routes = {normalize_text(str(item)).casefold().rstrip(".!?") for item in field["presentation_routes"]}
    if normalized not in routes:
        raise ProgramFidelityFailure("UNSUPPORTED_PRESENTATION", "request has no compiled Python route")


def build_program(value: dict[str, str]) -> str:
    proposed_literal = "True" if value["proposed-valid"] == "true" else "False"
    backup_literal = "True" if value["backup-valid"] == "true" else "False"
    reason_literal = repr(value["failure-reason"])
    return f'''proposed_valid = {proposed_literal}
backup_valid = {backup_literal}
failure_reason = {reason_literal}

def boolean_text(value):
    if value:
        return "true"
    return "false"

def select_plan(proposed, backup):
    if proposed:
        return "PROPOSED"
    if backup:
        return "BACKUP"
    return "NONE"

def build_decision(proposed, backup, reason):
    selected_plan = select_plan(proposed, backup)
    proposed_text = boolean_text(proposed)
    backup_text = boolean_text(backup)
    decision = {{
        "proposed-valid": proposed_text,
        "backup-valid": backup_text,
        "selected-plan": selected_plan,
        "failure-reason": reason,
    }}
    return decision

decision = build_decision(proposed_valid, backup_valid, failure_reason)
print(decision)'''


def verify_program_ast(text: str, field: dict[str, Any]) -> dict[str, Any]:
    try:
        tree = ast.parse(text, mode="exec")
    except SyntaxError as exc:
        raise ProgramFidelityFailure("INVALID_PYTHON", "program does not parse") from exc
    disallowed = sorted({type(node).__name__ for node in ast.walk(tree) if not isinstance(node, ALLOWED_AST_TYPES)})
    if disallowed:
        raise ProgramFidelityFailure("UNSAFE_PYTHON", "program contains disallowed AST nodes", {"nodes": disallowed})
    nodes = list(ast.walk(tree))
    if len(nodes) > int(field["program_shape"]["maximum_ast_nodes"]):
        raise ProgramFidelityFailure("RESOURCE_LIMIT", "program AST exceeds the frozen node limit")
    if len(tree.body) != 8:
        raise ProgramFidelityFailure("INVALID_PROGRAM_SHAPE", "top-level statement count changed")
    expected_types = [ast.Assign, ast.Assign, ast.Assign, ast.FunctionDef, ast.FunctionDef, ast.FunctionDef, ast.Assign, ast.Expr]
    if any(not isinstance(statement, expected) for statement, expected in zip(tree.body, expected_types)):
        raise ProgramFidelityFailure("INVALID_PROGRAM_SHAPE", "top-level statement sequence changed")

    assignments = [statement for statement in tree.body if isinstance(statement, ast.Assign)]
    module_names: list[str] = []
    for statement in assignments:
        if len(statement.targets) != 1 or not isinstance(statement.targets[0], ast.Name):
            raise ProgramFidelityFailure("INVALID_PROGRAM_SHAPE", "module assignment target changed")
        module_names.append(statement.targets[0].id)
    if module_names != MODULE_VARIABLES:
        raise ProgramFidelityFailure("INVALID_PROGRAM_SHAPE", "module variables changed", {"actual": module_names})

    functions = [statement for statement in tree.body if isinstance(statement, ast.FunctionDef)]
    if [function.name for function in functions] != list(FUNCTION_ARGUMENTS):
        raise ProgramFidelityFailure("INVALID_PROGRAM_SHAPE", "function sequence changed")
    for function in functions:
        arguments = function.args
        if (
            [item.arg for item in arguments.args] != FUNCTION_ARGUMENTS[function.name]
            or arguments.posonlyargs
            or arguments.kwonlyargs
            or arguments.vararg is not None
            or arguments.kwarg is not None
            or arguments.defaults
            or arguments.kw_defaults
            or function.decorator_list
            or function.returns is not None
        ):
            raise ProgramFidelityFailure("INVALID_PROGRAM_SHAPE", f"signature changed: {function.name}")

    call_counts = {name: 0 for name in EXPECTED_CALL_COUNTS}
    for call in (node for node in nodes if isinstance(node, ast.Call)):
        if not isinstance(call.func, ast.Name) or call.func.id not in call_counts or call.keywords:
            raise ProgramFidelityFailure("UNSAFE_PYTHON", "program contains an unapproved call")
        call_counts[call.func.id] += 1
    if call_counts != EXPECTED_CALL_COUNTS:
        raise ProgramFidelityFailure("INVALID_PROGRAM_SHAPE", "call graph changed", {"actual": call_counts})

    all_names = [node.id for node in nodes if isinstance(node, ast.Name)]
    if any(name.startswith("__") for name in all_names):
        raise ProgramFidelityFailure("UNSAFE_PYTHON", "dunder name is prohibited")
    maximum_lines = int(field["program_shape"]["maximum_lines"])
    maximum_bytes = int(field["program_shape"]["maximum_bytes"])
    line_count = text.count("\n") + 1
    byte_count = len(text.encode("utf-8"))
    if line_count > maximum_lines or byte_count > maximum_bytes:
        raise ProgramFidelityFailure("RESOURCE_LIMIT", "program exceeds line or byte limit")
    return {
        "node_count": len(nodes),
        "line_count": line_count,
        "byte_count": byte_count,
        "functions": [function.name for function in functions],
        "module_variables": module_names,
        "call_counts": call_counts,
        "capability_nodes": 0,
    }


def _resource_limits() -> None:
    resource.setrlimit(resource.RLIMIT_CPU, (1, 1))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1_048_576, 1_048_576))
    resource.setrlimit(resource.RLIMIT_NOFILE, (16, 16))


def execute_program(text: str, execution_parent: Path, field: dict[str, Any]) -> dict[str, Any]:
    execution_parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="program-", dir=execution_parent) as temporary:
        workdir = Path(temporary)
        program_path = workdir / "program.py"
        program_path.write_text(text, encoding="utf-8")
        environment = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONHASHSEED": "0",
            "LC_ALL": "C",
            "LANG": "C",
        }
        try:
            completed = subprocess.run(
                [sys.executable, "-I", "-S", "-B", str(program_path)],
                cwd=workdir,
                env=environment,
                capture_output=True,
                text=True,
                timeout=float(field["program_shape"]["execution_timeout_seconds"]),
                check=False,
                preexec_fn=_resource_limits,
                start_new_session=True,
            )
        except subprocess.TimeoutExpired as exc:
            raise ProgramFidelityFailure("EXECUTION_TIMED_OUT", "program exceeded the execution timeout") from exc
        if completed.returncode != 0:
            raise ProgramFidelityFailure(
                "EXECUTION_FAILED",
                "program returned a nonzero exit code",
                {"returncode": completed.returncode, "stderr": completed.stderr[:512]},
            )
        if completed.stderr or len(completed.stdout.encode("utf-8")) > 4096 or completed.stdout.count("\n") != 1:
            raise ProgramFidelityFailure("EXECUTION_FAILED", "program output channel shape changed")
        try:
            value = ast.literal_eval(completed.stdout.strip())
        except (SyntaxError, ValueError) as exc:
            raise ProgramFidelityFailure("EXECUTION_FAILED", "printed result is not a literal") from exc
        if not isinstance(value, dict):
            raise ProgramFidelityFailure("EXECUTION_FAILED", "printed result is not a dictionary")
        metadata = {
            "returncode": completed.returncode,
            "stdout_hash": sha256_bytes(completed.stdout.encode("utf-8")),
            "stderr_bytes": 0,
            "isolated_python": True,
            "site_disabled": True,
            "bytecode_disabled": True,
            "temporary_directory_removed": False,
        }
    metadata["temporary_directory_removed"] = not workdir.exists()
    if not metadata["temporary_directory_removed"]:
        raise ProgramFidelityFailure("ISOLATION_FAILURE", "execution directory was not removed")
    return {"value": value, "metadata": metadata}


def realize_artifact(
    runtime_output: dict[str, Any],
    presentation_request: str,
    compilation: dict[str, Any],
    field: dict[str, Any],
    execution_parent: Path,
) -> dict[str, Any]:
    policy = _validate_compilation(compilation, field)
    value = _validate_semantic_result(runtime_output)
    _validate_request(presentation_request, field)
    text = build_program(value)
    ast_metrics = verify_program_ast(text, field)
    execution = execute_program(text, execution_parent, field)
    if execution["value"] != value:
        raise ProgramFidelityFailure(
            "SEMANTIC_DRIFT",
            "executed program differs from the Runtime value",
            {"actual": execution["value"], "expected": value},
        )
    artifact = {
        "schema": ARTIFACT_SCHEMA,
        "status": "ANSWER",
        "format": "PYTHON",
        "text": text,
        "ast": ast_metrics,
        "execution": execution["metadata"],
        "execution_value_hash": digest("moth-python-function-execution-value/1.0", execution["value"]),
        "semantic_result_hash": semantic_hash(runtime_output),
        "policy_hash": policy_hash(policy),
    }
    artifact["artifact_hash"] = digest("moth-experimental-python-function-artifact/1.0", artifact)
    return artifact


def verify_artifact(
    artifact: dict[str, Any],
    runtime_output: dict[str, Any],
    compilation: dict[str, Any],
    field: dict[str, Any],
    execution_parent: Path,
) -> None:
    policy = _validate_compilation(compilation, field)
    value = _validate_semantic_result(runtime_output)
    if artifact.get("schema") != ARTIFACT_SCHEMA or artifact.get("status") != "ANSWER" or artifact.get("format") != "PYTHON":
        raise ProgramFidelityFailure("INVALID_ARTIFACT", "artifact envelope is invalid")
    without_hash = {key: item for key, item in artifact.items() if key != "artifact_hash"}
    if artifact.get("artifact_hash") != digest("moth-experimental-python-function-artifact/1.0", without_hash):
        raise ProgramFidelityFailure("ARTIFACT_TAMPERED", "artifact hash changed")
    if artifact.get("semantic_result_hash") != semantic_hash(runtime_output):
        raise ProgramFidelityFailure("HASH_BINDING_INVALID", "artifact is detached from Runtime semantics")
    if artifact.get("policy_hash") != policy_hash(policy):
        raise ProgramFidelityFailure("HASH_BINDING_INVALID", "artifact is detached from compiled policy")
    text = artifact.get("text")
    if not isinstance(text, str) or text != build_program(value):
        raise ProgramFidelityFailure("PROGRAM_DRIFT", "program bytes differ from the deterministic realization")
    if artifact.get("ast") != verify_program_ast(text, field):
        raise ProgramFidelityFailure("ARTIFACT_TAMPERED", "AST metrics changed")
    execution = execute_program(text, execution_parent, field)
    if execution["value"] != value:
        raise ProgramFidelityFailure("SEMANTIC_DRIFT", "replayed execution differs from Runtime semantics")
    if artifact.get("execution_value_hash") != digest("moth-python-function-execution-value/1.0", execution["value"]):
        raise ProgramFidelityFailure("SEMANTIC_DRIFT", "execution value hash changed")
    if artifact.get("execution") != execution["metadata"]:
        raise ProgramFidelityFailure("EXECUTION_DRIFT", "execution metadata changed")
