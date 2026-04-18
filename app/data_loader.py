"""Data loading utilities for the Raumprognose Tool.

Each public function loads one of the three Excel input files, validates
that the expected columns are present, and returns a :class:`pandas.DataFrame`.
"""

from __future__ import annotations

from pathlib import Path
from typing import IO

import pandas as pd

_DATA_DIR = Path(__file__).parent.parent / "data"

_GEBAEUDE_COLS = {"gebaeude", "raum", "nutzungsart", "flaeche_m2"}
_STUDIERENDE_COLS = {"jahr", "anzahl_studierende"}
_NUTZUNGSFAKTOREN_COLS = {"szenario", "nutzungsart", "faktor_m2_pro_student"}

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
            f"File '{source}' is missing required columns: {sorted(missing)}"
        )


def load_gebaeude_raeume(
    source: FileSource | None = None,
) -> pd.DataFrame:
    """Load the buildings-and-rooms Excel file.

    Args:
        source: Path, file-like object, or ``None`` to use the default
            ``data/gebaeude_raeume.xlsx``.

    Returns:
        DataFrame with columns ``gebaeude``, ``raum``, ``nutzungsart``,
        ``flaeche_m2``.

    Raises:
        ValueError: If required columns are missing.
    """
    path = source if source is not None else _DATA_DIR / "gebaeude_raeume.xlsx"
    df = pd.read_excel(path, engine="openpyxl")
    _validate_columns(df, _GEBAEUDE_COLS, "gebaeude_raeume.xlsx")
    return df


def load_studierende(
    source: FileSource | None = None,
) -> pd.DataFrame:
    """Load the student-numbers Excel file.

    Args:
        source: Path, file-like object, or ``None`` to use the default
            ``data/studierende.xlsx``.

    Returns:
        DataFrame with columns ``jahr``, ``anzahl_studierende``, sorted by year.

    Raises:
        ValueError: If required columns are missing.
    """
    path = source if source is not None else _DATA_DIR / "studierende.xlsx"
    df = pd.read_excel(path, engine="openpyxl")
    _validate_columns(df, _STUDIERENDE_COLS, "studierende.xlsx")
    return df.sort_values("jahr").reset_index(drop=True)


def load_nutzungsfaktoren(
    source: FileSource | None = None,
) -> pd.DataFrame:
    """Load the usage-factors Excel file.

    Args:
        source: Path, file-like object, or ``None`` to use the default
            ``data/nutzungsfaktoren.xlsx``.

    Returns:
        DataFrame with columns ``szenario``, ``nutzungsart``,
        ``faktor_m2_pro_student``.

    Raises:
        ValueError: If required columns are missing.
    """
    path = source if source is not None else _DATA_DIR / "nutzungsfaktoren.xlsx"
    df = pd.read_excel(path, engine="openpyxl")
    _validate_columns(df, _NUTZUNGSFAKTOREN_COLS, "nutzungsfaktoren.xlsx")
    return df
