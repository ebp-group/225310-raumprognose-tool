"""Generate sample Excel files for the Raumprognose Tool.

Run this script once to create the three input Excel files used by the
Streamlit dashboard:

    python scripts/generate_sample_data.py

Files written to the ``data/`` directory:
- ``gebaeude_raeume.xlsx``  – Buildings and rooms with usage type and area
- ``studierende.xlsx``       – Student numbers (historical + forecast)
- ``nutzungsfaktoren.xlsx``  – Area factors per student per scenario
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data"


def generate_gebaeude_raeume() -> None:
    """Create ``data/gebaeude_raeume.xlsx`` with building and room data."""
    rows = [
        # Hauptgebäude
        ("Hauptgebäude", "HG-101", "Vorlesung", 120.0),
        ("Hauptgebäude", "HG-102", "Vorlesung", 150.0),
        ("Hauptgebäude", "HG-201", "Büro", 25.0),
        ("Hauptgebäude", "HG-202", "Büro", 30.0),
        ("Hauptgebäude", "HG-203", "Büro", 28.0),
        ("Hauptgebäude", "HG-301", "Lernen", 80.0),
        # Naturwissenschaften
        ("Naturwissenschaften", "NW-101", "Labor", 95.0),
        ("Naturwissenschaften", "NW-102", "Labor", 110.0),
        ("Naturwissenschaften", "NW-103", "Labor", 88.0),
        ("Naturwissenschaften", "NW-201", "Vorlesung", 130.0),
        ("Naturwissenschaften", "NW-301", "Büro", 22.0),
        ("Naturwissenschaften", "NW-302", "Büro", 24.0),
        # Bibliothek
        ("Bibliothek", "BIB-001", "Bibliothek", 400.0),
        ("Bibliothek", "BIB-002", "Lernen", 200.0),
        ("Bibliothek", "BIB-003", "Lernen", 150.0),
        # Sportzentrum
        ("Sportzentrum", "SZ-001", "Sport", 600.0),
        ("Sportzentrum", "SZ-002", "Sport", 250.0),
        ("Sportzentrum", "SZ-003", "Büro", 18.0),
        ("Sportzentrum", "SZ-101", "Lernen", 60.0),
        ("Sportzentrum", "SZ-102", "Vorlesung", 90.0),
    ]
    df = pd.DataFrame(
        rows,
        columns=["gebaeude", "raum", "nutzungsart", "flaeche_m2"],
    )
    df.to_excel(DATA_DIR / "gebaeude_raeume.xlsx", index=False)
    print(f"Written {len(df)} rows → data/gebaeude_raeume.xlsx")


def generate_studierende() -> None:
    """Create ``data/studierende.xlsx`` with student number data."""
    rows = [
        (2024, 8500),
        (2030, 9200),
        (2040, 10100),
        (2050, 10800),
    ]
    df = pd.DataFrame(rows, columns=["jahr", "anzahl_studierende"])
    df.to_excel(DATA_DIR / "studierende.xlsx", index=False)
    print(f"Written {len(df)} rows → data/studierende.xlsx")


def generate_nutzungsfaktoren() -> None:
    """Create ``data/nutzungsfaktoren.xlsx`` with area factors per student per scenario."""
    nutzungsarten = ["Vorlesung", "Labor", "Büro", "Lernen", "Sport", "Bibliothek"]
    # Three scenarios with different m² per student values
    scenarios = {
        "Basis": [0.50, 0.30, 0.20, 0.40, 0.15, 0.25],
        "Wachstum": [0.60, 0.40, 0.25, 0.50, 0.20, 0.30],
        "Digital": [0.35, 0.25, 0.15, 0.55, 0.10, 0.20],
    }
    rows = []
    for szenario, faktoren in scenarios.items():
        for nutzungsart, faktor in zip(nutzungsarten, faktoren):
            rows.append((szenario, nutzungsart, faktor))
    df = pd.DataFrame(
        rows, columns=["szenario", "nutzungsart", "faktor_m2_pro_student"]
    )
    df.to_excel(DATA_DIR / "nutzungsfaktoren.xlsx", index=False)
    print(f"Written {len(df)} rows → data/nutzungsfaktoren.xlsx")


def main() -> None:
    """Generate all three sample Excel files."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    generate_gebaeude_raeume()
    generate_studierende()
    generate_nutzungsfaktoren()
    print("Sample data generation complete.")


if __name__ == "__main__":
    main()
