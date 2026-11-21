"""City Reputation Map: the outlet and same-category places around it on a real map.

Demo outlets replay the committed sample fixture. Other outlets are located with OpenStreetMap;
only the owner and competitors already scanned carry review numbers, everything else is "not scanned".
"""
import json
import re
import threading
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlmodel import Session, select

from backend.app.features.extras import competitors
from backend.app.features.extras.dates import parse_posted_at
from backend.app.features.extras.velocity import weekly_counts
from backend.app.models.entities import Outlet, Review
from backend.app.services import geo

RADIUS_M = 1500
PLACES_TTL = timedelta(days=7)  # nearby places change slowly; coordinates are kept until the address changes
RETRY_AFTER = timedelta(hours=1)  # after an address could not be found, before trying again
LIVE_NOTE = (
    "Places and locations come from OpenStreetMap, so some businesses may be missing. "
    "Ratings are shown only for your outlet and competitors you have scanned."
)


def _geo_path(outlet_id: str):
    return competitors.RESULT_DIR / f"geo_{outlet_id}.json"


def _load_geo(outlet_id: str) -> Optional[dict]:
    try:
        return json.loads(_geo_path(outlet_id).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _save_geo(outlet_id: str, data: dict) -> None:
    competitors.RESULT_DIR.mkdir(parents=True, exist_ok=True)
    _geo_path(outlet_id).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def _usable(cached: Optional[dict], info: dict) -> Optional[dict]:
    return cached if cached and cached.get("address") == info["address"] else None


def _places_fresh(cached: dict, now: datetime) -> bool:
    at = cached.get("places_at")
    return cached.get("places") is not None and bool(at) and now - datetime.fromisoformat(at) < PLACES_TTL


def locate(info: dict) -> Optional[dict]:
    """Cached {lat, lng, places} for the outlet, refreshing what is stale. None when the address can't be found.

    Slow (OpenStreetMap lookups can take tens of seconds), so the map endpoint runs it in the background.
    """
    now = datetime.now(timezone.utc)
    cached = _usable(_load_geo(info["id"]), info)
    if not cached or cached.get("lat") is None:
        coords = geo.geocode(info["name"], info["address"], info["city"])
        if not coords:
            _save_geo(info["id"], {"address": info["address"], "lat": None, "failed_at": now.isoformat()})
            return None
        cached = {"address": info["address"], "lat": coords[0], "lng": coords[1], "places": None, "places_at": None}
    if not _places_fresh(cached, now):
        places = geo.nearby(cached["lat"], cached["lng"], info["category"], RADIUS_M)
        if places is not None:
            own = _norm(info["name"])
            cached["places"] = [p for p in places if _norm(p["name"]) != own]
            cached["places_at"] = now.isoformat()
    _save_geo(info["id"], cached)
    return cached


_locating: set = set()
_locating_lock = threading.Lock()


def _in_background(fn) -> None:
    threading.Thread(target=fn, daemon=True).start()


def _start_locate(info: dict) -> None:
    with _locating_lock:
        if info["id"] in _locating:
            return
        _locating.add(info["id"])

    def run():
        try:
            locate(info)
        finally:
            with _locating_lock:
                _locating.discard(info["id"])

    _in_background(run)


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def _same_place(a: str, b: str) -> bool:
    a, b = _norm(a), _norm(b)
    return bool(a and b) and (a == b or (min(len(a), len(b)) >= 5 and (a in b or b in a)))


def _owner_stats(session: Session, outlet_id: str) -> dict:
    reviews = session.exec(select(Review).where(Review.outlet_id == outlet_id)).all()
    ratings = [r.rating for r in reviews if r.rating is not None]
    now = datetime.now(timezone.utc)
    last4 = weekly_counts([parse_posted_at(r.posted_at, now) for r in reviews], now, weeks=4)
    return {
        "rating": round(sum(ratings) / len(ratings), 1) if ratings else None,
        "reviews_per_week": round(sum(last4) / 4, 1) if reviews else None,
        "reviews_analysed": len(reviews),
    }


def _sample(outlet: Outlet) -> dict:
    data = json.loads((competitors.DEMO_DIR / "city_map.json").read_text(encoding="utf-8"))
    for o in data["outlets"]:
        if o.get("is_you"):
            o["name"] = f"{outlet.name} (you)"
    return data


def city_map_payload(session: Session, outlet: Outlet) -> dict:
    if outlet.is_demo:
        return _sample(outlet)

    info = competitors._outlet_info(outlet)
    locality = info["address"].split(",")[0].strip() if info["address"] else info["city"]
    base = {"source": "live", "locality": locality, "city": info["city"], "radius_m": RADIUS_M, "note": LIVE_NOTE}
    now = datetime.now(timezone.utc)
    loc = _usable(_load_geo(info["id"]), info)
    if loc and loc.get("lat") is None and now - datetime.fromisoformat(loc["failed_at"]) < RETRY_AFTER:
        return {
            **base, "status": "no_location", "center": None, "outlets": [],
            "note": "We couldn't find this outlet's address on OpenStreetMap. Add a fuller address (street, area) to see the map.",
        }
    if not loc or loc.get("lat") is None or not _places_fresh(loc, now):
        _start_locate(info)
    if not loc or loc.get("lat") is None:
        return {**base, "status": "locating", "center": None, "outlets": []}

    you = {"id": "you", "name": f"{outlet.name} (you)", "lat": loc["lat"], "lng": loc["lng"], "address": info["address"],
           "is_you": True, "scanned": True, "rating_change_60d": None, **_owner_stats(session, outlet.id)}
    scan = competitors.load_result(outlet.id)
    scanned = scan["outlets"][1:] if scan and scan.get("status") == "done" else []

    outlets: List[dict] = [you]
    for p in loc["places"] or []:
        match = next((s for s in scanned if _same_place(s["name"], p["name"])), None)
        outlets.append({
            "id": p["id"], "name": p["name"], "lat": p["lat"], "lng": p["lng"], "address": p["address"],
            "distance_m": p["distance_m"], "scanned": bool(match),
            "rating": match.get("rating") if match else None,
            "rating_change_60d": None, "reviews_per_week": None,
            "reviews_analysed": match["n"] if match else None,
        })
    places_status = "ok" if loc["places"] is not None else "loading" if info["id"] in _locating else "unavailable"
    return {**base, "status": "ok", "center": {"lat": loc["lat"], "lng": loc["lng"]}, "outlets": outlets,
            "places_status": places_status}


def nearby_candidates(info: dict) -> List[dict]:
    """Nearby places as competitor-picker candidates, nearest first. [] when the outlet can't be located."""
    cached = _usable(_load_geo(info["id"]), info)
    loc = cached if cached and cached.get("places") else locate(info)
    return [{"name": p["name"], "url": None, "area": p["address"] or f"{p['distance_m']} m away"}
            for p in (loc or {}).get("places") or []]
