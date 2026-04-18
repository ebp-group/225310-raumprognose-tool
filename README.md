# Raumprognose Tool

A **Flet** desktop application for spatial prognosis analysis of university/campus buildings,
backed by a **dbt + DuckDB** ETL pipeline.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| ETL / Transformations | [dbt](https://docs.getdbt.com/) + [DuckDB](https://duckdb.org/) |
| UI / Dashboard | [Flet](https://flet.dev/) (desktop) + [matplotlib](https://matplotlib.org/) |
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
│   └── utils.py                     # DuckDB connection helper
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
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -e ".[dev]"
```

### 3. Install pre-commit hooks

```bash
pre-commit install
```

## Generating Sample Data

Run the generation script once to create the three Excel input files under `data/`:

```bash
python scripts/generate_sample_data.py
```

This creates:
- `data/gebaeude_raeume.xlsx` – Buildings & rooms with usage type and floor area
- `data/studierende.xlsx` – Student numbers for 2024, 2030, 2040, 2050
- `data/nutzungsfaktoren.xlsx` – Area factors per student per scenario (Basis / Wachstum / Digital)

## Launching the Desktop Application

```bash
python app/flet_app.py
```

Or using the Flet CLI:

```bash
flet run app/flet_app.py
```

The application opens as a native desktop window with four tabs:

| Tab | Content |
|-----|---------|
| **Übersicht** | Raw input tables (buildings, students, usage factors) |
| **Ergebnisse** | Surplus/deficit table with green/red colour coding and summary metrics |
| **Diagramme** | Line chart (students), grouped bar chart (demand), bar charts (surplus/deficit) |
| **Export** | Save results as a styled Excel file or charts as PNG images |

Custom Excel files can be loaded via the sidebar file picker buttons.

## Running the ETL Pipeline

Run all dbt models from inside the `dbt_project/` directory:

```bash
cd dbt_project
dbt run
```

Or use the orchestration script from the project root:

```bash
python scripts/run_pipeline.py
```

To run the pipeline and then launch the desktop UI:

```bash
python scripts/run_pipeline.py --launch-ui
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
