import duckdb


def get_duckdb_connection(
    db_path: str, read_only: bool = True
) -> duckdb.DuckDBPyConnection:
    """Return a DuckDB connection to the given database file.

    Args:
        db_path: Path to the DuckDB database file.
        read_only: Whether to open the connection in read-only mode. Defaults to True.

    Returns:
        A DuckDB connection object.
    """
    return duckdb.connect(db_path, read_only=read_only)
