"""Tests de deteccion de columnas por palabras clave."""

import pytest

from sheets_agol_kit import map_columns, normalize


class TestNormalize:
    def test_minusculas(self):
        assert normalize("CAGUAS") == "caguas"

    def test_sin_acentos(self):
        assert normalize("Añasco, Río Grande") == "anasco, rio grande"

    def test_acepta_no_strings(self):
        assert normalize(123) == "123"


class TestMapColumns:
    HEADERS = ["Marca temporal", "¿Dónde está el lugar?", "¿En qué municipio?"]

    def test_detecta_por_keywords(self):
        mapping = map_columns(
            headers=self.HEADERS,
            keywords={
                "fecha": ["marca temporal"],
                "lugar": ["donde", "lugar"],
                "area": ["municipio"],
            },
        )
        assert mapping == {
            "fecha": "Marca temporal",
            "lugar": "¿Dónde está el lugar?",
            "area": "¿En qué municipio?",
        }

    def test_keywords_ignoran_acentos_y_mayusculas(self):
        mapping = map_columns(
            headers=["¿DÓNDE?"],
            keywords={"lugar": ["donde"]},
        )
        assert mapping["lugar"] == "¿DÓNDE?"

    def test_override_tiene_prioridad(self):
        mapping = map_columns(
            headers=self.HEADERS,
            keywords={"lugar": ["donde"]},
            overrides={"lugar": "¿En qué municipio?"},
        )
        assert mapping["lugar"] == "¿En qué municipio?"

    def test_override_vacio_se_ignora(self):
        mapping = map_columns(
            headers=self.HEADERS,
            keywords={"lugar": ["donde"]},
            overrides={"lugar": ""},
        )
        assert mapping["lugar"] == "¿Dónde está el lugar?"

    def test_campo_no_requerido_ausente_no_falla(self):
        mapping = map_columns(
            headers=self.HEADERS,
            keywords={"lugar": ["donde"], "telefono": ["telefono"]},
        )
        assert "telefono" not in mapping

    def test_requerido_ausente_lanza_valueerror(self):
        with pytest.raises(ValueError, match="telefono"):
            map_columns(
                headers=self.HEADERS,
                keywords={"telefono": ["telefono"]},
                required=("telefono",),
            )
