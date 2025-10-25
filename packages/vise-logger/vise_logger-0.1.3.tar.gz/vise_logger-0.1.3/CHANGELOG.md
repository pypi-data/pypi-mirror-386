## [0.1.3] – 2025-10-25

### Added
 - README: improve installation instructions; include VS Code install link.
 - Metadata: add `[project.urls]` links and further log locations (Kiro, Codex, Junie, multiple for Copilot).
 - Robustness: validate `VISE_LOG_API_KEY` environment variable at startup.

### Changed
 - Robustness: resolve `%LOCALAPPDATA%` and `%APPDATA%` in log locations more robustly.

Compare: https://github.com/DavidFarago/vise-logger/compare/v0.1.2...v0.1.3

## [0.1.2] – 2025-10-19

### Added
- Logging: log package version at startup.

### Fixed
- Windows: avoid reading from an already-open temp file to prevent “[Errno 13] Permission denied”.
- README: document MCP JSON config when installing from PyPI.
- README: document alternative VS Code installation via CLI.

> Note: 0.1.1 was published to TestPyPI-only; all changes are included here.
