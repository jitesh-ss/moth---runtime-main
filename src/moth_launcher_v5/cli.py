"""Neutral terminal launcher for independently versioned Moth runtimes."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from importlib import import_module
import sys

RUNTIME_MODULES = {
    "4.7": "moth_runtime.cli",
    "4.8": "moth_runtime_v4_8.cli",
    "4.9": "moth_runtime_v4_9.cli",
    "5.0": "moth_runtime_v5_0.cli",
}

USAGE = "usage: moth --runtime {4.7,4.8,4.9,5.0} <runtime options and command>"


class LauncherUsageError(ValueError):
    """Raised when the neutral launcher cannot select exactly one runtime."""


def select_runtime(arguments: Sequence[str]) -> tuple[str, list[str]]:
    """Extract exactly one runtime selector and preserve all other arguments."""
    versions: list[str] = []
    forwarded: list[str] = []
    index = 0
    scanning = True

    while index < len(arguments):
        argument = arguments[index]
        if scanning and argument == "--":
            scanning = False
            forwarded.append(argument)
            index += 1
            continue
        if scanning and argument == "--runtime":
            if index + 1 >= len(arguments) or arguments[index + 1].startswith("--"):
                raise LauncherUsageError("--runtime requires a value")
            versions.append(arguments[index + 1])
            index += 2
            continue
        if scanning and argument.startswith("--runtime="):
            value = argument.partition("=")[2]
            if not value:
                raise LauncherUsageError("--runtime requires a value")
            versions.append(value)
            index += 1
            continue
        forwarded.append(argument)
        index += 1

    if not versions:
        raise LauncherUsageError("exactly one --runtime selector is required")
    if len(versions) > 1:
        if len(set(versions)) == 1:
            raise LauncherUsageError("--runtime may be specified only once")
        raise LauncherUsageError(
            "conflicting runtime selectors: " + ", ".join(versions)
        )

    version = versions[0]
    if version not in RUNTIME_MODULES:
        supported = ", ".join(sorted(RUNTIME_MODULES))
        raise LauncherUsageError(
            f"unsupported runtime {version!r}; choose one of: {supported}"
        )
    return version, forwarded


def load_runtime_main(version: str) -> Callable[[list[str] | None], int]:
    """Lazy-load only the selected runtime CLI."""
    module = import_module(RUNTIME_MODULES[version])
    entrypoint = getattr(module, "main", None)
    if not callable(entrypoint):
        raise RuntimeError(f"runtime {version} has no callable CLI entry point")
    return entrypoint


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    try:
        version, forwarded = select_runtime(arguments)
    except LauncherUsageError as exc:
        print(USAGE, file=sys.stderr)
        print(f"moth: error: {exc}", file=sys.stderr)
        return 2

    runtime_main = load_runtime_main(version)
    return runtime_main(forwarded)


if __name__ == "__main__":
    raise SystemExit(main())
