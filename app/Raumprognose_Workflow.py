import io
import os
from pathlib import Path

import marimo

__generated_with = "0.23.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    mo.md(
        """
        # 🏛️ Raumprognose Tool – Workflow Notebook

        This notebook demonstrates the full Raumprognose workflow:

        1. **Load** the Excel input files into an in-memory DuckDB database
        2. **Calculate** current area, future demand, and surplus/deficit
        3. **Visualise** intermediate and final results
        4. **Export** the result tables to Excel
        """
    )
    return (mo,)


@app.cell
def _():
    import matplotlib.pyplot as plt
    import pandas as pd

    from .calculations import (
        current_area_by_nutzungsart,
        future_demand,
        surplus_deficit,
        wide_results,
    )
    from .data_loader import (
        load_gebaeude_raeume,
        load_nutzungsfaktoren,
        load_studierende,
    )
    from .utils import get_in_memory_connection, load_dataframe, query_to_dataframe

    return (
        Path,
        io,
        current_area_by_nutzungsart,
        future_demand,
        load_gebaeude_raeume,
        load_nutzungsfaktoren,
        load_studierende,
        os,
        pd,
        plt,
        surplus_deficit,
        wide_results,
        get_in_memory_connection,
        load_dataframe,
        query_to_dataframe,
    )


@app.cell
def _(
    Path,
    get_in_memory_connection,
    load_dataframe,
    load_gebaeude_raeume,
    load_nutzungsfaktoren,
    load_studierende,
    mo,
    os,
):
    mo.md("## 1 – Load Excel data into in-memory DuckDB")

    default_base_path = Path(
        r"C:\Users\ods\OneDrive - EBP\CH_P_225310 - PE_TPF_UniSG - General\40_BEARBEITUNG\04_Auswertung\02_Datenmodell"
    )
    base_path = Path(os.environ.get("RAUMPROG_DATA_DIR", str(default_base_path)))

    gebaeude_file = base_path / "260402_UniSG_Rauminventar_rev_260414.xlsx"
    studierende_file = base_path / "prognose_studierende_und_ma.xlsx"
    faktoren_file = base_path / "nutzungsfaktoren.xlsx"

    df_gebaeude = load_gebaeude_raeume(gebaeude_file)
    df_studierende = load_studierende(studierende_file)
    df_faktoren = load_nutzungsfaktoren(faktoren_file)

    con = get_in_memory_connection()
    load_dataframe(con, df_gebaeude, "gebaeude_raeume")
    load_dataframe(con, df_studierende, "studierende")
    load_dataframe(con, df_faktoren, "nutzungsfaktoren")

    _tables = con.execute("SHOW TABLES").fetchdf()
    mo.md(
        f"✅ Loaded **{len(df_gebaeude)}** rooms, "
        f"**{len(df_studierende)}** student-year rows, and "
        f"**{len(df_faktoren)}** usage-factor rows into DuckDB.\n\n"
        f"**Tables in DuckDB:** {', '.join(_tables['name'].tolist())}"
    )
    return con, df_faktoren, df_gebaeude, df_studierende


@app.cell
def _(con, mo, query_to_dataframe):
    mo.md("### Raw data from DuckDB")

    _gebaeude_tbl = query_to_dataframe(con, "SELECT * FROM gebaeude_raeume")
    _stud_tbl = query_to_dataframe(con, "SELECT * FROM studierende")
    _fakt_tbl = query_to_dataframe(con, "SELECT * FROM nutzungsfaktoren")

    mo.ui.tabs(
        {
            "🏢 Gebäude & Räume": mo.ui.table(_gebaeude_tbl),
            "🎓 Studierende": mo.ui.table(_stud_tbl),
            "📊 Nutzungsfaktoren": mo.ui.table(_fakt_tbl),
        }
    )
    return


@app.cell
def _(df_faktoren, mo):
    mo.md("## 2 – Run calculations")

    _scenarios = sorted(df_faktoren["Szenario"].unique().tolist())
    scenario_selector = mo.ui.dropdown(
        options=_scenarios,
        value=_scenarios[0],
        label="Szenario wählen",
    )
    scenario_selector
    return (scenario_selector,)


@app.cell
def _(current_area_by_nutzungsart, df_gebaeude, df_studierende, mo):
    mo.md("### Step A – Current area by usage type")

    _years = sorted(df_studierende["Jahr"].unique().tolist())
    df_current = current_area_by_nutzungsart(df_gebaeude, _years)

    mo.vstack([
        mo.md("""
**SQL (DuckDB):**
```sql
SELECT g."Raumtyp EBP", y."Jahr", SUM(g."Fläche") AS "Fläche"
FROM gebaeude_raeume AS g
CROSS JOIN (SELECT UNNEST(years) AS "Jahr") AS y
WHERE (g."Betriebsaufnahme" IS NULL OR g."Betriebsaufnahme" <= y."Jahr")
  AND (g."Betriebsende"    IS NULL OR g."Betriebsende"    >= y."Jahr")
GROUP BY g."Raumtyp EBP", y."Jahr"
ORDER BY g."Raumtyp EBP", y."Jahr"
```
"""),
        mo.ui.table(df_current),
    ])
    return (df_current,)


@app.cell
def _(df_faktoren, df_studierende, future_demand, mo, scenario_selector):
    mo.md("### Step B – Future demand")

    selected_scenario = scenario_selector.value
    df_demand = future_demand(df_studierende, df_faktoren, selected_scenario)

    mo.vstack([
        mo.md(f"""
**SQL (DuckDB)** – Szenario: `{selected_scenario}`
```sql
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
    FROM nutzungsfaktoren
    WHERE "Szenario" = '{selected_scenario}'
) AS f ON s."Kategorie" = f."Bezug"
ORDER BY f."Nutzungsart", s."Jahr"
```
*(Die Studierenden-Tabelle liegt bereits in Langform vor; `Kategorie` wird direkt mit `Bezug` verknüpft. CEIL rundet den Bezugswert auf das nächste Vielfache von „Schritt" auf, bevor mit dem Faktor multipliziert wird.)*
"""),
        mo.ui.table(df_demand),
    ])
    return df_demand, selected_scenario


@app.cell
def _(df_current, df_demand, mo, surplus_deficit):
    mo.md("### Step C – Surplus/deficit")

    df_sd = surplus_deficit(df_current, df_demand)

    mo.vstack([
        mo.md("""
**SQL (DuckDB):**
```sql
SELECT d."Nutzungsart", d."Jahr",
       c."Fläche",
       d."Bedarf_m2",
       c."Fläche" - d."Bedarf_m2" AS "Differenz_m2"
FROM demand AS d
LEFT JOIN current_area AS c
       ON d."Nutzungsart" = c."Raumtyp EBP"
```
*(Positive Differenz = Überschuss, negative Differenz = Defizit.  
`NULL` in „Fläche" und „Differenz\_m2" bedeutet: keine Ist-Fläche für diese Nutzungsart vorhanden.)*
"""),
        mo.ui.table(df_sd),
    ])
    return (df_sd,)


@app.cell
def _(df_sd, mo, wide_results):
    mo.md("### Step D – Wide result table")

    df_wide = wide_results(df_sd)

    mo.vstack([
        mo.md("""
**SQL (DuckDB):**
```sql
PIVOT sd
ON "Jahr"
USING FIRST("Differenz_m2")
GROUP BY "Nutzungsart"
ORDER BY "Nutzungsart"
```
*(Eine Spalte pro Prognosejahr; Werte = `Differenz_m2` aus Schritt C.)*
"""),
        mo.ui.table(df_wide.reset_index()),
    ])
    return (df_wide,)


@app.cell
def _(df_current, df_demand, df_sd, df_wide, mo, selected_scenario):
    mo.md(f"### Results for scenario: **{selected_scenario}**")

    mo.ui.tabs(
        {
            "Aktuelle Fläche (m²)": mo.ui.table(df_current),
            "Zukünftiger Bedarf (m²)": mo.ui.table(df_demand),
            "Überschuss / Defizit": mo.ui.table(df_sd),
            "Pivot-Ansicht (Differenz)": mo.ui.table(df_wide.reset_index()),
        }
    )
    return


@app.cell
def _(df_studierende, mo, plt):
    mo.md("## 3 – Charts")
    mo.md("### Entwicklung der Studierendenzahlen")

    _fig1, _ax1 = plt.subplots(figsize=(8, 4))
    _ax1.plot(
        df_studierende["Jahr"],
        df_studierende["Studierende"],
        marker="o",
        linewidth=2,
        color="#1f77b4",
    )
    _ax1.set_xlabel("Jahr")
    _ax1.set_ylabel("Studierende")
    _ax1.set_title("Entwicklung der Studierendenzahlen")
    _ax1.grid(True, alpha=0.3)
    _fig1.tight_layout()
    _fig1
    return


@app.cell
def _(df_demand, mo, plt, selected_scenario):
    mo.md(f"### Flächenbedarf – Szenario: {selected_scenario}")

    _years = sorted(df_demand["Jahr"].unique())
    _nutzungsarten = sorted(df_demand["Nutzungsart"].unique())
    _x = range(len(_nutzungsarten))
    _width = 0.8 / max(len(_years), 1)

    _fig2, _ax2 = plt.subplots(figsize=(10, 5))
    for _i, _year in enumerate(_years):
        _df_year = df_demand[df_demand["Jahr"] == _year]
        _values = []
        for _n in _nutzungsarten:
            _subset = _df_year[_df_year["Nutzungsart"] == _n]["Bedarf_m2"]
            _values.append(_subset.values[0] if len(_subset) > 0 else 0)
        _offset = (_i - len(_years) / 2 + 0.5) * _width
        _ax2.bar([_xi + _offset for _xi in _x], _values, _width, label=str(_year))

    _ax2.set_xlabel("Nutzungsart")
    _ax2.set_ylabel("Bedarf (m²)")
    _ax2.set_title(f"Flächenbedarf – Szenario: {selected_scenario}")
    _ax2.set_xticks(list(_x))
    _ax2.set_xticklabels(_nutzungsarten, rotation=45, ha="right")
    _ax2.legend()
    _ax2.grid(True, alpha=0.3, axis="y")
    _fig2.tight_layout()
    _fig2
    return


@app.cell
def _(df_sd, mo, plt):
    mo.md("### Überschuss / Defizit je Jahr")

    _years = sorted(df_sd["Jahr"].unique())
    _n_years = len(_years)
    _fig3, _axes = plt.subplots(1, _n_years, figsize=(5 * _n_years, 4), sharey=True)
    if _n_years == 1:
        _axes = [_axes]

    for _ax, _year in zip(_axes, _years):
        _df_year = df_sd[df_sd["Jahr"] == _year]
        _colors = ["#2ecc71" if v >= 0 else "#e74c3c" for v in _df_year["Differenz_m2"]]
        _ax.bar(_df_year["Nutzungsart"], _df_year["Differenz_m2"], color=_colors)
        _ax.set_xlabel("Nutzungsart")
        _ax.set_title(str(_year))
        _ax.axhline(y=0, color="black", linewidth=0.5)
        _ax.tick_params(axis="x", rotation=45)
        _ax.grid(True, alpha=0.3, axis="y")

    _axes[0].set_ylabel("Differenz (m²)")
    _fig3.suptitle("Überschuss / Defizit nach Nutzungsart", fontsize=14)
    _fig3.tight_layout()
    _fig3
    return


@app.cell
def _(Path, df_demand, df_sd, io, mo, os, pd, selected_scenario):
    mo.md("## 4 – Excel export")

    export_dir = Path(os.environ.get("RAUMPROG_EXPORT_DIR", "output")).resolve()
    export_dir.mkdir(parents=True, exist_ok=True)
    export_path = export_dir / f"raumprognose_{selected_scenario}.xlsx"

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_sd.to_excel(writer, sheet_name="Ergebnisse", index=False)
        df_demand.to_excel(writer, sheet_name="Flächenbedarf", index=False)

    excel_bytes = buffer.getvalue()
    export_path.write_bytes(excel_bytes)

    mo.md(
        f"✅ Excel export created: `{export_path}`  \\n"
        f"File size: **{len(excel_bytes):,} bytes**"
    )
    return excel_bytes, export_path


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
