"""Deteccion de columnas del formulario por palabras clave.

Cada proyecto define sus propios campos logicos y las palabras clave que los
identifican en los encabezados reales del Form; tambien puede forzar un
encabezado exacto por campo via overrides.
"""

import unicodedata
from collections.abc import Iterable, Mapping, Sequence


def normalize(text: object) -> str:
    """Minusculas y sin acentos, para comparar encabezados."""
    normalized = unicodedata.normalize("NFD", str(text).lower())
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")


def map_columns(
    headers: Sequence[str],
    keywords: Mapping[str, Sequence[str]],
    overrides: Mapping[str, str] | None = None,
    required: Iterable[str] = (),
) -> dict[str, str]:
    """Asocia cada campo logico con el encabezado real del Form.

    Args:
        headers: lista de encabezados reales de la pestana de respuestas.
        keywords: dict campo -> lista de palabras clave (se comparan
            normalizadas, sin acentos ni mayusculas).
        overrides: dict campo -> encabezado exacto; tiene prioridad sobre
            las palabras clave. Valores vacios se ignoran.
        required: campos que deben detectarse si o si.

    Devuelve dict campo -> encabezado. Lanza ValueError si falta un requerido.
    """
    overrides = overrides or {}
    mapping: dict[str, str] = {}
    for field, field_keywords in keywords.items():
        override = overrides.get(field)
        if override:
            mapping[field] = override
            continue
        for header in headers:
            if any(kw in normalize(header) for kw in field_keywords):
                mapping[field] = header
                break
    missing = [f for f in required if f not in mapping]
    if missing:
        raise ValueError(
            f"No se detectaron las columnas {missing}. "
            f"Encabezados encontrados: {list(headers)}. "
            "Usa overrides para indicarlas explicitamente."
        )
    return mapping
