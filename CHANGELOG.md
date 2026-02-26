# Changelog

All notable changes to this project are documented in this file.

## [0.1.1] - 2026-02-25

### Added

- Added `CHANGELOG.md` for release tracking.

### Changed

- Restructured project into a proper Python package using `src` layout.
- Added modern packaging metadata via `pyproject.toml`.
- Added package entrypoints and importable public API in `sso_auth`.
- Added distributable artifacts support (`wheel` and `sdist`).

### Fixed

- Removed top-level module name collision that blocked `import sso_auth`.
