# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es/1.1.0/)
y el proyecto usa [Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased]

### Added

- Documentación de configuración Google Form / Sheet / service account
  (`docs/configuration.md`), índice en `docs/README.md` y sección de
  problemas frecuentes.
- Ejemplo mínimo de sync (`examples/sync_minimal.py`) y guía en
  `examples/README.md`.
- `SECURITY.md`, plantilla de issues `config.yml` y Dependabot
  (pip + github-actions).

### Changed

- README: primer viewport más corto (instalación antes del contraste con
  Survey123); enlaces a docs de configuración y a `examples/`; tono
  técnico y sección de captura de ubicación / niveles de precisión.
- `.gitignore`: ignorar `pytest-cache-files-*/`.

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
