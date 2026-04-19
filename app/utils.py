"""DuckDB utility helpers for the Raumprognose Tool.

Two usage modes are supported:

* **Interactive (Flet app)** – Use :func:`get_in_memory_connection` to create
  a lightweight, in-memory DuckDB instance.  Load user-selected Excel files
  into it with :func:`load_dataframe` and run ad-hoc SQL via
  :func:`query_to_dataframe`.

* **Batch / CI** – Use :func:`get_duckdb_connection` to open an on-disk
  DuckDB database (e.g. one produced by *dbt*) for read-only queries.
"""

from __future__ import annotations

import duckdb
import pandas as pd

# ── On-disk connection (for dbt / batch pipeline results) ────────────────────


def get_duckdb_connection(
    db_path: str, read_only: bool = True
) -> duckdb.DuckDBPyConnection:
    """Return a DuckDB connection to the given database file.

    Args:
        db_path: Path to the DuckDB database file.
        read_only: Whether to open the connection in read-only mode.
            Defaults to ``True``.

    Returns:
        A DuckDB connection object.
    """
    return duckdb.connect(db_path, read_only=read_only)


# ── In-memory connection (for interactive / Flet app use) ────────────────────


def get_in_memory_connection() -> duckdb.DuckDBPyConnection:
    """Create and return a new in-memory DuckDB connection.

    The connection has no on-disk storage and is ideal for the interactive
    Flet workflow where the user picks Excel files at runtime.

    Returns:
        A DuckDB in-memory connection.
    """
    return duckdb.connect(database=":memory:")


def load_dataframe(
    conn: duckdb.DuckDBPyConnection,
    df: pd.DataFrame,
    table_name: str,
    *,
    replace: bool = True,
) -> None:
    """Register a pandas DataFrame as a DuckDB table.

    Args:
        conn: An open DuckDB connection.
        df: The DataFrame to load.
        table_name: Name of the target table inside DuckDB.  Must contain
            only alphanumeric characters and underscores.
        replace: When ``True`` (default) an existing table with the same
            name is replaced; otherwise an error is raised.

    Raises:
        ValueError: If *table_name* contains characters other than
            ``[a-zA-Z0-9_]``.
    """
    import re

    if not re.fullmatch(r"[a-zA-Z_]\w*", table_name):
        raise ValueError(
            f"Invalid table name {table_name!r}: "
            "must start with a letter or underscore and contain only "
            "alphanumeric characters and underscores."
        )
    mode = "CREATE OR REPLACE" if replace else "CREATE"
    conn.execute(f"{mode} TABLE {table_name} AS SELECT * FROM df")


def query_to_dataframe(
    conn: duckdb.DuckDBPyConnection,
    sql: str,
) -> pd.DataFrame:
    """Execute a SQL query and return the result as a pandas DataFrame.

    Args:
        conn: An open DuckDB connection.
        sql: The SQL query string.

    Returns:
        A DataFrame with the query results.
    """
    return conn.execute(sql).fetchdf()
