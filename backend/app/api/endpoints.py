import uuid
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from sse_starlette.sse import EventSourceResponse
from sqlmodel import Session, col, func, select
from backend.app.auth import create_access_token, get_current_user, hash_password, verify_password
from backend.app.db import get_session
from backend.app.limiter import limiter

from backend.app.models.entities import (
    AppUser,
    FixSuggestion,
    Outlet,
    Platform,
    ReplyDraft,
    Review,
    ReviewTheme,
    Source,
    Theme,
    TinyFishCall,
    ToneProfile,
)
from backend.app.models.schemas import (
    AuthLoginRequest,
    AuthSignupRequest,
    DraftRegenerateRequest,
    DraftStatusUpdate,
    FixSuggestionRead,
    OutletCandidate,
    OutletCreate,
    OutletRead,
    OutletSearchRequest,
    PlatformRead,
    PlatformSummary,
    ReplyDraftRead,
    ReviewRead,
    SourceRead,
    SummaryResponse,
    SyncResponse,
    ThemeRead,
    TinyFishCallRead,
    TokenResponse,
    ToneProfileRead,
    ToneProfileUpdate,
)
from backend.app.services.approval import validate_draft_transition
from backend.app.services.events import event_generator
from backend.app.services.pipeline import get_active_job, run_sync_pipeline
from backend.app.services.replies.generator import generate_reply_draft

router = APIRouter()


# --- Health Endpoints (SRS 4.1, M3-DEP-3) ---

@router.get("/health")
def health_check():
    """Cheap health ping without DB connection (for uptime monitor)."""
    return {"status": "ok", "service": "repsync-api"}


@router.get("/health/db")
def health_db_check(session: Session = Depends(get_session)):
    """Keep-alive ping that touches Supabase/database daily to prevent pausing."""
    platform_count = session.exec(select(func.count(col(Platform.key)))).one()
    return {"status": "ok", "database": "connected", "platforms_count": platform_count}


# --- Auth Endpoints (M3-SEC-1, M3-SEC-2) ---

@router.post("/api/auth/signup", response_model=TokenResponse)
def signup(req: AuthSignupRequest, session: Session = Depends(get_session)):
    existing = session.exec(select(AppUser).where(AppUser.email == req.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = AppUser(
        name=req.name,
        email=req.email,
        password_hash=hash_password(req.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    token = create_access_token({"sub": user.id, "email": user.email})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        name=user.name,
    )


@router.post("/api/auth/login", response_model=TokenResponse)
def login(req: AuthLoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(AppUser).where(AppUser.email == req.email)).first()
    if not user or not user.password_hash or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": user.id, "email": user.email})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        name=user.name,
    )


@router.post("/api/auth/demo", response_model=TokenResponse)
def login_demo(session: Session = Depends(get_session)):
    """Instant login as demo user."""
    user = session.exec(select(AppUser).where(AppUser.email == "demo@repsync.local")).first()
    if not user:
        user = AppUser(name="Demo Owner", email="demo@repsync.local")
        session.add(user)
        session.commit()
        session.refresh(user)

    token = create_access_token({"sub": user.id, "email": user.email})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        name=user.name,
    )


# --- Platform Registry (M3-MP-1, M3-MP-9) ---

@router.get("/api/platforms", response_model=List[PlatformRead])
def get_platforms(session: Session = Depends(get_session)):
    """Returns platform registry for UI filters and platform toggling."""
    platforms = session.exec(select(Platform)).all()
    return [
        PlatformRead(
            key=p.key,
            display_name=p.display_name,
            enabled=p.enabled,
            categories=p.categories,
            review_cap=p.review_cap,
        )
        for p in platforms
    ]


# --- Outlet Discovery & Creation (FR-1, M3-DB-2/4) ---

@router.post("/api/outlets/search", response_model=List[OutletCandidate])
@limiter.limit("30/minute")
def search_outlet_candidates(request: Request, req: OutletSearchRequest):

    """M1 Search candidates for business across platforms."""
    slug = req.name.lower().replace(" ", "-")
    return [
        OutletCandidate(
            name=req.name,
            city=req.city,
            category=req.category,
            address=f"Central Market, {req.city}",
            urls={
                "google_maps": f"https://www.google.com/maps/search/{slug}+{req.city}",
                "zomato": f"https://www.zomato.com/{req.city.lower()}/{slug}",
                "tripadvisor": f"https://www.tripadvisor.com/{slug}-{req.city.lower()}",
            },
        )
    ]


@router.post("/api/outlets", response_model=OutletRead)
def create_outlet(
    req: OutletCreate,
    current_user: AppUser = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Creates a new outlet and initializes Source rows for all enabled platforms."""
    tone = ToneProfile(user_id=current_user.id, style="warm")
    session.add(tone)
    session.commit()
    session.refresh(tone)

    outlet = Outlet(
        user_id=current_user.id,
        name=req.name,
        category=req.category,
        city=req.city,
        address=req.address,
        tone_profile_id=tone.id,
        is_demo=False,
    )
    session.add(outlet)
    session.commit()
    session.refresh(outlet)

    # Automatically initialize source rows for enabled platforms matching category
    platforms = session.exec(select(Platform).where(Platform.enabled == True)).all()  # noqa: E712
    sources = []
    for p in platforms:
        if outlet.category in p.categories:
            src = Source(
                outlet_id=outlet.id,
                platform=p.key,
                url=f"https://www.{p.key}.com/{outlet.name.lower().replace(' ', '-')}",
                status="pending",
            )
            session.add(src)
            session.commit()
            session.refresh(src)
            sources.append(src)

    return OutletRead(
        id=outlet.id,
        name=outlet.name,
        category=outlet.category,
        city=outlet.city,
        address=outlet.address,
        is_demo=outlet.is_demo,
        created_at=outlet.created_at,
        sources=[SourceRead(**s.model_dump()) for s in sources],
    )


@router.post("/api/outlets/demo/{key}", response_model=OutletRead)
def load_demo_outlet(
    key: str,
    session: Session = Depends(get_session),
):
    """Instant offline demo mode: returns pre-seeded outlet in <3s (M3-DB-4, M3-QA-6)."""
    outlet = None
    if key in {"restaurant", "kake"}:
        outlet = session.exec(select(Outlet).where(Outlet.name == "Kake Da Dhaba")).first()
    elif key in {"clinic", "dental"}:
        outlet = session.exec(select(Outlet).where(Outlet.name == "The White Dental Clinic")).first()
    else:
        outlet = session.exec(select(Outlet).where(Outlet.is_demo == True)).first()  # noqa: E712

    if not outlet:
        raise HTTPException(status_code=404, detail=f"Demo outlet '{key}' not found. Please run seed script.")

    sources = session.exec(select(Source).where(Source.outlet_id == outlet.id)).all()
    return OutletRead(
        id=outlet.id,
        name=outlet.name,
        category=outlet.category,
        city=outlet.city,
        address=outlet.address,
        is_demo=outlet.is_demo,
        created_at=outlet.created_at,
        sources=[SourceRead(**s.model_dump()) for s in sources],
    )


@router.get("/api/outlets/{id}", response_model=OutletRead)
def get_outlet(id: str, session: Session = Depends(get_session)):
    outlet = session.get(Outlet, id)
    if not outlet:
        raise HTTPException(status_code=404, detail="Outlet not found")
    sources = session.exec(select(Source).where(Source.outlet_id == outlet.id)).all()
    return OutletRead(
        id=outlet.id,
        name=outlet.name,
        category=outlet.category,
        city=outlet.city,
        address=outlet.address,
        is_demo=outlet.is_demo,
        created_at=outlet.created_at,
        sources=[SourceRead(**s.model_dump()) for s in sources],
    )


@router.delete("/api/outlets/{id}")
def delete_outlet(
    id: str,
    current_user: AppUser = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Cascade deletes outlet and all associated reviews, themes, drafts, and sources (NFR-5, M3-SEC-7)."""
    outlet = session.get(Outlet, id)
    if not outlet:
        raise HTTPException(status_code=404, detail="Outlet not found")

    if outlet.user_id and outlet.user_id != current_user.id and not outlet.is_demo:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this outlet")


    # Explicit cascade cleanup across SQLite and Postgres
    reviews = session.exec(select(Review).where(Review.outlet_id == id)).all()
    for r in reviews:
        drafts = session.exec(select(ReplyDraft).where(ReplyDraft.review_id == r.id)).all()
        for d in drafts:
            session.delete(d)
        session.delete(r)

    themes = session.exec(select(Theme).where(Theme.outlet_id == id)).all()
    for t in themes:
        session.delete(t)

    fixes = session.exec(select(FixSuggestion).where(FixSuggestion.outlet_id == id)).all()
    for f in fixes:
        session.delete(f)

    sources = session.exec(select(Source).where(Source.outlet_id == id)).all()
    for s in sources:
        session.delete(s)

    calls = session.exec(select(TinyFishCall).where(TinyFishCall.outlet_id == id)).all()
    for c in calls:
        session.delete(c)

    session.delete(outlet)
    session.commit()
    return {"status": "success", "message": f"Outlet {id} and all related data deleted successfully"}



# --- Sync & Real-Time SSE Stream (FR-2, FR-2.6, M3-PIPE-1) ---

@router.post("/api/outlets/{id}/sync", response_model=SyncResponse)
@limiter.limit("10/minute")
async def trigger_sync(
    request: Request,
    id: str,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):

    outlet = session.get(Outlet, id)
    if not outlet:
        raise HTTPException(status_code=404, detail="Outlet not found")

    # M3-API-5: Prevent concurrent syncs for the same outlet
    active_job = get_active_job(id)
    if active_job:
        return SyncResponse(
            job_id=active_job,
            outlet_id=id,
            status="running",
            message="A sync job is already in progress for this outlet",
        )

    job_id = str(uuid.uuid4())
    background_tasks.add_task(run_sync_pipeline, outlet_id=id, job_id=job_id)

    return SyncResponse(
        job_id=job_id,
        outlet_id=id,
        status="started",
        message="Review sync pipeline started in background",
    )


@router.get("/api/outlets/{id}/sync/stream")
async def sync_stream(id: str, session: Session = Depends(get_session)):
    """Server-Sent Events stream for stage, source status, and TinyFish call events."""
    outlet = session.get(Outlet, id)
    if not outlet:
        raise HTTPException(status_code=404, detail="Outlet not found")

    return EventSourceResponse(event_generator(id))


# --- Reviews, Sources & Filters (FR-2.5, FR-6, M3-MP-7) ---

@router.get("/api/outlets/{id}/sources", response_model=List[SourceRead])
def get_outlet_sources(id: str, session: Session = Depends(get_session)):
    sources = session.exec(select(Source).where(Source.outlet_id == id)).all()
    return [SourceRead(**s.model_dump()) for s in sources]


@router.get("/api/outlets/{id}/reviews", response_model=List[ReviewRead])
def get_reviews(
    id: str,
    platform: Optional[str] = Query(None, description="Comma-separated platforms"),
    rating: Optional[float] = Query(None, description="Minimum rating"),
    sentiment: Optional[str] = Query(None),
    has_owner_reply: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    query = select(Review).where(Review.outlet_id == id)

    if platform:
        platforms = [p.strip() for p in platform.split(",") if p.strip()]
        if platforms:
            query = query.where(col(Review.platform).in_(platforms))

    if rating is not None:
        query = query.where(Review.rating >= rating)

    if sentiment:
        query = query.where(Review.sentiment == sentiment)

    if has_owner_reply is not None:
        query = query.where(Review.has_owner_reply == has_owner_reply)

    query = query.order_by(col(Review.posted_at).desc()).offset(offset).limit(limit)
    reviews = session.exec(query).all()

    # Attach drafts if existing
    review_reads = []
    for r in reviews:
        draft = session.exec(select(ReplyDraft).where(ReplyDraft.review_id == r.id)).first()
        draft_read = ReplyDraftRead(**draft.model_dump()) if draft else None
        r_dict = r.model_dump()
        r_dict["draft"] = draft_read
        review_reads.append(ReviewRead(**r_dict))

    return review_reads


# --- Themes & Fixes (FR-3, FR-4) ---

@router.get("/api/outlets/{id}/themes", response_model=List[ThemeRead])
def get_themes(id: str, session: Session = Depends(get_session)):
    themes = session.exec(select(Theme).where(Theme.outlet_id == id)).all()
    total_reviews = session.exec(
        select(func.count(col(Review.id))).where(Review.outlet_id == id)
    ).one() or 1

    theme_reads = []
    for th in themes:
        count = session.exec(
            select(func.count(col(ReviewTheme.review_id))).where(ReviewTheme.theme_id == th.id)
        ).one()
        percentage = round((count / total_reviews) * 100, 1)
        theme_reads.append(
            ThemeRead(
                id=th.id,
                outlet_id=th.outlet_id,
                label=th.label,
                description=th.description,
                sentiment=th.sentiment,
                review_count=count,
                percentage=percentage,
            )
        )
    return theme_reads


@router.get("/api/outlets/{id}/fixes", response_model=List[FixSuggestionRead])
def get_fixes(id: str, session: Session = Depends(get_session)):
    fixes = session.exec(
        select(FixSuggestion).where(FixSuggestion.outlet_id == id).order_by(FixSuggestion.rank)
    ).all()
    return [FixSuggestionRead(**f.model_dump()) for f in fixes]


# --- Summary & Analytics (FR-6, M3-MP-8) ---

@router.get("/api/outlets/{id}/summary", response_model=SummaryResponse)
def get_summary(id: str, session: Session = Depends(get_session)):
    reviews = session.exec(select(Review).where(Review.outlet_id == id)).all()
    total = len(reviews)
    if total == 0:
        return SummaryResponse(
            total_reviews=0,
            average_rating=0.0,
            percent_negative=0.0,
            unanswered_negatives=0,
            per_platform={},
        )

    avg_rating = round(sum(r.rating or 0.0 for r in reviews) / total, 2)
    negatives = [r for r in reviews if r.sentiment == "negative"]
    pct_negative = round((len(negatives) / total) * 100, 1)
    unanswered_neg = len([r for r in negatives if not r.has_owner_reply])

    # Per-platform breakdown (M3-MP-8)
    per_platform: dict[str, PlatformSummary] = {}
    platforms = set(r.platform for r in reviews)
    for p in platforms:
        p_revs = [r for r in reviews if r.platform == p]
        p_total = len(p_revs)
        p_avg = round(sum(r.rating or 0.0 for r in p_revs) / p_total, 2) if p_total else 0.0
        p_neg = len([r for r in p_revs if r.sentiment == "negative"])
        p_pct_neg = round((p_neg / p_total) * 100, 1) if p_total else 0.0
        per_platform[p] = PlatformSummary(
            review_count=p_total,
            average_rating=p_avg,
            percent_negative=p_pct_neg,
        )

    return SummaryResponse(
        total_reviews=total,
        average_rating=avg_rating,
        percent_negative=pct_negative,
        unanswered_negatives=unanswered_neg,
        per_platform=per_platform,
    )


# --- Activity Log / TinyFish Calls (FR-2.6, M3-QA-8) ---

@router.get("/api/outlets/{id}/tinyfish-log", response_model=List[TinyFishCallRead])
def get_tinyfish_log(id: str, session: Session = Depends(get_session)):
    calls = session.exec(
        select(TinyFishCall).where(TinyFishCall.outlet_id == id).order_by(col(TinyFishCall.created_at).desc())
    ).all()
    return [TinyFishCallRead(**c.model_dump()) for c in calls]


# --- Draft Approval State Machine & Regeneration (FR-5, M3-QA-1) ---

@router.post("/api/reviews/{id}/draft", response_model=ReplyDraftRead)
def regenerate_draft(
    id: str,
    req: DraftRegenerateRequest,
    current_user: AppUser = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    review = session.get(Review, id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    outlet = session.get(Outlet, review.outlet_id)
    tone = session.get(ToneProfile, outlet.tone_profile_id) if outlet and outlet.tone_profile_id else None

    draft = session.exec(select(ReplyDraft).where(ReplyDraft.review_id == id)).first()
    new_text, guardrails = generate_reply_draft(review, tone, req.instruction, previous=draft.text if draft else None)


    if not draft:
        draft = ReplyDraft(
            review_id=id,
            text=new_text,
            status="draft",
            version=1,
            guardrail_flags=guardrails,
        )
        session.add(draft)
    else:
        # State machine transition: rejected -> draft or reset to draft on regenerate
        draft.text = new_text
        draft.status = "draft"
        draft.version += 1
        draft.guardrail_flags = guardrails
        draft.approved_at = None

    session.commit()
    session.refresh(draft)
    return ReplyDraftRead(**draft.model_dump())


@router.patch("/api/drafts/{id}", response_model=ReplyDraftRead)
def update_draft(
    id: str,
    req: DraftStatusUpdate,
    current_user: AppUser = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Updates draft status or edited text.
    Validates state machine transitions server-side (returns 409 on invalid transition).
    """
    draft = session.get(ReplyDraft, id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    updated_draft = validate_draft_transition(
        session=session,
        draft=draft,
        new_status=req.status,
        new_text=req.text,
        user_id=current_user.id,
    )
    return ReplyDraftRead(**updated_draft.model_dump())


# --- Tone Profile (FR-5.3) ---

@router.put("/api/tone", response_model=ToneProfileRead)
def update_tone_profile(
    req: ToneProfileUpdate,
    current_user: AppUser = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    tone = session.exec(select(ToneProfile).where(ToneProfile.user_id == current_user.id)).first()
    if not tone:
        tone = ToneProfile(user_id=current_user.id)

    tone.style = req.style
    tone.sample_replies = req.sample_replies
    tone.do_not_say = req.do_not_say
    session.add(tone)
    session.commit()
    session.refresh(tone)

    return ToneProfileRead(
        id=tone.id,
        style=tone.style,
        sample_replies=tone.sample_replies,
        do_not_say=tone.do_not_say,
    )
