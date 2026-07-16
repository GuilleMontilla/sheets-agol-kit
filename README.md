# sheets-agol-kit

![CI](https://img.shields.io/github/actions/workflow/status/GuilleMontilla/sheets-agol-kit/ci.yml?branch=main&label=CI)
![Version](https://img.shields.io/github/v/tag/GuilleMontilla/sheets-agol-kit?sort=semver&label=version)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Python library for the **form → geocoding → live map on ArcGIS Online**
pipeline, using free tools (Google Form + Sheets, Nominatim, public AGOL
account).

```
Google Form → Sheet (responses) → geocoding (Nominatim) → Sheet (clean tab)
    → CSV layer via gviz → Web Map on ArcGIS Online (public account)
```

Each project's domain is configurable: bounding box, column keywords,
output headers, and symbology are always passed as parameters.

## Installation

```
pip install "sheets-agol-kit @ git+https://github.com/GuilleMontilla/sheets-agol-kit"
```

Creating the Web Map on AGOL (`webmap.create_webmap`) requires the `agol`
extra (installs the `arcgis` library):

```
pip install "sheets-agol-kit[agol] @ git+https://github.com/GuilleMontilla/sheets-agol-kit"
```

## Usage

Before syncing a Sheet or creating the Web Map:

1. Set up the Form, Sheet, and Google Cloud service account:
   [docs/configuration.md](docs/configuration.md)
2. Full runnable example to adapt:
   [examples/](examples/)

### Geocode

```python
from sheets_agol_kit import Geocoder

geocoder = Geocoder(
    user_agent="my-project/1.0 (contact@example.com)",
    bounds={"min_lat": 17.6, "max_lat": 18.7, "min_lon": -68.0, "max_lon": -65.1},
    query_suffix="Puerto Rico",
    cache_file="geocode_cache.json",
)

geocoder.geocode("Plaza Palmer", "Caguas")
# {"lat": ..., "lon": ..., "precision": "place"}
```

Details on `precision` and accepted location formats:
[Location capture and precision levels](#location-capture-and-precision-levels).

### Sync a Sheet

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
        return None  # skip this response
    return [location["lat"], location["lon"], lugar, area]

written, total = sync(
    ss,
    responses_tab="Respuestas de formulario 1",
    output_tab="mapa",
    headers=["lat", "lon", "lugar", "area"],
    build_row=build_row,
)
```

### Create the Web Map on AGOL

```python
from sheets_agol_kit import (
    gviz_csv_url, build_webmap_json, unique_value_renderer, create_webmap,
)

webmap_json = build_webmap_json(
    csv_url=gviz_csv_url("SHEET_ID", "mapa"),
    fields=[{"name": "lat", "type": "esriFieldTypeDouble", "alias": "lat"}, ...],
    layer_title="My reports",
    renderer=unique_value_renderer("estado", {"reportado": [230, 57, 53, 255]}),
    extent={"xmin": -67.5, "ymin": 17.6, "xmax": -65.1, "ymax": 18.7},
)

item = create_webmap(
    username="agol_user",
    password="...",
    title="My live map",
    webmap_json=webmap_json,
)
print(item.homepage)
```

## Alternative to Survey123

[ArcGIS Survey123](https://www.esri.com/en-us/arcgis/products/arcgis-survey123/overview)
covers the same form → map pattern inside the ArcGIS ecosystem, but usually
requires an organization or a paid license. This project is not an Esri
product or a Survey123 clone (it does not cover, for example, native
offline capture or signatures): it reproduces the flow with the free stack
described above.

## Use cases

The library does not hard-code a domain. Typical configuration examples:

| Domain | Form input | Map output |
|---|---|---|
| Dumping / litter | place + municipality | layer by `estado` |
| Trees / inventory | species + neighborhood | layer by species |
| Citizen reports | what happened + zone | layer by type |

## Location capture and precision levels

Form responses often include free text, coordinates, or Google Maps links.
The geocoder normalizes those values to a point (`lat`, `lon`) and a
precision level.

### Formats with `gps` precision (no Nominatim call)

If the text already contains an exact location, `geocode` returns
`precision: "gps"`:

- Pasted coordinates: `18.486090, -66.783960`
- Long Google Maps URL: exact pin `!3d...!4d...` (priority) or view
  `@lat,lon`
- Short Share-button link (`maps.app.goo.gl` / `goo.gl/maps`):
  follows the redirect to the long URL and caches the result

### Cascade when there is no GPS

1. `"place"` — Nominatim with place + area + `query_suffix`
2. `"area"` — center of the fallback area (second argument to `geocode`)
3. `None` — could not geocode; in `sync`, that row is skipped

The persistent JSON cache avoids repeating identical queries. The bounding
box discards homonyms outside the region and restricts Nominatim with
`viewbox` + `bounded`.

## Modules

| Module | What it does |
|---|---|
| `geocoder` | `Geocoder`: Nominatim with persistent cache, pasted coordinates and Google Maps links, configurable bounding box and query suffix |
| `sheets` | Open a Sheet (service account), read responses, rewrite the clean tab, gviz CSV URL |
| `columns` | Detect Form columns by keywords, with optional overrides |
| `pipeline` | `sync()`: orchestrates read → transform → write |
| `webmap` | Build the Web Map JSON (CSV layer, renderer, pop-ups) and create it on AGOL |

## Development

```
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
```

Tests, lint, format, and types (same as CI):

```
pytest --cov
ruff check .
ruff format --check .
mypy
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Changes are recorded in
[CHANGELOG.md](CHANGELOG.md).

## License

[MIT](LICENSE)
