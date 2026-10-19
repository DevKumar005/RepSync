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
from backend.app.services.replies.generator import generate_reply_draft


def get_collector(platform_key: str, display_name: str):
    """
    Runtime Ingestion Bridge:
    - If MOCK_TINYFISH=1 on Render/locally (or API key is missing):
      Routes to mock_collector.py (since Dev's collector.py has no mock implementation).
    - If MOCK_TINYFISH=0 and TINYFISH_API_KEY is provided:
      Routes to Dev's live collector.py on main.
    """
    mock_env = os.getenv("MOCK_TINYFISH", "1").lower().strip()
    api_key = os.getenv("TINYFISH_API_KEY", "")

    # Live Mode
    if mock_env in {"0", "false", "no"} and api_key and "your-key-here" not in api_key:
        try:
            from backend.app.services.ingestion.collector import get_collector as get_live_collector
            return get_live_collector(platform_key, display_name)
        except Exception as e:
            print(f"Notice: Live collector unavailable ({e}), falling back to mock_collector.")
            from backend.app.services.ingestion.mock_collector import get_mock_collector
            return get_mock_collector(platform_key, display_name)

    # Mock Mode (Render MOCK_TINYFISH=1 or local dev/testing)
    from backend.app.services.ingestion.mock_collector import get_mock_collector
    return get_mock_collector(platform_key, display_name)


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
    broadcaster.clear_buffer(outlet_id)
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
                        input_dict = tf.input if isinstance(tf.input, dict) else {"raw": str(tf.input or "")}
                        call_row = TinyFishCall(
                            outlet_id=outlet_id,
                            platform=tf.platform or p.key,
                            endpoint=tf.endpoint,
                            input=input_dict,
                            status=tf.status or "success",
                            duration_ms=tf.duration_ms or 0,
                            items_returned=tf.items_returned or 0,
                            steps_used=tf.steps_used or 0,
                            cached=bool(tf.cached),
                        )
                        session.add(call_row)

                    # Persist Reviews with Deduplication (M3-MP-6)
                    new_reviews_count = 0
                    for rev_in in result.reviews:
                        # Normalize posted_at if string or datetime
                        if isinstance(rev_in.posted_at, str):
                            try:
                                posted_dt = datetime.fromisoformat(rev_in.posted_at.replace("Z", "+00:00"))
                            except Exception:
                                posted_dt = datetime.now(timezone.utc)
                        elif isinstance(rev_in.posted_at, datetime):
                            posted_dt = rev_in.posted_at
                        else:
                            posted_dt = datetime.now(timezone.utc)

                        date_str = posted_dt.strftime("%Y-%m-%d")
                        author_str = (rev_in.author or "Anonymous").strip()
                        text_str = (rev_in.text or "").strip()
                        dedup_hash = compute_dedup_hash(p.key, author_str, date_str, text_str)

                        existing_rev = session.exec(
                            select(Review).where(
                                Review.outlet_id == outlet_id,
                                Review.hash_for_dedup == dedup_hash,
                            )
                        ).first()

                        if not existing_rev:
                            sentiment = rev_in.sentiment
                            severity = rev_in.severity
                            mismatch = rev_in.rating_text_mismatch
                            if not sentiment:
                                sentiment, severity, mismatch = classify_sentiment(
                                    rev_in.rating or 3.0, text_str
                                )
                            rev = Review(
                                outlet_id=outlet_id,
                                source_id=src.id,
                                platform=p.key,
                                author=author_str,
                                rating=float(rev_in.rating or 3.0),
                                text=text_str,
                                language=rev_in.language or "en",
                                posted_at=posted_dt,
                                url=rev_in.url or src.url,
                                has_owner_reply=bool(rev_in.has_owner_reply or rev_in.owner_reply_text),
                                owner_reply_text=rev_in.owner_reply_text,
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

