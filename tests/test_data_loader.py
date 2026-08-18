"""Tests for the config-driven parts of ``app/data_loader.py``."""

from pathlib import Path

import data_loader
import pandas as pd
import pytest


def _faktoren_xlsx(tmp_path: Path) -> Path:
    """Write a minimal Nutzungsfaktoren workbook and return its path."""
    df = pd.DataFrame(
        {
            "szenario": ["Basis", "Basis"],
            "nutzungsart": ["Büro", "Sport"],
            "faktor_m2_pro_person": [2.0, 3.0],
            "schritt": [0, 0],
            "bezug": ["Forschung", "Studierende"],
        }
    )
    path = tmp_path / "nutzungsfaktoren.xlsx"
    df.to_excel(path, index=False, engine="openpyxl")
    return path


def _factors_by_nutzungsart(path: Path) -> pd.Series:
    df = data_loader.load_nutzungsfaktoren(path)
    return df.set_index("Nutzungsart")["Faktor_m2_pro_Person"]


def test_configured_multiplier_is_applied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only the Nutzungsarten listed in the config get their factor scaled."""
    monkeypatch.setattr(data_loader, "nutzungsart_multipliers", lambda: {"Büro": 14.5})

    factors = _factors_by_nutzungsart(_faktoren_xlsx(tmp_path))

    assert factors["Büro"] == pytest.approx(2.0 * 14.5)
    assert factors["Sport"] == pytest.approx(3.0)


def test_multiplier_can_target_several_nutzungsarten(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        data_loader,
        "nutzungsart_multipliers",
        lambda: {"Büro": 14.5, "Sport": 2.0},
    )

    factors = _factors_by_nutzungsart(_faktoren_xlsx(tmp_path))

    assert factors["Büro"] == pytest.approx(29.0)
    assert factors["Sport"] == pytest.approx(6.0)


def test_no_multipliers_leaves_factors_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(data_loader, "nutzungsart_multipliers", dict)

    factors = _factors_by_nutzungsart(_faktoren_xlsx(tmp_path))

    assert factors["Büro"] == pytest.approx(2.0)
    assert factors["Sport"] == pytest.approx(3.0)


def test_missing_columns_raise_before_column_access(tmp_path: Path) -> None:
    """A missing column yields the readable ValueError, not a KeyError.

    ``load_studierende`` used to coerce ``Jahr``/``Anzahl`` before validating,
    so an unrelated missing column surfaced as a KeyError instead.
    """
    path = tmp_path / "studierende.xlsx"
    pd.DataFrame(
        {"Jahr": [2030], "Anzahl": [10], "Kategorie": ["Studierende"]}
    ).to_excel(path, index=False, engine="openpyxl")

    with pytest.raises(ValueError, match="Beschreibung"):
        data_loader.load_studierende(path)
