# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Raumprognose Tool — a **Flet** (Python) desktop application for spatial prognosis analysis of university/campus
buildings. Users load Excel input files, the app computes current area, future demand, and surplus/deficit per
usage type (Nutzungsart) across scenarios, and results can be exported to Excel/PNG.

## Commands

```bash
# Install deps (uv-managed project; dev tools install by default via dependency-groups)
uv sync

# Run the desktop app
uv run app/flet_app.py
# or
uv run flet run app/flet_app.py

# Run tests
uv run pytest
uv run pytest tests/test_calculations.py::test_current_area_by_nutzungsart_groups_and_sorts  # single test

# Lint / format
black .
ruff check . --fix

# Run all pre-commit hooks
pre-commit run --all-files

# Regenerate the sample Excel input files under data/
uv run scripts/generate_sample_data.py

# Batch/CI pipeline (dbt) + optionally launch UI
uv run scripts/run_pipeline.py               # dbt run only
uv run scripts/run_pipeline.py --launch-ui   # dbt run, then launch Flet UI
uv run scripts/run_pipeline.py --app-only    # skip dbt, launch Flet UI directly
# equivalent console-script entry point: run_pipeline / run_pipeline --launch-ui / run_pipeline --app-only

# Build the Windows executable
uv run flet pack app/flet_app.py --name RaumprognoseTool --icon app/assets/icon.ico --add-data=app/assets:assets
```

CI (`.github/workflows/build-windows.yml`) runs `uv sync` then `uv run pytest` on every push/PR
touching `app/**`, `tests/**`, `pyproject.toml`, or `uv.lock`, and builds the Windows exe on release.

## Architecture

Two independent workflows share the same calculation logic in `app/`:

1. **Interactive (Flet app)** — the primary workflow. Entry point `app/flet_app.py:main(page)`. User picks Excel
   files via the sidebar file picker, data is loaded with pandas (`app/data_loader.py`), optionally queried via an
   **in-memory** DuckDB connection (`app/utils.py:get_in_memory_connection`), calculations run in pandas
   (`app/calculations.py`), and results are shown in a 4-tab UI (Übersicht / Ergebnisse / Diagramme / Export) and
   exportable as styled Excel or PNG charts. No dbt required.
2. **Batch/CI (dbt)** — optional. `scripts/run_pipeline.py` runs `dbt run` inside `dbt_project/` against an
   **on-disk** DuckDB database (`app/utils.py:get_duckdb_connection`), for automated/nightly reporting. The dbt
   models are largely scaffolded (staging/intermediate are empty `.gitkeep` placeholders; only
   `dbt_project/models/raw_data/rauminventar.sql` exists), so most business logic still lives in
   `app/calculations.py`, not in SQL models.

Module responsibilities in `app/`:
- `data_loader.py` — loads and column-validates the three Excel inputs (`gebaeude_raeume`, `studierende`,
  `nutzungsfaktoren`) into DataFrames.
- `calculations.py` — pure pandas functions: `current_area_by_nutzungsart`, `future_demand`, `surplus_deficit`,
  `area_by_eigentumsform`, `wide_results`. These are the functions to target for calculation-logic changes and are
  unit-tested independently of the UI.
- `utils.py` — thin DuckDB connection/query helpers for both the in-memory (interactive) and on-disk (batch) modes.
- `flet_app.py` — the entire UI: layout, tabs, chart building (matplotlib figures), Excel export
  (`_build_excel`, `_build_excel_rounded`), and `main(page)` as the Flet entry point. This is a large, monolithic
  single-file UI module by design (mirrors Flet's typical app structure) — new UI logic generally goes here as
  additional module-level helper functions rather than a new file.
- `Raumprognose_Workflow.py` — a marimo notebook (not a plain script) that demonstrates the end-to-end
  load → calculate → visualize → export workflow interactively; useful as a reference/reproduction of the pipeline
  outside the Flet UI.

Data files live in `data/*.xlsx` (buildings/rooms, student numbers, usage factors per scenario); scenarios are
named Basis / Wachstum / Digital. `scripts/generate_sample_data.py` regenerates these three files from scratch.

Tests (`tests/`) cover `calculations.py` (pure function tests with hand-built DataFrames) and `flet_app.py`'s Excel
export helpers — there is no UI/widget-level testing.
