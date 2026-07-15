"""Geocodificacion con Nominatim, cache persistente y coordenadas pegadas.

Si el texto trae coordenadas o un enlace de Google Maps pegado, se usan esas
coordenadas exactas (precision "gps") sin consultar Nominatim. En caso
contrario consulta Nominatim (OpenStreetMap) con cache persistente en JSON:
cada texto se geocodifica una sola vez en la vida del proyecto.

Todo lo especifico de una region (bounding box, sufijo de la consulta, ruta
del cache, user agent) se pasa como parametro al constructor de Geocoder.
"""

import json
import logging
import re
import time
from collections.abc import Mapping
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Politica de uso de Nominatim: maximo 1 peticion por segundo
DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS = 1.1

# Coordenadas pegadas de Google Maps: "18.486090, -66.783960" (tambien
# aparecen asi en las URLs largas, despues de la "@").
_COORDS_RE = re.compile(r"(-?\d{1,2}\.\d{3,})\s*[,/@ ]\s*(-?\d{1,3}\.\d{3,})")
# Pin exacto dentro de una URL larga de Google Maps: ...!3d18.48!4d-66.78...
_PIN_RE = re.compile(r"!3d(-?\d{1,3}\.\d+)!4d(-?\d{1,3}\.\d+)")
# Enlace corto del boton "Compartir" (no contiene coordenadas; hay que
# seguir la redireccion hasta la URL larga).
_SHORT_LINK_RE = re.compile(r"https?://(?:maps\.app\.goo\.gl|goo\.gl/maps)/\S+")

Coords = dict[str, float]
GeocodeResult = dict[str, float | str]


class Geocoder:
    """Geocodificador parametrizable.

    Args:
        user_agent: identificador para Nominatim (incluye un email de contacto).
        bounds: dict con min_lat/max_lat/min_lon/max_lon; los resultados fuera
            del bounding box se descartan (homonimos de otras regiones) y la
            consulta a Nominatim se restringe con viewbox+bounded. Si es None,
            no se filtra.
        query_suffix: texto que se agrega al final de cada consulta a
            Nominatim (ej. "Puerto Rico").
        cache_file: ruta del JSON de cache persistente.
        min_seconds_between_requests: espera minima entre consultas a Nominatim.
    """

    def __init__(
        self,
        user_agent: str,
        *,
        bounds: Mapping[str, float] | None = None,
        query_suffix: str = "",
        cache_file: str | Path = "geocode_cache.json",
        min_seconds_between_requests: float = DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS,
    ) -> None:
        self.user_agent = user_agent
        self.bounds = bounds
        self.query_suffix = query_suffix
        self.cache_file = Path(cache_file)
        self.min_seconds_between_requests = min_seconds_between_requests
        self._last_request_time = 0.0
        self.cache: dict[str, Coords | None] = self._load_cache()

    # --- cache ---

    def _load_cache(self) -> dict[str, Coords | None]:
        if self.cache_file.exists():
            return json.loads(self.cache_file.read_text(encoding="utf-8"))
        return {}

    def _save_cache(self) -> None:
        self.cache_file.write_text(
            json.dumps(self.cache, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # --- bounding box ---

    def _in_bounds(self, lat: float, lon: float) -> bool:
        if self.bounds is None:
            return True
        return (
            self.bounds["min_lat"] <= lat <= self.bounds["max_lat"]
            and self.bounds["min_lon"] <= lon <= self.bounds["max_lon"]
        )

    # --- coordenadas pegadas / enlaces de Google Maps ---

    def _extract_coords(self, text: str) -> Coords | None:
        """Extrae lat/lon de coordenadas pegadas o de una URL larga de Google Maps.

        Devuelve {"lat": ..., "lon": ...} o None. Prioriza el pin exacto
        (!3d/!4d) sobre las coordenadas de la vista (@lat,lon). Descarta
        puntos fuera del bounding box.
        """
        match = _PIN_RE.search(text) or _COORDS_RE.search(text)
        if not match:
            return None
        lat, lon = float(match.group(1)), float(match.group(2))
        if not self._in_bounds(lat, lon):
            logger.debug(
                "Coordenadas (%s, %s) fuera del bounding box; se descartan", lat, lon
            )
            return None
        return {"lat": lat, "lon": lon}

    def _resolve_short_link(self, url: str) -> str:
        """Sigue la redireccion de un enlace corto y devuelve la URL larga final."""
        response = requests.get(
            url,
            headers={"User-Agent": self.user_agent},
            allow_redirects=True,
            timeout=15,
        )
        response.raise_for_status()
        return response.url

    def _parse_google_maps(self, text: str) -> Coords | None:
        """Coordenadas exactas si el texto es un copy-paste de Google Maps.

        Los enlaces cortos requieren una peticion HTTP (seguir la redireccion),
        asi que se cachean igual que las consultas a Nominatim; los fallos de
        red no se cachean para poder reintentar en la proxima corrida.
        """
        short_link = _SHORT_LINK_RE.search(text)
        if not short_link:
            return self._extract_coords(text)
        url = short_link.group(0)
        if url in self.cache:
            return self.cache[url]
        try:
            final_url = self._resolve_short_link(url)
        except requests.RequestException as exc:
            logger.info("No se pudo resolver el enlace corto %s: %s", url, exc)
            return None
        result = self._extract_coords(final_url)
        self.cache[url] = result
        self._save_cache()
        return result

    # --- Nominatim ---

    def _query_nominatim(self, query: str) -> Coords | None:
        """Consulta Nominatim respetando el limite de peticiones.

        Devuelve {"lat": ..., "lon": ...} o None si no hay resultado valido.
        Lanza excepcion en errores de red/servidor (el llamador decide
        reintentar), para no cachear fallos transitorios como "no encontrado".
        """
        wait = self.min_seconds_between_requests - (
            time.monotonic() - self._last_request_time
        )
        if wait > 0:
            time.sleep(wait)
        params: dict[str, str | int] = {"q": query, "format": "json", "limit": 1}
        if self.bounds is not None:
            # Nota: para regiones sin country code propio (ej. Puerto Rico,
            # clasificado bajo "us") se restringe con viewbox+bounded en vez
            # de countrycodes.
            params["viewbox"] = (
                f"{self.bounds['min_lon']},{self.bounds['max_lat']},"
                f"{self.bounds['max_lon']},{self.bounds['min_lat']}"
            )
            params["bounded"] = 1
        response = requests.get(
            NOMINATIM_URL,
            params=params,
            headers={"User-Agent": self.user_agent},
            timeout=15,
        )
        self._last_request_time = time.monotonic()
        response.raise_for_status()
        results = response.json()
        if not results:
            return None
        lat, lon = float(results[0]["lat"]), float(results[0]["lon"])
        if not self._in_bounds(lat, lon):
            logger.debug(
                "Nominatim devolvio (%s, %s) fuera del bounding box para %r",
                lat,
                lon,
                query,
            )
            return None
        return {"lat": lat, "lon": lon}

    def _cached_query(self, query: str) -> Coords | None:
        if query in self.cache:
            return self.cache[query]
        result = self._query_nominatim(query)
        self.cache[query] = result
        self._save_cache()
        return result

    def _build_query(self, *parts: str) -> str:
        return ", ".join(p for p in (*parts, self.query_suffix) if p)

    # --- API publica ---

    def geocode(self, place: str | None, area: str | None = "") -> GeocodeResult | None:
        """Geocodifica un lugar con un area de respaldo.

        Devuelve {"lat", "lon", "precision"} o None si nada geocodifica:

        - precision "gps": el texto traia coordenadas o un enlace de Google Maps.
        - precision "place": Nominatim encontro el lugar exacto.
        - precision "area": se cayo al centro del area de respaldo.
        """
        place = (place or "").strip()
        area = (area or "").strip()
        if place:
            coords = self._parse_google_maps(place)
            if coords:
                return {**coords, "precision": "gps"}
        if place and area:
            result = self._cached_query(self._build_query(place, area))
            if result:
                return {**result, "precision": "place"}
        if area:
            result = self._cached_query(self._build_query(area))
            if result:
                logger.debug(
                    "%r no geocodifico; se usa el centro del area %r", place, area
                )
                return {**result, "precision": "area"}
        return None
