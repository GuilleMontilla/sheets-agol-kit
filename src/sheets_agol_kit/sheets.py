"""Lectura y escritura de Google Sheets via gspread (service account).

Ninguna funcion lee variables de entorno: sheet id, ruta de la service
account y nombres de pestanas llegan siempre como argumentos.
"""

import gspread


def open_spreadsheet(sheet_id, service_account_file):
    """Abre un Sheet por su ID usando una service account de Google Cloud."""
    client = gspread.service_account(filename=service_account_file)
    return client.open_by_key(sheet_id)


def read_responses(spreadsheet, tab):
    """Devuelve las filas de una pestana como lista de diccionarios."""
    return spreadsheet.worksheet(tab).get_all_records()


def write_rows(spreadsheet, tab, headers, rows):
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
    worksheet.update([headers] + rows, value_input_option="RAW")
    return created


def gviz_csv_url(sheet_id, tab):
    """URL del endpoint gviz que expone una pestana como CSV (Sheet publico)."""
    return (
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq"
        f"?tqx=out:csv&sheet={tab}"
    )
