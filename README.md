# sheets-agol-kit

Librería Python reusable para construir mapas vivos con herramientas gratuitas:

```
Google Form → Sheet (respuestas) → geocoding (Nominatim) → Sheet (pestaña limpia)
    → capa CSV vía gviz → Web Map en ArcGIS Online (cuenta pública)
```

Nada del dominio está fijo en el código: bounding box, palabras clave de
columnas, encabezados de salida y simbología se pasan como parámetros. La
misma librería sirve para reportes ciudadanos, inventarios, avistamientos o
cualquier flujo Form → mapa.

## Instalación

```
pip install "sheets-agol-kit @ git+https://github.com/TU_USUARIO/sheets-agol-kit"
```

Para crear el Web Map en AGOL (módulo `webmap.create_webmap`) hace falta el
extra `agol` (instala la librería `arcgis`, que es pesada):

```
pip install "sheets-agol-kit[agol] @ git+https://github.com/TU_USUARIO/sheets-agol-kit"
```

## Módulos

| Módulo | Qué hace |
|---|---|
| `geocoder` | `Geocoder`: Nominatim con caché persistente, coordenadas pegadas y enlaces de Google Maps, bounding box y sufijo de consulta configurables |
| `sheets` | Abrir un Sheet (service account), leer respuestas, reescribir la pestaña limpia, URL gviz del CSV |
| `columns` | Detectar columnas del Form por palabras clave, con overrides opcionales |
| `pipeline` | `sync()`: orquesta lectura → transformación → escritura |
| `webmap` | Construir el JSON del Web Map (capa CSV, renderer, pop-ups) y crearlo en AGOL |

## Uso

### Geocodificar

```python
from sheets_agol_kit import Geocoder

geocoder = Geocoder(
    user_agent="mi-proyecto/1.0 (contacto@ejemplo.com)",
    bounds={"min_lat": 17.6, "max_lat": 18.7, "min_lon": -68.0, "max_lon": -65.1},
    query_suffix="Puerto Rico",
    cache_file="geocode_cache.json",
)

geocoder.geocode("Plaza Palmer", "Caguas")
# {"lat": ..., "lon": ..., "precision": "place"}
```

`precision` indica cómo se obtuvo el punto:

- `"gps"`: el texto traía coordenadas o un enlace de Google Maps.
- `"place"`: Nominatim encontró el lugar exacto.
- `"area"`: se cayó al centro del área de respaldo (segundo argumento).

### Sincronizar un Sheet

```python
from sheets_agol_kit import open_spreadsheet, map_columns, sync

ss = open_spreadsheet("SHEET_ID", "credentials/service_account.json")

columns = map_columns(
    headers=["¿Dónde está?", "¿En qué municipio?", "Marca temporal"],
    keywords={"lugar": ["donde", "lugar"], "area": ["municipio"], "fecha": ["marca temporal"]},
    required=("lugar", "area"),
)

def build_row(response):
    lugar = response.get(columns["lugar"], "")
    area = response.get(columns["area"], "")
    location = geocoder.geocode(lugar, area)
    if location is None:
        return None  # se omite la respuesta
    return [location["lat"], location["lon"], lugar, area]

written, total = sync(
    ss,
    responses_tab="Respuestas de formulario 1",
    output_tab="mapa",
    headers=["lat", "lon", "lugar", "area"],
    build_row=build_row,
)
```

### Crear el Web Map en AGOL

```python
from sheets_agol_kit import (
    gviz_csv_url, build_webmap_json, unique_value_renderer, create_webmap,
)

webmap_json = build_webmap_json(
    csv_url=gviz_csv_url("SHEET_ID", "mapa"),
    fields=[{"name": "lat", "type": "esriFieldTypeDouble", "alias": "lat"}, ...],
    layer_title="Mis reportes",
    renderer=unique_value_renderer("estado", {"reportado": [230, 57, 53, 255]}),
    extent={"xmin": -67.5, "ymin": 17.6, "xmax": -65.1, "ymax": 18.7},
)

item = create_webmap(
    username="usuario_agol",
    password="...",
    title="Mi mapa vivo",
    webmap_json=webmap_json,
)
print(item.homepage)
```

## Proyecto de ejemplo

[reporte-ciudadano-agol](https://github.com/tek-innovators/reporte-ciudadano-agol):
mapa vivo de reportes ciudadanos de zonas de vertido de basura en Puerto Rico
construido sobre esta librería.

## Desarrollo

```
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```
