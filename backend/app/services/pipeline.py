import asyncio
import hashlib
import os
from datetime import datetime, timezone
from typing import Dict, Optional

from sqlmodel import Session, select
from backend.app.db import engine
from backend.app.models.entities import (
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
from backend.app.services.analysis.analyzer import analyze_themes_and_fixes, classify_sentiment
from backend.app.services.events import broadcaster
from backend.app.services.ingestion.collector import get_collector
from backend.app.services.replies.generator import generate_reply_draft

# Concurrency & Active Job Registry
_active_jobs: Dict[str, str] = {}  # outlet_id -> job_id
_agent_semaphore = asyncio.Semaphore(2)  # Concurrency limit of 2 for Agent runs (M3-MP-3)


def get_active_job(outlet_id: str) -> Optional[str]:
    return _active_jobs.get(outlet_id)


def compute_dedup_hash(platform: str, author: str, date_str: str, text: str) -> str:
    norm = f"{platform.lower()}:{(author or '').strip().lower()}:{date_str}:{(text or '')[:100].strip().lower()}"
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


async def run_sync_pipeline(outlet_id: str, job_id: str) -> None:
    """
    Executes the full RepSync ingestion, analysis, and drafting pipeline.
    """
    _active_jobs[outlet_id] = job_id
    try:
        with Session(engine) as session:
            outlet = session.get(Outlet, outlet_id)
            if not outlet:
                return

            tone = session.get(ToneProfile, outlet.tone_profile_id) if outlet.tone_profile_id else None

            # --- STAGE 1: Searching ---
            await broadcaster.emit(
                outlet_id=outlet_id,
                event_type="stage",
                status="running",
                message="Stage 1/5: Searching for review sources across platforms...",
                extra={"stage": "searching"},
            )

            # Discover enabled platforms for this outlet category
            all_platforms = session.exec(select(Platform).where(Platform.enabled == True)).all()  # noqa: E712
            target_platforms = [p for p in all_platforms if outlet.category in p.categories]

            # Ensure Source rows exist
            sources_map: Dict[str, Source] = {}
            for p in target_platforms:
                src = session.exec(
                    select(Source).where(Source.outlet_id == outlet_id, Source.platform == p.key)
                ).first()
                if not src:
                    src = Source(
                        outlet_id=outlet_id,
                        platform=p.key,
                        url=f"https://www.{p.key}.com/{outlet.name.lower().replace(' ', '-')}",
                        status="pending",
                    )
                    session.add(src)
                    session.commit()
                    session.refresh(src)
                sources_map[p.key] = src

            await asyncio.sleep(0.3)  # smooth stage progression

            # --- STAGE 2: Collecting ---
            await broadcaster.emit(
                outlet_id=outlet_id,
                event_type="stage",
                status="running",
                message=f"Stage 2/5: Collecting reviews from {len(target_platforms)} platforms...",
                extra={"stage": "collecting"},
            )

            today_midnight = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            calls_today = session.exec(
                select(TinyFishCall).where(
                    TinyFishCall.endpoint == "agent",
                    TinyFishCall.created_at >= today_midnight,
                )
            ).all()
            total_steps_today = sum(c.steps_used for c in calls_today)
            daily_step_budget = int(os.getenv("AGENT_DAILY_STEP_BUDGET", "50"))
            skip_agent_live = total_steps_today >= daily_step_budget

            async def collect_for_platform(p: Platform) -> None:
                src = sources_map[p.key]
                src.status = "running"
                session.add(src)
                session.commit()

                async def platform_emit(event_type: str, source: str, status: str, message: str) -> None:
                    await broadcaster.emit(
                        outlet_id=outlet_id,
                        event_type=event_type,
                        source=source,
                        status=status,
                        message=message,
                    )

                try:
                    collector = get_collector(p.key, p.display_name)
                    async with _agent_semaphore:
                        result = await collector.collect(
                            business_name=outlet.name,
                            city=outlet.city,
                            category=outlet.category,
                            target_url=src.url,
                            emit_callback=platform_emit,
                            skip_agent=skip_agent_live,
                        )


                    # Persist TinyFish calls
                    for tf in result.tinyfish_calls:
                        call_row = TinyFishCall(
                            outlet_id=outlet_id,
                            platform=tf.platform,
                            endpoint=tf.endpoint,
                            input=tf.input or {},
                            status=tf.status,
                            duration_ms=tf.duration_ms,
                            items_returned=tf.items_returned,
                            steps_used=tf.steps_used,
                            cached=tf.cached,
                        )
                        session.add(call_row)

                    # Persist Reviews with Deduplication (M3-MP-6)
                    new_reviews_count = 0
                    for rev_in in result.reviews:
                        date_str = rev_in.posted_at.strftime("%Y-%m-%d") if rev_in.posted_at else "unknown"
                        dedup_hash = compute_dedup_hash(p.key, rev_in.author or "", date_str, rev_in.text or "")

                        existing_rev = session.exec(
                            select(Review).where(
                                Review.outlet_id == outlet_id,
                                Review.hash_for_dedup == dedup_hash,
                            )
                        ).first()

                        if not existing_rev:
                            sentiment, severity, mismatch = classify_sentiment(
                                rev_in.rating or 3.0, rev_in.text or ""
                            )
                            rev = Review(
                                outlet_id=outlet_id,
                                source_id=src.id,
                                platform=p.key,
                                author=rev_in.author,
                                rating=rev_in.rating,
                                text=rev_in.text,
                                language=rev_in.language,
                                posted_at=rev_in.posted_at or datetime.now(timezone.utc),
                                url=rev_in.url,
                                has_owner_reply=rev_in.has_owner_reply,
                                sentiment=sentiment,
                                severity=severity,
                                rating_text_mismatch=mismatch,
                                hash_for_dedup=dedup_hash,
                            )
                            session.add(rev)
                            new_reviews_count += 1

                    src.status = result.status
                    src.review_count = src.review_count + new_reviews_count
                    src.agent_steps_used += result.agent_steps_used
                    src.last_synced_at = datetime.now(timezone.utc)
                    session.add(src)
                    session.commit()

                except Exception as err:
                    print(f"Error collecting from {p.key}: {err}")
                    src.status = "failed"
                    src.error = str(err)
                    session.add(src)
                    session.commit()
                    await broadcaster.emit(
                        outlet_id=outlet_id,
                        event_type="source_status",
                        source=p.key,
                        status="failed",
                        message=f"{p.display_name} collection failed: {err}",
                    )

            # Run all platform collectors concurrently
            await asyncio.gather(*[collect_for_platform(p) for p in target_platforms])

            # --- STAGE 3: Normalising ---
            await broadcaster.emit(
                outlet_id=outlet_id,
                event_type="stage",
                status="running",
                message="Stage 3/5: Normalising reviews, detecting languages and mismatches...",
                extra={"stage": "normalising"},
            )
            await asyncio.sleep(0.3)

            # --- STAGE 4: Analysing (Themes & Fixes) ---
            await broadcaster.emit(
                outlet_id=outlet_id,
                event_type="stage",
                status="running",
                message="Stage 4/5: Analysing sentiment, clustering themes, and generating top fixes...",
                extra={"stage": "analysing"},
            )

            all_reviews = session.exec(select(Review).where(Review.outlet_id == outlet_id)).all()
            themes_data, fixes_data = analyze_themes_and_fixes(all_reviews, outlet.category)

            # Persist Themes
            for td in themes_data:
                existing_th = session.exec(
                    select(Theme).where(Theme.outlet_id == outlet_id, Theme.label == td["label"])
                ).first()
                if not existing_th:
                    th = Theme(
                        outlet_id=outlet_id,
                        label=td["label"],
                        sentiment=td["sentiment"],
                        description=td["description"],
                    )
                    session.add(th)
                    session.commit()
                    session.refresh(th)
                    for r_id in td.get("review_ids", []):
                        rt = ReviewTheme(review_id=r_id, theme_id=th.id)
                        session.add(rt)
                    session.commit()

            # Persist Top Fixes
            for fd in fixes_data:
                existing_fix = session.exec(
                    select(FixSuggestion).where(
                        FixSuggestion.outlet_id == outlet_id,
                        FixSuggestion.rank == fd["rank"],
                    )
                ).first()
                if not existing_fix:
                    fix = FixSuggestion(
                        outlet_id=outlet_id,
                        rank=fd["rank"],
                        title=fd["title"],
                        rationale=fd["rationale"],
                        evidence_count=fd["evidence_count"],
                    )
                    session.add(fix)
            session.commit()

            # --- STAGE 5: Drafting ---
            await broadcaster.emit(
                outlet_id=outlet_id,
                event_type="stage",
                status="running",
                message="Stage 5/5: Drafting AI replies for negative customer reviews with safety guardrails...",
                extra={"stage": "drafting"},
            )

            negative_reviews = [r for r in all_reviews if r.sentiment == "negative" and not r.has_owner_reply]
            for nr in negative_reviews:
                existing_draft = session.exec(
                    select(ReplyDraft).where(ReplyDraft.review_id == nr.id)
                ).first()
                if not existing_draft:
                    reply_text, guardrails = generate_reply_draft(nr, tone)
                    draft = ReplyDraft(
                        review_id=nr.id,
                        text=reply_text,
                        status="draft",
                        version=1,
                        prompt_version="v2",
                        guardrail_flags=guardrails,
                    )
                    session.add(draft)
            session.commit()

            # --- COMPLETE: Done ---
            await broadcaster.emit(
                outlet_id=outlet_id,
                event_type="done",
                status="success",
                message="Sync pipeline completed successfully! Dashboard updated.",
                extra={"stage": "done"},
            )

    except Exception as exc:
        print(f"Sync pipeline critical exception: {exc}")
        await broadcaster.emit(
            outlet_id=outlet_id,
            event_type="done",
            status="failed",
            message=f"Sync pipeline encountered an error: {exc}",
            extra={"stage": "failed"},
        )
    finally:
        _active_jobs.pop(outlet_id, None)


# Bridge alias for M1 ingestion contract
stream_outlet_sync = run_sync_pipeline

