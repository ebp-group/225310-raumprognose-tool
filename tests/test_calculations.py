import pandas as pd
from pandas.testing import assert_frame_equal
import pytest

from app.calculations import (
    current_area_by_nutzungsart,
    future_demand,
    surplus_deficit,
    wide_results,
)


def test_current_area_by_nutzungsart_groups_and_sorts() -> None:
    df_gebaeude = pd.DataFrame(
        {
            "Raumtyp EBP": ["Seminar", "Labor", "Seminar", "Büro"],
            "Fläche": [50.0, 80.0, 70.0, 30.0],
        }
    )

    result = current_area_by_nutzungsart(df_gebaeude)

    expected = pd.DataFrame(
        {
            "Raumtyp EBP": ["Büro", "Labor", "Seminar"],
            "Fläche": [30.0, 80.0, 120.0],
        }
    )
    assert_frame_equal(result, expected)


def test_future_demand_filters_scenario_and_calculates_cross_product() -> None:
    df_studierende = pd.DataFrame(
        {
            "Jahr": [2030, 2040],
            "Anzahl": [1000, 1200],
            "Kategorie": ["Studierende", "Studierende"],
        }
    )
    df_faktoren = pd.DataFrame(
        {
            "Szenario": ["Basis", "Basis", "Digital"],
            "Nutzungsart": ["Seminar", "Labor", "Seminar"],
            "Faktor_m2_pro_Person": [2.0, 1.5, 1.2],
            "Bezug": ["Studierende", "Studierende", "Studierende"],
            "Schritt": [None, None, None],
        }
    )

    result = future_demand(df_studierende, df_faktoren, "Basis")

    expected = pd.DataFrame(
        {
            "Nutzungsart": ["Labor", "Labor", "Seminar", "Seminar"],
            "Jahr": [2030, 2040, 2030, 2040],
            "Bedarf_m2": [1500.0, 1800.0, 2000.0, 2400.0],
        }
    )
    assert_frame_equal(result, expected)


def test_future_demand_uses_bezug_and_rounds_by_schritt() -> None:
    df_studierende = pd.DataFrame(
        {
            "Jahr": [2030, 2030, 2040, 2040],
            "Anzahl": [3200, 1500, 6100, 3100],
            "Kategorie": [
                "Studierende",
                "Services_Monatslohn",
                "Studierende",
                "Services_Monatslohn",
            ],
        }
    )
    df_faktoren = pd.DataFrame(
        {
            "Szenario": ["Basis", "Basis"],
            "Nutzungsart": ["Seminar", "Labor"],
            "Faktor_m2_pro_Person": [1.0, 2.0],
            "Bezug": ["Studierende", "Services_Monatslohn"],
            "Schritt": [3000, 3000],
        }
    )

    result = future_demand(df_studierende, df_faktoren, "Basis")

    expected = pd.DataFrame(
        {
            "Nutzungsart": ["Labor", "Labor", "Seminar", "Seminar"],
            "Jahr": [2030, 2040, 2030, 2040],
            "Bedarf_m2": [6000.0, 12000.0, 6000.0, 9000.0],
        }
    )
    assert_frame_equal(result, expected)


def test_future_demand_raises_error_for_unknown_bezug_column() -> None:
    df_studierende = pd.DataFrame(
        {
            "Jahr": [2030],
            "Anzahl": [1000],
            "Kategorie": ["Studierende"],
        }
    )
    df_faktoren = pd.DataFrame(
        {
            "Szenario": ["Basis"],
            "Nutzungsart": ["Seminar"],
            "Faktor_m2_pro_Person": [2.0],
            "Bezug": ["NichtVorhanden"],
            "Schritt": [None],
        }
    )

    with pytest.raises(ValueError, match="Bezug-Kategorien"):
        future_demand(df_studierende, df_faktoren, "Basis")


def test_surplus_deficit_merges_current_and_demand_and_computes_difference() -> None:
    df_current = pd.DataFrame(
        {
            "Raumtyp EBP": ["Seminar", "Labor"],
            "Fläche": [2200.0, 1600.0],
        }
    )
    df_demand = pd.DataFrame(
        {
            "Nutzungsart": ["Seminar", "Labor", "Büro"],
            "Jahr": [2030, 2030, 2030],
            "Bedarf_m2": [2000.0, 1700.0, 500.0],
        }
    )

    result = surplus_deficit(df_current, df_demand)

    expected = pd.DataFrame(
        {
            "Nutzungsart": ["Seminar", "Labor", "Büro"],
            "Jahr": [2030, 2030, 2030],
            "Fläche": [2200.0, 1600.0, float("nan")],
            "Bedarf_m2": [2000.0, 1700.0, 500.0],
            "Differenz_m2": [200.0, -100.0, float("nan")],
        }
    )
    assert_frame_equal(result, expected)


def test_wide_results_pivots_by_year() -> None:
    df_sd = pd.DataFrame(
        {
            "Nutzungsart": ["Labor", "Labor", "Seminar", "Seminar"],
            "Jahr": [2030, 2040, 2030, 2040],
            "Differenz_m2": [100.0, 50.0, -20.0, 10.0],
        }
    )

    result = wide_results(df_sd)

    expected = pd.DataFrame(
        {
            2030: [100.0, -20.0],
            2040: [50.0, 10.0],
        },
        index=pd.Index(["Labor", "Seminar"], name="Nutzungsart"),
    )
    expected.columns.name = "Jahr"

    assert_frame_equal(result, expected)
