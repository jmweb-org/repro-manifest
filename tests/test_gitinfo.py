from __future__ import annotations

from repro_manifest.gitinfo import collect_git


class FakeGit:
    """A scripted git runner mapping argument tuples to canned stdout."""

    def __init__(self, responses: dict[tuple[str, ...], str | None]):
        self.responses = responses
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, args: list[str]) -> str | None:
        key = tuple(args)
        self.calls.append(key)
        return self.responses.get(key)


def test_not_a_work_tree_returns_empty():
    git = FakeGit({("rev-parse", "--is-inside-work-tree"): "false\n"})
    section, patch = collect_git(git)
    assert section == {}
    assert patch is None


def test_clean_tree():
    git = FakeGit(
        {
            ("rev-parse", "--is-inside-work-tree"): "true\n",
            ("rev-parse", "HEAD"): "abc123\n",
            ("rev-parse", "--abbrev-ref", "HEAD"): "main\n",
            ("status", "--porcelain"): "",
        }
    )
    section, patch = collect_git(git)
    assert section["commit"] == "abc123"
    assert section["branch"] == "main"
    assert section["dirty"] == "false"
    assert "dirty_files" not in section
    assert patch is None


def test_dirty_tree_captures_patch():
    git = FakeGit(
        {
            ("rev-parse", "--is-inside-work-tree"): "true\n",
            ("rev-parse", "HEAD"): "deadbeef\n",
            ("rev-parse", "--abbrev-ref", "HEAD"): "feature\n",
            ("status", "--porcelain"): " M train.py\n?? new.py\n",
            ("diff", "HEAD"): "diff --git a/train.py b/train.py\n+change\n",
        }
    )
    section, patch = collect_git(git)
    assert section["dirty"] == "true"
    assert section["dirty_files"] == "2"
    assert patch is not None
    assert "train.py" in patch


def test_missing_git_binary_returns_empty():
    section, patch = collect_git(lambda args: None)
    assert section == {}
    assert patch is None
