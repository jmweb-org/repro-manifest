"""Read and write manifests as JSON."""

from __future__ import annotations

import json
from pathlib import Path

from repro_manifest.models import Manifest


def dumps(manifest: Manifest) -> str:
    return json.dumps(manifest.to_dict(), indent=2, sort_keys=False)


def loads(text: str) -> Manifest:
    return Manifest.from_dict(json.loads(text))


def save(manifest: Manifest, path: str | Path) -> None:
    Path(path).write_text(dumps(manifest) + "\n", encoding="utf-8")


def load(path: str | Path) -> Manifest:
    return loads(Path(path).read_text(encoding="utf-8"))
