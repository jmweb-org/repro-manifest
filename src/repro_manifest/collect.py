"""Assemble a run manifest from the live environment.

Every source is injectable so the whole manifest can be built deterministically
in tests. The defaults read the real interpreter, environment, git tree and
installed packages.
"""

from __future__ import annotations

import hashlib
import os
import platform
import sys
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

from repro_manifest.gitinfo import GitRunner, collect_git, subprocess_git
from repro_manifest.models import (
    SECTION_COMMAND,
    SECTION_CONFIG,
    SECTION_GIT,
    SECTION_PACKAGES,
    SECTION_RUNTIME,
    SECTION_SEEDS,
    Manifest,
)

SEED_ENV_NAMES = ("PYTHONHASHSEED",)
SEED_ENV_SUFFIX = "_SEED"


def collect_runtime() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "executable": sys.executable,
    }


def collect_command(argv: Sequence[str], cwd: str) -> dict[str, str]:
    return {"argv": " ".join(argv), "cwd": cwd}


def hash_config_files(paths: Iterable[str | Path]) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in paths:
        path = Path(raw)
        try:
            data = path.read_bytes()
        except OSError:
            out[str(path)] = "missing"
            continue
        out[str(path)] = "sha256:" + hashlib.sha256(data).hexdigest()
    return dict(sorted(out.items()))


def collect_seeds(
    environ: Mapping[str, str], extra: Mapping[str, int] | None = None
) -> dict[str, str]:
    out: dict[str, str] = {}
    for name, value in environ.items():
        if name in SEED_ENV_NAMES or name.endswith(SEED_ENV_SUFFIX):
            out[name] = value
    for name, value in (extra or {}).items():
        out[name] = str(value)
    return dict(sorted(out.items()))


def collect_packages(distributions: Iterable[tuple[str, str]] | None = None) -> dict[str, str]:
    if distributions is None:
        distributions = _installed_distributions()
    packages: dict[str, str] = {}
    for name, version in distributions:
        packages[name.lower().replace("_", "-")] = version
    return dict(sorted(packages.items()))


def _installed_distributions() -> Iterable[tuple[str, str]]:
    from importlib.metadata import distributions

    for dist in distributions():
        name = dist.metadata["Name"]
        if name:
            yield name, dist.version


def build_manifest(
    *,
    argv: Sequence[str] | None = None,
    cwd: str | None = None,
    config_paths: Iterable[str | Path] = (),
    seeds: Mapping[str, int] | None = None,
    environ: Mapping[str, str] | None = None,
    git_runner: GitRunner | None = None,
    distributions: Iterable[tuple[str, str]] | None = None,
) -> Manifest:
    argv = list(argv) if argv is not None else list(sys.argv)
    cwd = cwd if cwd is not None else os.getcwd()
    environ = environ if environ is not None else os.environ
    git_runner = git_runner if git_runner is not None else subprocess_git(cwd)

    git_section, patch = collect_git(git_runner)
    sections: dict[str, dict[str, str]] = {
        SECTION_RUNTIME: collect_runtime(),
        SECTION_GIT: git_section,
        SECTION_COMMAND: collect_command(argv, cwd),
        SECTION_CONFIG: hash_config_files(config_paths),
        SECTION_SEEDS: collect_seeds(environ, seeds),
        SECTION_PACKAGES: collect_packages(distributions),
    }
    sections = {name: values for name, values in sections.items() if values}
    return Manifest(sections=sections, patch=patch)
