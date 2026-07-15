"""Tests del geocodificador, sin tocar la red (requests siempre mockeado)."""

import json

import pytest
import requests

from sheets_agol_kit import Geocoder

PR_BOUNDS = {"min_lat": 17.6, "max_lat": 18.7, "min_lon": -68.0, "max_lon": -65.1}

LONG_MAPS_URL = (
    "https://www.google.com/maps/place/Plaza+Palmer/@18.2341,-66.0361,17z/"
    "data=!3m1!4b1!4m6!3m5!1s0x0:0x0!8m2!3d18.234567!4d-66.039876"
)


class FakeResponse:
    def __init__(self, payload=None, url=""):
        self._payload = payload
        self.url = url

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


@pytest.fixture
def geocoder(tmp_path):
    return Geocoder(
        user_agent="tests/1.0",
        bounds=PR_BOUNDS,
        query_suffix="Puerto Rico",
        cache_file=tmp_path / "cache.json",
        min_seconds_between_requests=0,
    )


def forbid_network(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("no debe tocar la red")

    monkeypatch.setattr("sheets_agol_kit.geocoder.requests.get", fail)


def mock_nominatim(monkeypatch, results_by_query):
    """Mockea requests.get devolviendo resultados segun la consulta 'q'."""
    calls = []

    def fake_get(url, params=None, headers=None, timeout=None):
        calls.append(params["q"])
        return FakeResponse(payload=results_by_query.get(params["q"], []))

    monkeypatch.setattr("sheets_agol_kit.geocoder.requests.get", fake_get)
    return calls


class TestCoordenadasPegadas:
    def test_coordenadas_de_google_maps(self, geocoder, monkeypatch):
        forbid_network(monkeypatch)
        result = geocoder.geocode("18.486090, -66.783960", "Isabela")
        assert result == {"lat": 18.486090, "lon": -66.783960, "precision": "gps"}

    def test_pin_exacto_de_url_larga(self, geocoder, monkeypatch):
        forbid_network(monkeypatch)
        result = geocoder.geocode(LONG_MAPS_URL, "Caguas")
        assert result == {"lat": 18.234567, "lon": -66.039876, "precision": "gps"}

    def test_coordenadas_fuera_del_bounding_box_se_descartan(
        self, geocoder, monkeypatch
    ):
        # Madrid: fuera de Puerto Rico; debe caer a Nominatim con el area
        calls = mock_nominatim(
            monkeypatch,
            {"Caguas, Puerto Rico": [{"lat": "18.23", "lon": "-66.03"}]},
        )
        result = geocoder.geocode("40.416775, -3.703790", "Caguas")
        assert result == {"lat": 18.23, "lon": -66.03, "precision": "area"}
        assert calls  # si consulto Nominatim


class TestEnlaceCorto:
    def test_sigue_redireccion_y_cachea(self, geocoder, monkeypatch):
        short_url = "https://maps.app.goo.gl/abc123"
        calls = []

        def fake_get(url, headers=None, allow_redirects=None, timeout=None):
            calls.append(url)
            return FakeResponse(url=LONG_MAPS_URL)

        monkeypatch.setattr("sheets_agol_kit.geocoder.requests.get", fake_get)

        first = geocoder.geocode(short_url, "Caguas")
        second = geocoder.geocode(short_url, "Caguas")
        assert (
            first
            == second
            == {
                "lat": 18.234567,
                "lon": -66.039876,
                "precision": "gps",
            }
        )
        assert calls == [short_url]  # la segunda vez sale del cache

    def test_fallo_de_red_no_se_cachea(self, geocoder, monkeypatch):
        short_url = "https://maps.app.goo.gl/abc123"

        def fake_get(
            url, params=None, headers=None, allow_redirects=None, timeout=None
        ):
            if "goo.gl" in url:
                raise requests.ConnectionError("sin red")
            return FakeResponse(payload=[])

        monkeypatch.setattr("sheets_agol_kit.geocoder.requests.get", fake_get)
        assert geocoder.geocode(short_url, "") is None
        assert short_url not in geocoder.cache


class TestCascadaDePrecision:
    def test_place_cuando_nominatim_encuentra_el_lugar(self, geocoder, monkeypatch):
        mock_nominatim(
            monkeypatch,
            {"Plaza Palmer, Caguas, Puerto Rico": [{"lat": "18.23", "lon": "-66.03"}]},
        )
        result = geocoder.geocode("Plaza Palmer", "Caguas")
        assert result == {"lat": 18.23, "lon": -66.03, "precision": "place"}

    def test_area_cuando_el_lugar_no_geocodifica(self, geocoder, monkeypatch):
        mock_nominatim(
            monkeypatch,
            {"Caguas, Puerto Rico": [{"lat": "18.23", "lon": "-66.03"}]},
        )
        result = geocoder.geocode("sitio inexistente xyz", "Caguas")
        assert result == {"lat": 18.23, "lon": -66.03, "precision": "area"}

    def test_none_cuando_nada_geocodifica(self, geocoder, monkeypatch):
        mock_nominatim(monkeypatch, {})
        assert geocoder.geocode("nada", "tampoco") is None

    def test_resultado_fuera_del_bounding_box_se_descarta(self, geocoder, monkeypatch):
        # Nominatim devuelve un homonimo fuera de la region
        mock_nominatim(
            monkeypatch,
            {"Santa Isabel, Puerto Rico": [{"lat": "33.95", "lon": "-118.4"}]},
        )
        assert geocoder.geocode("", "Santa Isabel") is None

    def test_entradas_vacias_o_none(self, geocoder, monkeypatch):
        forbid_network(monkeypatch)
        assert geocoder.geocode("", "") is None
        assert geocoder.geocode(None, None) is None


class TestCache:
    def test_cache_persiste_entre_instancias(self, tmp_path, monkeypatch):
        cache_file = tmp_path / "cache.json"
        query = "Plaza Palmer, Caguas, Puerto Rico"
        calls = mock_nominatim(
            monkeypatch, {query: [{"lat": "18.23", "lon": "-66.03"}]}
        )

        def make_geocoder():
            return Geocoder(
                user_agent="tests/1.0",
                bounds=PR_BOUNDS,
                query_suffix="Puerto Rico",
                cache_file=cache_file,
                min_seconds_between_requests=0,
            )

        first = make_geocoder().geocode("Plaza Palmer", "Caguas")
        assert calls == [query]
        assert json.loads(cache_file.read_text(encoding="utf-8"))[query] == {
            "lat": 18.23,
            "lon": -66.03,
        }

        # Nueva instancia: mismo resultado sin volver a consultar
        second = make_geocoder().geocode("Plaza Palmer", "Caguas")
        assert first == second
        assert calls == [query]

    def test_no_encontrado_tambien_se_cachea(self, geocoder, monkeypatch):
        calls = mock_nominatim(monkeypatch, {})
        geocoder.geocode("nada", "tampoco")
        geocoder.geocode("nada", "tampoco")
        # 2 consultas la primera vez (place y area), 0 la segunda
        assert len(calls) == 2
