# Contributing to sheets-agol-kit

Thanks for your interest. Quick guide:

## Setup

```
git clone https://github.com/GuilleMontilla/sheets-agol-kit
cd sheets-agol-kit
python -m venv .venv
.venv\Scripts\activate      # on Linux/macOS: source .venv/bin/activate
pip install -e .[dev]
```

## Before opening a PR

Run locally the same checks as CI:

```
pytest --cov
ruff check .
ruff format --check .
mypy
```

- Every behavior change needs a test. Tests must not hit the network:
  mock `requests` with `monkeypatch` (see `tests/test_geocoder.py`).
- Domain specifics stay out of library code: bounding boxes, keywords,
  headers, and symbology are always passed as parameters.

## Conventions

- Short branches from `main`: `feat/short-name`, `fix/short-name`.
- Commits follow [Conventional Commits](https://www.conventionalcommits.org/):
  `feat:`, `fix:`, `docs:`, `chore:`, `test:`.
- Add the matching entry in `CHANGELOG.md` (Unreleased section).

## Reporting bugs or proposing features

Use the repository issue templates.
