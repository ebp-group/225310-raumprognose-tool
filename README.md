# Raumprognose Tool

An ETL pipeline built with **dbt + DuckDB** and a **Streamlit** frontend for spatial prognosis analysis.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| ETL / Transformations | [dbt](https://docs.getdbt.com/) + [DuckDB](https://duckdb.org/) |
| UI / Dashboard | [Streamlit](https://streamlit.io/) |
| Language | Python ≥ 3.10 |
| Code Quality | [black](https://black.readthedocs.io/), [ruff](https://docs.astral.sh/ruff/), [pre-commit](https://pre-commit.com/) |

## Project Structure

```
225310-raumprognose-tool/
├── .pre-commit-config.yaml   # Pre-commit hooks (black, ruff, etc.)
├── pyproject.toml             # Project metadata and dependencies
├── README.md
├── .gitignore
├── dbt_project/
│   ├── dbt_project.yml        # dbt project configuration
│   ├── profiles.yml           # DuckDB connection config
│   ├── models/
│   │   ├── staging/           # Raw data cleaning models
│   │   ├── intermediate/      # Business logic transformations
│   │   └── marts/             # Final analytical models
│   ├── seeds/                 # Static CSV data
│   ├── tests/                 # Data quality tests
│   └── macros/                # Reusable SQL snippets
├── app/
│   ├── streamlit_app.py       # Main Streamlit entry point
│   └── utils.py               # Helper functions (DuckDB connection)
├── data/                      # DuckDB database files (git-ignored)
└── scripts/
    └── run_pipeline.py        # Orchestration script
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

## Launching the Streamlit UI

```bash
streamlit run app/streamlit_app.py
```

Or run the full pipeline and launch the UI in one step:

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