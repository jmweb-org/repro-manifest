from __future__ import annotations

import json

from typer.testing import CliRunner

from repro_manifest import __version__
from repro_manifest import cli as cli_module
from repro_manifest.models import SECTION_GIT, Manifest
from repro_manifest.storage import dumps, load, loads, save

runner = CliRunner()


def test_manifest_round_trip_with_patch():
    m = Manifest(
        sections={SECTION_GIT: {"commit": "abc", "dirty": "true"}},
        patch="diff --git a/x b/x\n+1\n",
    )
    restored = loads(dumps(m))
    assert restored == m


def test_save_and_load(tmp_path):
    m = Manifest(sections={"runtime": {"python": "3.12.3"}})
    path = tmp_path / "m.json"
    save(m, path)
    assert path.read_text().endswith("\n")
    assert load(path) == m


def test_version():
    result = runner.invoke(cli_module.app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_capture_to_stdout_is_valid_json():
    result = runner.invoke(cli_module.app, ["capture"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "sections" in payload
    assert "runtime" in payload["sections"]


def test_capture_to_file(tmp_path):
    out = tmp_path / "m.json"
    result = runner.invoke(cli_module.app, ["capture", "-o", str(out)])
    assert result.exit_code == 0
    assert "runtime" in json.loads(out.read_text())["sections"]


def test_show_runs():
    assert runner.invoke(cli_module.app, ["show"]).exit_code == 0


def test_run_writes_manifest_and_forwards_exit_code(tmp_path):
    out = tmp_path / "m.json"
    result = runner.invoke(
        cli_module.app,
        ["run", "-o", str(out), "--", "sh", "-c", "exit 5"],
    )
    assert result.exit_code == 5
    assert out.exists()
    assert "command" in json.loads(out.read_text())["sections"]


def test_run_without_command_errors():
    assert runner.invoke(cli_module.app, ["run"]).exit_code == 2


def _write(tmp_path, name, sections, patch=None):
    path = tmp_path / name
    save(Manifest(sections=sections, patch=patch), path)
    return path


def test_diff_json(tmp_path):
    a = _write(tmp_path, "a.json", {SECTION_GIT: {"commit": "abc"}})
    b = _write(tmp_path, "b.json", {SECTION_GIT: {"commit": "def"}})
    result = runner.invoke(cli_module.app, ["diff", str(a), str(b), "--json"])
    assert result.exit_code == 0
    changes = json.loads(result.stdout)
    assert changes[0]["key"] == "commit"
    assert changes[0]["risk"] == "high"


def test_diff_check_fails_on_high_risk(tmp_path):
    a = _write(tmp_path, "a.json", {SECTION_GIT: {"commit": "abc"}})
    b = _write(tmp_path, "b.json", {SECTION_GIT: {"commit": "def"}})
    result = runner.invoke(cli_module.app, ["diff", str(a), str(b), "--check"])
    assert result.exit_code == cli_module.EXIT_HIGH_RISK


def test_diff_missing_file_is_bad_input(tmp_path):
    a = _write(tmp_path, "a.json", {SECTION_GIT: {"commit": "abc"}})
    result = runner.invoke(cli_module.app, ["diff", str(a), str(tmp_path / "missing.json")])
    assert result.exit_code == cli_module.EXIT_BAD_INPUT
