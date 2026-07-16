"""Nominatim geocoding with persistent cache and pasted coordinates.

If the text already contains coordinates or a pasted Google Maps link,
those exact coordinates are used (precision "gps") without calling
Nominatim. Otherwise it queries Nominatim (OpenStreetMap) with a
persistent JSON cache: each text is geocoded only once for the life of
the project.

Everything region-specific (bounding box, query suffix, cache path,
user agent) is passed as a constructor parameter to Geocoder.
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

# Nominatim usage policy: at most 1 request per second
DEFAULT_MIN_SECONDS_BETWEEN_REQUESTS = 1.1

# Pasted Google Maps coordinates: "18.486090, -66.783960" (also appear
# in long URLs after "@").
_COORDS_RE = re.compile(r"(-?\d{1,2}\.\d{3,})\s*[,/@ ]\s*(-?\d{1,3}\.\d{3,})")
# Exact pin inside a long Google Maps URL: ...!3d18.48!4d-66.78...
_PIN_RE = re.compile(r"!3d(-?\d{1,3}\.\d+)!4d(-?\d{1,3}\.\d+)")
# Short "Share" button link (no coordinates; must follow the redirect
# to the long URL).
_SHORT_LINK_RE = re.compile(r"https?://(?:maps\.app\.goo\.gl|goo\.gl/maps)/\S+")

Coords = dict[str, float]
GeocodeResult = dict[str, float | str]


class Geocoder:
    """Configurable geocoder.

    Args:
        user_agent: identifier for Nominatim (include a contact email).
        bounds: dict with min_lat/max_lat/min_lon/max_lon; results outside
            the bounding box are discarded (homonyms from other regions)
            and Nominatim queries are restricted with viewbox+bounded.
            If None, no filtering is applied.
        query_suffix: text appended to every Nominatim query
            (e.g. "Puerto Rico").
        cache_file: path to the persistent JSON cache.
        min_seconds_between_requests: minimum wait between Nominatim calls.
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

    # --- pasted coordinates / Google Maps links ---

    def _extract_coords(self, text: str) -> Coords | None:
        """Extract lat/lon from pasted coordinates or a long Google Maps URL.

        Returns {"lat": ..., "lon": ...} or None. Prefers the exact pin
        (!3d/!4d) over view coordinates (@lat,lon). Discards points
        outside the bounding box.
        """
        match = _PIN_RE.search(text) or _COORDS_RE.search(text)
        if not match:
            return None
        lat, lon = float(match.group(1)), float(match.group(2))
        if not self._in_bounds(lat, lon):
            logger.debug(
                "Coordinates (%s, %s) outside bounding box; discarded", lat, lon
            )
            return None
        return {"lat": lat, "lon": lon}

    def _resolve_short_link(self, url: str) -> str:
        """Follow a short-link redirect and return the final long URL."""
        response = requests.get(
            url,
            headers={"User-Agent": self.user_agent},
            allow_redirects=True,
            timeout=15,
        )
        response.raise_for_status()
        return response.url

    def _parse_google_maps(self, text: str) -> Coords | None:
        """Exact coordinates if the text is a Google Maps paste.

        Short links require an HTTP request (follow the redirect), so they
        are cached like Nominatim queries; network failures are not cached
        so the next run can retry.
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
            logger.info("Could not resolve short link %s: %s", url, exc)
            return None
        result = self._extract_coords(final_url)
        self.cache[url] = result
        self._save_cache()
        return result

    # --- Nominatim ---

    def _query_nominatim(self, query: str) -> Coords | None:
        """Query Nominatim while respecting the request rate limit.

        Returns {"lat": ..., "lon": ...} or None if there is no valid
        result. Raises on network/server errors (caller decides whether
        to retry) so transient failures are not cached as "not found".
        """
        wait = self.min_seconds_between_requests - (
            time.monotonic() - self._last_request_time
        )
        if wait > 0:
            time.sleep(wait)
        params: dict[str, str | int] = {"q": query, "format": "json", "limit": 1}
        if self.bounds is not None:
            # Note: for regions without their own country code (e.g. Puerto
            # Rico, classified under "us"), restrict with viewbox+bounded
            # instead of countrycodes.
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
                "Nominatim returned (%s, %s) outside bounding box for %r",
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

    # --- public API ---

    def geocode(self, place: str | None, area: str | None = "") -> GeocodeResult | None:
        """Geocode a place with a fallback area.

        Returns {"lat", "lon", "precision"} or None if nothing geocodes:

        - precision "gps": the text contained coordinates or a Google Maps link.
        - precision "place": Nominatim found the exact place.
        - precision "area": fell back to the center of the area.
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
                logger.debug("%r did not geocode; using area center %r", place, area)
                return {**result, "precision": "area"}
        return None
