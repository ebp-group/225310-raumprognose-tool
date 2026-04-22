"""Raumprognose Tool – Flet Desktop Application.

Run with:
    flet run app/flet_app.py
    Or directly:
    python app/flet_app.py

Assets (splash screen, icon) are served from the ``app/assets/`` directory.
"""

from __future__ import annotations

import base64
import io
import os
import sys
import asyncio
from pathlib import Path
from typing import Any, cast
import logging

import flet as ft
import flet_datatable2 as fdt
import matplotlib

matplotlib.use("Agg")  # noqa: E402 – must be set before importing pyplot
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils.dataframe import dataframe_to_rows

# Ensure the app directory is on the path for sibling imports
sys.path.insert(0, os.path.dirname(__file__))

from calculations import current_area_by_nutzungsart, future_demand, surplus_deficit
from data_loader import load_gebaeude_raeume, load_nutzungsfaktoren, load_studierende

SPLASH_DURATION_SECONDS = 2
SPLASH_FADE_OUT_MS = 300

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log.setLevel(logging.DEBUG)

# ── UI helper functions ───────────────────────────────────────────────────────

def get_assets_dir() -> Path:
    default_assets_dir = Path(__file__).parent / "assets"   # fallback for local runs
    return Path(os.environ.get("FLET_ASSETS_DIR", str(default_assets_dir))).resolve()


def _df_to_datatable(df: pd.DataFrame, max_rows: int = 200) -> ft.DataTable:
    """Convert a pandas DataFrame to a Flet DataTable widget."""
    columns = [
        ft.DataColumn(label=ft.Text(str(col), weight=ft.FontWeight.BOLD))
        for col in df.columns
    ]
    rows = []
    for _, row in df.head(max_rows).iterrows():
        cells = [ft.DataCell(ft.Text(str(val))) for val in row]
        rows.append(fdt.DataRow2(cells=cells))
    return ft.DataTable(
        columns=columns,
        rows=rows,
        border=ft.Border.all(1, ft.Colors.GREY_300),
        heading_row_color=ft.Colors.BLUE_GREY_50,
        horizontal_lines=ft.BorderSide(1, ft.Colors.GREY_200),
    )


def _metric_card(label: str, value: str, is_surplus: bool) -> ft.Card:
    """Build a compact metric display card."""
    return ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text(label, size=14, color=ft.Colors.GREY_600),
                    ft.Text(value, size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        "Überschuss" if is_surplus else "Defizit",
                        size=12,
                        color=ft.Colors.GREEN if is_surplus else ft.Colors.RED,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
            ),
            padding=16,
            alignment=ft.Alignment.CENTER,
        ),
        elevation=2,
    )


def _fig_to_base64(fig: plt.Figure) -> str:
    """Render a matplotlib figure to a base64-encoded PNG string."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# ── Chart builders ────────────────────────────────────────────────────────────


def _create_students_chart(df_studierende: pd.DataFrame) -> plt.Figure:
    """Line chart with one line per category over time."""
    fig, ax = plt.subplots(figsize=(8, 4))

    if {"Jahr", "Kategorie", "Anzahl"}.issubset(df_studierende.columns):
        chart_df = (
            df_studierende.pivot_table(
                index="Jahr",
                columns="Kategorie",
                values="Anzahl",
                aggfunc="sum",
            )
            .reset_index()
            .sort_values("Jahr")
        )
    else:
        chart_df = df_studierende.sort_values("Jahr").copy()

    def _series_for(category: str) -> pd.Series | None:
        if category in chart_df.columns:
            return chart_df[category]
        contains = category.lower()
        matches = [
            c
            for c in chart_df.columns
            if c != "Jahr" and contains.lower() in str(c).lower()
        ]
        if not matches:
            return None
        return chart_df.loc[:, matches].sum(axis=1)

    categories = [
        ("Studierende", "#1f77b4"),
        ("Forschung", "#2ca02c"),
        ("Services", "#ff7f0e"),
        ("Stundenlohn", "#d62728"),
    ]

    for label, color in categories:
        values = _series_for(label)
        if values is None:
            continue
        ax.plot(
            chart_df["Jahr"],
            values,
            marker="o",
            linewidth=2,
            label=label,
            color=color,
        )

    ax.set_xlabel("Jahr")
    ax.set_ylabel("Anzahl")
    ax.set_title("Entwicklung nach Kategorie")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def _create_demand_chart(df_demand: pd.DataFrame, scenario: str) -> plt.Figure:
    """Grouped bar chart of area demand by usage type and year."""
    fig, ax = plt.subplots(figsize=(10, 5))
    #years = sorted(df_demand["jahr"].unique())
    years = [2026, 2030, 2040, 2050]

    nutzungsarten = sorted(df_demand["Nutzungsart"].unique())
    x = range(len(nutzungsarten))
    width = 0.8 / max(len(years), 1)

    for i, year in enumerate(years):
        df_year = df_demand[df_demand["Jahr"] == year]
        values = []
        for n in nutzungsarten:
            subset = df_year[df_year["Nutzungsart"] == n]["Bedarf_m2"]
            values.append(subset.values[0] if len(subset) > 0 else 0)
        offset = (i - len(years) / 2 + 0.5) * width
        ax.bar([xi + offset for xi in x], values, width, label=str(year))

    ax.set_xlabel("Nutzungsart")
    ax.set_ylabel("Bedarf (m²)")
    ax.set_title(f"Flächenbedarf – Szenario: {scenario}")
    ax.set_xticks(list(x))
    ax.set_xticklabels(nutzungsarten, rotation=45, ha="right")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    return fig


def _create_surplus_deficit_charts(df_sd: pd.DataFrame) -> list[plt.Figure]:
    """One bar chart per forecast year showing surplus/deficit by usage type."""
    # years = sorted(df_sd["jahr"].unique())
    years = [2026, 2030, 2040, 2050]
    figs: list[plt.Figure] = []
    for year in years:
        fig, ax = plt.subplots(figsize=(5, 4))
        df_year = df_sd[df_sd["Jahr"] == year]
        colors = ["#2ecc71" if v >= 0 else "#e74c3c" for v in df_year["Differenz_m2"]]
        ax.bar(df_year["Nutzungsart"], df_year["Differenz_m2"], color=colors)
        ax.set_xlabel("Nutzungsart")
        ax.set_ylabel("Differenz (m²)")
        ax.set_title(str(year))
        ax.axhline(y=0, color="black", linewidth=0.5)
        ax.tick_params(axis="x", rotation=45)
        ax.grid(True, alpha=0.3, axis="y")
        fig.tight_layout()
        figs.append(fig)
    return figs


# ── Excel export builder ─────────────────────────────────────────────────────


def _build_excel(
    df_results: pd.DataFrame,
    df_stud: pd.DataFrame,
    df_dem: pd.DataFrame,
) -> bytes:
    """Build a styled multi-sheet Excel workbook and return it as bytes.

    Args:
        df_results: Full surplus/deficit DataFrame.
        df_stud: Student numbers DataFrame.
        df_dem: Future demand DataFrame.

    Returns:
        Raw bytes of the ``.xlsx`` workbook.
    """
    wb = Workbook()

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="1F4E79")
    green_fill = PatternFill("solid", fgColor="C6EFCE")
    red_fill = PatternFill("solid", fgColor="FFC7CE")
    center = Alignment(horizontal="center")

    def _write_sheet(
        ws: Any, df: pd.DataFrame, title: str, diff_col: str | None = None
    ) -> None:
        ws.title = title
        for r_idx, row in enumerate(
            dataframe_to_rows(df, index=False, header=True), start=1
        ):
            ws.append(row)
            if r_idx == 1:
                for cell in ws[r_idx]:
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = center
            elif diff_col and r_idx > 1:
                col_names = list(df.columns)
                if diff_col in col_names:
                    c_idx = col_names.index(diff_col) + 1
                    val = ws.cell(row=r_idx, column=c_idx).value
                    try:
                        if float(val) >= 0:
                            ws.cell(row=r_idx, column=c_idx).fill = green_fill
                        else:
                            ws.cell(row=r_idx, column=c_idx).fill = red_fill
                    except (TypeError, ValueError):
                        pass

    ws1 = wb.active
    _write_sheet(ws1, df_results, "Ergebnisse", diff_col="Differenz_m2")

    ws2 = wb.create_sheet()
    _write_sheet(ws2, df_stud, "Studierende")

    ws3 = wb.create_sheet()
    _write_sheet(ws3, df_dem, "Flächenbedarf")

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ── Main application ─────────────────────────────────────────────────────────


def main(page: ft.Page) -> None:
    """Build and display the Raumprognose desktop application."""

    page.title = "🏛️ Raumprognose Tool"
    page.window.width = 1400
    page.window.height = 900
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

    # ── Splash screen overlay ─────────────────────────────────────────────

    splash_image = ft.Image(src="splash.png", fit=ft.BoxFit.CONTAIN)
    splash_overlay = ft.Container(
        content=splash_image,
        alignment=ft.Alignment.CENTER,
        bgcolor=ft.Colors.WHITE,
        expand=True,
        opacity=1.0,
        animate_opacity=ft.Animation(SPLASH_FADE_OUT_MS, ft.AnimationCurve.EASE_OUT),
    )
    page.overlay.append(splash_overlay)
    page.update()

    async def dismiss_splash() -> None:
        """Fade out and remove the splash screen after a short delay."""
        await asyncio.sleep(SPLASH_DURATION_SECONDS)
        splash_overlay.opacity = 0
        splash_overlay.update
        page.update()
        # Wait for the fade-out animation to finish, then remove the overlay.
        await asyncio.sleep(SPLASH_FADE_OUT_MS / 1000 + 0.1)

        if splash_overlay in page.overlay:
            page.overlay.remove(splash_overlay)
            page.update()

    page.run_task(dismiss_splash)

    # ── Mutable application state ─────────────────────────────────────────

    # TODO: remove hardcoded paths and use file pickers instead
    base_path = Path(r"C:\Users\ods\OneDrive - EBP\CH_P_225310 - PE_TPF_UniSG - General\40_BEARBEITUNG\04_Auswertung\02_Datenmodell")

    state: dict[str, Any] = {
        "df_gebaeude": None,
        "df_studierende": None,
        "df_faktoren": None,
        "scenario": "Basis",
        "custom_gebaeude": (base_path / "260402_UniSG_Rauminventar_rev_260414.xlsx"),
        "custom_studierende": (base_path / "prognose_studierende_und_ma.xlsx"),
        "custom_faktoren": (base_path / "nutzungsfaktoren.xlsx"),
    }

    # ── Data loading ──────────────────────────────────────────────────────

    def load_all_data(e) -> bool:
        """Load all three datasets. Returns *True* on success."""
        if any(state[f"custom_{key}"] is None for key in ("gebaeude", "studierende", "faktoren")):
            page.show_dialog(
                ft.SnackBar(
                    content=ft.Text("Bitte zuerst alle Dateien auswählen."),
                    bgcolor=ft.Colors.RED_400,
                )
            )
            return False
        try:
            state["df_gebaeude"] = load_gebaeude_raeume(state["custom_gebaeude"])
            state["df_studierende"] = load_studierende(state["custom_studierende"])
            state["df_faktoren"] = load_nutzungsfaktoren(state["custom_faktoren"])

            _update_scenario_options()
            rebuild_content()
            page.update()
            return True
        except Exception as exc:
            log.exception("Error loading data")
            page.show_dialog(
                ft.SnackBar(
                    content=ft.Text(f"Fehler beim Laden der Daten: {exc}"),
                    bgcolor=ft.Colors.RED_400,
                )
            )
            return False

    def get_results() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Return (current_area, demand, surplus_deficit) DataFrames."""
        df_current = current_area_by_nutzungsart(state["df_gebaeude"])
        df_demand = future_demand(
            state["df_studierende"], state["df_faktoren"], state["scenario"]
        )
        df_sd = surplus_deficit(df_current, df_demand)
        return df_current, df_demand, df_sd
        

    # ── File picker ──────────────────────────────────────────────────────

    gebaeude_label = ft.Text("Keine Datei gewählt", size=12, italic=True)
    studierende_label = ft.Text("Keine Datei gewählt", size=12, italic=True)
    faktoren_label = ft.Text("Keine Datei gewählt", size=12, italic=True)

    async def _pick_file(key: str, label: ft.Text):
        """Open a file-picker dialog for one of the three input datasets.

        The picked file path is stored in ``state["custom_{key}"]`` and
        the sidebar label is updated accordingly.

        Args:
            key: State key suffix – one of ``"gebaeude"``, ``"studierende"``,
                or ``"faktoren"``.
            label: The sidebar :class:`ft.Text` label to update with the
                chosen file name.
        """
        files = await ft.FilePicker().pick_files(
            allowed_extensions=["xlsx"],
            file_type=ft.FilePickerFileType.CUSTOM,
            dialog_title=f"{key.capitalize()} (.xlsx)",
        )
        if files:
            state[f"custom_{key}"] = files[0].path
            label.value = Path(files[0].path).name
        else:
            state[f"custom_{key}"] = None
            label.value = "Keine Datei gewählt"
        
        _update_scenario_options()
        rebuild_content()
        page.update()

    async def load_inventory_file(e) -> None:
        await _pick_file("gebaeude", gebaeude_label)

    async def load_person_file(e) -> None:
        await _pick_file("studierende", studierende_label)

    async def load_faktoren_file(e) -> None:
        await _pick_file("faktoren", faktoren_label)



    # Export handlers
    async def _save_excel(_e):
        _, df_demand, df_sd = get_results()
        excel_bytes = _build_excel(df_sd, state["df_studierende"], df_demand)
        path = await ft.FilePicker().save_file(
            file_name=f"raumprognose_{state['scenario']}.xlsx",
            allowed_extensions=["xlsx"],
            file_type=ft.FilePickerFileType.CUSTOM,
        )
        if path:
            with open(path, "wb") as f:
                f.write(excel_bytes)
            page.show_dialog(ft.SnackBar(content=ft.Text(f"Gespeichert: {path}")))
            page.update()

    async def _save_students_png(_e):
        fig = _create_students_chart(state["df_studierende"])
        path = await ft.FilePicker().save_file(
            file_name="studierende.png",
            allowed_extensions=["png"],
            file_type=ft.FilePickerFileType.CUSTOM,
        )
        if path:
            fig.savefig(path, format="png", dpi=150, bbox_inches="tight")
            page.show_dialog(ft.SnackBar(content=ft.Text(f"Gespeichert: {path}")))
            page.update()
        plt.close(fig)

    async def _save_demand_png(_e):
        _, df_demand, _ = get_results()
        fig = _create_demand_chart(df_demand, state["scenario"])
        path = await ft.FilePicker().save_file(
            file_name=f"flaechenbedarf_{state['scenario']}.png",
            allowed_extensions=["png"],
            file_type=ft.FilePickerFileType.CUSTOM,
        )
        if path:
            fig.savefig(path, format="png", dpi=150, bbox_inches="tight")
            page.show_dialog(ft.SnackBar(content=ft.Text(f"Gespeichert: {path}")))
            page.update()
        plt.close(fig)

    # ── Scenario dropdown ─────────────────────────────────────────────────

    def _scenario_options() -> list[ft.dropdown.Option]:
        """Return dropdown options derived from the loaded factors DataFrame."""
        if state["df_faktoren"] is not None:
            return [
                ft.dropdown.Option(s)
                for s in sorted(state["df_faktoren"]["Szenario"].unique().tolist())
            ]
        return []

    def _on_scenario_changed(e: ft.ControlEvent):
        state["scenario"] = e.control.value
        rebuild_content()
        page.update()

    scenario_dropdown = ft.Dropdown(
        label="Szenario wählen",
        options=_scenario_options(),
        value=state["scenario"],
        on_select=_on_scenario_changed,
        width=220,
    )

    def _update_scenario_options():
        """Sync the scenario dropdown with the currently loaded factors data.

        If the previously selected scenario is no longer available after a
        file change, the first available scenario is selected automatically.
        """
        scenario_dropdown.options = _scenario_options()
        if state["df_faktoren"] is not None:
            available = state["df_faktoren"]["Szenario"].unique().tolist()
            if state["scenario"] not in available:
                state["scenario"] = available[0] if available else "Basis"
                scenario_dropdown.value = state["scenario"]

    # ── Content container ─────────────────────────────────────────────────

    content_area = ft.Container(expand=True, padding=0)

    def rebuild_content():
        """Rebuild all tab content from current state."""
        log.debug("Rebuilding content with scenario: %s", state["scenario"])
        log.debug("Factors data:\n%s", state["df_faktoren"])
        log.debug("Student data:\n%s", state["df_studierende"])
        log.debug("Building data:\n%s", state["df_gebaeude"])
        if any(
            state[k] is None for k in ("df_gebaeude", "df_studierende", "df_faktoren")
        ):
            log.debug("Missing data, showing placeholder")
            content_area.content = ft.Container(
                content=ft.Text(
                    "Bitte zuerst Daten laden.",
                    size=16,
                    color=ft.Colors.BLUE,
                ),
                padding=40,
            )
            return
        
        log.debug("Calculating results...")
        _, df_demand, df_sd = get_results()
        years = sorted(df_sd["Jahr"].unique())

        df_studierende_display = state["df_studierende"].rename(
            columns={
                "Forschung_Monatslohn": "Forschung (Monatslohn)",
                "Forschung_Stundenlohn": "Forschung (Stundenlohn)",
                "Services_Monatslohn": "Services (Monatslohn)",
                "Services_Stundenlohn": "Services (Stundenlohn)",
            }
        )

        # ── Tab 1: Übersicht ──────────────────────────────────────────────
        tab1 = ft.Column(
            [
                ft.Text("Gebäude & Räume", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Column(
                        [_df_to_datatable(state["df_gebaeude"])],
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    height=300,
                ),
                ft.Divider(),
                ft.Text(
                    "Studierende & Mitarbeitende",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Container(
                    content=ft.Column(
                        [_df_to_datatable(df_studierende_display),],
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    height=300,
                ),
                ft.Divider(),
                ft.Text(
                    f"Nutzungsfaktoren – Szenario: {state['scenario']}",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Container(
                    content=ft.Column(
                            [_df_to_datatable(state["df_faktoren"][state["df_faktoren"]["Szenario"] == state["scenario"]])],
                            scroll=ft.ScrollMode.AUTO,
                        ),
                    height=300,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
        )

        # ── Tab 2: Ergebnisse ─────────────────────────────────────────────
        metric_cards = []
        for year in [2026, 2030, 2040, 2050]:
            total_diff = df_sd[df_sd["Jahr"] == year]["Differenz_m2"].sum()
            metric_cards.append(
                _metric_card(
                    label=str(year),
                    value=f"{total_diff:,.0f} m²",
                    is_surplus=total_diff >= 0,
                )
            )

        # Pivot table with colour coding
        pivot = df_sd.pivot_table(
            index="Nutzungsart",
            columns="Jahr",
            values="Differenz_m2",
            aggfunc="first",
        )
        pivot.columns = [str(c) for c in pivot.columns]

        pivot_columns = [
            ft.DataColumn(ft.Text("Nutzungsart", weight=ft.FontWeight.BOLD))
        ] + [
            ft.DataColumn(ft.Text(col, weight=ft.FontWeight.BOLD))
            for col in pivot.columns
        ]
        pivot_rows = []
        for nutzungsart, row in pivot.iterrows():
            cells: list[ft.DataCell] = [ft.DataCell(ft.Text(str(nutzungsart)))]
            for val in row:
                try:
                    v = float(val)
                    bg = (
                        ft.Colors.GREEN_100
                        if v > 0
                        else (ft.Colors.RED_100 if v < 0 else None)
                    )
                    tc = "#276221" if v > 0 else ("#9c0006" if v < 0 else None)
                    cells.append(
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(f"{v:.1f}", color=tc),
                                bgcolor=bg,
                                padding=8,
                            )
                        )
                    )
                except (TypeError, ValueError):
                    cells.append(ft.DataCell(ft.Text(str(val))))
            pivot_rows.append(ft.DataRow(cells=cells))

        pivot_table = ft.DataTable(
            columns=pivot_columns,
            rows=pivot_rows,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            heading_row_color=ft.Colors.BLUE_GREY_50,
            horizontal_lines=ft.BorderSide(1, ft.Colors.GREY_200),
        )

        df_sd_display = df_sd.rename(
            columns={
                "Fläche": "Ist-Fläche (m²)",
                "Bedarf_m2": "Bedarf (m²)",
                "Differenz_m2": "Differenz (m²)",
            }
        )

        tab2 = ft.Column(
            [
                ft.Text(
                    f"Flächen-Über-/Unterschuss – Szenario: {state['scenario']}",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Row(metric_cards, spacing=16, wrap=False, scroll=ft.ScrollMode.AUTO),
                ft.Divider(),
                ft.Text(
                    "Differenz (m²) pro Nutzungsart und Jahr "
                    "(grün = Überschuss, rot = Defizit)",
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Container(
                    content=ft.Column([pivot_table], scroll=ft.ScrollMode.AUTO),
                ),
                ft.Divider(),
                ft.Text(
                    "Vollständige Ergebnistabelle",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Container(
                    content=ft.Column(
                        [_df_to_datatable(df_sd_display)],
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    height=300,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
        )

        # ── Tab 3: Diagramme ─────────────────────────────────────────────
        fig_students = _create_students_chart(state["df_studierende"])
        fig_demand = _create_demand_chart(df_demand, state["scenario"])
        sd_figs = _create_surplus_deficit_charts(df_sd)

        sd_chart_controls = [
            ft.Container(
                content=ft.Image(src=_fig_to_base64(fig)),
                expand=True,
            )
            for fig in sd_figs
        ]

        tab3 = ft.Column(
            controls=[
                ft.Text(
                    "Studierendenzahlen & Kategorien im Zeitverlauf",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Container(
                    content=ft.Image(src=_fig_to_base64(fig_students)),
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Divider(),
                ft.Text(
                    "Flächenbedarf nach Nutzungsart und Jahr",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Container(
                    content=ft.Image(src=_fig_to_base64(fig_demand)),
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Divider(),
                ft.Text(
                    "Über-/Unterschuss nach Nutzungsart",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Row(cast(list[ft.Control], sd_chart_controls), spacing=8, wrap=True),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=16,
        )

        # Close all matplotlib figures to free memory
        plt.close("all")

        # ── Tab 4: Export ─────────────────────────────────────────────────
        tab4 = ft.Column(
            [
                ft.Text(
                    "Ergebnisse exportieren",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Button(
                    "📥 Ergebnisse als Excel speichern",
                    on_click=_save_excel,
                    icon=ft.Icons.SAVE,
                ),
                ft.Divider(),
                ft.Text(
                    "Diagramme als PNG speichern",
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Row(
                    [
                        ft.Button(
                            "📥 Studierendenzahlen (PNG)",
                            on_click=_save_students_png,
                            icon=ft.Icons.IMAGE,
                        ),
                        ft.Button(
                            "📥 Flächenbedarf (PNG)",
                            on_click=_save_demand_png,
                            icon=ft.Icons.IMAGE,
                        ),
                    ],
                    spacing=16,
                ),
            ],
            spacing=16,
        )

        # ── Assemble tabs ────────────────────────────────────────────────

        content_area.content = ft.Tabs(
            selected_index=0,
            length=4,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(
                        tabs=[
                            ft.Tab(label=ft.Text("📋 Übersicht")),
                            ft.Tab(label=ft.Text("📊 Ergebnisse")),
                            ft.Tab(label=ft.Text("📈 Diagramme")),
                            ft.Tab(label=ft.Text("⬇️ Export")),
                        ]
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[
                            ft.Container(content=tab1, padding=20),
                            ft.Container(content=tab2, padding=20),
                            ft.Container(content=tab3, padding=20),
                            ft.Container(content=tab4, padding=20),
                        ],
                    ),
                ],
            ),
        )

    # ── Sidebar ───────────────────────────────────────────────────────────

    sidebar = ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    "⚙️ Einstellungen",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Divider(),
                ft.Text("Szenario", weight=ft.FontWeight.BOLD),
                scenario_dropdown,
                ft.Divider(),
                ft.Text(
                    "📂 Eigene Dateien laden",
                    weight=ft.FontWeight.BOLD,
                    size=14,
                ),
                ft.Button(
                    "Gebäude & Räume",
                    on_click=load_inventory_file,
                    icon=ft.Icons.UPLOAD_FILE,
                    width=220,
                ),
                gebaeude_label,
                ft.Button(
                    "Studierende & Mitarbeitende",
                    on_click=load_person_file,
                    icon=ft.Icons.UPLOAD_FILE,
                    width=220,
                ),
                studierende_label,
                ft.Button(
                    "Nutzungsfaktoren",
                    on_click=load_faktoren_file,
                    icon=ft.Icons.UPLOAD_FILE,
                    width=220,
                ),
                faktoren_label,
                ft.Divider(),
                ft.Button(
                    "Szenario berechnen",
                    on_click=load_all_data,
                    icon=ft.Icons.CALCULATE,
                    width=220,
                ),
            ],
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
        ),
        width=280,
        padding=20,
        bgcolor=ft.Colors.GREY_50,
        border=ft.Border.only(right=ft.BorderSide(1, ft.Colors.GREY_300)),
    )

    # ── Initial data load & render ────────────────────────────────────────

    _update_scenario_options()
    rebuild_content()

    page.add(
        ft.Row(
            [sidebar, content_area],
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
    )


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
