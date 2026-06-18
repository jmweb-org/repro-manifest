"""Command-line interface for repro-manifest."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer
from rich.console import Console

from repro_manifest import __version__
from repro_manifest.collect import build_manifest
from repro_manifest.diff import diff_manifests, has_high_risk
from repro_manifest.render import changes_to_json, render_changes, render_manifest
from repro_manifest.runner import run_and_capture
from repro_manifest.storage import dumps, load, save

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Capture a reproducibility manifest for a run and diff two manifests.",
)
_out = Console()
_err = Console(stderr=True)

EXIT_OK = 0
EXIT_HIGH_RISK = 1
EXIT_BAD_INPUT = 2


def _version_callback(value: bool) -> None:
    if value:
        _out.print(f"repro-manifest {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    _version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show the version and exit.",
    ),
) -> None:
    """repro-manifest command-line interface."""


@app.command("capture")
def capture(
    output: Path | None = typer.Option(
        None, "-o", "--output", help="Write the manifest here (default: stdout)."
    ),
    config: list[Path] = typer.Option(None, "--config", help="Config file to hash (repeatable)."),
) -> None:
    """Capture a manifest of the current environment and git state."""

    manifest = build_manifest(config_paths=config or [])
    if output is None:
        _out.print_json(dumps(manifest))
    else:
        save(manifest, output)
        _err.print(f"repro-manifest: wrote {output}")


@app.command("show")
def show(
    config: list[Path] = typer.Option(None, "--config", help="Config file to hash."),
) -> None:
    """Pretty-print the current manifest."""

    _out.print(render_manifest(build_manifest(config_paths=config or [])))


@app.command(
    "run",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def run(
    ctx: typer.Context,
    output: Path = typer.Option(
        Path("manifest.json"), "-o", "--output", help="Where to write the manifest."
    ),
    config: list[Path] = typer.Option(None, "--config", help="Config file to hash."),
) -> None:
    """Write a manifest, then run COMMAND (after a literal --)."""

    command = list(ctx.args)
    if not command:
        _err.print("repro-manifest: no command given; pass it after --")
        raise typer.Exit(2)
    code = run_and_capture(command, output, config_paths=config or [])
    raise typer.Exit(code)


@app.command("diff")
def diff(
    old: Path = typer.Argument(..., help="Baseline manifest."),
    new: Path = typer.Argument(..., help="Manifest to compare."),
    as_json: bool = typer.Option(False, "--json", help="Emit changes as JSON."),
    check: bool = typer.Option(False, "--check", help="Exit non-zero on any high-risk change."),
) -> None:
    """Explain why two runs differ, highest risk first."""

    try:
        old_m = load(old)
        new_m = load(new)
    except (OSError, json.JSONDecodeError) as exc:
        _err.print(f"repro-manifest: could not read manifest: {exc}")
        raise typer.Exit(EXIT_BAD_INPUT) from exc

    changes = diff_manifests(old_m, new_m)
    if as_json:
        _out.print_json(json.dumps(changes_to_json(changes)))
    else:
        _out.print(render_changes(changes))

    if check and has_high_risk(changes):
        raise typer.Exit(EXIT_HIGH_RISK)


def entrypoint() -> None:
    try:
        app()
    except KeyboardInterrupt:  # pragma: no cover - interactive only
        print("repro-manifest: interrupted", file=sys.stderr)
        raise SystemExit(130) from None
