"""Calculation functions for the Raumprognose Tool.

All functions are pure (no side-effects, no UI calls) and work
exclusively with :class:`pandas.DataFrame` objects so they can be tested
independently of the UI layer.  Internally every function opens a
short-lived in-memory DuckDB connection and runs SQL for the computation.
"""

from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd


def current_area_by_nutzungsart(df_gebaeude: pd.DataFrame) -> pd.DataFrame:
    """Aggregate the current total area (m²) by usage type.

    Args:
        df_gebaeude: Buildings-and-rooms DataFrame with at least the columns
            ``Raumtyp EBP`` and ``Fläche``.

    Returns:
        DataFrame with columns ``Raumtyp EBP`` and ``Fläche``,
        sorted by ``Raumtyp EBP``.

    SQL equivalent::

        SELECT "Raumtyp EBP", SUM("Fläche") AS "Fläche"
        FROM gebaeude
        GROUP BY "Raumtyp EBP"
        ORDER BY "Raumtyp EBP"
    """
    with duckdb.connect(":memory:") as conn:
        conn.register("gebaeude", df_gebaeude)
        return conn.execute("""
            SELECT "Raumtyp EBP", SUM("Fläche") AS "Fläche"
            FROM gebaeude
            GROUP BY "Raumtyp EBP"
            ORDER BY "Raumtyp EBP"
        """).fetchdf()


def future_demand(
    df_studierende: pd.DataFrame,
    df_faktoren: pd.DataFrame,
    szenario: str,
) -> pd.DataFrame:
    """Calculate future room demand (m²) per usage type and forecast year.

    For each (year, usage-type) combination the demand is:
        ``Rundungswert(Bezugsspalte, Schritt) × Faktor_m2_pro_Person``

    Args:
        df_studierende: Student-numbers DataFrame with column ``Jahr`` and
            one or more measure columns referenced by ``Bezug``.
        df_faktoren: Usage-factors DataFrame with columns ``Szenario``,
            ``Nutzungsart``, ``Faktor_m2_pro_Person``, ``Bezug``,
            ``Schritt``.
        szenario: The scenario name to use for filtering *df_faktoren*.

    Returns:
        DataFrame with columns ``Nutzungsart``, ``Jahr``, ``Bedarf_m2``.

    SQL equivalent::

        SELECT f."Nutzungsart", s."Jahr",
               s."Studierende" * f."Faktor_m2_pro_Person" AS "Bedarf_m2"
        FROM studierende AS s
        CROSS JOIN (
            SELECT "Nutzungsart", "Faktor_m2_pro_Person"
            FROM faktoren
            WHERE "Szenario" = ?
        ) AS f
        ORDER BY f."Nutzungsart", s."Jahr"
    """
    df_faktoren_szenario = df_faktoren[df_faktoren["Szenario"] == szenario].copy()
    if df_faktoren_szenario.empty:
        return pd.DataFrame(columns=["Nutzungsart", "Jahr", "Bedarf_m2"])

    bezug_values = set(df_faktoren_szenario["Bezug"].dropna().unique())
    missing_bezug_columns = sorted(bezug_values - set(df_studierende.columns))
    if missing_bezug_columns:
        raise ValueError(
            "Folgende Bezug-Spalten fehlen in den Studierenden-Daten: "
            f"{missing_bezug_columns}"
        )

    df_studierende_long = df_studierende.melt(
        id_vars=["Jahr"],
        var_name="Bezug",
        value_name="_bezugswert",
    )
    df_studierende_long = df_studierende_long[df_studierende_long["Bezug"].isin(bezug_values)]

    df_joined = df_studierende_long.merge(
        df_faktoren_szenario[
            ["Nutzungsart", "Faktor_m2_pro_Person", "Bezug", "Schritt"]
        ],
        on="Bezug",
        how="inner",
    )

    step = pd.to_numeric(df_joined["Schritt"], errors="coerce")
    bezugswert = pd.to_numeric(df_joined["_bezugswert"], errors="coerce")
    has_step = step.notna() & (step > 0)
    gerundet = bezugswert.where(~has_step, np.ceil(bezugswert / step) * step)

    df_joined["Bedarf_m2"] = gerundet * df_joined["Faktor_m2_pro_Person"]

    return (
        df_joined[["Nutzungsart", "Jahr", "Bedarf_m2"]]
        .sort_values(["Nutzungsart", "Jahr"])
        .reset_index(drop=True)
    )


def surplus_deficit(
    df_current: pd.DataFrame,
    df_demand: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate surplus or deficit of area per usage type and year.

    A positive value means there is currently more area than needed (surplus);
    a negative value means there is not enough area (deficit).

    Args:
        df_current: Output of :func:`current_area_by_nutzungsart` with columns
            ``Raumtyp EBP`` and ``Fläche``.
        df_demand: Output of :func:`future_demand` with columns ``Nutzungsart``,
            ``Jahr``, ``Bedarf_m2``.

    Returns:
        DataFrame with columns ``Nutzungsart``, ``Jahr``, ``Fläche``,
        ``Bedarf_m2``, ``Differenz_m2`` (positive = surplus, negative = deficit).

    SQL equivalent::

        SELECT d."Nutzungsart", d."Jahr",
               c."Fläche",
               d."Bedarf_m2",
               c."Fläche" - d."Bedarf_m2" AS "Differenz_m2"
        FROM demand AS d
        LEFT JOIN current_area AS c ON d."Nutzungsart" = c."Raumtyp EBP"
    """
    with duckdb.connect(":memory:") as conn:
        conn.register("current_area", df_current)
        conn.register("demand", df_demand)
        # ROW_NUMBER preserves the original row order of the demand table.
        return conn.execute("""
            SELECT d."Nutzungsart", d."Jahr",
                   c."Fläche",
                   d."Bedarf_m2",
                   c."Fläche" - d."Bedarf_m2" AS "Differenz_m2"
            FROM (SELECT *, ROW_NUMBER() OVER () AS _rn FROM demand) AS d
            LEFT JOIN current_area AS c ON d."Nutzungsart" = c."Raumtyp EBP"
            ORDER BY d._rn
        """).fetchdf()


def wide_results(df_sd: pd.DataFrame) -> pd.DataFrame:
    """Pivot the surplus/deficit table to a wide format for display.

    Args:
        df_sd: Output of :func:`surplus_deficit`.

    Returns:
        DataFrame indexed by ``Nutzungsart`` with one column per forecast year
        showing ``Differenz_m2``.

    SQL equivalent::

        PIVOT sd
        ON "Jahr"
        USING FIRST("Differenz_m2")
        GROUP BY "Nutzungsart"
        ORDER BY "Nutzungsart"
    """
    with duckdb.connect(":memory:") as conn:
        conn.register("sd", df_sd)
        result = conn.execute("""
            PIVOT sd
            ON "Jahr"
            USING FIRST("Differenz_m2")
            GROUP BY "Nutzungsart"
            ORDER BY "Nutzungsart"
        """).fetchdf()
    result = result.set_index("Nutzungsart")
    # DuckDB PIVOT names pivot columns after their string representation;
    # convert back to integers to match the original pandas pivot_table output.
    result.columns = pd.Index([int(c) for c in result.columns], name="Jahr")
    return result
