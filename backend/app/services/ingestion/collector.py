import asyncio
import hashlib
import os
from datetime import datetime, timezone
from typing import Callable, List, Optional
from urllib.parse import urlparse

try:
    from backend.app.tinyfish.client import TinyFishService
    from backend.app.services.ingestion.extractor import extract_reviews_from_markdown
except ImportError:
    from app.tinyfish.client import TinyFishService
    from app.services.ingestion.extractor import extract_reviews_from_markdown

try:
    from backend.app.models.schemas import CollectionResult, ReviewIn, TinyFishCallIn
except ImportError:
    from app.models.schemas import CollectionResult, ReviewIn, TinyFishCallIn

API_KEY = os.getenv("TINYFISH_API_KEY", "")

PLATFORM_SEARCH_TEMPLATES = {
    "restaurant": {
        "zomato": "{name} {city} zomato reviews",
        "tripadvisor": "{name} {city} tripadvisor restaurant reviews",
        "google_maps": "{name} restaurant {city} google maps reviews",
        "eazydiner": "{name} {city} eazydiner reviews",
        "justdial": "{name} restaurant {city} justdial reviews",
    },
    "clinic": {
        "practo": "{name} {city} practo clinic stories reviews",
        "lybrate": "{name} {city} lybrate reviews",
        "google_maps": "{name} clinic {city} google maps reviews",
        "justdial": "{name} clinic {city} justdial reviews",
    },
    "salon": {
        "google_maps": "{name} salon {city} google maps reviews",
        "justdial": "{name} salon {city} justdial reviews",
    },
}

PLATFORM_DOMAINS = {
    "zomato": "zomato.com",
    "tripadvisor": "tripadvisor.com",
    "eazydiner": "eazydiner.com",
    "practo": "practo.com",
    "lybrate": "lybrate.com",
    "justdial": "justdial.com",
    "google_maps": "google.com",
}

ESCALATION_MIN_REVIEWS = 1


def compute_dedup_hash(platform: str, author: str, date_str: str, text: str) -> str:
    norm = f"{platform.lower()}:{(author or '').strip().lower()}:{date_str}:{(text or '')[:100].strip().lower()}"
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


def _matches_domain(url: str, domain: str) -> bool:
    try:
        return domain.lower() in urlparse(url).netloc.lower()
    except Exception:
        return False


class MultiPlatformCollector:
    """Production TinyFish collector executing Search -> Fetch -> Agent escalation."""

    def __init__(self, platform_key: str, display_name: str) -> None:
        self.platform = platform_key
        self.display_name = display_name
        self.tf = TinyFishService()

    async def collect(
        self,
        business_name: str,
        city: str,
        category: str,
        target_url: Optional[str] = None,
        emit_callback: Optional[Callable] = None,
        skip_agent: bool = False,
    ) -> CollectionResult:
        tinyfish_calls: List[TinyFishCallIn] = []
        raw_reviews: list[dict] = []
        agent_steps_used = 0
        resolved_url = target_url

        if emit_callback:
            await emit_callback(
                event_type="source_status",
                source=self.platform,
                status="running",
                message=f"Starting review collection for {self.display_name}...",
            )

        # 1. Search Stage (Discovery)
        is_placeholder = (
            not resolved_url
            or "http" not in resolved_url
            or f"www.{self.platform}.com" in resolved_url
            or (self.platform == "google_maps" and "/maps/search/" in resolved_url)
            or (self.platform == "zomato" and "/ncr/" not in resolved_url and "/reviews" not in resolved_url)
            or (self.platform == "tripadvisor" and "Restaurant_Review" not in resolved_url)
        )
        if is_placeholder:
            tmpl = PLATFORM_SEARCH_TEMPLATES.get(category, {}).get(
                self.platform, f"{{name}} {category} {{city}} {self.platform} reviews"
            )
            query = tmpl.format(name=business_name, city=city)
            results, s_log = await asyncio.to_thread(self.tf.search, query)

            tinyfish_calls.append(
                TinyFishCallIn(
                    platform=self.platform,
                    endpoint="search",
                    input={"query": query},
                    status=s_log.status,
                    duration_ms=s_log.duration_ms,
                    items_returned=s_log.items_returned,
                    steps_used=0,
                    cached=s_log.cached,
                )
            )

            found_url = None
            target_domain = PLATFORM_DOMAINS.get(self.platform, self.platform)
            for item in results:
                u = item.get("url") or item.get("link") or ""
                if _matches_domain(u, target_domain):
                    if self.platform == "zomato" and "/reviews" not in u:
                        u = u.rstrip("/") + "/reviews"
                    elif self.platform == "tripadvisor" and "#REVIEWS" not in u:
                        u = u.rstrip("/") + "#REVIEWS"
                    found_url = u
                    break

            if found_url:
                resolved_url = found_url
            elif not resolved_url or f"www.{self.platform}.com" in resolved_url:
                if self.platform == "google_maps":
                    resolved_url = f"https://www.google.com/maps/search/{business_name.replace(' ', '+')}+{city.replace(' ', '+')}"
                elif self.platform == "tripadvisor":
                    resolved_url = f"https://www.tripadvisor.com/Search?q={business_name.replace(' ', '+')}+{city.replace(' ', '+')}"
                else:
                    resolved_url = f"https://www.{self.platform}.com/{business_name.lower().replace(' ', '-')}"

            if emit_callback:
                await emit_callback(
                    event_type="tinyfish_call",
                    source=self.platform,
                    status=s_log.status,
                    message=f"TinyFish Search: Found {self.display_name} URL ({s_log.duration_ms}ms)",
                )

        # 2. Fetch Stage (Free Markdown Extraction)
        markdown, f_log = await asyncio.to_thread(self.tf.fetch, resolved_url)
        tinyfish_calls.append(
            TinyFishCallIn(
                platform=self.platform,
                endpoint="fetch",
                input={"url": resolved_url},
                status=f_log.status,
                duration_ms=f_log.duration_ms,
                items_returned=f_log.items_returned,
                steps_used=0,
                cached=f_log.cached,
            )
        )

        if markdown:
            extracted = extract_reviews_from_markdown(markdown, platform=self.display_name)
            raw_reviews.extend(extracted)
            if emit_callback:
                await emit_callback(
                    event_type="tinyfish_call",
                    source=self.platform,
                    status="success",
                    message=f"TinyFish Fetch: Extracted {len(extracted)} reviews via Markdown",
                )

        # 3. Agent Escalation (Metered Headless Run)
        if len(raw_reviews) < ESCALATION_MIN_REVIEWS:
            if skip_agent:
                if emit_callback:
                    await emit_callback(
                        event_type="tinyfish_call",
                        source=self.platform,
                        status="cached",
                        message="Agent daily step budget reached; loaded reviews from 24h cache",
                    )
            else:
                loop = asyncio.get_running_loop()

                def on_step(s_num: int, p_text: str):
                    if emit_callback:
                        msg = f"{self.display_name} Agent Step {s_num}: {p_text}" if p_text else f"{self.display_name} Agent: Step {s_num} in progress..."
                        try:
                            asyncio.run_coroutine_threadsafe(
                                emit_callback(
                                    event_type="tinyfish_call",
                                    source=self.platform,
                                    status="running",
                                    message=msg[:120],
                                ),
                                loop,
                            )
                        except Exception:
                            pass

                agent_reviews, a_log = await asyncio.to_thread(
                    self.tf.run_agent,
                    url=resolved_url,
                    platform=self.display_name,
                    max_reviews=10,
                    on_step=on_step,
                )
                agent_steps_used = a_log.steps_used or 0
                tinyfish_calls.append(
                    TinyFishCallIn(
                        platform=self.platform,
                        endpoint="agent",
                        input={"url": resolved_url},
                        status=a_log.status,
                        duration_ms=a_log.duration_ms,
                        items_returned=a_log.items_returned,
                        steps_used=agent_steps_used,
                        cached=a_log.cached,
                    )
                )
                raw_reviews.extend(agent_reviews)
                if emit_callback:
                    await emit_callback(
                        event_type="tinyfish_call",
                        source=self.platform,
                        status=a_log.status,
                        message=f"TinyFish Agent: Extracted {len(agent_reviews)} reviews ({agent_steps_used} steps)",
                    )

        # 4. Normalise to ReviewIn models
        reviews: List[ReviewIn] = []
        now = datetime.now(timezone.utc)
        for r in raw_reviews:
            txt = (r.get("text") or "").strip()
            if not txt:
                continue
            author = (r.get("author") or "Anonymous").strip()
            try:
                rating = float(r.get("rating") or 3.0)
            except (ValueError, TypeError):
                rating = 3.0

            reply = r.get("owner_reply_text")
            has_reply = bool(reply) or bool(r.get("has_owner_reply", False))

            reviews.append(
                ReviewIn(
                    platform=self.platform,
                    author=author,
                    rating=max(1.0, min(5.0, rating)),
                    text=txt,
                    language="en",
                    posted_at=now,
                    url=resolved_url,
                    has_owner_reply=has_reply,
                    sentiment=None,
                    severity=None,
                    rating_text_mismatch=False,
                )
            )

        status_result = "success" if len(reviews) >= 5 else ("partial" if reviews else "failed")

        if emit_callback:
            await emit_callback(
                event_type="source_status",
                source=self.platform,
                status=status_result,
                message=f"{self.display_name}: Collected {len(reviews)} reviews",
            )

        return CollectionResult(
            platform=self.platform,
            status=status_result,
            reviews=reviews,
            agent_steps_used=agent_steps_used,
            tinyfish_calls=tinyfish_calls,
            error=None,
        )


def get_collector(platform_key: str, display_name: str) -> MultiPlatformCollector:
    return MultiPlatformCollector(platform_key, display_name)
