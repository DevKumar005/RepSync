from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator



# --- Collector & TinyFish Contracts (SRS 2.3) ---

class TinyFishCallIn(BaseModel):
    platform: Optional[str] = None
    endpoint: Literal["search", "fetch", "agent"]
    input: Optional[Dict[str, Any]] = None
    status: Optional[str] = "success"
    duration_ms: int = 0
    items_returned: int = 0
    steps_used: int = 0
    cached: bool = False


class ReviewIn(BaseModel):
    platform: str
    author: Optional[str] = None
    rating: Optional[float] = None
    text: Optional[str] = None
    language: Optional[str] = "en"
    posted_at: Optional[datetime] = None
    url: Optional[str] = None
    owner_reply_text: Optional[str] = None
    has_owner_reply: bool = False
    sentiment: Optional[Literal["positive", "neutral", "negative"]] = None
    severity: Optional[int] = None
    rating_text_mismatch: bool = False


class CollectionResult(BaseModel):
    platform: str
    status: Literal["success", "partial", "failed"]
    reviews: List[ReviewIn] = []
    agent_steps_used: int = 0
    tinyfish_calls: List[TinyFishCallIn] = []
    error: Optional[str] = None


# --- Outlets & Platforms ---

class OutletSearchRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    city: str = Field(..., min_length=2, max_length=100)
    category: Literal["restaurant", "clinic", "salon"]


class OutletCandidate(BaseModel):
    name: str
    city: str
    category: str
    address: Optional[str] = None
    urls: Dict[str, str] = {}


class OutletCreate(BaseModel):
    name: Optional[str] = None
    category: Literal["restaurant", "clinic", "salon"]
    city: str = Field(..., min_length=2, max_length=100)
    address: Optional[str] = None
    candidate: Optional[Any] = None

    @model_validator(mode="after")
    def resolve_name(self):
        if not self.name and self.candidate:
            if isinstance(self.candidate, dict):
                self.name = self.candidate.get("name") or self.candidate.get("title")
            elif hasattr(self.candidate, "name"):
                self.name = self.candidate.name
        if not self.name:
            self.name = "My Outlet"
        return self



class SourceRead(BaseModel):
    id: str
    outlet_id: str
    platform: str
    url: Optional[str] = None
    status: str = "pending"
    error: Optional[str] = None
    review_count: int = 0
    agent_steps_used: int = 0
    last_synced_at: Optional[datetime] = None



class PlatformRead(BaseModel):
    key: str
    display_name: str
    enabled: bool
    categories: List[str]
    review_cap: int


class OutletRead(BaseModel):
    id: str
    name: str
    category: str
    city: str
    address: Optional[str] = None
    is_demo: bool
    created_at: datetime
    sources: List[SourceRead] = []


# --- Reviews & Drafts ---

class ReplyDraftRead(BaseModel):
    id: str
    review_id: str
    text: str
    status: str
    version: int
    prompt_version: Optional[str] = None
    guardrail_flags: List[str] = []
    edited_by: Optional[str] = None
    approved_at: Optional[datetime] = None


class ReviewRead(BaseModel):
    id: str
    outlet_id: str
    source_id: Optional[str] = None
    platform: str
    author: Optional[str] = None
    rating: Optional[float] = None
    text: Optional[str] = None
    language: Optional[str] = None
    posted_at: Optional[datetime] = None
    url: Optional[str] = None
    owner_reply_text: Optional[str] = None
    has_owner_reply: bool
    sentiment: Optional[str] = None
    severity: Optional[int] = None
    rating_text_mismatch: bool
    draft: Optional[ReplyDraftRead] = None


class DraftStatusUpdate(BaseModel):
    status: Optional[Literal["draft", "edited", "approved", "rejected", "posted"]] = None
    text: Optional[str] = None


class DraftRegenerateRequest(BaseModel):
    instruction: Optional[str] = None


# --- Themes & Fixes ---

class ThemeRead(BaseModel):
    id: str
    outlet_id: str
    label: str
    description: Optional[str] = None
    sentiment: Optional[str] = None
    review_count: int = 0
    percentage: float = 0.0


class FixSuggestionRead(BaseModel):
    id: str
    outlet_id: str
    rank: int
    title: str
    rationale: Optional[str] = None
    evidence_count: int = 0


# --- Tone Profile ---

class ToneProfileUpdate(BaseModel):
    style: Literal["warm", "formal", "apologetic", "concise"] = "warm"
    sample_replies: Union[List[str], str] = []
    do_not_say: Union[List[str], str] = []

    @field_validator("sample_replies", "do_not_say", mode="before")
    @classmethod
    def parse_string_or_list(cls, v):
        if isinstance(v, str):
            if not v.strip():
                return []
            return [item.strip() for item in v.replace("\n", ",").split(",") if item.strip()]
        return v or []



class ToneProfileRead(BaseModel):
    id: str
    style: str
    sample_replies: List[str] = []
    do_not_say: List[str] = []


# --- Activity Log & Summary ---

class TinyFishCallRead(BaseModel):
    id: str
    outlet_id: str
    platform: Optional[str] = None
    endpoint: str
    input: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    duration_ms: int = 0
    items_returned: int = 0
    steps_used: int = 0
    cached: bool = False
    created_at: datetime


class PlatformSummary(BaseModel):
    review_count: int = 0
    average_rating: float = 0.0
    percent_negative: float = 0.0


class SummaryResponse(BaseModel):
    total_reviews: int
    average_rating: float
    percent_negative: float
    unanswered_negatives: int
    per_platform: Dict[str, PlatformSummary] = {}


class SyncResponse(BaseModel):
    job_id: str
    outlet_id: str
    status: str
    message: str


# --- Auth ---

class AuthSignupRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)


class AuthLoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    name: str


# --- M1 Ingestion Contract Aliases ---
NormalizedReview = ReviewIn
TinyFishCallLog = TinyFishCallIn
SourceSyncStatus = CollectionResult

