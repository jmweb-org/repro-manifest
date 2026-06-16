"""Pure diff between two manifests, ranked by how likely a change is to make
two runs disagree.

A different commit, a dirty working tree, a changed seed or config hash, or a
different interpreter are high risk. Package and command changes are medium.
Everything is generic over sections except the uncommitted patch, which is
compared as a whole.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from repro_manifest.models import (
    SECTION_COMMAND,
    SECTION_CONFIG,
    SECTION_GIT,
    SECTION_PACKAGES,
    SECTION_RUNTIME,
    SECTION_SEEDS,
    Manifest,
)


class ChangeKind(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"


class Risk(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


_RISK_ORDER = {Risk.HIGH: 0, Risk.MEDIUM: 1, Risk.LOW: 2}


@dataclass(frozen=True, slots=True)
class Change:
    section: str
    key: str
    kind: ChangeKind
    old: str | None
    new: str | None
    risk: Risk

    @property
    def sort_key(self) -> tuple[int, str, str]:
        return (_RISK_ORDER[self.risk], self.section, self.key)


def _minor(version: str) -> str:
    parts = version.split(".")
    return ".".join(parts[:2]) if len(parts) >= 2 else version


def _major(version: str) -> str:
    return version.split(".", 1)[0].strip()


def _classify(section: str, key: str, old: str | None, new: str | None) -> Risk:
    if section == SECTION_GIT:
        return Risk.HIGH
    if section == SECTION_SEEDS:
        return Risk.HIGH
    if section == SECTION_CONFIG:
        return Risk.HIGH
    if section == SECTION_RUNTIME:
        if key == "python" and old and new and _minor(old) != _minor(new):
            return Risk.HIGH
        if key in {"implementation", "executable"}:
            return Risk.HIGH
        return Risk.MEDIUM
    if section == SECTION_COMMAND:
        return Risk.MEDIUM
    if section == SECTION_PACKAGES:
        if old and new and _major(old) != _major(new):
            return Risk.HIGH
        return Risk.MEDIUM if (old is None) != (new is None) else Risk.LOW
    return Risk.LOW


def _diff_section(name: str, old: dict[str, str], new: dict[str, str]) -> list[Change]:
    changes: list[Change] = []
    for key in sorted(set(old) | set(new)):
        before = old.get(key)
        after = new.get(key)
        if before == after:
            continue
        if before is None:
            kind = ChangeKind.ADDED
        elif after is None:
            kind = ChangeKind.REMOVED
        else:
            kind = ChangeKind.CHANGED
        changes.append(Change(name, key, kind, before, after, _classify(name, key, before, after)))
    return changes


def diff_manifests(old: Manifest, new: Manifest) -> list[Change]:
    """Return every difference between two manifests, highest risk first."""

    names = list(dict.fromkeys([*old.sections, *new.sections]))
    changes: list[Change] = []
    for name in names:
        changes.extend(_diff_section(name, old.section(name), new.section(name)))
    if (old.patch or None) != (new.patch or None):
        changes.append(
            Change(
                section=SECTION_GIT,
                key="uncommitted_patch",
                kind=ChangeKind.CHANGED,
                old=_patch_summary(old.patch),
                new=_patch_summary(new.patch),
                risk=Risk.HIGH,
            )
        )
    changes.sort(key=lambda c: c.sort_key)
    return changes


def _patch_summary(patch: str | None) -> str:
    if not patch:
        return "none"
    lines = patch.count("\n") + 1
    return f"{lines} lines"


def has_high_risk(changes: list[Change]) -> bool:
    return any(c.risk is Risk.HIGH for c in changes)
