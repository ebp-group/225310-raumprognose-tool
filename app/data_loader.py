"""Data loading utilities for the Raumprognose Tool.

Each public function loads one of the three Excel input files, validates
that the expected columns are present, and returns a :class:`pandas.DataFrame`.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import IO, Any

import pandas as pd
from config import get_config, nutzungsart_multipliers

_GEBAEUDE_COLS = {
    "Eigentumsform",
    "Abgabeart",
    "Eigentümer",
    "Raumtyp EBP",
    "Fläche m²",
    "Betriebsaufnahme",
    "Betriebsende",
}
_STUDIERENDE_COLS = {"Jahr", "Anzahl", "Beschreibung", "Kategorie"}
_NUTZUNGSFAKTOREN_COLS = {
    "szenario",
    "nutzungsart",
    "faktor_m2_pro_person",
    "schritt",
    "bezug",
}


def _data_setting(key: str) -> Any:
    """Return ``data.<key>`` from the configuration."""
    return (get_config().get("data") or {}).get(key)


FileSource = str | Path | IO[bytes]


def _validate_columns(df: pd.DataFrame, expected: set[str], source: str) -> None:
    """Raise :class:`ValueError` when *df* is missing expected columns.

    Args:
        df: DataFrame to validate.
        expected: Set of required column names.
        source: Human-readable name of the file (used in the error message).

    Raises:
        ValueError: If any expected column is absent from *df*.
    """
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(
            f"File '{os.path.basename(source)}' is missing required columns: {sorted(missing)}"
        )


def load_gebaeude_raeume(
    source: FileSource,
) -> pd.DataFrame:
    """Load the buildings-and-rooms Excel file.

    Args:
        source: Path, file-like object
            ``data/gebaeude_raeume.xlsx``.

    Returns:
        DataFrame with columns ``gebaeude``, ``raum``, ``nutzungsart``,
        ``flaeche_m2``.

    Raises:
        ValueError: If required columns are missing.
    """
    df = pd.read_excel(
        source, engine="openpyxl", header=0, usecols=_data_setting("gebaeude_usecols")
    )
    _validate_columns(df, _GEBAEUDE_COLS, os.path.basename(source))

    df = df.rename(
        columns={
            "Fläche m²": "Fläche",
        }
    )

    df["Betriebsaufnahme"] = pd.to_numeric(
        df["Betriebsaufnahme"], errors="coerce"
    ).astype("Int64")
    df["Betriebsende"] = pd.to_numeric(df["Betriebsende"], errors="coerce").astype(
        "Int64"
    )
    df["Fläche"] = pd.to_numeric(df["Fläche"], errors="coerce").astype("float64")

    return df[df["Raumtyp EBP"].notna()].filter(
        [
            "Eigentumsform",
            "Abgabeart",
            "Eigentümer",
            "Raumtyp EBP",
            "Fläche",
            "Betriebsaufnahme",
            "Betriebsende",
        ]
    )


def load_flaechenpotenzial(source: FileSource) -> pd.DataFrame | None:
    """Load the optional Flächenpotenzial sheet from the Rauminventar workbook.

    The sheet name comes from ``data.flaechenpotenzial_sheet`` in ``config.yml``.
    The sheet is optional; buildings-and-rooms
    workbooks without it simply don't offer the Flächenpotenzial chart. When
    present, it is expected to hold exactly three columns in order: the
    evaluation year (``Jahr Auswertung``), the building (``Gebäude``), and the
    potential area in m² (e.g. ``Flächenpotential HNF 1 / 2 / 3 / 5 m2``) —
    matched by position rather than exact header text, since that last header
    may vary.

    Args:
        source: Path or file-like object pointing at the same workbook passed
            to :func:`load_gebaeude_raeume`.

    Returns:
        DataFrame with columns ``Jahr Auswertung``, ``Gebäude``, and
        ``Flächenpotential``, or ``None`` if the workbook has no such sheet.

    Raises:
        ValueError: If the sheet exists but has fewer than 3 columns.
    """
    sheet_name = _data_setting("flaechenpotenzial_sheet")
    excel_file = pd.ExcelFile(source, engine="openpyxl")
    if sheet_name not in excel_file.sheet_names:
        return None

    df = pd.read_excel(excel_file, sheet_name=sheet_name, header=0)
    if df.shape[1] < 3:
        raise ValueError(
            f"Sheet '{sheet_name}' in '{os.path.basename(source)}' "
            "must have at least 3 columns (Jahr Auswertung, Gebäude, Flächenpotential)."
        )

    df = df.iloc[:, :3].copy()
    df.columns = ["Jahr Auswertung", "Gebäude", "Flächenpotential"]
    df["Jahr Auswertung"] = pd.to_numeric(
        df["Jahr Auswertung"], errors="coerce"
    ).astype("Int64")
    df["Flächenpotential"] = pd.to_numeric(
        df["Flächenpotential"], errors="coerce"
    ).astype("float64")
    return df


def load_studierende(
    source: FileSource,
) -> pd.DataFrame:
    """Load the student-numbers Excel file.

    Args:
        source: Path, file-like object
            ``data/studierende.xlsx``.

    Returns:
        DataFrame with columns ``jahr``, ``anzahl_studierende``, sorted by year.

    Raises:
        ValueError: If required columns are missing.
    """
    df = pd.read_excel(source, engine="openpyxl")
    _validate_columns(df, _STUDIERENDE_COLS, os.path.basename(source))

    df["Jahr"] = df["Jahr"].astype(int)
    df["Anzahl"] = df["Anzahl"].round(0).astype(int)

    return df


def load_nutzungsfaktoren(source: FileSource) -> pd.DataFrame:
    """Load the usage-factors Excel file.

    Args:
        source: Path, file-like object
            ``data/nutzungsfaktoren.xlsx``.

    Returns:
        DataFrame with columns ``szenario``, ``nutzungsart``,
        ``faktor_m2_pro_student``.

    Raises:
        ValueError: If required columns are missing.
    """
    df = pd.read_excel(source, engine="openpyxl")
    _validate_columns(df, _NUTZUNGSFAKTOREN_COLS, os.path.basename(source))

    df["faktor_m2_pro_person"] = df["faktor_m2_pro_person"].astype(float)
    df["schritt"] = df["schritt"].astype(int)

    # Per-Nutzungsart multipliers from config.yml (e.g. m² per workplace for
    # offices, where the raw factor is "persons per unit" rather than m²).
    for nutzungsart, multiplier in nutzungsart_multipliers().items():
        df.loc[df["nutzungsart"] == nutzungsart, "faktor_m2_pro_person"] *= multiplier

    df = df.rename(
        columns={
            "szenario": "Szenario",
            "nutzungsart": "Nutzungsart",
            "faktor_m2_pro_person": "Faktor_m2_pro_Person",
            "schritt": "Schritt",
            "bezug": "Bezug",
        }
    )
    return df
