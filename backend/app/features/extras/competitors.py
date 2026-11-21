"""Competitor Gap Matrix ("Ghost Auditor"): discover, collect, analyse and compare competitors.

Live mode (MOCK_TINYFISH=0 with a key, non-demo outlet) uses the existing TinyFish wrappers.
Otherwise a committed sample fixture is replayed, and the result is marked "source": "sample".
"""
import asyncio
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote_plus, unquote

from sqlmodel import Session, select

from backend.app.db import engine
from backend.app.features.extras.advice import build_advice
from backend.app.features.extras.dates import parse_posted_at
from backend.app.features.extras.gaps import compute_gap_matrix, top_gaps
from backend.app.features.extras.topics import analyze_topics
from backend.app.models.entities import Outlet, Review, TinyFishCall
from backend.app.services.events import broadcaster

ROOT_DIR = Path(__file__).resolve().parents[4]
DEMO_DIR = ROOT_DIR / "data" / "demo"
RESULT_DIR = ROOT_DIR / "data" / "cache" / "extras"
MAX_COMPETITORS = 3
MAX_REVIEWS = 50
AGENT_ESCALATE_BELOW = 10
AGENT_MAX_REVIEWS = 10  # the agent's 65s cap discards everything on timeout, so ask for what it can finish
LOW_SAMPLE = 10  # fewer analysed reviews than this gets a "small sample" warning in the UI
DEMO_OUTLETS = {"Kake Da Dhaba": "restaurant", "The White Dental Clinic": "clinic"}
DISCOVERY_QUERIES = {
    "restaurant": "best restaurants near {locality} {city} google maps",
    "clinic": "clinics near {locality} {city} google maps",
    "salon": "salons near {locality} {city} google maps",
}
_LISTICLE = re.compile(r"\b(best|top|\d+|list|near|reviews?|menu|restaurants|clinics|salons|zomato|justdial)\b", re.I)

_jobs: dict = {}  # outlet_id -> "running"


# --- storage -------------------------------------------------------------

def _result_path(outlet_id: str) -> Path:
    return RESULT_DIR / f"competitors_{outlet_id}.json"


def load_result(outlet_id: str) -> Optional[dict]:
    path = _result_path(outlet_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def save_result(outlet_id: str, result: dict) -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    _result_path(outlet_id).write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")


def is_running(outlet_id: str) -> bool:
    return outlet_id in _jobs


def mark_running(outlet_id: str) -> None:
    """Called by the scan endpoint before the background task starts, so polls never see a stale state."""
    _jobs[outlet_id] = "running"


def load_fixture(key: Optional[str]) -> Optional[dict]:
    if not key:
        return None
    path = DEMO_DIR / f"competitors_{key}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


# --- mode selection ------------------------------------------------------

def _outlet_info(outlet: Outlet) -> dict:
    return {
        "id": outlet.id, "name": outlet.name, "category": outlet.category, "city": outlet.city,
        "address": outlet.address or "", "is_demo": outlet.is_demo,
    }


def sample_key(info: dict) -> Optional[str]:
    if info["is_demo"] and info["name"] in DEMO_OUTLETS:
        return DEMO_OUTLETS[info["name"]]
    return info["category"] if (DEMO_DIR / f"competitors_{info['category']}.json").exists() else None


def live_enabled(info: dict) -> bool:
    mock_env = os.getenv("MOCK_TINYFISH", "1").lower().strip()
    api_key = os.getenv("TINYFISH_API_KEY", "")
    return (
        not info["is_demo"]
        and mock_env in {"0", "false", "no"}
        and bool(api_key)
        and "your-key-here" not in api_key
    )


# --- helpers -------------------------------------------------------------

_MASKS = [
    (re.compile(r"\S+@\S+\.\S+"), "[email]"),
    (re.compile(r"\+?\d[\d\s-]{8,}\d"), "[phone]"),
    (re.compile(r"https?://\S+"), "[link]"),
    (re.compile(r"@\w+"), "@[user]"),
]


def mask_quote(text: str, limit: int = 140) -> str:
    out = " ".join((text or "").split())
    for pattern, repl in _MASKS:
        out = pattern.sub(repl, out)
    return out if len(out) <= limit else out[: limit - 1].rstrip() + "…"


def owner_reviews(session: Session, outlet_id: str) -> List[dict]:
    rows = session.exec(select(Review).where(Review.outlet_id == outlet_id)).all()
    return [{"text": r.text or "", "rating": r.rating or 3.0, "posted_at": r.posted_at} for r in rows]


async def _emit(outlet_id: str, event_type: str, message: str, status: str = "running") -> None:
    await broadcaster.emit(
        outlet_id=outlet_id, event_type=event_type, source="competitors", status=status,
        message=message, extra={"feature": "competitors"},
    )


def _avg_rating(reviews: List[dict]) -> Optional[float]:
    """Mean star rating of the collected reviews (not the platform's overall rating)."""
    ratings = [r["rating"] for r in reviews if r.get("rating") is not None]
    return round(sum(ratings) / len(ratings), 1) if ratings else None


def build_result(info: dict, owner: List[dict], competitors: List[dict], source: str, collected_at: datetime) -> dict:
    """Pure aggregation step. Competitor dicts: {key, name, url?, reviews: [{text, rating, posted_at, topics?}]}."""
    owner_topics = analyze_topics(owner) if owner else []
    outlets = [{"key": "you", "name": info["name"], "topics": owner_topics}]
    comp_topics = {}
    for c in competitors:
        reviews = c["reviews"][:MAX_REVIEWS]
        if all("topics" in r for r in reviews):
            topics = [r["topics"] for r in reviews]
        else:
            topics = analyze_topics(reviews)
        comp_topics[c["key"]] = topics
        outlets.append({"key": c["key"], "name": c["name"], "topics": topics})

    matrix = compute_gap_matrix(outlets)
    gaps = top_gaps(matrix)

    quotes = {}
    for g in gaps:
        picked = []
        for c in competitors:
            for r, t in zip(c["reviews"][:MAX_REVIEWS], comp_topics[c["key"]]):
                if g["theme"] in t and len(picked) < 2:
                    picked.append({"outlet_key": c["key"], "text": mask_quote(r["text"])})
        quotes[g["theme"]] = picked

    return {
        "status": "done",
        "source": source,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "collected_at": collected_at.isoformat(),
        "outlets": [
            {"key": "you", "name": info["name"], "n": len(owner_topics), "url": None,
             "low_sample": len(owner_topics) < LOW_SAMPLE},
            *[
                {"key": c["key"], "name": c["name"], "n": len(comp_topics[c["key"]]), "url": c.get("url"),
                 "low_sample": len(comp_topics[c["key"]]) < LOW_SAMPLE, "rating": _avg_rating(c["reviews"][:MAX_REVIEWS])}
                for c in competitors
            ],
        ],
        "matrix": matrix,
        "advice": build_advice(gaps, info["category"]),
        "quotes": quotes,
        # Parsed review dates per competitor, used by the velocity endpoint. No reviewer names stored.
        "dates": {
            c["key"]: [
                d.isoformat() if (d := parse_posted_at(r.get("posted_at"), collected_at)) else None
                for r in c["reviews"][:MAX_REVIEWS]
            ]
            for c in competitors
        },
    }


# --- discovery -----------------------------------------------------------

def _name_from_result(item: dict) -> Optional[str]:
    url = item.get("url") or item.get("link") or ""
    title = (item.get("title") or "").strip()
    if "/maps/place/" in url:
        name = unquote(url.split("/maps/place/")[1].split("/")[0]).replace("+", " ")
    else:
        name = re.split(r"\s[-|–]\s|,|\|", title)[0].strip()
    if not name or len(name) < 3 or len(name) > 60 or _LISTICLE.search(name):
        return None
    return name


async def discover(info: dict, session: Session) -> dict:
    """Up to 6 candidate competitors; the first 3 are pre-selected in the UI."""
    if not live_enabled(info):
        fixture = load_fixture(sample_key(info))
        if not fixture:
            return {"source": "sample", "candidates": [], "message": "No sample competitors for this category."}
        return {
            "source": "sample",
            "candidates": [{"name": c["name"], "url": None, "area": c.get("area")} for c in fixture["competitors"]],
        }

    from backend.app.tinyfish.client import TinyFishService

    locality = info["address"].split(",")[0].strip() if info["address"] else ""
    query = DISCOVERY_QUERIES.get(info["category"], DISCOVERY_QUERIES["restaurant"]).format(
        locality=locality, city=info["city"]
    )
    tf = TinyFishService()
    results, log = await asyncio.to_thread(tf.search, query)
    _log_call(session, info["id"], "search", {"query": query, "purpose": "competitor discovery"}, log)
    await _emit(info["id"], "tinyfish_call", f"TinyFish Search: competitor discovery ({log.items_returned} results)", log.status)

    seen, candidates = set(), []
    own = info["name"].lower()
    for item in results:
        name = _name_from_result(item)
        if not name or own in name.lower() or name.lower() in own or name.lower() in seen:
            continue
        seen.add(name.lower())
        url = item.get("url") or item.get("link")
        candidates.append({"name": name, "url": url if url and "/maps/place/" in url else None, "area": None})

    if len(candidates) < MAX_COMPETITORS:
        # Free fallback: same-category OpenStreetMap places around the outlet, nearest first
        from backend.app.features.extras.city_map import nearby_candidates
        from backend.app.services.places import search_places

        places = await asyncio.to_thread(nearby_candidates, info)
        if not places:
            places = [
                {"name": p["name"], "url": None, "area": p["address"]}
                for p in await asyncio.to_thread(
                    search_places, f"{info['category']}s in {locality}" if locality else f"{info['category']}s",
                    info["city"], info["category"],
                )
            ]
        for p in places:
            if p["name"].lower() in seen or own in p["name"].lower():
                continue
            seen.add(p["name"].lower())
            candidates.append(p)
    return {"source": "live", "candidates": candidates[:6]}


# --- collection ----------------------------------------------------------

def _log_call(session: Session, outlet_id: str, endpoint: str, input_dict: dict, log) -> None:
    session.add(TinyFishCall(
        outlet_id=outlet_id,
        platform="google_maps",
        endpoint=endpoint,
        input=input_dict,
        status=log.status,
        duration_ms=log.duration_ms or 0,
        items_returned=log.items_returned or 0,
        steps_used=log.steps_used or 0,
        cached=bool(log.cached),
    ))
    session.commit()


def _agent_budget_exhausted(session: Session) -> bool:
    if os.getenv("SKIP_AGENT", "0").lower() in {"1", "true", "yes"}:
        return True
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    calls = session.exec(
        select(TinyFishCall).where(
            TinyFishCall.endpoint == "agent", TinyFishCall.created_at >= today, TinyFishCall.cached == False  # noqa: E712
        )
    ).all()
    return sum(c.steps_used for c in calls) >= int(os.getenv("AGENT_DAILY_STEP_BUDGET", "500"))


def _pick_maps_url(results: List[dict], name: str) -> Optional[str]:
    """First Google Maps place link that belongs to this business. Other sites and other places are skipped."""
    words = [w for w in re.findall(r"[a-z0-9]+", name.lower()) if len(w) >= 3 and w != "the"]
    for item in results:
        u = item.get("url") or item.get("link") or ""
        if "/maps/place/" not in u:
            continue
        place = unquote(u.split("/maps/place/")[1].split("/")[0]).replace("+", " ").lower()
        if not words or any(w in place for w in words):
            return u
    return None


def _maps_search_url(name: str, city: str) -> str:
    """Same fallback the owner collector uses: the agent opens the top matching result from here."""
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(f'{name} {city}')}"


async def _collect_live(info: dict, comp: dict, session: Session, tf, skip_agent: bool) -> dict:
    from backend.app.services.ingestion.collector import (
        _agent_escalation_semaphore,
        _extract_reviews_from_search_snippets,
    )
    from backend.app.services.ingestion.extractor import extract_reviews_from_markdown

    oid, name = info["id"], comp["name"]
    url = comp.get("url")
    snippets: List[dict] = []
    if not url:
        query = f"{name} {info['category']} {info['city']} google maps reviews"
        results, log = await asyncio.to_thread(tf.search, query)
        _log_call(session, oid, "search", {"query": query, "competitor": name}, log)
        await _emit(oid, "tinyfish_call", f"TinyFish Search: {name} ({log.items_returned} results)", log.status)
        snippets = _extract_reviews_from_search_snippets(results, platform="google_maps", business_name=name)
        url = _pick_maps_url(results, name) or _maps_search_url(name, info["city"])

    markdown, f_log = await asyncio.to_thread(tf.fetch, url)
    _log_call(session, oid, "fetch", {"url": url, "competitor": name}, f_log)
    raw = await asyncio.to_thread(extract_reviews_from_markdown, markdown, "Google Maps") if markdown else []
    await _emit(oid, "tinyfish_call", f"TinyFish Fetch: {name}, {len(raw)} reviews", f_log.status)

    if not raw and snippets:
        raw.extend(snippets)
        await _emit(oid, "tinyfish_call", f"TinyFish Search: {name}, {len(snippets)} reviews from search snippets", "ok")

    if len(raw) < AGENT_ESCALATE_BELOW and not skip_agent:
        async with _agent_escalation_semaphore:
            agent_reviews, a_log = await asyncio.to_thread(
                tf.run_agent, url=url, platform="Google Maps", max_reviews=AGENT_MAX_REVIEWS
            )
        _log_call(session, oid, "agent", {"url": url, "competitor": name}, a_log)
        await _emit(oid, "tinyfish_call", f"TinyFish Agent: {name}, {len(agent_reviews)} reviews", a_log.status)
        raw.extend(agent_reviews)

    seen, reviews = set(), []
    for r in raw:
        text = (r.get("text") or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        try:
            rating = max(1.0, min(5.0, float(r.get("rating") or 3.0)))
        except (TypeError, ValueError):
            rating = 3.0
        reviews.append({"text": text, "rating": rating, "posted_at": str(r.get("posted_at") or "")})
    return {**comp, "url": url, "reviews": reviews[:MAX_REVIEWS]}


async def run_scan(outlet_id: str, chosen: Optional[List[dict]] = None) -> None:
    _jobs[outlet_id] = "running"
    try:
        with Session(engine) as session:
            outlet = session.get(Outlet, outlet_id)
            if not outlet:
                return
            info = _outlet_info(outlet)
            owner = owner_reviews(session, outlet_id)
            collected_at = datetime.now(timezone.utc)
            await _emit(outlet_id, "stage", "Competitor scan: finding competitors…")

            if live_enabled(info):
                from backend.app.tinyfish.client import TinyFishService

                picks = [c for c in (chosen or []) if c.get("name")][:MAX_COMPETITORS]
                if not picks:
                    picks = (await discover(info, session))["candidates"][:MAX_COMPETITORS]
                tf = TinyFishService()
                skip_agent = _agent_budget_exhausted(session)
                competitors = []
                for key, comp in zip("ABC", picks):
                    await _emit(outlet_id, "stage", f"Competitor scan: collecting reviews for {comp['name']}…")
                    competitors.append(await _collect_live(info, {"key": key, "name": comp["name"], "url": comp.get("url")}, session, tf, skip_agent))
                    await asyncio.sleep(1.0)  # throttle between competitors
                source = "live"
            else:
                fixture = load_fixture(sample_key(info))
                if not fixture:
                    raise RuntimeError("No sample competitor data for this category, and live scanning is off.")
                wanted = {c["name"] for c in (chosen or []) if c.get("name")}
                pool = [c for c in fixture["competitors"] if not wanted or c["name"] in wanted] or fixture["competitors"]
                competitors = []
                for key, comp in zip("ABC", pool[:MAX_COMPETITORS]):
                    await _emit(outlet_id, "stage", f"[Sample] Loading saved reviews for {comp['name']}…")
                    await asyncio.sleep(0.4)
                    await _emit(
                        outlet_id, "tinyfish_call",
                        f"[Sample] {comp['name']}: {len(comp['reviews'])} sample reviews (no live TinyFish call)", "cached",
                    )
                    competitors.append({"key": key, "name": comp["name"], "url": None, "reviews": comp["reviews"]})
                source = "sample"

        await _emit(outlet_id, "stage", "Competitor scan: analysing complaints and computing gaps…")
        result = await asyncio.to_thread(build_result, info, owner, competitors, source, collected_at)
        save_result(outlet_id, result)
        await _emit(outlet_id, "stage", "Competitor scan complete", status="success")
    except Exception as e:
        print(f"Competitor scan failed for {outlet_id}: {e}")
        save_result(outlet_id, {"status": "failed", "error": str(e), "generated_at": datetime.now(timezone.utc).isoformat()})
        await _emit(outlet_id, "stage", f"Competitor scan failed: {e}", status="failed")
    finally:
        _jobs.pop(outlet_id, None)
