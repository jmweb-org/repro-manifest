"""Capture git provenance for a run.

The single git entry point is a callable that runs a git subcommand and returns
its stdout, so tests inject a fake instead of shelling out. A run launched from
a dirty tree records the commit, the dirty flag, the changed files, and the
full patch of uncommitted changes, which is what makes it reproducible when the
commit hash alone is not enough.
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path

GitRunner = Callable[[list[str]], str | None]


def subprocess_git(cwd: str | Path | None = None) -> GitRunner:
    def run(args: list[str]) -> str | None:
        try:
            result = subprocess.run(  # noqa: S603
                ["git", *args],  # noqa: S607
                cwd=str(cwd) if cwd else None,
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            return None
        if result.returncode != 0:
            return None
        return result.stdout

    return run


def collect_git(run: GitRunner) -> tuple[dict[str, str], str | None]:
    """Return (section, patch). Empty section if this is not a git work tree."""

    inside = run(["rev-parse", "--is-inside-work-tree"])
    if inside is None or inside.strip() != "true":
        return {}, None

    section: dict[str, str] = {}
    commit = _first_line(run(["rev-parse", "HEAD"]))
    if commit:
        section["commit"] = commit
    branch = _first_line(run(["rev-parse", "--abbrev-ref", "HEAD"]))
    if branch:
        section["branch"] = branch

    status = run(["status", "--porcelain"]) or ""
    changed = [line[3:] for line in status.splitlines() if line.strip()]
    section["dirty"] = "true" if changed else "false"
    if changed:
        section["dirty_files"] = str(len(changed))

    patch = None
    if changed:
        diff = run(["diff", "HEAD"])
        patch = diff if diff else None
    return section, patch


def _first_line(text: str | None) -> str | None:
    if not text:
        return None
    line = text.strip().splitlines()[0] if text.strip() else ""
    return line or None
