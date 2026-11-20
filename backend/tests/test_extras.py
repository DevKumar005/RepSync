import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

import backend.app.models.entities  # noqa: F401
from backend.app.db import get_session
from backend.app.features.extras import advice, competitors
from backend.app.features.extras.dates import parse_posted_at
from backend.app.features.extras.gaps import compute_gap_matrix, top_gaps
from backend.app.features.extras.router import router as extras_router
from backend.app.limiter import limiter
from backend.app.models.entities import Outlet
from backend.app.seed import seed_demo_outlets, seed_demo_user, seed_platforms

NOW = datetime(2026, 11, 20, 12, 0, tzinfo=timezone.utc)


@pytest.fixture(name="engine")
def engine_fixture(monkeypatch, tmp_path):
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(eng)
    with Session(eng) as s:
        seed_platforms(s)
        seed_demo_outlets(s, seed_demo_user(s))
    monkeypatch.setattr(competitors, "engine", eng)
    monkeypatch.setattr(competitors, "RESULT_DIR", tmp_path)
    monkeypatch.setenv("MOCK_LLM", "1")
    monkeypatch.setenv("MOCK_TINYFISH", "1")
    yield eng
    SQLModel.metadata.drop_all(eng)


@pytest.fixture(name="client")
def client_fixture(engine):
    app = FastAPI()
    app.state.limiter = limiter
    app.include_router(extras_router)

    def _session():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = _session
    return TestClient(app)


def _demo_id(engine, name="Kake Da Dhaba") -> str:
    with Session(engine) as s:
        return s.exec(select(Outlet).where(Outlet.name == name)).first().id


# --- relative date parser ---

@pytest.mark.parametrize("text,days", [
    ("10 hours ago", 10 / 24),
    ("6 days ago", 6),
    ("a week ago", 7),
    ("2 weeks ago", 14),
    ("one month ago", 30),
    ("2 months ago", 60),
    ("yesterday", 1),
    ("a year ago", 365),
    ("3 din pehle", 3),
    ("Edited 4 days ago", 4),
])
def test_parse_relative(text, days):
    got = parse_posted_at(text, collected_at=NOW)
    assert got is not None
    assert abs((NOW - got).total_seconds() - days * 86400) < 1


def test_parse_iso_and_absolute():
    assert parse_posted_at("2026-11-01T10:00:00Z", NOW) == datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)
    assert parse_posted_at("2026-11-01", NOW).date().isoformat() == "2026-11-01"
    assert parse_posted_at("12 Oct 2026", NOW).date().isoformat() == "2026-10-12"
    naive = datetime(2026, 11, 2, 9, 0)
    assert parse_posted_at(naive, NOW).tzinfo is not None


def test_parse_garbage_and_fallback_to_now():
    assert parse_posted_at("", NOW) is None
    assert parse_posted_at("sometime last summer", NOW) is None
    assert parse_posted_at(None, NOW) is None
    got = parse_posted_at("3 days ago")  # no collected_at -> relative to now
    assert abs((datetime.now(timezone.utc) - got) - timedelta(days=3)) < timedelta(seconds=5)


# --- gap computation ---

def _outlet(key, n, topic_counts):
    topics = []
    for t, c in topic_counts.items():
        topics += [[t]] * c
    topics += [[]] * (n - len(topics))
    return {"key": key, "name": key.upper(), "topics": topics}


def test_gap_matrix_classifies_threat_opportunity_parity():
    rows = compute_gap_matrix([
        _outlet("you", 10, {"slow service": 4, "hygiene": 1, "food quality": 1}),
        _outlet("A", 20, {"slow service": 1, "hygiene": 6, "food quality": 2}),
        _outlet("B", 20, {"rude staff": 1}),
    ])
    by_theme = {r["theme"]: r for r in rows}
    assert by_theme["slow service"]["status"] == "threat"
    assert by_theme["slow service"]["cells"][0]["rate"] == 40.0
    assert by_theme["slow service"]["versus_key"] == "B"       # B has 0% -> largest gap
    assert by_theme["slow service"]["gap_pp"] == 40.0
    assert by_theme["hygiene"]["status"] == "opportunity"      # A 30% vs you 10%
    assert by_theme["food quality"]["status"] == "parity"      # 10% vs 10%
    assert "rude staff" not in by_theme                        # fewer than 3 mentions overall
    assert [r["status"] for r in rows][:2] == ["threat", "opportunity"]
    assert all(c["n"] in (10, 20) for r in rows for c in r["cells"])


def test_gap_needs_enough_mentions_on_worse_side():
    rows = compute_gap_matrix([
        _outlet("you", 4, {"overpriced": 1}),          # 25% but only one mention
        _outlet("A", 20, {"overpriced": 2}),
    ])
    assert rows[0]["status"] == "parity"


def test_advice_numbers_come_from_code(monkeypatch):
    rows = compute_gap_matrix([
        _outlet("you", 10, {"slow service": 4}),
        _outlet("A", 20, {"slow service": 1}),
    ])
    gaps = top_gaps(rows)
    monkeypatch.setattr(advice, "_llm_tips", lambda g, c: {"slow service": "Cut waits by 50% with 3 extra staff."})
    out = advice.build_advice(gaps, "restaurant", use_llm=True)
    assert out[0]["text"].startswith("Slow service: 40% of your reviews (4 of 10) vs 5% at A (1 of 20).")
    assert "50%" not in out[0]["text"]                     # LLM tip with digits rejected
    monkeypatch.setattr(advice, "_llm_tips", lambda g, c: {"slow service": "Add a floor captain at peak hours."})
    assert advice.build_advice(gaps, "restaurant", use_llm=True)[0]["text"].endswith("Add a floor captain at peak hours.")


def test_mask_quote():
    q = competitors.mask_quote("Call me on 98765 43210 or a@b.com https://x.y " + "x" * 200)
    assert "98765" not in q and "a@b.com" not in q and "https" not in q
    assert len(q) <= 140


# --- sample scan end to end ---

def test_sample_scan_for_demo_outlet(client, engine):
    oid = _demo_id(engine)
    assert client.get(f"/api/outlets/{oid}/competitors").json()["status"] == "none"
    cands = client.get(f"/api/outlets/{oid}/competitors/candidates").json()
    assert cands["source"] == "sample" and len(cands["candidates"]) == 3

    asyncio.run(competitors.run_scan(oid, []))
    res = client.get(f"/api/outlets/{oid}/competitors").json()
    assert res["status"] == "done" and res["source"] == "sample"
    assert [o["key"] for o in res["outlets"]] == ["you", "A", "B", "C"]
    assert res["outlets"][0]["n"] == 5
    slow = next(r for r in res["matrix"] if r["theme"] == "slow service")
    assert slow["status"] == "threat" and slow["cells"][0]["count"] == 2
    assert len(res["advice"]) == 3
    assert all(len(v) == len(res["dates"]["A"]) for v in [res["dates"]["A"]])
    assert "author" not in str(res)


def test_scan_endpoint_and_unknown_outlet(client, engine):
    oid = _demo_id(engine, "The White Dental Clinic")
    assert client.post(f"/api/outlets/{oid}/competitors/scan", json={}).json()["status"] in {"started", "running"}
    assert client.get("/api/outlets/nope/competitors").status_code == 404
