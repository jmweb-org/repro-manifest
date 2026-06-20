# repro-manifest

Wrap a run to capture a portable manifest of its environment, code, config and
seeds, then diff two manifests to explain why two runs differed.

Most ad-hoc runs leave no reproducibility receipt, and they are routinely
launched from a dirty working tree, so the commit hash alone does not
reproduce them. Reconstructing why two runs disagree by hand wastes an
afternoon. `repro-manifest` writes one JSON file per run and gives you a diff
built to answer exactly that question.

```console
$ repro-manifest run -o run.json -- python train.py --lr 0.1
# ... train.py runs; run.json now describes the launch

$ repro-manifest diff good.json run.json
risk  section  key                change
high  git      commit             a1b2c3d -> e4f5a6b
high  git      uncommitted_patch  none -> 38 lines
high  seeds    PYTHONHASHSEED     0 -> 1
medium  command  argv             ... --lr 0.05 -> ... --lr 0.1
```

## Install

```console
$ pip install repro-manifest
```

No services, no account, no SDK to weave into your training loop. One command,
one JSON file.

## What a manifest records

| Section | Contents |
| --- | --- |
| `runtime` | Python version, implementation, platform, interpreter path |
| `git` | Commit, branch, dirty flag, changed-file count, and a patch of uncommitted changes |
| `command` | The exact argv and working directory |
| `config` | SHA-256 of each config file you point it at |
| `seeds` | `PYTHONHASHSEED`, any `*_SEED` variable, and seeds you pass in |
| `packages` | Installed distributions and versions, read from the live environment |

Capturing from the live environment catches drift a lockfile missed, and the
patch makes a dirty-tree run reproducible when the commit hash is not enough.

## Commands

```console
$ repro-manifest run -o run.json -- python train.py   # capture, then run
$ repro-manifest capture -o run.json                  # capture without running
$ repro-manifest capture --config configs/train.yaml  # hash a config file
$ repro-manifest show                                  # pretty-print the current manifest
$ repro-manifest diff a.json b.json                    # explain the difference
$ repro-manifest diff a.json b.json --json             # machine-readable
$ repro-manifest diff a.json b.json --check            # exit non-zero on a high-risk change
```

## Risk levels

A change is **high** risk when it routinely breaks reproducibility: a different
commit, a dirty or differing uncommitted patch, a changed seed, a changed
config hash, a different interpreter, or a Python minor-version bump. A
major-version package bump is high; other package and command changes are
**medium**. Only high-risk changes trip `--check`.

This tool owns per-run provenance and seeds. For comparing the full software
and hardware stack on its own, see its sibling
[mlenv](https://github.com/jmweb-org/mlenv).

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Ran; no high-risk change (or `--check` not set). For `run`, the command's own code |
| 1 | `--check` found a high-risk change |
| 2 | A manifest file was missing or invalid |

## License

MIT. See [LICENSE](LICENSE).
