"""Disposable filesystem instance for compiled instruction policies."""

from __future__ import annotations

import base64
from copy import deepcopy
from pathlib import Path, PurePosixPath
from typing import Any

from .compiler import validate_policy
from .model import canonical_bytes, digest, make_archive, policy_hash, sha256_bytes


class IsolatedInstructionInstance:
    """Execute one frozen task inside one caller-provided temporary directory."""

    def __init__(self, root: Path, field: dict[str, Any]):
        self.root = root.resolve()
        self.field = field
        self.workspace = self.root / "workspace"
        self.workspace.mkdir(parents=True, exist_ok=False)
        self.archives: list[dict[str, Any]] = []

    def _populate(self, task: dict[str, Any]) -> None:
        for relative, text in sorted(task.get("files", {}).items()):
            path = self.workspace / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(str(text), encoding="utf-8")
        for relative, encoded in sorted(task.get("binary_files", {}).items()):
            path = self.workspace / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(base64.b64decode(encoded))

    def _snapshot(self) -> dict[str, dict[str, str]]:
        result: dict[str, dict[str, str]] = {}
        for path in sorted(item for item in self.workspace.rglob("*") if item.is_file()):
            data = path.read_bytes()
            result[path.relative_to(self.workspace).as_posix()] = {
                "base64": base64.b64encode(data).decode("ascii"),
                "sha256": sha256_bytes(data),
            }
        return result

    @staticmethod
    def _safe_relative(target: str) -> bool:
        value = PurePosixPath(target)
        return bool(target) and not value.is_absolute() and ".." not in value.parts

    def execute(self, policy: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
        validate_policy(policy, self.field)
        self._populate(task)
        before = self._snapshot()
        task_hash = digest("moth-instruction-task/1.0", task)
        current_text: str | None = None
        staged_text: str | None = None
        resulting_text: str | None = None
        before_target_hash: str | None = None
        after_target_hash: str | None = None
        evidence: dict[str, str] | None = None
        trace: list[dict[str, Any]] = []
        target_value = task.get("target")
        target: str | None = target_value if isinstance(target_value, str) else None
        status = "ANSWER"
        code: str | None = None

        def stop(new_status: str, new_code: str, action: str, detail: str) -> None:
            nonlocal status, code
            status = new_status
            code = new_code
            trace.append({"action": action, "outcome": new_status, "code": new_code, "detail": detail})

        for action in policy["workflow"]:
            if status != "ANSWER":
                break
            if action == "LOCATE_TARGET":
                if target is None:
                    stop("REFUSED", "TARGET_NOT_UNIQUE", action, "target is not singular")
                    continue
                if not self._safe_relative(target):
                    stop("REFUSED", "SCOPE_VIOLATION", action, "target escapes permitted workspace")
                    continue
                if target not in before:
                    stop("REFUSED", "TARGET_NOT_UNIQUE", action, "target is missing")
                    continue
            elif action == "READ_TARGET":
                assert target is not None
                try:
                    current_text = (self.workspace / target).read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    stop("REFUSED", "UNSUPPORTED_TARGET", action, "target is not UTF-8 text")
                    continue
                before_target_hash = sha256_bytes(current_text.encode("utf-8"))
            elif action == "CHECK_TEXT_FILE":
                assert target is not None
                if PurePosixPath(target).suffix.casefold() not in {".txt", ".md", ".json", ".toml", ".yaml", ".yml"}:
                    stop("REFUSED", "UNSUPPORTED_TARGET", action, "target is not an admitted text file")
                    continue
            elif action == "CHECK_SCOPE":
                if task.get("extra_change"):
                    stop("REFUSED", "SCOPE_VIOLATION", action, "request includes an unrelated change")
                    continue
                if task.get("protected") and not task.get("authorized"):
                    stop("AUTHORITY_REQUIRED", "PROTECTED_TARGET", action, "protected target lacks authorization")
                    continue
            elif action == "COUNT_MATCHES":
                old = task.get("old")
                new = task.get("new")
                if not isinstance(old, str) or not old or not isinstance(new, str) or old == new:
                    stop("REFUSED", "PRECONDITION_FAILED", action, "replacement values are invalid")
                    continue
                assert current_text is not None
                if current_text.count(old) != 1:
                    stop("REFUSED", "PRECONDITION_FAILED", action, "old text does not occur exactly once")
                    continue
            elif action == "STAGE_REPLACEMENT":
                assert current_text is not None
                staged_text = current_text.replace(task["old"], task["new"], 1)
            elif action == "APPLY_REPLACEMENT":
                assert target is not None and staged_text is not None
                (self.workspace / target).write_text(staged_text, encoding="utf-8")
            elif action == "READ_RESULT":
                assert target is not None
                resulting_text = (self.workspace / target).read_text(encoding="utf-8")
            elif action == "VERIFY_EXACT_CHANGE":
                assert target is not None and current_text is not None and staged_text is not None
                current_snapshot = self._snapshot()
                other_before = {key: value for key, value in before.items() if key != target}
                other_after = {key: value for key, value in current_snapshot.items() if key != target}
                if resulting_text != staged_text or other_before != other_after:
                    (self.workspace / target).write_text(current_text, encoding="utf-8")
                    stop("REFUSED", "VERIFICATION_FAILED", action, "exact-change verification failed")
                    continue
            elif action == "HASH_RESULT":
                assert resulting_text is not None
                after_target_hash = sha256_bytes(resulting_text.encode("utf-8"))
            elif action == "RECORD_EVIDENCE":
                assert before_target_hash is not None and after_target_hash is not None
                evidence = {"before_sha256": before_target_hash, "after_sha256": after_target_hash}
            elif action == "REPORT_RESULT":
                pass
            else:
                raise AssertionError(f"validated but unimplemented action: {action}")
            trace.append({"action": action, "outcome": "SATISFIED"})

        after = self._snapshot()
        changed_paths = sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path))
        if status == "ANSWER":
            assert target is not None and after_target_hash is not None
            report: dict[str, Any] | None = {
                "target": target,
                "verification": "PASSED",
                "after_sha256": after_target_hash,
            }
            if evidence is not None:
                report["evidence"] = evidence
        else:
            report = None

        core = {
            "schema": "moth-instruction-instance-result/1.0",
            "task_id": task["id"],
            "task_hash": task_hash,
            "policy_hash": policy_hash(policy),
            "status": status,
            "code": code,
            "trace": trace,
            "report": report,
            "changed_paths": changed_paths,
            "before_workspace_hash": digest("moth-task-workspace/1.0", before),
            "after_workspace_hash": digest("moth-task-workspace/1.0", after),
            "final_workspace": after,
            "dispatch_count": 0,
            "network_attempts": 0,
        }
        result = {**core, "result_hash": digest("moth-instruction-instance-result/1.0", core)}
        archive = make_archive(result)
        self.archives.append(deepcopy(archive))
        return result
