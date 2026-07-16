"""Read and write Google Sheets via gspread (service account).

No function reads environment variables: sheet id, service-account path,
and tab names are always passed as arguments.
"""

from pathlib import Path
from typing import Any

import gspread
from gspread.utils import ValueInputOption


def open_spreadsheet(
    sheet_id: str, service_account_file: str | Path
) -> gspread.Spreadsheet:
    """Open a Sheet by ID using a Google Cloud service account."""
    client = gspread.service_account(filename=service_account_file)
    return client.open_by_key(sheet_id)


def read_responses(spreadsheet: gspread.Spreadsheet, tab: str) -> list[dict[str, Any]]:
    """Return the rows of a tab as a list of dictionaries."""
    return spreadsheet.worksheet(tab).get_all_records()


def write_rows(
    spreadsheet: gspread.Spreadsheet,
    tab: str,
    headers: list[str],
    rows: list[list[Any]],
) -> bool:
    """Rewrite a full tab with headers + rows.

    Creates the tab if it does not exist. Returns True if it was created.
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
    """gviz endpoint URL that exposes a tab as CSV (public Sheet)."""
    return (
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq"
        f"?tqx=out:csv&sheet={tab}"
    )
