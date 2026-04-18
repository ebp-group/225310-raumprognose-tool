"""Orchestration script to run the dbt ETL pipeline and optionally launch the UI."""

import argparse
import subprocess
import sys
from pathlib import Path

DBT_PROJECT_DIR = Path(__file__).parent.parent / "dbt_project"
APP_ENTRY_POINT = Path(__file__).parent.parent / "app" / "flet_app.py"


def run_dbt() -> int:
    """Run `dbt run` inside the dbt_project directory.

    Returns:
        The return code of the dbt process.
    """
    print("Running dbt pipeline...")
    result = subprocess.run(
        ["dbt", "run", "--profiles-dir", str(DBT_PROJECT_DIR)],
        cwd=DBT_PROJECT_DIR,
        check=False,
    )
    if result.returncode != 0:
        print("dbt run failed.", file=sys.stderr)
    else:
        print("dbt run completed successfully.")
    return result.returncode


def launch_app() -> None:
    """Launch the Flet desktop application."""
    print("Launching Flet app...")
    subprocess.run(
        [sys.executable, str(APP_ENTRY_POINT)],
        check=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the Raumprognose ETL pipeline and optionally start the UI."
    )
    parser.add_argument(
        "--skip-dbt",
        action="store_true",
        help="Skip the dbt run step.",
    )
    parser.add_argument(
        "--launch-ui",
        action="store_true",
        help="Launch the Flet desktop UI after the ETL pipeline.",
    )
    args = parser.parse_args()

    if not args.skip_dbt:
        rc = run_dbt()
        if rc != 0:
            sys.exit(rc)

    if args.launch_ui:
        launch_app()


if __name__ == "__main__":
    main()
