"""Data loading utilities for the Raumprognose Tool.

Each public function loads one of the three Excel input files, validates
that the expected columns are present, and returns a :class:`pandas.DataFrame`.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import IO

import pandas as pd
from utils import get_in_memory_connection, query_to_dataframe

_DATA_DIR = Path(__file__).parent.parent / "data"

_GEBAEUDE_COLS = {"Eigentumsform", "Abgabeart", "Eigentümer", "Raumtyp EBP", "Fläche m²", "Betriebsaufnahme", "Betriebsende"}
_STUDIERENDE_COLS = {"jahr", "anzahl_studierende", "anzahl_forschung_monatslohn", "anzahl_services_monatslohn", "anzahl_forschung_studenlohn", "anzahl_services_stundenlohn"}
_NUTZUNGSFAKTOREN_COLS = {"szenario", "nutzungsart", "faktor_m2_pro_person", "schritt"}


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
    df = pd.read_excel(source, engine="openpyxl", header=0, usecols="A:S")
    _validate_columns(df, _GEBAEUDE_COLS, os.path.basename(source))
    df = df.rename(columns={
        "Fläche m²": "Fläche",
    })

    return df[df["Raumtyp EBP"].notna()].filter(["Eigentumsform", "Abgabeart", "Eigentümer", "Raumtyp EBP", "Fläche", "Betriebsaufnahme", "Betriebsende"])


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
    df["jahr"] = df["jahr"].astype(int)
    df["anzahl_studierende"] = df["anzahl_studierende"].round(0).astype(int)
    df["anzahl_forschung_monatslohn"] = df["anzahl_forschung_monatslohn"].round(0).astype(int)
    df["anzahl_services_monatslohn"] = df["anzahl_services_monatslohn"].round(0).astype(int)
    df["anzahl_forschung_studenlohn"] = df["anzahl_forschung_studenlohn"].round(0).astype(int)
    df["anzahl_services_stundenlohn"] = df["anzahl_services_stundenlohn"].round(0).astype(int)
    _validate_columns(df, _STUDIERENDE_COLS,  os.path.basename(source))

    df = df.rename(columns={
        "jahr": "Jahr",
        "anzahl_studierende": "Studierende",
        "anzahl_forschung_monatslohn": "Forschung_Monatslohn",
        "anzahl_services_monatslohn": "Services_Monatslohn",
        "anzahl_forschung_studenlohn": "Forschung_Stundenlohn",
        "anzahl_services_stundenlohn": "Services_Stundenlohn",
    })
    return df


def load_nutzungsfaktoren(
    source: FileSource
) -> pd.DataFrame:
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
    df = df.rename(columns={
        "szenario": "Szenario",
        "nutzungsart": "Nutzungsart",
        "faktor_m2_pro_person": "Faktor_m2_pro_Person",
        "schritt": "Schritt",
    })
    return df
