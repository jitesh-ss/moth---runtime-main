import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from experiments.runtime_v5_0_compiled_surface_skill.compiler import compile_skill
from experiments.runtime_v5_0_compiled_python_function_surface.model import ProgramFidelityFailure
from experiments.runtime_v5_0_compiled_python_function_surface.realizer import (
    build_program,
    execute_program,
    realize_artifact,
    verify_program_ast,
)


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
VALUE = {
    "proposed-valid": "false",
    "backup-valid": "true",
    "selected-plan": "BACKUP",
    "failure-reason": "RESOURCE",
}


def _field() -> dict:
    return json.loads((FIXTURES / "python-function-surface-field-en-1.0.json").read_text())


def test_program_contains_functions_variables_and_computes_exact_value() -> None:
    field = _field()
    text = build_program(VALUE)
    metrics = verify_program_ast(text, field)
    assert metrics["functions"] == ["boolean_text", "select_plan", "build_decision"]
    assert metrics["module_variables"] == ["proposed_valid", "backup_valid", "failure_reason", "decision"]
    with TemporaryDirectory() as temporary:
        result = execute_program(text, Path(temporary), field)
    assert result["value"] == VALUE
    assert result["metadata"]["temporary_directory_removed"] is True


@pytest.mark.parametrize(
    "suffix",
    ["\nimport os", "\nopen('x', 'w')", "\nvalue.lower()", "\nfor x in decision:\n    print(x)"],
)
def test_program_ast_rejects_capabilities(suffix: str) -> None:
    with pytest.raises(ProgramFidelityFailure):
        verify_program_ast(build_program(VALUE) + suffix, _field())


def test_artifact_is_bound_to_compiled_policy_and_execution() -> None:
    field = _field()
    compilation = compile_skill((FIXTURES / "python-function-output/SKILL.md").read_text(), field)
    runtime_output = {"kind": "FACTOR_RESULT", "value": VALUE}
    with TemporaryDirectory() as temporary:
        artifact = realize_artifact(
            runtime_output,
            "Return an actual Python code block with functions and variables.",
            compilation,
            field,
            Path(temporary),
        )
    assert artifact["status"] == "ANSWER"
    assert artifact["execution"]["returncode"] == 0

