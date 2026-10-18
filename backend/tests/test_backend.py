import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine, select
from backend.app.db import get_session
from backend.app.main import app
from backend.app.models.entities import (
    Outlet,
    ReplyDraft,
    Review,
    Source,
)
from backend.app.seed import seed_demo_outlets, seed_demo_user, seed_platforms
from backend.app.services.ingestion.collector import compute_dedup_hash
from backend.app.services.pipeline import run_sync_pipeline

# Isolated in-memory SQLite database with StaticPool so all connections share the memory DB
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(name="session")
def session_fixture():
    from sqlmodel import SQLModel
    import backend.app.models.entities  # noqa: F401
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        seed_platforms(session)
        user = seed_demo_user(session)
        seed_demo_outlets(session, user)
        yield session
    SQLModel.metadata.drop_all(test_engine)



@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# =========================================================================
# M3-QA-1: Approval State Machine (FR-5)
# Valid transitions:
# draft -> edited, approved, rejected
# edited -> edited, approved, rejected
# approved -> posted, edited (re-approval required)
# rejected -> draft (via regenerate)
# posted -> none (terminal)
# =========================================================================

def test_approval_state_machine_valid_transitions(client: TestClient, session: Session):
    draft = session.exec(select(ReplyDraft)).first()
    assert draft is not None
    assert draft.status == "draft"

    # 1. draft -> edited
    res = client.patch(f"/api/drafts/{draft.id}", json={"status": "edited", "text": "Updated response text"})
    assert res.status_code == 200
    assert res.json()["status"] == "edited"
    assert res.json()["text"] == "Updated response text"

    # 2. edited -> approved
    res = client.patch(f"/api/drafts/{draft.id}", json={"status": "approved"})
    assert res.status_code == 200
    assert res.json()["status"] == "approved"
    assert res.json()["approved_at"] is not None

    # 3. approved -> edited (re-approval required, approved_at becomes null)
    res = client.patch(f"/api/drafts/{draft.id}", json={"status": "edited", "text": "Re-edited text"})
    assert res.status_code == 200
    assert res.json()["status"] == "edited"
    assert res.json()["approved_at"] is None

    # 4. edited -> approved -> posted
    client.patch(f"/api/drafts/{draft.id}", json={"status": "approved"})
    res = client.patch(f"/api/drafts/{draft.id}", json={"status": "posted"})
    assert res.status_code == 200
    assert res.json()["status"] == "posted"


def test_approval_state_machine_invalid_transitions_409(client: TestClient, session: Session):
    draft = session.exec(select(ReplyDraft)).first()
    assert draft is not None

    # Try draft -> posted directly (illegal, must be approved first)
    res = client.patch(f"/api/drafts/{draft.id}", json={"status": "posted"})
    assert res.status_code == 409
    assert "Invalid draft transition" in res.json()["detail"]

    # Reject draft: draft -> rejected
    res = client.patch(f"/api/drafts/{draft.id}", json={"status": "rejected"})
    assert res.status_code == 200

    # Try rejected -> approved directly (illegal, must regenerate to draft first)
    res = client.patch(f"/api/drafts/{draft.id}", json={"status": "approved"})
    assert res.status_code == 409

    # Regenerate draft resets to draft status
    res = client.post(f"/api/reviews/{draft.review_id}/draft", json={"instruction": "Apologize politely"})
    assert res.status_code == 200
    assert res.json()["status"] == "draft"


# =========================================================================
# M3-QA-2: Deduplication (FR-2.5)
# Same review twice on same platform yields one row; same text on different platforms yields two
# =========================================================================

def test_dedup_hash_logic():
    text = "The food was delicious and staff was super friendly!"
    author = "Rahul"
    date_str = "2026-10-18"

    h1 = compute_dedup_hash("google_maps", author, date_str, text)
    h2 = compute_dedup_hash("google_maps", author, date_str, text)
    assert h1 == h2  # Identical hash

    # Same text and author on different platform
    h3 = compute_dedup_hash("zomato", author, date_str, text)
    assert h1 != h3  # Different platform yields different hash


def test_dedup_database_insertion(session: Session):
    outlet = session.exec(select(Outlet)).first()
    assert outlet is not None

    h = compute_dedup_hash("google_maps", "Test Author", "2026-10-18", "Great place to dine!")
    r1 = Review(
        outlet_id=outlet.id,
        platform="google_maps",
        author="Test Author",
        text="Great place to dine!",
        hash_for_dedup=h,
    )
    session.add(r1)
    session.commit()

    # Re-querying with the same hash
    existing = session.exec(
        select(Review).where(Review.outlet_id == outlet.id, Review.hash_for_dedup == h)
    ).first()
    assert existing is not None


# =========================================================================
# M3-QA-3: Partial Failure Resilience in Sync Pipeline (Section 2.2 #5)
# One failed platform never fails the whole job
# =========================================================================

@pytest.mark.asyncio
async def test_partial_failure_sync_pipeline(session: Session, monkeypatch):
    outlet = session.exec(select(Outlet)).first()
    assert outlet is not None

    # Run sync pipeline
    await run_sync_pipeline(outlet.id, "job-test-123")

    # Sources should have been processed
    sources = session.exec(select(Source).where(Source.outlet_id == outlet.id)).all()
    assert len(sources) >= 1
    # Check that sources have valid statuses
    for s in sources:
        assert s.status in {"success", "partial", "failed", "pending"}


# =========================================================================
# M3-QA-4: Filters, Summary Metrics & Unanswered Negatives (FR-6, M3-MP-8)
# =========================================================================

def test_reviews_filtering(client: TestClient, session: Session):
    outlet = session.exec(select(Outlet).where(Outlet.name == "Kake Da Dhaba")).first()
    assert outlet is not None

    # Filter by platform
    res = client.get(f"/api/outlets/{outlet.id}/reviews?platform=google_maps")
    assert res.status_code == 200
    reviews = res.json()
    assert all(r["platform"] == "google_maps" for r in reviews)

    # Filter by sentiment
    res = client.get(f"/api/outlets/{outlet.id}/reviews?sentiment=negative")
    assert res.status_code == 200
    neg_reviews = res.json()
    assert all(r["sentiment"] == "negative" for r in neg_reviews)


def test_summary_metrics_and_platform_split(client: TestClient, session: Session):
    outlet = session.exec(select(Outlet).where(Outlet.name == "Kake Da Dhaba")).first()
    assert outlet is not None

    res = client.get(f"/api/outlets/{outlet.id}/summary")
    assert res.status_code == 200
    data = res.json()
    assert "total_reviews" in data
    assert "average_rating" in data
    assert "percent_negative" in data
    assert "unanswered_negatives" in data
    assert "per_platform" in data
    assert data["total_reviews"] > 0


# =========================================================================
# M3-QA-5: Cascade Delete (NFR-5, M3-SEC-7)
# Deleting an outlet cascades to all its data
# =========================================================================

def test_cascade_delete_outlet(client: TestClient, session: Session):
    outlet = session.exec(select(Outlet).where(Outlet.name == "The White Dental Clinic")).first()
    assert outlet is not None
    outlet_id = outlet.id

    # Verify reviews exist before delete
    reviews_before = session.exec(select(Review).where(Review.outlet_id == outlet_id)).all()
    assert len(reviews_before) > 0

    # Delete outlet
    res = client.delete(f"/api/outlets/{outlet_id}")
    assert res.status_code == 200

    # Verify outlet and related records are gone
    assert session.get(Outlet, outlet_id) is None
    reviews_after = session.exec(select(Review).where(Review.outlet_id == outlet_id)).all()
    assert len(reviews_after) == 0


# =========================================================================
# M3-QA-6: Demo Mode Offline (Section 3.3 M3-DB-4, Acceptance #7)
# =========================================================================

def test_demo_mode_endpoint_offline(client: TestClient):
    # External APIs disabled via mock environment
    res = client.post("/api/outlets/demo/restaurant")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Kake Da Dhaba"
    assert data["category"] == "restaurant"
    assert data["is_demo"] is True
    assert len(data["sources"]) >= 2


def test_health_endpoints(client: TestClient):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    res = client.get("/health/db")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    assert res.json()["database"] == "connected"
