# Changelog

All notable changes to ToolSym will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial monorepo scaffold consolidating `Tool_Condition_Monitoring` and
  `CNC-Tool-CAD-to-Mask-Simulation` into a single `toolsym` package with two
  PySide6 desktop apps (`toolsym-tcm`, `toolsym-sim`) and a CLI (`toolsym`).
- Shared algorithm library (`toolsym.{config,io,geometry,signal,symmetry,reconstruction,simulation}`)
  extracted from the two source repos so GUIs only orchestrate, never compute.
- `toolsym.config` with `TOOLSYM_DATA` env var resolution, centralised
  `CameraIntrinsics` and `VoxelGridSpec` loaders — removes all hardcoded paths.
- pyproject-based packaging with optional dependency groups
  (`simulation`, `gpu`, `ml`, `dev`, `docs`).
- CI on Windows/macOS/Linux, release pipeline that publishes to PyPI and
  bundles PyInstaller `.exe` artefacts per app.
- Test fixtures, ruff + mypy + pre-commit configuration.

## [0.1.0] — TBD

First public alpha. See `MIGRATION.md` for the mapping from the legacy
repos to the new package layout.

[Unreleased]: https://github.com/alirezafalah/ToolSym/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/alirezafalah/ToolSym/releases/tag/v0.1.0
