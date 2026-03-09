import os
from pathlib import Path

import streamlit as st

from utils import get_duckdb_connection

_DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "raumprognose.duckdb"
DB_PATH = os.environ.get("RAUMPROGNOSE_DB_PATH", str(_DEFAULT_DB_PATH))

st.set_page_config(page_title="Raumprognose Tool", layout="wide")
st.title("Raumprognose Tool")

try:
    conn = get_duckdb_connection(DB_PATH)
    tables = conn.execute("SHOW TABLES").fetchdf()
    if tables.empty:
        st.info(
            "No tables found in the database yet. Run the ETL pipeline first: "
            "`dbt run` inside the `dbt_project/` directory."
        )
    else:
        st.subheader("Available Tables")
        st.dataframe(tables)

        valid_table_names = set(tables["name"].tolist())
        selected_table = st.selectbox("Select a table to preview", tables["name"])
        if selected_table and selected_table in valid_table_names:
            df = conn.execute(
                f"SELECT * FROM {selected_table} LIMIT 100"  # noqa: S608
            ).fetchdf()
            st.subheader(f"Preview: {selected_table} (first 100 rows)")
            st.dataframe(df)
except Exception as e:
    st.error(f"Could not connect to DuckDB database at `{DB_PATH}`: {e}")
