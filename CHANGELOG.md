# Changelog

All notable changes to Dashway are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Planned
- Power-ups: shield, slow motion, score multiplier
- Top-5 local leaderboard (SQLite)
- Pause menu
- Online leaderboard (FastAPI + JWT)

---

## [1.0.0] — 2024

### Added
- Full code refactor: snake_case naming, Google-style docstrings, type hints
- Renamed project from "VROUM 1" to **Dashway**
- `.gitignore`, `LICENSE` (MIT), `CHANGELOG.md`
- GitHub Actions CI pipeline (flake8 lint + pytest scaffold)
- GitHub Actions Release pipeline (PyInstaller → Windows .exe on tag push)
- Architecture diagram (Mermaid) in README

### Changed
- `save.txt` read/write now catches exceptions gracefully (no crash on first run)
- Dead code and commented-out debug draws removed from all modules
- `camelCase` methods kept as backward-compatible aliases; primary API is now `snake_case`
- Speed-increase logic moved to a dedicated `_increase_speed()` method

### Fixed
- `Menu.update_label` now correctly replaces labels without accumulating stale entries

---

## [0.1.0] — 2023-12-06 (Original)

### Added
- Initial group project release for the OpenIT 24-hour dev marathon
- Three-lane car dodger with coins, bombs, and a shop
- PyInstaller build (`dist/main.exe`)
