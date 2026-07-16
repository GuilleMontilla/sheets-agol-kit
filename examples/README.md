# Examples

Copy-paste scripts to adapt after setting up Google Form, Sheet, and
service account.

1. Follow [docs/configuration.md](../docs/configuration.md) (checklist at the end).
2. Edit the placeholders in `sync_minimal.py` (`SHEET_ID`, paths, keywords).
3. Run:

```
pip install -e .
python examples/sync_minimal.py
```

`sync_minimal.py` reads the responses tab, geocodes, and rewrites the
clean tab (`mapa` by default).
