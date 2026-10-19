import hashlib
import re
from datetime import datetime, timezone
from typing import Literal, Optional
from pydantic import BaseModel, Field


class CandidatePlatformUrl(BaseModel):
    platform: str
    url: str
    title: str = ""
    snippet: str = ""


class NormalizedReview(BaseModel):
    platform: str
    external_id: str
    author: str
    rating: float = Field(ge=1.0, le=5.0)
    text: str
    posted_at: str
    owner_reply_text: Optional[str] = None
    has_owner_reply: bool = False
    dedup_hash: str


class TinyFishCallLog(BaseModel):
    endpoint: Literal["search", "fetch", "agent"]
    input: str
    status: Literal["ok", "cached", "failed"]
    duration_ms: int
    items_returned: int = 0
    steps_used: Optional[int] = None
    cached: bool = False
    error_message: Optional[str] = None
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class SourceSyncStatus(BaseModel):
    platform: str
    listing_url: str
    status: Literal["ok", "partial", "failed"]
    reviews_collected: int = 0
    error_reason: Optional[str] = None


class CollectionResult(BaseModel):
    outlet_name: str
    city: str
    category: str
    sources: list[SourceSyncStatus]
    reviews: list[NormalizedReview]
    tinyfish_calls: list[TinyFishCallLog]
    total_steps_used: int = 0

def compute_dedup_hash(platform: str, author: str, rating: float, text: str) -> str:
    """
    Section 7.2: sha256(platform + author + rating + text[:100])
    Strips whitespace/punctuation variance so Fetch + Agent duplicates always match.
    """
    clean_author = re.sub(r"\W+", "", (author or "anonymous").lower())
    clean_text = re.sub(r"\W+", "", (text or "").lower())[:100]
    raw = f"{platform.lower()}|{clean_author}|{int(round(rating))}|{clean_text}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()