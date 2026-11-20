import logging
import threading
import time
from typing import List
from urllib.parse import quote_plus

import httpx

logger = logging.getLogger(__name__)

# OpenStreetMap Nominatim: free, no key. Usage policy requires an identifying
# User-Agent and at most 1 request per second.
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "RepSync/1.0 (+https://github.com/DevKumar005/RepSync)"
# Skip bus stops, roads and localities that merely share the business name
BUSINESS_CATEGORIES = {"amenity", "shop", "healthcare", "office", "craft", "tourism", "leisure"}

_throttle_lock = threading.Lock()
_last_call = 0.0


def _wait_for_slot() -> None:
    global _last_call
    with _throttle_lock:
        delay = 1.0 - (time.monotonic() - _last_call)
        if delay > 0:
            time.sleep(delay)
        _last_call = time.monotonic()


def search_places(name: str, city: str, category: str, limit: int = 10) -> List[dict]:
    """Business branches matching name in city. Returns [] when the lookup fails."""
    _wait_for_slot()
    try:
        resp = httpx.get(
            NOMINATIM_URL,
            params={"q": f"{name}, {city}", "format": "jsonv2", "limit": 20, "countrycodes": "in"},
            headers={"User-Agent": USER_AGENT},
            timeout=8.0,
        )
        resp.raise_for_status()
    except httpx.HTTPError as e:
        logger.warning("OpenStreetMap search failed: %s", e)
        return []

    places = []
    for p in resp.json():
        if p.get("category") not in BUSINESS_CATEGORIES:
            continue
        place_name = p.get("name") or name
        display = p.get("display_name", "")
        address = display[len(place_name) + 2:] if display.startswith(f"{place_name}, ") else display
        places.append({
            "place_id": f"osm-{p.get('osm_type', 'x')}-{p.get('osm_id')}",
            "name": place_name,
            "address": address,
            # Name + full address pins Google Maps to this exact branch for review collection
            "maps_url": f"https://www.google.com/maps/search/?api=1&query={quote_plus(f'{place_name}, {address}')}",
        })
        if len(places) >= limit:
            break
    return places
