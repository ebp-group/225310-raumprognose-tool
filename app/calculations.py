"""Calculation functions for the Raumprognose Tool.

All functions are pure (no side-effects, no UI calls) and work
exclusively with :class:`pandas.DataFrame` objects so they can be tested
independently of the UI layer.  Internally every function opens a
short-lived in-memory DuckDB connection and runs SQL for the computation.
"""

from __future__ import annotations

import duckdb
import pandas as pd


def current_area_by_nutzungsart(
    df_gebaeude: pd.DataFrame,
    years: list[int],
) -> pd.DataFrame:
    """Aggregate the available total area (m²) by usage type and year.

    Only rooms whose operational period covers a given year are included:
    a room is counted for year *y* when
    ``Betriebsaufnahme <= y <= Betriebsende``.  ``NULL`` in either bound is
    treated as "unbounded" (i.e. the room is always available in that
    direction).

    Args:
        df_gebaeude: Buildings-and-rooms DataFrame with at least the columns
            ``Raumtyp EBP``, ``Fläche``, ``Betriebsaufnahme``, and
            ``Betriebsende``.
        years: List of forecast years for which the available area should be
            calculated.

    Returns:
        DataFrame with columns ``Raumtyp EBP``, ``Jahr``, and ``Fläche``,
        sorted by ``Raumtyp EBP`` and ``Jahr``.

    SQL equivalent::

        SELECT g."Raumtyp EBP", y."Jahr", SUM(g."Fläche") AS "Fläche"
        FROM gebaeude AS g
        CROSS JOIN (SELECT UNNEST(years) AS "Jahr") AS y
        WHERE (g."Betriebsaufnahme" IS NULL OR g."Betriebsaufnahme" <= y."Jahr")
          AND (g."Betriebsende"    IS NULL OR g."Betriebsende"    >= y."Jahr")
        GROUP BY g."Raumtyp EBP", y."Jahr"
        ORDER BY g."Raumtyp EBP", y."Jahr"
    """
    with duckdb.connect(":memory:") as conn:
        conn.register("gebaeude", df_gebaeude)
        return conn.execute(
            """
            -- CAST to BIGINT so DuckDB's UNNEST int32 aligns with pandas int64
            SELECT g."Raumtyp EBP", CAST(y."Jahr" AS BIGINT) AS "Jahr", SUM(g."Fläche") AS "Fläche"
            FROM gebaeude AS g
            CROSS JOIN (SELECT UNNEST(?) AS "Jahr") AS y
            WHERE (g."Betriebsaufnahme" IS NULL OR g."Betriebsaufnahme" <= y."Jahr")
              AND (g."Betriebsende"    IS NULL OR g."Betriebsende"    >= y."Jahr")
            GROUP BY g."Raumtyp EBP", y."Jahr"
            ORDER BY g."Raumtyp EBP", y."Jahr"
            """,
            [years],
        ).fetchdf()


def future_demand(
    df_studierende: pd.DataFrame,
    df_faktoren: pd.DataFrame,
    szenario: str,
) -> pd.DataFrame:
    """Calculate future room demand (m²) per usage type and forecast year.

    For each (year, usage-type) combination the demand is:
        ``Rundungswert(Bezugsspalte, Schritt) × Faktor_m2_pro_Person``

    Args:
        df_studierende: Student/person-numbers DataFrame in long format with
            columns ``Jahr``, ``Kategorie`` and ``Anzahl``.
        df_faktoren: Usage-factors DataFrame with columns ``Szenario``,
            ``Nutzungsart``, ``Faktor_m2_pro_Person``, ``Bezug``,
            ``Schritt``.
        szenario: The scenario name to use for filtering *df_faktoren*.

    Returns:
        DataFrame with columns ``Nutzungsart``, ``Jahr``, ``Bedarf_m2``.

    SQL equivalent::

        SELECT f."Nutzungsart", s."Jahr",
               CASE
                   WHEN f."Schritt" IS NOT NULL AND f."Schritt" > 0
                   THEN CEIL(CAST(s."Anzahl" AS DOUBLE) / f."Schritt")
                        * f."Schritt"
                   ELSE CAST(s."Anzahl" AS DOUBLE)
                END * f."Faktor_m2_pro_Person" AS "Bedarf_m2"
        FROM studierende AS s
        JOIN (
            SELECT "Nutzungsart", "Faktor_m2_pro_Person", "Bezug", "Schritt"
            FROM faktoren
            WHERE "Szenario" = ?
        ) AS f ON s."Kategorie" = f."Bezug"
        ORDER BY f."Nutzungsart", s."Jahr"
    """
    required_stud_cols = {"Jahr", "Kategorie", "Anzahl"}
    missing_stud_cols = sorted(required_stud_cols - set(df_studierende.columns))
    if missing_stud_cols:
        raise ValueError(
            "Folgende Spalten fehlen in den Studierenden-Daten: "
            f"{missing_stud_cols}"
        )

    # Validate early in Python so we can produce clear error messages before
    # handing off to DuckDB.
    df_faktoren_szenario = df_faktoren[df_faktoren["Szenario"] == szenario]
    if df_faktoren_szenario.empty:
        return pd.DataFrame(columns=["Nutzungsart", "Jahr", "Bedarf_m2"])

    bezug_values = set(df_faktoren_szenario["Bezug"].dropna().unique())
    if not bezug_values:
        raise ValueError(
            f"Im Szenario '{szenario}' sind keine gültigen Bezug-Werte vorhanden."
        )
    studierende_kategorien = set(df_studierende["Kategorie"].dropna().unique())
    missing_bezug_kategorien = sorted(bezug_values - studierende_kategorien)
    if missing_bezug_kategorien:
        raise ValueError(
            "Folgende Bezug-Kategorien fehlen in den Studierenden-Daten: "
            f"{missing_bezug_kategorien}"
        )

    with duckdb.connect(":memory:") as conn:
        conn.register("studierende", df_studierende)
        conn.register("faktoren", df_faktoren)
        return conn.execute(
            """
            SELECT Nutzungsart, Jahr, sum(Bedarf_m2) AS Bedarf_m2
            FROM ( 
            SELECT f."Nutzungsart", s."Jahr",
                   CASE
                       WHEN f."Schritt" IS NOT NULL AND f."Schritt" > 0
                       THEN CEIL(CAST(s."Anzahl" AS DOUBLE) / f."Schritt")
                            * f."Schritt"
                       ELSE CAST(s."Anzahl" AS DOUBLE)
                   END * f."Faktor_m2_pro_Person" as "Bedarf_m2"
            FROM studierende AS s
            JOIN (
                SELECT "Nutzungsart", "Faktor_m2_pro_Person", "Bezug", "Schritt"
                FROM faktoren
                WHERE "Szenario" = ?
            ) AS f ON s."Kategorie" = f."Bezug"
            )
            GROUP BY Nutzungsart, Jahr
            ORDER BY Nutzungsart, Jahr
            """,
            [szenario],
        ).fetchdf()


def surplus_deficit(
    df_current: pd.DataFrame,
    df_demand: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate surplus or deficit of area per usage type and year.

    A positive value means there is currently more area than needed (surplus);
    a negative value means there is not enough area (deficit).

    Args:
        df_current: Output of :func:`current_area_by_nutzungsart` with columns
            ``Raumtyp EBP``, ``Jahr``, and ``Fläche``.
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
        LEFT JOIN current_area AS c
               ON d."Nutzungsart" = c."Raumtyp EBP"
              AND d."Jahr"        = c."Jahr"
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
            LEFT JOIN current_area AS c
                   ON d."Nutzungsart" = c."Raumtyp EBP"
                  AND d."Jahr"        = c."Jahr"
            ORDER BY d._rn
        """).fetchdf()


def area_by_eigentumsform(
    df_gebaeude: pd.DataFrame,
    years: list[int],
) -> pd.DataFrame:
    """Aggregate the available total area (m²) by ownership type and year.

    Only rooms whose operational period covers a given year are included:
    a room is counted for year *y* when
    ``Betriebsaufnahme <= y <= Betriebsende``.  ``NULL`` in either bound is
    treated as "unbounded" (i.e. the room is always available in that
    direction).

    Special case: rows where ``Eigentumsform = 'Mietliegenschaften'`` **and**
    ``Eigentümer = 'Hochbauamt St. Gallen'`` are counted under the category
    ``'Eigenmiete'`` instead of ``'Mietliegenschaften'``.

    Args:
        df_gebaeude: Buildings-and-rooms DataFrame with at least the columns
            ``Eigentumsform``, ``Eigentümer``, ``Fläche``, ``Betriebsaufnahme``,
            and ``Betriebsende``.
        years: List of forecast years for which the available area should be
            calculated.

    Returns:
        DataFrame with columns ``Eigentumsform``, ``Jahr``, and ``Fläche``,
        sorted by ``Eigentumsform`` and ``Jahr``.

    SQL equivalent::

        SELECT
            CASE
                WHEN g."Eigentumsform" = 'Mietliegenschaften'
                     AND g."Eigentümer" = 'Hochbauamt St. Gallen'
                THEN 'Eigenmiete'
                ELSE g."Eigentumsform"
            END AS "Eigentumsform",
            y."Jahr",
            SUM(g."Fläche") AS "Fläche"
        FROM gebaeude AS g
        CROSS JOIN (SELECT UNNEST(years) AS "Jahr") AS y
        WHERE (g."Betriebsaufnahme" IS NULL OR g."Betriebsaufnahme" <= y."Jahr")
          AND (g."Betriebsende"    IS NULL OR g."Betriebsende"    >= y."Jahr")
        GROUP BY
            CASE
                WHEN g."Eigentumsform" = 'Mietliegenschaften'
                     AND g."Eigentümer" = 'Hochbauamt St. Gallen'
                THEN 'Eigenmiete'
                ELSE g."Eigentumsform"
            END,
            y."Jahr"
        ORDER BY "Eigentumsform", y."Jahr"
    """
    with duckdb.connect(":memory:") as conn:
        conn.register("gebaeude", df_gebaeude)
        df =  conn.execute(
            """
            SELECT
                CASE
                    WHEN g."Eigentumsform" = 'Mietliegenschaften'
                         AND g."Eigentümer" = 'Hochbauamt St. Gallen'
                    THEN 'Eigenmiete'
                    ELSE g."Eigentumsform"
                END AS "Eigentumsform",
                CAST(y."Jahr" AS BIGINT) AS "Jahr",
                SUM(g."Fläche") AS "Fläche"
            FROM gebaeude AS g
            CROSS JOIN (SELECT UNNEST(?) AS "Jahr") AS y
            WHERE (g."Betriebsaufnahme" IS NULL OR g."Betriebsaufnahme" <= y."Jahr")
              AND (g."Betriebsende"    IS NULL OR g."Betriebsende"    >= y."Jahr")
            GROUP BY
                CASE
                    WHEN g."Eigentumsform" = 'Mietliegenschaften'
                         AND g."Eigentümer" = 'Hochbauamt St. Gallen'
                    THEN 'Eigenmiete'
                    ELSE g."Eigentumsform"
                END,
                y."Jahr"
            ORDER BY "Eigentumsform", y."Jahr"
            """,
            [years],
        ).fetchdf()
        df.loc[df["Eigentumsform"] == "Eigenmiete", "Eigentumsform"] = "Eigentum Kanton St.Gallen - Miete temporär"
        df.loc[df["Eigentumsform"] == "Mietliegenschaften", "Eigentumsform"] = "Eigentum Dritter - Miete temporär"
        df.loc[df["Eigentumsform"] == "Nutzungsvereinbarung", "Eigentumsform"] = "Eigentum Kanton St.Gallen - langfristige Nutzung"
        df.loc[df["Eigentumsform"] == "Stiftungs- und Drittliegenschaften", "Eigentumsform"] = "Eigentum Stiftungen - Miete temporär"
        return df


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


def flaechenpotenzial_total(df_flaechenpotenzial: pd.DataFrame, year: int) -> float:
    """Sum the Flächenpotenzial values for a given evaluation year.

    Args:
        df_flaechenpotenzial: DataFrame with at least the columns
            ``Jahr Auswertung`` and ``Flächenpotential``, as returned by
            :func:`data_loader.load_flaechenpotenzial`.
        year: Evaluation year (``Jahr Auswertung``) to sum over.

    Returns:
        Sum of ``Flächenpotential`` for rows matching *year*.
    """
    matching = df_flaechenpotenzial.loc[
        df_flaechenpotenzial["Jahr Auswertung"] == year, "Flächenpotential"
    ]
    return float(matching.sum())
