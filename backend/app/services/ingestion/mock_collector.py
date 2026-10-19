import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Callable, List, Optional
from backend.app.models.schemas import CollectionResult, ReviewIn, TinyFishCallIn

API_KEY = os.getenv("TINYFISH_API_KEY", "")


def compute_dedup_hash(platform: str, author: str, date_str: str, text: str) -> str:
    norm = f"{platform.lower()}:{(author or '').strip().lower()}:{date_str}:{(text or '')[:100].strip().lower()}"
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


# Sample high quality reviews for offline/mock fallback per platform and category
FALLBACK_REVIEWS = {
    "restaurant": {
        "google_maps": [
            ("Kavita Rao", 5.0, "Wonderful experience! The appetizers and curries were mouthwatering. Warm hospitality from the staff.", "positive", None, False),
            ("Gaurav Kapoor", 2.0, "Waited 40 minutes for our table despite reservation. Food was decent but AC was barely working.", "negative", 2, True),
            ("Deepak Nair", 4.0, "Good ambience and delicious main course. Price is reasonable for Connaught Place.", "positive", None, False),
        ],
        "zomato": [
            ("Tanvi Sen", 1.0, "Disappointing food delivery. Gravy spilled in the container and naans were rubbery and cold.", "negative", 3, False),
            ("Arjun Singhania", 4.5, "Authentic flavours! Biryani and kebabs are must-try. Fast packaging.", "positive", None, False),
        ],
        "tripadvisor": [
            ("Elena Rostova", 5.0, "A culinary gem in Delhi. Beautiful decor, attentive waitstaff, and incredible tandoori dishes.", "positive", None, False),
            ("Markus Weber", 2.0, "Extremely loud during peak dinner hours. Service was hurried and inattentive.", "negative", 1, False),
        ],
    },
    "clinic": {
        "google_maps": [
            ("Pooja Bhatia", 5.0, "Extremely hygienic clinic and courteous staff. Doctor explained the treatment clearly.", "positive", None, False),
            ("Ramesh Chandra", 2.0, "Doctor was 35 minutes late for our scheduled appointment. Reception was dismissive.", "negative", 2, False),
        ],
        "practo": [
            ("Meera Joshi", 5.0, "Zero pain during procedure! Best dentist consultation I have had in Mumbai.", "positive", None, False),
            ("Nikhil Bansal", 3.0, "Treatment was satisfactory but waiting room was overcrowded.", "neutral", 1, False),
        ],
        "justdial": [
            ("Sunil Shinde", 4.0, "Reasonable consultation charges and prompt follow-up advice.", "positive", None, False),
        ],
    },
    "salon": {
        "google_maps": [
            ("Ananya Roy", 5.0, "Outstanding haircut and styling by seniors. Ambience was very relaxing.", "positive", None, False),
            ("Simran Kaur", 2.0, "Stylist seemed rushed and did not listen to hair length preferences. Overpriced.", "negative", 2, False),
        ],
        "justdial": [
            ("Preeti Deshmukh", 4.0, "Good facial and manicure services. Staff was polite and skilled.", "positive", None, False),
            ("Neha Varma", 2.0, "Waited 20 minutes even with prior booking. Towels smelled damp.", "negative", 1, False),
        ],
    },
}


class MockMultiPlatformCollector:
    """Mock TinyFish collector providing instant, zero-cost deterministic review data."""

    def __init__(self, platform_key: str, display_name: str) -> None:
        self.platform = platform_key
        self.display_name = display_name

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
        reviews: List[ReviewIn] = []
        agent_steps_used = 0

        # Notify SSE: starting collection
        if emit_callback:
            await emit_callback(
                event_type="source_status",
                source=self.platform,
                status="running",
                message=f"[MOCK] Starting review collection for {self.display_name}...",
            )

        # 1. Mock Search Stage
        query = f"{business_name} {city} {self.display_name} reviews"
        url = target_url or f"https://www.{self.platform}.com/{business_name.lower().replace(' ', '-')}"

        search_call = TinyFishCallIn(
            platform=self.platform,
            endpoint="search",
            input={"query": query},
            status="success",
            duration_ms=150,
            items_returned=1,
            steps_used=0,
            cached=True,
        )
        tinyfish_calls.append(search_call)

        if emit_callback:
            await emit_callback(
                event_type="tinyfish_call",
                source=self.platform,
                status="success",
                message=f"[MOCK] Search: Found {self.display_name} URL",
            )

        # 2. Mock Fetch Stage
        fetch_call = TinyFishCallIn(
            platform=self.platform,
            endpoint="fetch",
            input={"url": url},
            status="success",
            duration_ms=200,
            items_returned=5,
            steps_used=0,
            cached=True,
        )
        tinyfish_calls.append(fetch_call)

        if emit_callback:
            await emit_callback(
                event_type="tinyfish_call",
                source=self.platform,
                status="success",
                message=f"[MOCK] Fetch: Extracted reviews from {self.display_name}",
            )

        # 3. Assemble sample reviews
        cat_reviews = FALLBACK_REVIEWS.get(category, FALLBACK_REVIEWS["restaurant"])
        platform_samples = cat_reviews.get(self.platform, cat_reviews.get("google_maps", []))

        # Mock agent call for Google Maps if applicable
        if self.platform == "google_maps":
            if skip_agent:
                if emit_callback:
                    await emit_callback(
                        event_type="tinyfish_call",
                        source=self.platform,
                        status="cached",
                        message="[MOCK] Agent daily step budget reached; loaded reviews from 24h cache",
                    )
                agent_steps_used = 0
            else:
                agent_steps_used = 2
                agent_call = TinyFishCallIn(
                    platform=self.platform,
                    endpoint="agent",
                    input={"goal": f"Expand and extract all reviews for {business_name}"},
                    status="success",
                    duration_ms=800,
                    items_returned=len(platform_samples),
                    steps_used=2,
                    cached=True,
                )
                tinyfish_calls.append(agent_call)
                if emit_callback:
                    await emit_callback(
                        event_type="tinyfish_call",
                        source=self.platform,
                        status="success",
                        message=f"[MOCK] Agent: Extracted {len(platform_samples)} reviews with 2 steps",
                    )

        now = datetime.now(timezone.utc)
        for idx, (author, rating, text, sentiment, severity, has_reply) in enumerate(platform_samples):
            posted = now - timedelta(days=idx * 3 + 1)
            reviews.append(
                ReviewIn(
                    platform=self.platform,
                    author=author,
                    rating=rating,
                    text=text,
                    language="en",
                    posted_at=posted,
                    url=url,
                    has_owner_reply=has_reply,
                    sentiment=sentiment,
                    severity=severity,
                    rating_text_mismatch=False,
                )
            )

        status_result = "success" if reviews else "partial"

        if emit_callback:
            await emit_callback(
                event_type="source_status",
                source=self.platform,
                status=status_result,
                message=f"[MOCK] {self.display_name}: Collected {len(reviews)} reviews",
            )

        return CollectionResult(
            platform=self.platform,
            status=status_result,
            reviews=reviews,
            agent_steps_used=agent_steps_used,
            tinyfish_calls=tinyfish_calls,
            error=None,
        )


def get_mock_collector(platform_key: str, display_name: str) -> MockMultiPlatformCollector:
    return MockMultiPlatformCollector(platform_key, display_name)
