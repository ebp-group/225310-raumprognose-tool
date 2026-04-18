"""Calculation functions for the Raumprognose Tool.

All functions are pure (no side-effects, no UI calls) and work
exclusively with :class:`pandas.DataFrame` objects so they can be tested
independently of the UI layer.
"""

from __future__ import annotations

import pandas as pd


def current_area_by_nutzungsart(df_gebaeude: pd.DataFrame) -> pd.DataFrame:
    """Aggregate the current total area (m²) by usage type.

    Args:
        df_gebaeude: Buildings-and-rooms DataFrame with at least the columns
            ``nutzungsart`` and ``flaeche_m2``.

    Returns:
        DataFrame with columns ``nutzungsart`` and ``flaeche_m2_gesamt``,
        sorted by ``nutzungsart``.
    """
    result = (
        df_gebaeude.groupby("nutzungsart", as_index=False)["flaeche_m2"]
        .sum()
        .rename(columns={"flaeche_m2": "flaeche_m2_gesamt"})
        .sort_values("nutzungsart")
        .reset_index(drop=True)
    )
    return result


def future_demand(
    df_studierende: pd.DataFrame,
    df_faktoren: pd.DataFrame,
    szenario: str,
) -> pd.DataFrame:
    """Calculate future room demand (m²) per usage type and forecast year.

    For each (year, usage-type) combination the demand is:
        ``anzahl_studierende × faktor_m2_pro_student``

    Args:
        df_studierende: Student-numbers DataFrame with columns ``jahr`` and
            ``anzahl_studierende``.
        df_faktoren: Usage-factors DataFrame with columns ``szenario``,
            ``nutzungsart``, ``faktor_m2_pro_student``.
        szenario: The scenario name to use for filtering *df_faktoren*.

    Returns:
        DataFrame with columns ``nutzungsart``, ``jahr``, ``bedarf_m2``.
    """
    faktoren_sel = df_faktoren[df_faktoren["szenario"] == szenario].copy()
    cross = df_studierende.merge(faktoren_sel, how="cross")
    cross["bedarf_m2"] = cross["anzahl_studierende"] * cross["faktor_m2_pro_student"]
    return (
        cross[["nutzungsart", "jahr", "bedarf_m2"]]
        .sort_values(["nutzungsart", "jahr"])
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
            ``nutzungsart`` and ``flaeche_m2_gesamt``.
        df_demand: Output of :func:`future_demand` with columns ``nutzungsart``,
            ``jahr``, ``bedarf_m2``.

    Returns:
        DataFrame with columns ``nutzungsart``, ``jahr``, ``flaeche_m2_gesamt``,
        ``bedarf_m2``, ``differenz_m2`` (positive = surplus, negative = deficit).
    """
    merged = df_demand.merge(df_current, on="nutzungsart", how="left")
    merged["differenz_m2"] = merged["flaeche_m2_gesamt"] - merged["bedarf_m2"]
    return merged[
        ["nutzungsart", "jahr", "flaeche_m2_gesamt", "bedarf_m2", "differenz_m2"]
    ].reset_index(drop=True)


def wide_results(df_sd: pd.DataFrame) -> pd.DataFrame:
    """Pivot the surplus/deficit table to a wide format for display.

    Args:
        df_sd: Output of :func:`surplus_deficit`.

    Returns:
        DataFrame indexed by ``nutzungsart`` with one column per forecast year
        showing ``differenz_m2``.
    """
    return df_sd.pivot_table(
        index="nutzungsart",
        columns="jahr",
        values="differenz_m2",
        aggfunc="first",
    )
