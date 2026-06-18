"""Capture a manifest, optionally around a wrapped command."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from repro_manifest.collect import build_manifest
from repro_manifest.storage import save


def capture_manifest(
    *,
    argv: Sequence[str] | None = None,
    config_paths: Sequence[str | Path] = (),
):
    return build_manifest(argv=argv, config_paths=config_paths)


def run_and_capture(
    command: Sequence[str],
    manifest_path: str | Path,
    *,
    config_paths: Sequence[str | Path] = (),
    exec_fn=None,
) -> int:
    """Write a manifest describing the launch, then run ``command``.

    The manifest is captured and saved before the command starts, so it is
    present even if the command later fails. Returns the command's exit code.
    """

    if not command:
        raise ValueError("command must not be empty")
    manifest = build_manifest(argv=list(command), config_paths=config_paths)
    save(manifest, manifest_path)
    runner = exec_fn or _spawn
    return runner(command)


def _spawn(command: Sequence[str]) -> int:
    try:
        completed = subprocess.run(list(command), check=False)  # noqa: S603
    except FileNotFoundError:
        print(f"repro-manifest: command not found: {command[0]}", file=sys.stderr)
        return 127
    return completed.returncode
