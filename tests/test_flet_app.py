import io

import pandas as pd
from openpyxl import load_workbook

from app.flet_app import _build_excel_rounded


def test_build_excel_rounded_appends_total_row_per_year() -> None:
    df_sd = pd.DataFrame(
        {
            "Nutzungsart": ["Labor", "Labor", "Seminar", "Seminar"],
            "Jahr": [2030, 2040, 2030, 2040],
            "Fläche": [49.0, 81.0, 102.0, 153.0],
            "Bedarf_m2": [76.0, 125.0, 151.0, 195.0],
            "Differenz_m2": [-27.0, -44.0, -49.0, -42.0],
        }
    )

    workbook = load_workbook(io.BytesIO(_build_excel_rounded(df_sd)))
    sheet = workbook["Gerundete Flächen"]
    total_row = sheet.max_row

    assert sheet.cell(row=total_row, column=1).value == "Total"
    assert sheet.cell(row=total_row, column=2).value == 150
    assert sheet.cell(row=total_row, column=3).value == 225
    assert sheet.cell(row=total_row, column=4).value == -75
    assert sheet.cell(row=total_row, column=5).value == 235
    assert sheet.cell(row=total_row, column=6).value == 320
    assert sheet.cell(row=total_row, column=7).value == -85
