import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlmodel import Column, Field, JSON, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# --- SQLModel Database Models ---

class AppUser(SQLModel, table=True):
    __tablename__ = "app_user"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str
    email: str = Field(unique=True, index=True)
    password_hash: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)



class ToneProfile(SQLModel, table=True):
    __tablename__ = "tone_profile"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: Optional[str] = Field(default=None, foreign_key="app_user.id")
    style: str = Field(default="warm")  # warm, professional, witty, empathetic
    sample_replies: List[str] = Field(default=[], sa_column=Column(JSON))
    do_not_say: List[str] = Field(default=[], sa_column=Column(JSON))


class Outlet(SQLModel, table=True):
    __tablename__ = "outlet"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: Optional[str] = Field(default=None, foreign_key="app_user.id")
    name: str
    category: str  # restaurant, clinic, salon
    city: str
    address: Optional[str] = None
    tone_profile_id: Optional[str] = Field(default=None, foreign_key="tone_profile.id")
    is_demo: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utc_now)


class Platform(SQLModel, table=True):
    __tablename__ = "platform"

    key: str = Field(primary_key=True)  # google_maps, justdial, tripadvisor, zomato, practo
    display_name: str
    enabled: bool = Field(default=True)
    categories: List[str] = Field(default=[], sa_column=Column(JSON))
    review_cap: int = Field(default=50)


class Source(SQLModel, table=True):
    __tablename__ = "source"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    outlet_id: str = Field(foreign_key="outlet.id", ondelete="CASCADE", index=True)
    platform: str = Field(foreign_key="platform.key", index=True)
    url: Optional[str] = None
    status: str = Field(default="pending")  # pending, running, success, partial, failed, skipped
    error: Optional[str] = None
    review_count: int = Field(default=0)
    agent_steps_used: int = Field(default=0)
    last_synced_at: Optional[datetime] = None


class Review(SQLModel, table=True):
    __tablename__ = "review"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    outlet_id: str = Field(foreign_key="outlet.id", ondelete="CASCADE", index=True)
    source_id: Optional[str] = Field(default=None, foreign_key="source.id", ondelete="CASCADE")
    platform: str = Field(index=True)
    author: Optional[str] = None
    rating: Optional[float] = None
    text: Optional[str] = None
    language: Optional[str] = "en"
    posted_at: Optional[datetime] = None
    url: Optional[str] = None
    owner_reply_text: Optional[str] = None
    has_owner_reply: bool = Field(default=False)
    sentiment: Optional[str] = Field(default=None, index=True)  # positive, neutral, negative
    severity: Optional[int] = None  # 1, 2, 3
    rating_text_mismatch: bool = Field(default=False)
    hash_for_dedup: str = Field(index=True)


class Theme(SQLModel, table=True):
    __tablename__ = "theme"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    outlet_id: str = Field(foreign_key="outlet.id", ondelete="CASCADE", index=True)
    label: str
    description: Optional[str] = None
    sentiment: Optional[str] = None  # positive, negative
    created_at: datetime = Field(default_factory=utc_now)


class ReviewTheme(SQLModel, table=True):
    __tablename__ = "review_theme"

    review_id: str = Field(foreign_key="review.id", ondelete="CASCADE", primary_key=True)
    theme_id: str = Field(foreign_key="theme.id", ondelete="CASCADE", primary_key=True)
    confidence: Optional[float] = 1.0


class FixSuggestion(SQLModel, table=True):
    __tablename__ = "fix_suggestion"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    outlet_id: str = Field(foreign_key="outlet.id", ondelete="CASCADE", index=True)
    rank: int
    title: str
    rationale: Optional[str] = None
    evidence_count: Optional[int] = 0


class ReplyDraft(SQLModel, table=True):
    __tablename__ = "reply_draft"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    review_id: str = Field(foreign_key="review.id", ondelete="CASCADE", index=True)
    text: str
    status: str = Field(default="draft")  # draft, edited, approved, rejected, posted
    version: int = Field(default=1)
    prompt_version: Optional[str] = "v2"
    guardrail_flags: List[str] = Field(default=[], sa_column=Column(JSON))
    edited_by: Optional[str] = Field(default=None, foreign_key="app_user.id")
    approved_at: Optional[datetime] = None


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_log"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: Optional[str] = Field(default=None, foreign_key="app_user.id")
    action: str
    entity: str
    entity_id: Optional[str] = None
    details: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TinyFishCall(SQLModel, table=True):
    __tablename__ = "tinyfish_call"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    outlet_id: str = Field(foreign_key="outlet.id", ondelete="CASCADE", index=True)
    platform: Optional[str] = None
    endpoint: str  # search, fetch, agent
    input: Optional[Dict[str, Any]] = Field(default={}, sa_column=Column(JSON))
    status: Optional[str] = None
    duration_ms: Optional[int] = 0
    items_returned: Optional[int] = 0
    steps_used: int = Field(default=0)
    cached: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utc_now)


class CacheEntry(SQLModel, table=True):
    __tablename__ = "cache_entry"

    cache_key: str = Field(primary_key=True)
    payload: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: Optional[datetime] = None
