# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-01-31

### Fixed

- **Permission Error**: Changed default cache directory from `project_root/.code-compass` to `~/.code-compass/<project_hash>` to avoid permission issues when running in system directories (e.g., `C:\Windows\System32`)
- **Encoding Error**: Added support for multiple encodings (UTF-8, UTF-8-SIG, Latin-1, CP1252, GBK) and automatic BOM removal to handle Windows-created files correctly
- **PageRank Division by Zero**: Fixed crash when indexing single-file projects or projects with no import relationships

### Changed

- Cache directory now uses user home directory with project-specific subdirectories
- File encoding detection now tries multiple encodings automatically
- PageRank algorithm now handles edge cases (empty projects, single files, no imports)

## [0.1.0] - 2026-01-30

### Added

- Initial release
- Python code parsing and indexing
- PageRank-based file importance ranking
- Code map generation (text and JSON formats)
- Symbol search (exact and fuzzy)
- SQLite-based caching with WAL mode
- CLI interface with 5 commands: index, map, find, stats, clear
- 44 unit tests with 100% pass rate
- Comprehensive documentation and README
