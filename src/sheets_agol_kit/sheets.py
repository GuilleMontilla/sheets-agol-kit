"""Lectura y escritura de Google Sheets via gspread (service account).

Ninguna funcion lee variables de entorno: sheet id, ruta de la service
account y nombres de pestanas llegan siempre como argumentos.
"""

from pathlib import Path
from typing import Any

import gspread
from gspread.utils import ValueInputOption


def open_spreadsheet(
    sheet_id: str, service_account_file: str | Path
) -> gspread.Spreadsheet:
    """Abre un Sheet por su ID usando una service account de Google Cloud."""
    client = gspread.service_account(filename=service_account_file)
    return client.open_by_key(sheet_id)


def read_responses(spreadsheet: gspread.Spreadsheet, tab: str) -> list[dict[str, Any]]:
    """Devuelve las filas de una pestana como lista de diccionarios."""
    return spreadsheet.worksheet(tab).get_all_records()


def write_rows(
    spreadsheet: gspread.Spreadsheet,
    tab: str,
    headers: list[str],
    rows: list[list[Any]],
) -> bool:
    """Reescribe una pestana completa con encabezados + filas.

    Crea la pestana si no existe. Devuelve True si la creo.
    """
    created = False
    try:
        worksheet = spreadsheet.worksheet(tab)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=tab, rows=max(len(rows) + 10, 100), cols=len(headers)
        )
        created = True
    worksheet.clear()
    worksheet.update([headers] + rows, value_input_option=ValueInputOption.raw)
    return created


def gviz_csv_url(sheet_id: str, tab: str) -> str:
    """URL del endpoint gviz que expone una pestana como CSV (Sheet publico)."""
    return (
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq"
        f"?tqx=out:csv&sheet={tab}"
    )
