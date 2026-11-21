"""Outlet coordinates and nearby same-category places, from OpenStreetMap (free, no key).

Only geocode() and nearby() are used elsewhere, so another provider (e.g. Mappls) can replace them later.
"""
import logging
import math
from typing import List, Optional, Tuple

import httpx

from backend.app.services.places import NOMINATIM_URL, USER_AGENT, _wait_for_slot

logger = logging.getLogger(__name__)

# Public Overpass servers; the second is tried when the first is busy
OVERPASS_URLS = ["https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter"]
# OSM tags that count as "the same kind of business" for each outlet category
CATEGORY_FILTERS = {
    "restaurant": ['["amenity"~"^(restaurant|fast_food|cafe|food_court)$"]'],
    "clinic": ['["amenity"~"^(clinic|doctors|dentist)$"]', '["healthcare"~"^(clinic|dentist|doctor)$"]'],
    "salon": ['["shop"~"^(hairdresser|beauty)$"]'],
}
# Nominatim search phrases for the same categories, used when every Overpass server is busy
FALLBACK_PHRASES = {
    "restaurant": ["restaurant", "cafe", "fast food"],
    "clinic": ["clinic"],
    "salon": ["hairdresser", "beauty shop"],
}


def geocode(name: str, address: str, city: str) -> Optional[Tuple[float, float]]:
    """(lat, lng) of the outlet, trying the most specific query first. None when nothing matches."""
    queries = [f"{name}, {address}" if address else None, f"{address}, {city}" if address else None, f"{name}, {city}"]
    for q in [q for q in queries if q]:
        _wait_for_slot()
        try:
            resp = httpx.get(
                NOMINATIM_URL,
                params={"q": q, "format": "jsonv2", "limit": 1, "countrycodes": "in"},
                headers={"User-Agent": USER_AGENT},
                timeout=8.0,
            )
            resp.raise_for_status()
            hits = resp.json()
        except (httpx.HTTPError, ValueError) as e:
            logger.warning("OpenStreetMap geocode failed: %s", e)
            continue
        if hits:
            return float(hits[0]["lat"]), float(hits[0]["lon"])
    return None


def distance_m(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    lat1, lng1, lat2, lng2 = map(math.radians, (*a, *b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lng2 - lng1) / 2) ** 2
    return 6371000 * 2 * math.asin(math.sqrt(h))


def _address(tags: dict) -> str:
    parts = [tags.get("addr:housenumber"), tags.get("addr:street"), tags.get("addr:suburb") or tags.get("addr:city")]
    return ", ".join(p for p in parts if p)


def _overpass(lat: float, lng: float, category: str, radius_m: int) -> Optional[List[dict]]:
    filters = CATEGORY_FILTERS.get(category, CATEGORY_FILTERS["restaurant"])
    body = "".join(f'nwr{f}["name"](around:{radius_m},{lat},{lng});' for f in filters)
    query = f"[out:json][timeout:10];({body});out center 200;"
    for url in OVERPASS_URLS:
        try:
            resp = httpx.post(url, data={"data": query}, headers={"User-Agent": USER_AGENT}, timeout=12.0)
            resp.raise_for_status()
            elements = resp.json().get("elements", [])
        except (httpx.HTTPError, ValueError) as e:
            logger.warning("Overpass query failed on %s: %s", url, e)
            continue
        return [
            {"id": f"osm-{el['type']}-{el['id']}", "name": el.get("tags", {}).get("name:en") or el.get("tags", {}).get("name"),
             "lat": el.get("lat", el.get("center", {}).get("lat")), "lng": el.get("lon", el.get("center", {}).get("lon")),
             "address": _address(el.get("tags", {}))}
            for el in elements
        ]
    return None


def _nominatim(lat: float, lng: float, category: str, radius_m: int) -> Optional[List[dict]]:
    dlat = radius_m / 111320
    dlng = dlat / max(math.cos(math.radians(lat)), 0.01)
    viewbox = f"{lng - dlng},{lat + dlat},{lng + dlng},{lat - dlat}"
    found, failed = [], 0
    phrases = FALLBACK_PHRASES.get(category, FALLBACK_PHRASES["restaurant"])
    for phrase in phrases:
        _wait_for_slot()
        try:
            resp = httpx.get(
                NOMINATIM_URL,
                params={"q": phrase, "format": "jsonv2", "limit": 40, "bounded": 1, "viewbox": viewbox},
                headers={"User-Agent": USER_AGENT},
                timeout=8.0,
            )
            resp.raise_for_status()
            hits = resp.json()
        except (httpx.HTTPError, ValueError) as e:
            logger.warning("OpenStreetMap nearby search failed: %s", e)
            failed += 1
            continue
        found += [
            {"id": f"osm-{h.get('osm_type', 'x')}-{h.get('osm_id')}", "name": h.get("name"),
             "lat": float(h["lat"]), "lng": float(h["lon"]),
             "address": ", ".join(h.get("display_name", "").split(", ")[1:3])}
            for h in hits
        ]
    return None if failed == len(phrases) else found


def nearby(lat: float, lng: float, category: str, radius_m: int = 1500, limit: int = 40) -> Optional[List[dict]]:
    """Named places of the same category around (lat, lng), nearest first. None when no source answered."""
    raw = _overpass(lat, lng, category, radius_m)
    if raw is None:
        raw = _nominatim(lat, lng, category, radius_m)
        if not raw:
            return None  # an empty answer from the fallback is not worth caching for a week
    places, seen = [], set()
    for p in raw:
        name = (p["name"] or "").strip()
        if not name or p["lat"] is None or name.lower() in seen:
            continue
        seen.add(name.lower())
        dist = distance_m((lat, lng), (p["lat"], p["lng"]))
        if dist <= radius_m:
            places.append({**p, "name": name, "distance_m": round(dist)})
    places.sort(key=lambda p: p["distance_m"])
    return places[:limit]
