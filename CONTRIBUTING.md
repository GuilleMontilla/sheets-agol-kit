# Contribuir a sheets-agol-kit

Gracias por tu interés. Guía rápida:

## Setup

```
git clone https://github.com/GuilleMontilla/sheets-agol-kit
cd sheets-agol-kit
python -m venv .venv
.venv\Scripts\activate      # en Linux/macOS: source .venv/bin/activate
pip install -e .[dev]
```

## Antes de abrir un PR

Corre localmente lo mismo que el CI:

```
pytest --cov
ruff check .
ruff format --check .
mypy
```

- Todo cambio de comportamiento lleva su test. Los tests no tocan la red:
  mockea `requests` con `monkeypatch` (ver `tests/test_geocoder.py`).
- Nada del dominio va fijo en el código de la librería: bounding boxes,
  palabras clave, encabezados y simbología llegan siempre como parámetros.

## Convenciones

- Ramas cortas desde `main`: `feat/nombre-corto`, `fix/nombre-corto`.
- Commits en formato [Conventional Commits](https://www.conventionalcommits.org/):
  `feat:`, `fix:`, `docs:`, `chore:`, `test:`.
- Anota la entrada correspondiente en `CHANGELOG.md` (sección Unreleased).

## Reportar bugs o proponer mejoras

Usa los templates de issues del repositorio.
