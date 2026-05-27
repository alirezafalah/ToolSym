# Contributing to ToolSym

Thanks for taking the time to contribute. This document covers how to set
up a development environment, the conventions the project follows, and the
PR workflow.

## Quick start

```bash
git clone https://github.com/alirezafalah/ToolSym.git
cd ToolSym
python -m venv .venv
.venv\Scripts\activate              # Windows
# source .venv/bin/activate         # macOS / Linux
pip install -e ".[dev]"             # core + dev tools
pip install -e ".[simulation,dev]"  # core + simulation extras + dev tools
pre-commit install
pytest
```

The simulation extras (`pyvista`, `vtk`, `cadquery`) are heavy and only
required if you are touching `toolsym.simulation`, `toolsym.reconstruction.cad_voxelizer`,
or the `toolsym-sim` app. Skip them when working on signal/symmetry code.

## Layout

```
toolsym/                shared library (pure functions, no Qt)
  config.py             paths, intrinsics, voxel-grid spec
  io/                   masks, signals, voxels read/write
  geometry/             master-mask, tilt regression, ROI
  signal/               1D pipeline (hybrid paper)
  symmetry/             phase-shift comparison (symmetry paper)
  reconstruction/       visual hull (real) + voxelizer (CAD)
  simulation/           render, noise, augment
  widgets/              shared PySide6 widgets and theme
apps/
  toolsym_tcm/          analysis app (image-to-signal, symmetry, visual hull)
  toolsym_sim/          dataset-generation app (render, noise, augment, voxelize)
tests/                  pytest, organised by package
```

**Hard rule:** modules under `toolsym/` (except `widgets/`) must not import
any Qt symbol. GUIs orchestrate, library computes.

## Coding style

- **Formatter / linter:** [ruff](https://docs.astral.sh/ruff/). `ruff format`
  and `ruff check` are enforced by pre-commit and CI. Line length 100.
- **Type hints:** required on every public function. Mypy runs on `toolsym/`
  and `apps/` in CI; ignore third-party imports per `pyproject.toml`.
- **Naming exceptions:** single-letter coefficient names (`A`, `B`, `C`, `D`)
  are kept to match the sinusoidal model in the hybrid paper. Ruff is
  configured to allow this.
- **Docstrings:** required on public functions. Reference the relevant paper
  section when the function implements a published algorithm.
- **No bare paths:** never hardcode an absolute path. Use `toolsym.config.data_root()`
  to resolve the user's DATA folder.

## Tests

- New algorithms must come with at least one pytest case under `tests/`.
- Mark slow tests with `@pytest.mark.slow`, GPU tests with `@pytest.mark.gpu`,
  GUI tests with `@pytest.mark.gui`, simulation-extras tests with
  `@pytest.mark.simulation`. CI's default run excludes all four.
- Algorithm regression tests should hit `tests/fixtures/` — a small bundled
  tool (a few frames + the expected CSV/NPZ output). Reproducing published
  numbers is the strongest evidence a refactor didn't break the science.

## Commits

- Conventional Commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`,
  `chore:`, `ci:`. Scope optional.
- Each commit should leave the test suite green.
- Reference papers when modifying algorithm behaviour (e.g. *"Implements
  Eq. 7 from Falah 2025"*).

## Pull requests

- Branch from `main`.
- Fill in the PR template (TODO).
- CI must be green before review.
- Squash-merge with a Conventional Commit title.

## Releases

Tag-based. Push a tag `vX.Y.Z` on `main` and the release workflow will:

1. Build sdist + wheel and publish to PyPI.
2. Build PyInstaller bundles for `toolsym-tcm` and `toolsym-sim` on
   Windows/macOS/Linux.
3. Create a GitHub Release with auto-generated notes and all artefacts.

Bump `version` in `pyproject.toml` and `CITATION.cff` in the same commit
as the tag.

## Questions

Open an issue or email falirezah94@gmail.com.
