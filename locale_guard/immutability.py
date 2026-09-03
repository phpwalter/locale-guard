from __future__ import annotations

import subprocess
from pathlib import Path


class ImmutabilityError(RuntimeError):
    pass


def tool_root() -> Path:
    return Path(__file__).resolve().parents[1]


def check_immutable_dependency() -> None:
    root = tool_root()
    git_marker = root / ".git"
    if not git_marker.exists():
        return
    result = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=no"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise ImmutabilityError(result.stderr.strip() or "unable to inspect LocaleGuard Git state")
    changes = [line for line in result.stdout.splitlines() if line.strip()]
    if changes:
        joined = "\n".join(changes)
        raise ImmutabilityError("LocaleGuard immutable dependency contains tracked modifications:\n" + joined)
