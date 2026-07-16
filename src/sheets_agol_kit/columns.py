"""Detect form columns by keywords.

Each project defines its own logical fields and the keywords that match
them in the real Form headers; it can also force an exact header per
field via overrides.
"""

import unicodedata
from collections.abc import Iterable, Mapping, Sequence


def normalize(text: object) -> str:
    """Lowercase and strip accents, for comparing headers."""
    normalized = unicodedata.normalize("NFD", str(text).lower())
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")


def map_columns(
    headers: Sequence[str],
    keywords: Mapping[str, Sequence[str]],
    overrides: Mapping[str, str] | None = None,
    required: Iterable[str] = (),
) -> dict[str, str]:
    """Map each logical field to the real Form header.

    Args:
        headers: list of real headers from the responses tab.
        keywords: dict field -> list of keywords (compared normalized,
            without accents or case).
        overrides: dict field -> exact header; takes priority over
            keywords. Empty values are ignored.
        required: fields that must be detected.

    Returns dict field -> header. Raises ValueError if a required field
    is missing.
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
            f"Could not detect columns {missing}. "
            f"Headers found: {list(headers)}. "
            "Use overrides to specify them explicitly."
        )
    return mapping
