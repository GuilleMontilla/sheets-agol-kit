# Ejemplos

Scripts listos para copiar y adaptar tras configurar Google Form, Sheet y
service account.

1. Sigue [docs/configuration.md](../docs/configuration.md) (checklist al final).
2. Edita los placeholders de `sync_minimal.py` (`SHEET_ID`, rutas, keywords).
3. Ejecuta:

```
pip install -e .
python examples/sync_minimal.py
```

`sync_minimal.py` lee la pestaña de respuestas, geocodifica y reescribe la
pestaña limpia (`mapa` por defecto).
