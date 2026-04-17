# Changelog

All notable changes to this project are documented in this file.

## [0.3.0] - 2026-04-17

### Added

- Added `sso_auth.browser` optional module for headless Playwright automation.
- `BrowserSession`: sync context manager that handles launch, smart hybrid login, stealth patches, and storage_state persistence.
- Smart hybrid login: injects existing storage_state first, falls back to auto-UI login via Keycloak form when session expires.
- `stealth.apply_patches()`: lightweight JS init patches to remove `navigator.webdriver` and align browser fingerprint.
- `HumanBehavior`: configurable random delay and per-character typing helpers.
- `scraping` helpers: `download_to`, `extract_table`, `wait_any`.
- CLI subcommands `sso-auth browser open` and `sso-auth browser clear`.
- Unit tests for human behavior, login branching, and storage round-trip.

### Changed

- Bumped version to `0.3.0`.
- Playwright added as optional dependency (`pip install sso-auth[browser]`).

## [0.2.0] - 2026-04-17

### Added

- Added modular SDK architecture (`client`, `auth`, `storage`, `models`, `exceptions`, `config`).
- Added `SsoClient` facade with login, refresh, ensure_valid, logout, and token refresh callbacks.
- Added secure persistence: OS keyring for credentials/refresh token and local state/cookies files.
- Added new Typer-based CLI commands: `login`, `logout`, `whoami`, `token`, `refresh`, `status`.
- Added pytest test suite for auth flow, refresh flow, client behavior, and CLI token command.

### Changed

- Upgraded package to version `0.2.0`.
- Switched script entrypoint from `sso_auth.core:cli_main` to `sso_auth.cli:run`.
- Refactored legacy `core.py` into backward-compatible wrappers over the new SDK.
- Expanded project dependencies for typed models, settings, keyring, and rich CLI.

### Security

- Added `.gitignore` to prevent committing secrets/artifacts.
- Removed tracked `sso_tokens.json` token artifact from workspace.

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