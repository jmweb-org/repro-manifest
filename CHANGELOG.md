# Changelog

All notable changes to this project are documented here. The format is based
on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-06-22

### Added
- Docker image and a published container entry point.
- Continuous integration across Python 3.10, 3.11 and 3.12.
- Expanded documentation, including the relationship to mlenv.

## [0.1.0] - 2026-06-18

### Added
- `run` command: write a manifest describing the launch, then run the wrapped
  command and forward its exit code.
- `capture` and `show` commands for the current environment and git state.
- Manifest captures runtime, git provenance (commit, branch, dirty flag and a
  patch of uncommitted changes), the command, config-file hashes, seeds and
  installed packages.
- `diff` command: explain why two runs differ, ranked by risk, with `--json`
  and a `--check` gate.

[0.2.0]: https://github.com/jmweb-org/repro-manifest/releases/tag/v0.2.0
[0.1.0]: https://github.com/jmweb-org/repro-manifest/releases/tag/v0.1.0
