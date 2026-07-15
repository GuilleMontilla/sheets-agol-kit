"""Tests del pipeline de sincronizacion con un spreadsheet falso."""

import gspread

from sheets_agol_kit import sync
from sheets_agol_kit.sheets import write_rows


class FakeWorksheet:
    def __init__(self, records=()):
        self._records = list(records)
        self.cleared = False
        self.updated = None

    def get_all_records(self):
        return self._records

    def clear(self):
        self.cleared = True

    def update(self, values, value_input_option=None):
        self.updated = values


class FakeSpreadsheet:
    def __init__(self, tabs):
        self.tabs = tabs

    def worksheet(self, tab):
        if tab not in self.tabs:
            raise gspread.WorksheetNotFound(tab)
        return self.tabs[tab]

    def add_worksheet(self, title, rows, cols):
        worksheet = FakeWorksheet()
        self.tabs[title] = worksheet
        return worksheet


RESPONSES = [
    {"Lugar": "Plaza Palmer", "Municipio": "Caguas"},
    {"Lugar": "", "Municipio": ""},  # no geocodificable: se omite
    {"Lugar": "El Morro", "Municipio": "San Juan"},
]


def build_row(response):
    if not response["Lugar"]:
        return None
    return [response["Lugar"], response["Municipio"]]


def test_sync_filtra_filas_none_y_devuelve_conteos():
    output = FakeWorksheet()
    ss = FakeSpreadsheet({"respuestas": FakeWorksheet(RESPONSES), "mapa": output})

    written, total = sync(
        ss,
        responses_tab="respuestas",
        output_tab="mapa",
        headers=["lugar", "area"],
        build_row=build_row,
    )

    assert (written, total) == (2, 3)
    assert output.cleared
    assert output.updated == [
        ["lugar", "area"],
        ["Plaza Palmer", "Caguas"],
        ["El Morro", "San Juan"],
    ]


def test_write_rows_crea_la_pestana_si_no_existe():
    ss = FakeSpreadsheet({})
    created = write_rows(ss, "mapa", ["lugar"], [["Plaza Palmer"]])
    assert created is True
    assert ss.tabs["mapa"].updated == [["lugar"], ["Plaza Palmer"]]


def test_write_rows_reusa_la_pestana_existente():
    existing = FakeWorksheet()
    ss = FakeSpreadsheet({"mapa": existing})
    created = write_rows(ss, "mapa", ["lugar"], [])
    assert created is False
    assert existing.cleared
    assert existing.updated == [["lugar"]]
