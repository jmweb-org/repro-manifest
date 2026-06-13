"""Data structures for a run manifest.

A manifest is a set of named sections (each a string-to-string mapping) plus an
optional patch: the diff of uncommitted changes captured at run time. Sections
hold everything that diffs cleanly key by key; the patch is handled separately
because it is free-form text.
"""

from __future__ import annotations

from dataclasses import dataclass, field

SCHEMA_VERSION = 1

SECTION_RUNTIME = "runtime"
SECTION_GIT = "git"
SECTION_COMMAND = "command"
SECTION_CONFIG = "config"
SECTION_SEEDS = "seeds"
SECTION_PACKAGES = "packages"
SECTION_GPU = "gpu"

SECTION_ORDER = (
    SECTION_RUNTIME,
    SECTION_GIT,
    SECTION_COMMAND,
    SECTION_CONFIG,
    SECTION_SEEDS,
    SECTION_PACKAGES,
    SECTION_GPU,
)


@dataclass(frozen=True, slots=True)
class Manifest:
    """A reproducibility receipt for a single run."""

    sections: dict[str, dict[str, str]] = field(default_factory=dict)
    patch: str | None = None
    schema_version: int = SCHEMA_VERSION

    def section(self, name: str) -> dict[str, str]:
        return self.sections.get(name, {})

    def to_dict(self) -> dict:
        ordered: dict[str, dict[str, str]] = {}
        for name in SECTION_ORDER:
            if name in self.sections:
                ordered[name] = dict(self.sections[name])
        for name, values in self.sections.items():
            if name not in ordered:
                ordered[name] = dict(values)
        out: dict = {"schema_version": self.schema_version, "sections": ordered}
        if self.patch is not None:
            out["patch"] = self.patch
        return out

    @classmethod
    def from_dict(cls, data: dict) -> Manifest:
        sections = {
            str(name): {str(k): str(v) for k, v in values.items()}
            for name, values in data.get("sections", {}).items()
        }
        return cls(
            sections=sections,
            patch=data.get("patch"),
            schema_version=int(data.get("schema_version", SCHEMA_VERSION)),
        )
