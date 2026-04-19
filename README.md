# Raumprognose Tool

A **Flet** desktop application for spatial prognosis analysis of university/campus buildings.
The interactive app uses **pandas** and an in-memory **DuckDB** engine for calculations.
An optional **dbt + DuckDB** batch pipeline is available for CI / automated reporting.

## Architecture

The tool supports two workflows:

| Workflow | Description | Entry point |
|----------|-------------|-------------|
| **Interactive (Flet app)** | User picks Excel files → reviews data → triggers calculation → exports results. Uses pandas for calculations and (optionally) in-memory DuckDB for SQL queries. No dbt required. | `uv run app/flet_app.py` |
| **Batch / CI** | Runs the dbt pipeline against canonical data files, materializes results into an on-disk DuckDB database. Suitable for automated/nightly reporting. | `uv run scripts/run_pipeline.py` |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| UI / Dashboard | [Flet](https://flet.dev/) (desktop) + [matplotlib](https://matplotlib.org/) |
| Calculations (interactive) | [pandas](https://pandas.pydata.org/) + [DuckDB](https://duckdb.org/) (in-memory) |
| Batch ETL (optional) | [dbt](https://docs.getdbt.com/) + [DuckDB](https://duckdb.org/) (on-disk) |
| Data / Excel I/O | [pandas](https://pandas.pydata.org/) + [openpyxl](https://openpyxl.readthedocs.io/) |
| Language | Python ≥ 3.10 |
| Code Quality | [black](https://black.readthedocs.io/), [ruff](https://docs.astral.sh/ruff/), [pre-commit](https://pre-commit.com/) |

## Project Structure

```
225310-raumprognose-tool/
├── .pre-commit-config.yaml         # Pre-commit hooks (black, ruff, etc.)
├── pyproject.toml                   # Project metadata and dependencies
├── README.md
├── .gitignore
├── data/
│   ├── gebaeude_raeume.xlsx         # Buildings and rooms sample data
│   ├── studierende.xlsx             # Student numbers (historical + forecast)
│   └── nutzungsfaktoren.xlsx        # Area factors per student per scenario
├── app/
│   ├── flet_app.py                  # Main Flet desktop application
│   ├── data_loader.py               # Excel file loading + validation
│   ├── calculations.py              # Area calculations (demand, surplus/deficit)
│   └── utils.py                     # DuckDB helpers (in-memory + on-disk)
├── dbt_project/
│   ├── dbt_project.yml              # dbt project configuration
│   ├── profiles.yml                 # DuckDB connection config
│   ├── models/
│   │   ├── staging/                 # Raw data cleaning models
│   │   ├── intermediate/            # Business logic transformations
│   │   └── marts/                   # Final analytical models
│   ├── seeds/                       # Static CSV data
│   ├── tests/                       # Data quality tests
│   └── macros/                      # Reusable SQL snippets
└── scripts/
    ├── generate_sample_data.py      # Generates the 3 sample Excel files
    └── run_pipeline.py              # Orchestration script
```

## Setup

### 1. Create and activate a virtual environment

```bash
uv venv
uv sync --all-extras
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
uv sync
uv pip install -e .
```

### 3. Install pre-commit hooks

```bash
pre-commit install
```

## Generating Sample Data

Run the generation script once to create the three Excel input files under `data/`:

```bash
uv run scripts/generate_sample_data.py
```

This creates:
- `data/gebaeude_raeume.xlsx` – Buildings & rooms with usage type and floor area
- `data/studierende.xlsx` – Student numbers for 2024, 2030, 2040, 2050
- `data/nutzungsfaktoren.xlsx` – Area factors per student per scenario (Basis / Wachstum / Digital)

## Launching the Desktop Application

```bash
uv run app/flet_app.py
```

Or using the Flet CLI:

```bash
uv run flet run app/flet_app.py
```

The application opens as a native desktop window with four tabs:

| Tab | Content |
|-----|---------|
| **Übersicht** | Raw input tables (buildings, students, usage factors) |
| **Ergebnisse** | Surplus/deficit table with green/red colour coding and summary metrics |
| **Diagramme** | Line chart (students), grouped bar chart (demand), bar charts (surplus/deficit) |
| **Export** | Save results as a styled Excel file or charts as PNG images |

Custom Excel files can be loaded via the sidebar file picker buttons.

## Running the ETL Pipeline (Batch / CI mode)

The dbt pipeline is **optional** — the Flet app works without it.  Use it
when you want to materialise results into an on-disk DuckDB database from
canonical data files.

Run all dbt models from inside the `dbt_project/` directory:

```bash
cd dbt_project
dbt run
```

Or use the orchestration script from the project root:

```bash
uv run scripts/run_pipeline.py
```

To run the pipeline and then launch the desktop UI:

```bash
uv run scripts/run_pipeline.py --launch-ui
```

To skip dbt entirely and launch only the Flet app:

```bash
uv run scripts/run_pipeline.py --app-only
```

There is even a shorthand for this:

```bash
run_pipeline              # only run dbt
run_pipeline --launch-ui  # run dbt AND launch the UI after
run_pipeline --app-only   # launch the UI without dbt
```

## Development

Run code formatting and linting:

```bash
black .
ruff check . --fix
```

Run all pre-commit checks manually:

```bash
pre-commit run --all-files
```

# TODO

- [ ] Herleitungsmodell in ein Excel zusammenführen (+3 Zeilen für Forschung, Services, und Stundenlohn), einige Raumkategorien steigen stufenweise an (~ alle 3'000 Studierende braucht es einen neuen Vorlesungssaal)
- [ ] Prognosedaten in ein Excel zusammenführen (für jedes Jahr, gemäss den gegeben Excels), 1x für Studiernde und 1x für Mitarbeitende
- [ ] Prognose für jedes Jahr rechnen, Output dann aber nur für definierte Jahre (z.B. 2030, 2040, 2050), Peaks unterwegs erkennen
- [ ] IST ändert sich jedes Jahr gemäss Jahr der Inbetriebnahme bzw. Ausserbetriebnahme
- [ ] Es gibt 2 Herleitungsmodelle und 2 Prognosemodelle (steigend + capped), insgesamt 4 Berechnungen