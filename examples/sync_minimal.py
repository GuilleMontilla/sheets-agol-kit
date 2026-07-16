"""Ejemplo minimo: respuestas del Form -> geocoding -> pestana limpia.

Antes de ejecutar, completa la configuracion de Google:
ver docs/configuration.md

Uso (desde la raiz del repo, con la libreria instalada):

    pip install -e .
    python examples/sync_minimal.py
"""

from pathlib import Path

from sheets_agol_kit import Geocoder, map_columns, open_spreadsheet, sync

# --- Ajusta estos valores a tu proyecto ---
SHEET_ID = "TU_SHEET_ID"
SERVICE_ACCOUNT = Path("credentials/service_account.json")
RESPONSES_TAB = "Respuestas de formulario 1"
OUTPUT_TAB = "mapa"

geocoder = Geocoder(
    user_agent="sheets-agol-kit-example/1.0 (contacto@ejemplo.com)",
    bounds={"min_lat": 17.6, "max_lat": 18.7, "min_lon": -68.0, "max_lon": -65.1},
    query_suffix="Puerto Rico",
    cache_file="geocode_cache.json",
)

ss = open_spreadsheet(SHEET_ID, SERVICE_ACCOUNT)
headers = list(ss.worksheet(RESPONSES_TAB).row_values(1))

columns = map_columns(
    headers=headers,
    keywords={
        "lugar": ["donde", "lugar"],
        "area": ["municipio", "area", "barrio"],
    },
    required=("lugar", "area"),
)


def build_row(response: dict) -> list | None:
    lugar = response.get(columns["lugar"], "")
    area = response.get(columns["area"], "")
    location = geocoder.geocode(lugar, area)
    if location is None:
        return None
    return [location["lat"], location["lon"], lugar, area, location["precision"]]


written, total = sync(
    ss,
    responses_tab=RESPONSES_TAB,
    output_tab=OUTPUT_TAB,
    headers=["lat", "lon", "lugar", "area", "precision"],
    build_row=build_row,
)
print(f"Escritas {written} de {total} respuestas en la pestana '{OUTPUT_TAB}'.")
