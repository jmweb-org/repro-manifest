from __future__ import annotations

from repro_manifest.collect import (
    build_manifest,
    collect_command,
    collect_seeds,
    hash_config_files,
)
from repro_manifest.models import (
    SECTION_CONFIG,
    SECTION_GIT,
    SECTION_PACKAGES,
    SECTION_SEEDS,
)


def test_collect_command():
    out = collect_command(["python", "train.py", "--lr", "0.1"], "/work")
    assert out["argv"] == "python train.py --lr 0.1"
    assert out["cwd"] == "/work"


def test_hash_config_files_hashes_present_and_marks_missing(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("lr: 0.1\n")
    out = hash_config_files([cfg, tmp_path / "absent.yaml"])
    assert out[str(cfg)].startswith("sha256:")
    assert out[str(tmp_path / "absent.yaml")] == "missing"


def test_hash_is_stable(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("seed: 7\n")
    first = hash_config_files([cfg])
    second = hash_config_files([cfg])
    assert first == second


def test_collect_seeds_from_env_and_extra():
    seeds = collect_seeds(
        {"PYTHONHASHSEED": "0", "NUMPY_SEED": "42", "PATH": "/bin"},
        extra={"torch": 123},
    )
    assert seeds == {"NUMPY_SEED": "42", "PYTHONHASHSEED": "0", "torch": "123"}


def test_build_manifest_is_deterministic_with_injected_sources():
    def git(args):
        table = {
            ("rev-parse", "--is-inside-work-tree"): "true\n",
            ("rev-parse", "HEAD"): "c0ffee\n",
            ("rev-parse", "--abbrev-ref", "HEAD"): "main\n",
            ("status", "--porcelain"): "",
        }
        return table.get(tuple(args))

    manifest = build_manifest(
        argv=["python", "train.py"],
        cwd="/work",
        config_paths=[],
        seeds={"global": 1},
        environ={"PYTHONHASHSEED": "0"},
        git_runner=git,
        distributions=[("numpy", "1.26.0"), ("torch", "2.3.0")],
    )
    assert manifest.section(SECTION_GIT)["commit"] == "c0ffee"
    assert manifest.section(SECTION_SEEDS)["PYTHONHASHSEED"] == "0"
    assert manifest.section(SECTION_SEEDS)["global"] == "1"
    assert manifest.section(SECTION_PACKAGES)["torch"] == "2.3.0"
    assert SECTION_CONFIG not in manifest.sections
