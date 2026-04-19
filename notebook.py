import marimo

__generated_with = "0.23.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    mo.md("""
        # 🏛️ Raumprognose Tool – Workflow Notebook

        This notebook demonstrates the full Raumprognose workflow:

        1. **Load** the Excel input files into an in-memory DuckDB database
        2. **Calculate** current area, future demand, and surplus/deficit
        3. **Visualise** the results as tables and charts
        """)
    return (mo,)


@app.cell
def _():
    import sys
    from pathlib import Path

    import duckdb
    import matplotlib.pyplot as plt
    import pandas as pd

    # Ensure the app package is importable
    _repo_root = Path("__file__").resolve().parent
    if str(_repo_root) not in sys.path:
        sys.path.insert(0, str(_repo_root))

    from app.calculations import (
        current_area_by_nutzungsart,
        future_demand,
        surplus_deficit,
        wide_results,
    )
    from app.data_loader import (
        load_gebaeude_raeume,
        load_nutzungsfaktoren,
        load_studierende,
    )

    return (
        Path,
        current_area_by_nutzungsart,
        duckdb,
        future_demand,
        load_gebaeude_raeume,
        load_nutzungsfaktoren,
        load_studierende,
        pd,
        plt,
        surplus_deficit,
        wide_results,
    )


@app.cell
def _(Path, duckdb, load_gebaeude_raeume, load_nutzungsfaktoren, load_studierende, mo):
    mo.md("## 1 – Load Excel data into in-memory DuckDB")

    # Load the three Excel files via the existing data_loader module
    df_gebaeude = load_gebaeude_raeume()
    df_studierende = load_studierende()
    df_faktoren = load_nutzungsfaktoren()

    # Store them in an in-memory DuckDB database
    con = duckdb.connect(":memory:")
    con.execute("CREATE TABLE gebaeude_raeume AS SELECT * FROM df_gebaeude")
    con.execute("CREATE TABLE studierende AS SELECT * FROM df_studierende")
    con.execute("CREATE TABLE nutzungsfaktoren AS SELECT * FROM df_faktoren")

    _tables = con.execute("SHOW TABLES").fetchdf()
    mo.md(
        f"✅ Loaded **{len(df_gebaeude)}** rooms, "
        f"**{len(df_studierende)}** student-year rows, and "
        f"**{len(df_faktoren)}** usage-factor rows into DuckDB.\n\n"
        f"**Tables in DuckDB:** {', '.join(_tables['name'].tolist())}"
    )
    return con, df_faktoren, df_gebaeude, df_studierende


@app.cell
def _(con, mo):
    mo.md("### Raw data from DuckDB")

    _gebaeude_tbl = con.execute("SELECT * FROM gebaeude_raeume").fetchdf()
    _stud_tbl = con.execute("SELECT * FROM studierende").fetchdf()
    _fakt_tbl = con.execute("SELECT * FROM nutzungsfaktoren").fetchdf()

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

    _scenarios = sorted(df_faktoren["szenario"].unique().tolist())
    scenario_selector = mo.ui.dropdown(
        options=_scenarios,
        value=_scenarios[0],
        label="Szenario wählen",
    )
    scenario_selector
    return (scenario_selector,)


@app.cell
def _(
    current_area_by_nutzungsart,
    df_faktoren,
    df_gebaeude,
    df_studierende,
    future_demand,
    mo,
    scenario_selector,
    surplus_deficit,
    wide_results,
):
    _selected = scenario_selector.value

    # Use the existing calculation functions from app.calculations
    df_current = current_area_by_nutzungsart(df_gebaeude)
    df_demand = future_demand(df_studierende, df_faktoren, _selected)
    df_sd = surplus_deficit(df_current, df_demand)
    df_wide = wide_results(df_sd)

    mo.md(f"### Results for scenario: **{_selected}**")
    return df_current, df_demand, df_sd, df_wide


@app.cell
def _(df_current, df_demand, df_sd, df_wide, mo):
    mo.md("### Result tables")

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
        df_studierende["jahr"],
        df_studierende["anzahl_studierende"],
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
def _(df_demand, mo, plt, scenario_selector):
    mo.md(f"### Flächenbedarf – Szenario: {scenario_selector.value}")

    _years = sorted(df_demand["jahr"].unique())
    _nutzungsarten = sorted(df_demand["nutzungsart"].unique())
    _x = range(len(_nutzungsarten))
    _width = 0.8 / max(len(_years), 1)

    _fig2, _ax2 = plt.subplots(figsize=(10, 5))
    for _i, _year in enumerate(_years):
        _df_year = df_demand[df_demand["jahr"] == _year]
        _values = []
        for _n in _nutzungsarten:
            _subset = _df_year[_df_year["nutzungsart"] == _n]["bedarf_m2"]
            _values.append(_subset.values[0] if len(_subset) > 0 else 0)
        _offset = (_i - len(_years) / 2 + 0.5) * _width
        _ax2.bar([_xi + _offset for _xi in _x], _values, _width, label=str(_year))

    _ax2.set_xlabel("Nutzungsart")
    _ax2.set_ylabel("Bedarf (m²)")
    _ax2.set_title(f"Flächenbedarf – Szenario: {scenario_selector.value}")
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

    _years = sorted(df_sd["jahr"].unique())
    _n_years = len(_years)
    _fig3, _axes = plt.subplots(1, _n_years, figsize=(5 * _n_years, 4), sharey=True)
    if _n_years == 1:
        _axes = [_axes]

    for _ax, _year in zip(_axes, _years):
        _df_year = df_sd[df_sd["jahr"] == _year]
        _colors = ["#2ecc71" if v >= 0 else "#e74c3c" for v in _df_year["differenz_m2"]]
        _ax.bar(_df_year["nutzungsart"], _df_year["differenz_m2"], color=_colors)
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
def _(con, mo, scenario_selector):
    mo.md("### DuckDB-Abfrage: Gesamtübersicht")

    _query = f"""
    SELECT
        n.nutzungsart,
        s.jahr,
        s.anzahl_studierende,
        n.faktor_m2_pro_student,
        s.anzahl_studierende * n.faktor_m2_pro_student AS bedarf_m2,
        g.flaeche_m2_gesamt,
        g.flaeche_m2_gesamt - (s.anzahl_studierende * n.faktor_m2_pro_student) AS differenz_m2
    FROM nutzungsfaktoren n
    CROSS JOIN studierende s
    LEFT JOIN (
        SELECT nutzungsart, SUM(flaeche_m2) AS flaeche_m2_gesamt
        FROM gebaeude_raeume
        GROUP BY nutzungsart
    ) g ON g.nutzungsart = n.nutzungsart
    WHERE n.szenario = '{scenario_selector.value}'
    ORDER BY n.nutzungsart, s.jahr
    """

    _result = con.execute(_query).fetchdf()
    mo.ui.table(_result)
    return


if __name__ == "__main__":
    app.run()
