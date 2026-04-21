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

    from .data_loader import (
        load_gebaeude_raeume,
        load_nutzungsfaktoren,
        load_studierende,
    )
    from .utils import get_in_memory_connection, load_dataframe, query_to_dataframe

    return (
        Path,
        io,
        load_gebaeude_raeume,
        load_nutzungsfaktoren,
        load_studierende,
        os,
        pd,
        plt,
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
def _(df_gebaeude, mo):
    mo.md("### Step A – Current area by usage type (intermediate)")

    df_current_grouped = df_gebaeude.groupby("Raumtyp EBP", as_index=False)["Fläche"].sum()
    df_current = (
        df_current_grouped.sort_values("Raumtyp EBP").reset_index(drop=True)
    )

    mo.ui.tabs(
        {
            "Grouped": mo.ui.table(df_current_grouped),
            "Final": mo.ui.table(df_current),
        }
    )
    return df_current, df_current_grouped


@app.cell
def _(df_faktoren, df_studierende, mo, scenario_selector):
    mo.md("### Step B – Future demand (intermediate)")

    selected_scenario = scenario_selector.value
    faktoren_sel = df_faktoren[df_faktoren["Szenario"] == selected_scenario].copy()
    cross = df_studierende.merge(faktoren_sel, how="cross")
    cross["Bedarf_m2"] = cross["Studierende"] * cross["Faktor_m2_pro_Person"]

    df_demand = (
        cross[["Nutzungsart", "Jahr", "Bedarf_m2"]]
        .sort_values(["Nutzungsart", "Jahr"])
        .reset_index(drop=True)
    )

    mo.ui.tabs(
        {
            "Selected factors": mo.ui.table(faktoren_sel),
            "Cross join (head)": mo.ui.table(cross.head(100)),
            "Final": mo.ui.table(df_demand),
        }
    )
    return cross, df_demand, faktoren_sel, selected_scenario


@app.cell
def _(df_current, df_demand, mo):
    mo.md("### Step C – Surplus/deficit (intermediate)")

    merged = df_demand.merge(
        df_current,
        left_on="Nutzungsart",
        right_on="Raumtyp EBP",
        how="left",
    )
    merged["Differenz_m2"] = merged["Fläche"] - merged["Bedarf_m2"]

    df_sd = merged[["Nutzungsart", "Jahr", "Fläche", "Bedarf_m2", "Differenz_m2"]].reset_index(
        drop=True
    )

    mo.ui.tabs(
        {
            "Merged": mo.ui.table(merged),
            "Final": mo.ui.table(df_sd),
        }
    )
    return df_sd, merged


@app.cell
def _(df_sd, mo):
    mo.md("### Step D – Wide result table")

    df_wide = df_sd.pivot_table(
        index="Nutzungsart",
        columns="Jahr",
        values="Differenz_m2",
        aggfunc="first",
    )
    mo.ui.table(df_wide.reset_index())
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
def _(Path, df_demand, df_sd, io, mo, pd, selected_scenario):
    mo.md("## 4 – Excel export")

    export_dir = Path(__file__).resolve().parent.parent / "output"
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
