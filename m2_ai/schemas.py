from typing import Literal , Optional
from pydantic import BaseModel, Field
from typing import Optional

class ThemeDef(BaseModel):
    label: str
    description: str


class Assignment(BaseModel):
    review_id: str
    primary: str
    secondary: Optional[str] = None


class ThemeAssignmentResult(BaseModel):
    themes: list[ThemeDef]
    assignments: list[Assignment]


class ReviewAnalysis(BaseModel):
    language: Optional[Literal["english", "hindi", "hinglish"]] = None
    sentiment: Literal["positive", "neutral", "negative"]
    topics: list[str] = Field(default_factory=list)
    severity: int = Field(ge=1, le=3)

class Theme(BaseModel):
    label: str
    description: str
    review_ids: list[str]


class ThemeResult(BaseModel):
    themes: list[Theme]


class Fix(BaseModel):
    theme: str
    title: str
    rationale: str


class FixResult(BaseModel):
    fixes: list[Fix]