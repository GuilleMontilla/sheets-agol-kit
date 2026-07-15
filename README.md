# sheets-agol-kit

![CI](https://img.shields.io/github/actions/workflow/status/GuilleMontilla/sheets-agol-kit/ci.yml?branch=main&label=CI)
![Version](https://img.shields.io/github/v/tag/GuilleMontilla/sheets-agol-kit?sort=semver&label=versi%C3%B3n)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/licencia-MIT-green)

La gente responde un Google Form pegando ubicación (texto, coordenadas o
un enlace de Maps). Tú quieres un **mapa vivo en ArcGIS Online** con
cuenta pública y herramientas gratuitas — sin hosted feature layers ni
servicios de pago.

```
Google Form → Sheet (respuestas) → geocoding (Nominatim) → Sheet (pestaña limpia)
    → capa CSV vía gviz → Web Map en ArcGIS Online (cuenta pública)
```

`sheets-agol-kit` es esa tubería empaquetada. Nada del dominio está fijo
en el código: bounding box, palabras clave de columnas, encabezados de
salida y simbología se pasan como parámetros. El mismo kit sirve para
varios proyectos Form → mapa.

## Instalación

```
pip install "sheets-agol-kit @ git+https://github.com/GuilleMontilla/sheets-agol-kit"
```

Para crear el Web Map en AGOL (módulo `webmap.create_webmap`) hace falta el
extra `agol` (instala la librería `arcgis`, que es pesada):

```
pip install "sheets-agol-kit[agol] @ git+https://github.com/GuilleMontilla/sheets-agol-kit"
```

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

Ver [El truco](#el-truco-ubicación-pegada-y-cascada-de-precisión) para
qué significa `precision` y qué formatos de Maps se capturan.

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

## Para qué sirve

El dominio lo defines tú con parámetros. Tres ejemplos típicos:

| Dominio | Entrada del Form | Salida en el mapa |
|---|---|---|
| Vertidos / basura | lugar + municipio | capa por `estado` |
| Árboles / inventario | especie + barrio | capa por especie |
| Reportes ciudadanos | qué pasó + zona | capa por tipo |

Proyecto real construido sobre este kit: `reporte-ciudadano-agol`
(repositorio privado de T3K Innovators) — mapa vivo de zonas de vertido
de basura en Puerto Rico.

## El truco: ubicación pegada y cascada de precisión

Lo menos genérico del kit es cómo convierte lo que la gente pega en el
Form en un punto en el mapa.

### Formatos que capturan GPS (sin consultar Nominatim)

Si el texto trae ubicación exacta, `geocode` devuelve
`precision: "gps"`:

- Coordenadas pegadas: `18.486090, -66.783960`
- URL larga de Google Maps: pin exacto `!3d...!4d...` (prioridad) o vista
  `@lat,lon`
- Enlace corto del botón Compartir (`maps.app.goo.gl` / `goo.gl/maps`):
  sigue la redirección hasta la URL larga y cachea el resultado

### Cascada si no hay GPS

1. `"place"` — Nominatim con lugar + área + `query_suffix`
2. `"area"` — centro del área de respaldo (segundo argumento de `geocode`)
3. `None` — nada geocodificó; en `sync`, esa fila se omite

El caché persistente en JSON evita reconsultar el mismo texto. El
bounding box descarta homónimos fuera de la región y restringe Nominatim
con `viewbox` + `bounded`.

## Módulos

| Módulo | Qué hace |
|---|---|
| `geocoder` | `Geocoder`: Nominatim con caché persistente, coordenadas pegadas y enlaces de Google Maps, bounding box y sufijo de consulta configurables |
| `sheets` | Abrir un Sheet (service account), leer respuestas, reescribir la pestaña limpia, URL gviz del CSV |
| `columns` | Detectar columnas del Form por palabras clave, con overrides opcionales |
| `pipeline` | `sync()`: orquesta lectura → transformación → escritura |
| `webmap` | Construir el JSON del Web Map (capa CSV, renderer, pop-ups) y crearlo en AGOL |

## Desarrollo

```
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
```

Tests, lint, formato y tipos (lo mismo que corre el CI):

```
pytest --cov
ruff check .
ruff format --check .
mypy
```

## Contribuir

Lee [CONTRIBUTING.md](CONTRIBUTING.md). Los cambios se registran en
[CHANGELOG.md](CHANGELOG.md).

## Licencia

[MIT](LICENSE)
