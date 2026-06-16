from __future__ import annotations

from repro_manifest.diff import Risk, diff_manifests, has_high_risk
from repro_manifest.models import (
    SECTION_COMMAND,
    SECTION_GIT,
    SECTION_PACKAGES,
    SECTION_RUNTIME,
    SECTION_SEEDS,
    Manifest,
)


def man(patch=None, **sections):
    return Manifest(sections={k: dict(v) for k, v in sections.items()}, patch=patch)


def test_identical_manifests_have_no_changes():
    m = man(**{SECTION_GIT: {"commit": "abc"}})
    assert diff_manifests(m, m) == []


def test_commit_change_is_high():
    old = man(**{SECTION_GIT: {"commit": "abc"}})
    new = man(**{SECTION_GIT: {"commit": "def"}})
    changes = diff_manifests(old, new)
    assert changes[0].risk is Risk.HIGH
    assert has_high_risk(changes)


def test_seed_change_is_high():
    old = man(**{SECTION_SEEDS: {"PYTHONHASHSEED": "0"}})
    new = man(**{SECTION_SEEDS: {"PYTHONHASHSEED": "1"}})
    assert diff_manifests(old, new)[0].risk is Risk.HIGH


def test_command_change_is_medium():
    old = man(**{SECTION_COMMAND: {"argv": "python train.py"}})
    new = man(**{SECTION_COMMAND: {"argv": "python train.py --lr 0.2"}})
    changes = diff_manifests(old, new)
    assert changes[0].risk is Risk.MEDIUM
    assert not has_high_risk(changes)


def test_package_major_bump_is_high():
    old = man(**{SECTION_PACKAGES: {"torch": "2.3.0"}})
    new = man(**{SECTION_PACKAGES: {"torch": "3.0.0"}})
    assert diff_manifests(old, new)[0].risk is Risk.HIGH


def test_package_patch_bump_is_low():
    old = man(**{SECTION_PACKAGES: {"numpy": "1.26.0"}})
    new = man(**{SECTION_PACKAGES: {"numpy": "1.26.1"}})
    assert diff_manifests(old, new)[0].risk is Risk.LOW


def test_python_minor_change_is_high():
    old = man(**{SECTION_RUNTIME: {"python": "3.11.9"}})
    new = man(**{SECTION_RUNTIME: {"python": "3.12.0"}})
    assert diff_manifests(old, new)[0].risk is Risk.HIGH


def test_uncommitted_patch_difference_is_high():
    old = man(**{SECTION_GIT: {"commit": "abc"}})
    new = man(patch="diff --git ...\n+x\n", **{SECTION_GIT: {"commit": "abc"}})
    changes = diff_manifests(old, new)
    patch_changes = [c for c in changes if c.key == "uncommitted_patch"]
    assert patch_changes and patch_changes[0].risk is Risk.HIGH


def test_changes_sorted_high_risk_first():
    old = man(
        **{
            SECTION_COMMAND: {"argv": "python a.py"},
            SECTION_GIT: {"commit": "abc"},
        }
    )
    new = man(
        **{
            SECTION_COMMAND: {"argv": "python b.py"},
            SECTION_GIT: {"commit": "xyz"},
        }
    )
    changes = diff_manifests(old, new)
    assert changes[0].risk is Risk.HIGH
    assert changes[-1].risk is Risk.MEDIUM
