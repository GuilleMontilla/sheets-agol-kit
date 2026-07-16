# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Google Form / Sheet / service account setup docs
  (`docs/configuration.md`), docs index (`docs/README.md`), and a
  common-issues section.
- Minimal sync example (`examples/sync_minimal.py`) and
  `examples/README.md`.
- `SECURITY.md`, issue template `config.yml`, and Dependabot
  (pip + github-actions).

### Changed

- Documentation language switched to English for broader reach.
- README: shorter first viewport (install before Survey123 contrast);
  links to configuration docs and `examples/`; technical tone and
  location-capture / precision section.
- `.gitignore`: ignore `pytest-cache-files-*/`.

## [0.1.0] - 2026-07-15

### Added

- `Geocoder`: Nominatim with persistent JSON cache, pasted coordinates
  and Google Maps links (short and long), configurable bounding box and
  query suffix, `gps`/`place`/`area` precision levels.
- `sheets`: open a Sheet with a service account, read responses, rewrite
  the clean tab, and gviz CSV URL.
- `columns.map_columns`: Form column detection by keywords, with
  optional overrides.
- `pipeline.sync`: read → transform → write orchestration.
- `webmap`: Web Map JSON construction (CSV layer, unique-value renderer,
  pop-ups) and item creation on ArcGIS Online (optional `[agol]` extra).

[Unreleased]: https://github.com/GuilleMontilla/sheets-agol-kit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/GuilleMontilla/sheets-agol-kit/releases/tag/v0.1.0
