"""HTTP routes for the extras features. Registered in main.py only when ENABLE_EXTRAS is on."""
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from backend.app.db import get_session
from backend.app.features.extras import competitors, velocity
from backend.app.features.extras.dates import parse_posted_at
from backend.app.limiter import limiter
from backend.app.models.entities import Outlet, Review

router = APIRouter(tags=["extras"])


class CompetitorPick(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    url: Optional[str] = Field(None, max_length=500)


class ScanRequest(BaseModel):
    competitors: List[CompetitorPick] = Field(default_factory=list, max_length=3)


def _outlet_or_404(session: Session, outlet_id: str) -> Outlet:
    outlet = session.get(Outlet, outlet_id)
    if not outlet:
        raise HTTPException(status_code=404, detail="Outlet not found")
    return outlet


# --- Feature 1: Competitor Gap Matrix ---

@router.get("/api/outlets/{id}/competitors/candidates")
async def competitor_candidates(id: str, session: Session = Depends(get_session)):
    info = competitors._outlet_info(_outlet_or_404(session, id))
    return await competitors.discover(info, session)


@router.post("/api/outlets/{id}/competitors/scan")
@limiter.limit("5/minute")
async def competitor_scan(
    request: Request,
    id: str,
    background_tasks: BackgroundTasks,
    req: Optional[ScanRequest] = None,
    session: Session = Depends(get_session),
):
    _outlet_or_404(session, id)
    if competitors.is_running(id):
        return {"status": "running", "message": "A competitor scan is already running"}
    picks = [c.model_dump() for c in (req.competitors if req else [])]
    competitors.mark_running(id)
    background_tasks.add_task(competitors.run_scan, id, picks)
    return {"status": "started", "message": "Competitor scan started"}


@router.get("/api/outlets/{id}/competitors")
def competitor_result(id: str, session: Session = Depends(get_session)):
    info = competitors._outlet_info(_outlet_or_404(session, id))
    if competitors.is_running(id):
        return {"status": "running"}
    result = competitors.load_result(id)
    if result:
        return result
    return {
        "status": "none",
        "live": competitors.live_enabled(info),
        "sample_available": competitors.sample_key(info) is not None,
    }


# --- Feature 3: Review velocity ---

def velocity_payload(session: Session, outlet: Outlet) -> dict:
    now = velocity.utc_now()
    owner_dates = [
        parse_posted_at(r.posted_at, now)
        for r in session.exec(select(Review).where(Review.outlet_id == outlet.id)).all()
    ]
    series = [velocity.build_series("you", outlet.name, owner_dates, now)]
    source = "sample" if outlet.is_demo else "live"
    result = competitors.load_result(outlet.id)
    if result and result.get("status") == "done":
        for o in result["outlets"][1:]:
            dates = [parse_posted_at(d) for d in result.get("dates", {}).get(o["key"], [])]
            series.append(velocity.build_series(o["key"], o["name"], dates, now))
        if result.get("source") == "sample":
            source = "sample"
    return {"weeks": velocity.week_labels(now), "series": series, "source": source, "note": velocity.SAMPLE_NOTE}


@router.get("/api/outlets/{id}/velocity")
def outlet_velocity(id: str, session: Session = Depends(get_session)):
    return velocity_payload(session, _outlet_or_404(session, id))
