# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es/1.1.0/)
y el proyecto usa [Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased]

## [0.1.0] - 2026-07-15

### Added

- `Geocoder`: Nominatim con caché persistente en JSON, extracción de
  coordenadas pegadas y enlaces de Google Maps (cortos y largos),
  bounding box y sufijo de consulta configurables, precisiones
  `gps`/`place`/`area`.
- `sheets`: abrir un Sheet con service account, leer respuestas,
  reescribir la pestaña limpia y URL gviz del CSV.
- `columns.map_columns`: detección de columnas del Form por palabras
  clave, con overrides opcionales.
- `pipeline.sync`: orquestación lectura → transformación → escritura.
- `webmap`: construcción del JSON del Web Map (capa CSV, renderer por
  valores únicos, pop-ups) y creación del item en ArcGIS Online
  (extra opcional `[agol]`).

[Unreleased]: https://github.com/GuilleMontilla/sheets-agol-kit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/GuilleMontilla/sheets-agol-kit/releases/tag/v0.1.0
