from typing import Callable, Optional
from urllib.parse import quote_plus, urlparse

from app.tinyfish.client import TinyFishService
from app.services.ingestion.extractor import extract_reviews_from_markdown
from app.services.ingestion.schemas import (
    CandidatePlatformUrl,
    CollectionResult,
    NormalizedReview,
    SourceSyncStatus,
    TinyFishCallLog,
    compute_dedup_hash,
)

# Category -> Primary Platforms & Domain Allowlists (Section 4.1 & 4.5)
CATEGORY_PLATFORMS = {
    "restaurant": [
        ("Zomato", "zomato.com", "{name} {city} zomato reviews"),
        ("EazyDiner", "eazydiner.com", "{name} {city} eazydiner reviews"),
    ],
    "clinic": [
        ("Practo", "practo.com", "{name} {city} practo clinic stories reviews"),
        ("Lybrate", "lybrate.com", "{name} {city} lybrate reviews"),
    ],
    "salon": [
        ("JustDial", "justdial.com", "{name} {city} salon justdial"),
        ("EazyDiner", "eazydiner.com", "{name} {city} reviews"),
    ],
}

ESCALATION_MIN_REVIEWS = 6  # Escalate to Agent if Fetch yields fewer than 6 reviews
MAX_REVIEWS_PER_PLATFORM = 50  # Section 4.2: Cap 50 reviews per platform for the demo


def _matches_domain(url: str, allowed_domain: str) -> bool:
    try:
        host = urlparse(url).netloc.lower()
        return allowed_domain.lower() in host
    except Exception:
        return False


def discover_outlet_platforms(
    name: str,
    city: str,
    category: str,
    tf_service: Optional[TinyFishService] = None,
    on_log: Optional[Callable[[TinyFishCallLog], None]] = None,
) -> tuple[list[CandidatePlatformUrl], list[TinyFishCallLog]]:
    """
    FR-1.1 / FR-1.2 / FR-2.1: Uses TinyFish Search (free) + domain allowlist
    to find candidate listing URLs across at least 2 platforms per category.
    """
    tf = tf_service or TinyFishService()
    cat_key = category.strip().lower()
    platform_configs = CATEGORY_PLATFORMS.get(cat_key, CATEGORY_PLATFORMS["restaurant"])

    candidates: list[CandidatePlatformUrl] = []
    call_logs: list[TinyFishCallLog] = []

    for platform_name, allowed_domain, query_template in platform_configs:
        if platform_name == "Google Maps":
            maps_query = quote_plus(f"{name} {city}")
            maps_url = f"https://www.google.com/maps/search/{maps_query}"
            candidates.append(
                CandidatePlatformUrl(
                    platform="Google Maps",
                    url=maps_url,
                    title=f"{name} ({city}) - Google Maps Reviews",
                    snippet="Direct Google Maps place & customer reviews lookup",
                )
            )
            continue

        query = query_template.format(name=name, city=city)
        results, log = tf.search(query=query, on_log=on_log)
        call_logs.append(log)

        for item in results:
            url = item.get("url") or item.get("link") or ""
            if _matches_domain(url, allowed_domain):
                # Prefer /reviews on Zomato if it matched the main restaurant page
                if platform_name == "Zomato" and "/reviews" not in url and "/ncr/" in url:
                    url = url.rstrip("/") + "/reviews"
                candidates.append(
                    CandidatePlatformUrl(
                        platform=platform_name,
                        url=url,
                        title=item.get("title", ""),
                        snippet=item.get("description") or item.get("snippet") or "",
                    )
                )
                break  # one URL per platform

    return candidates, call_logs


def _normalize_and_dedup(
    raw_reviews: list[dict],
    platform: str,
    seen_hashes: set[str],
) -> list[NormalizedReview]:
    """
    FR-2.4 / FR-2.5: Normalises extracted reviews into the unified Review schema,
    flags owner replies, and deduplicates across runs using compute_dedup_hash.
    """
    normalized: list[NormalizedReview] = []
    for raw in raw_reviews:
        text = (raw.get("text") or "").strip()
        if not text:
            continue
        author = (raw.get("author") or "Anonymous").strip()
        try:
            rating = float(raw.get("rating") or 3.0)
            rating = max(1.0, min(5.0, rating))
        except (ValueError, TypeError):
            rating = 3.0

        posted_at = (raw.get("posted_at") or "Recently").strip()
        owner_reply = raw.get("owner_reply_text")
        if owner_reply:
            owner_reply = str(owner_reply).strip()
        has_reply = bool(owner_reply) or bool(raw.get("has_owner_reply", False))

        d_hash = compute_dedup_hash(platform, author, rating, text)
        if d_hash in seen_hashes:
            continue
        seen_hashes.add(d_hash)

        normalized.append(
            NormalizedReview(
                platform=platform,
                external_id=d_hash[:16],
                author=author,
                rating=rating,
                text=text,
                posted_at=posted_at,
                owner_reply_text=owner_reply,
                has_owner_reply=has_reply,
                dedup_hash=d_hash,
            )
        )
        if len(normalized) >= MAX_REVIEWS_PER_PLATFORM:
            break
    return normalized


def collect(
    outlet_name: str,
    city: str,
    category: str,
    platform_urls: Optional[list[CandidatePlatformUrl]] = None,
    use_cache: bool = True,
    on_log: Optional[Callable[[TinyFishCallLog], None]] = None,
    on_step: Optional[Callable[[int, str], None]] = None,
) -> CollectionResult:
    """
    Main M1 Ingestion Pipeline (Section 4.1 & 4.2):
    1. Search (if platform_urls not already provided)
    2. Fetch (Free) -> Gemini Markdown Extraction (skipped for JS-only Google Maps canvas)
    3. Smart Escalation -> TinyFish Agent (only if Fetch blocked or < ESCALATION_MIN_REVIEWS)
    4. Normalise, Deduplicate, and Log every TinyFish call
    """
    tf = TinyFishService()
    all_logs: list[TinyFishCallLog] = []
    all_reviews: list[NormalizedReview] = []
    source_statuses: list[SourceSyncStatus] = []
    seen_hashes: set[str] = set()

    def _record_log(log: TinyFishCallLog):
        all_logs.append(log)
        if on_log:
            on_log(log)

    # 1. Discover URLs if not passed in
    if not platform_urls:
        platform_urls, _ = discover_outlet_platforms(
            name=outlet_name,
            city=city,
            category=category,
            tf_service=tf,
            on_log=_record_log,
        )

    # 2. Process each platform independently (NFR-2: 1 failed source never crashes the run)
    for target in platform_urls:
        platform = target.platform
        url = target.url
        raw_collected: list[dict] = []

        try:
            # Step 2a: Try FREE TinyFish Fetch first (except Google Maps which is JS-only canvas)
            if platform != "Google Maps":
                markdown, _ = tf.fetch(url=url, use_cache=use_cache, on_log=_record_log)
                if markdown:
                    extracted = extract_reviews_from_markdown(markdown, platform=platform)
                    raw_collected.extend(extracted)

            # Step 2b: Smart Escalation Rule (Section 4.1 & 4.2)
            # Escalate to Web Agent ONLY if Fetch failed/blocked or returned < ESCALATION_MIN_REVIEWS
            if len(raw_collected) < ESCALATION_MIN_REVIEWS:
                agent_reviews, _ = tf.run_agent(
                    url=url,
                    platform=platform,
                    max_reviews=10,
                    use_cache=use_cache,
                    on_log=_record_log,
                    on_step=on_step,
                )
                raw_collected.extend(agent_reviews)

            # Step 2c: Normalise & Deduplicate
            platform_reviews = _normalize_and_dedup(raw_collected, platform, seen_hashes)
            all_reviews.extend(platform_reviews)

            status_val = (
                "ok"
                if len(platform_reviews) >= 5
                else ("partial" if platform_reviews else "failed")
            )
            source_statuses.append(
                SourceSyncStatus(
                    platform=platform,
                    listing_url=url,
                    status=status_val,
                    reviews_collected=len(platform_reviews),
                )
            )
        except Exception as e:
            # Per-source failure isolation (FR-2.6 / NFR-2)
            source_statuses.append(
                SourceSyncStatus(
                    platform=platform,
                    listing_url=url,
                    status="failed",
                    reviews_collected=0,
                    error_reason=str(e),
                )
            )

    total_steps = sum(log.steps_used or 0 for log in all_logs)
    return CollectionResult(
        outlet_name=outlet_name,
        city=city,
        category=category,
        sources=source_statuses,
        reviews=all_reviews,
        tinyfish_calls=all_logs,
        total_steps_used=total_steps,
    )