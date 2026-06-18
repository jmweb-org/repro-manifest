"""Render manifests and diffs for the terminal and as JSON."""

from __future__ import annotations

from rich.console import Group
from rich.table import Table
from rich.text import Text

from repro_manifest.diff import Change, Risk
from repro_manifest.models import SECTION_ORDER, Manifest

_RISK_STYLE = {Risk.HIGH: "bold red", Risk.MEDIUM: "yellow", Risk.LOW: "dim"}


def render_manifest(manifest: Manifest) -> Group:
    blocks: list[Table] = []
    names = list(SECTION_ORDER) + [n for n in manifest.sections if n not in SECTION_ORDER]
    for name in names:
        values = manifest.section(name)
        if not values:
            continue
        table = Table(title=name, title_justify="left", box=None, pad_edge=False)
        table.add_column("key", style="cyan")
        table.add_column("value", overflow="fold")
        for key, value in values.items():
            table.add_row(key, value)
        blocks.append(table)
    if manifest.patch:
        lines = manifest.patch.count("\n") + 1
        note = Table(title="patch", title_justify="left", box=None, pad_edge=False)
        note.add_column("key", style="cyan")
        note.add_column("value")
        note.add_row("uncommitted", f"{lines} lines")
        blocks.append(note)
    return Group(*blocks)


def changes_to_json(changes: list[Change]) -> list[dict]:
    return [
        {
            "section": c.section,
            "key": c.key,
            "kind": c.kind.value,
            "old": c.old,
            "new": c.new,
            "risk": c.risk.value,
        }
        for c in changes
    ]


def render_changes(changes: list[Change]) -> Group:
    if not changes:
        return Group(Text("manifests match", style="green"))
    table = Table(box=None, pad_edge=False)
    table.add_column("risk")
    table.add_column("section", style="cyan")
    table.add_column("key")
    table.add_column("change")
    for c in changes:
        table.add_row(
            Text(c.risk.value, style=_RISK_STYLE[c.risk]),
            c.section,
            c.key,
            _format(c),
        )
    return Group(table)


def _format(change: Change) -> str:
    if change.kind.value == "added":
        return f"+ {change.new}"
    if change.kind.value == "removed":
        return f"- {change.old}"
    return f"{change.old} -> {change.new}"
