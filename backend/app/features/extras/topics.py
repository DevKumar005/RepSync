"""Complaint-topic tagging for reviews.

Live mode runs the existing v2 analysis prompt (ai/prompts/v2/analysis.txt) with the existing
LLMClient and ReviewAnalysis schema, unchanged. ai/pipeline.analyze_reviews cannot be imported
from the backend (it opens its prompt via a cwd-relative path), so this mirrors its loop.
Offline / MOCK_LLM mode uses a keyword tagger restricted to the same topic vocabulary.
"""
import os
import re
from pathlib import Path
from typing import Dict, List

ROOT_DIR = Path(__file__).resolve().parents[4]
ANALYSIS_PROMPT = ROOT_DIR / "ai" / "prompts" / "v2" / "analysis.txt"
MAX_LLM_REVIEWS = 50

TOPICS = [
    "slow service", "food quality", "overpriced", "hygiene", "rude staff",
    "poor management", "doctor behaviour", "poor quality work",
]

_KEYWORDS: Dict[str, List[str]] = {
    "slow service": [
        r"\bslow", r"\bwait(ed)?\b", r"\bwaiting\b(?! (room|area|hall))", r"\bdelay", r"\blate\b", r"\bforgot", r"\bignored", r"took forever",
        r"respect (\w+\W? )*time", r"\bder (se|lagi|ho)", r"intezaar", r"देर", r"इंतज़ार", r"इंतजार",
    ],
    "food quality": [
        r"\bcold\b", r"\bbland", r"\bstale", r"tasteless", r"undercooked", r"\boily", r"not fresh",
        r"\braw\b", r"\bbekaar khana", r"\bthanda", r"बासी", r"बेस्वाद", r"ठंडा",
    ],
    "overpriced": [
        r"overpriced", r"expensive", r"\bcostly", r"\bpricey", r"\bcharges?\b", r"higher than quoted",
        r"hidden", r"\bmehnga", r"महंगा", r"rip-?off",
    ],
    "hygiene": [
        r"\bdirty", r"unhygienic", r"\bsmell", r"cockroach", r"\bflies\b", r"unclean", r"\bganda", r"गंदा", r"गंदगी",
    ],
    "rude staff": [
        r"\brude", r"arrogant", r"unprofessional", r"misbehav", r"badtameez", r"बदतमीज", r"\bshouted",
    ],
    "poor management": [
        r"overcrowd", r"\bcrowded", r"\bchaos", r"mismanag", r"booking (was )?(not|cancel)", r"disorgani[sz]",
        r"\bcramped", r"no seating", r"double[- ]booked",
    ],
    "doctor behaviour": [
        r"doctor (was )?rush", r"did ?n[o']t listen", r"did ?n[o']t examine", r"barely examined",
    ],
    "poor quality work": [
        r"bad haircut", r"\buneven", r"wrong colou?r", r"pain (persisted|came back)", r"filling fell",
        r"treatment failed", r"had to redo",
    ],
}
_COMPILED = {t: [re.compile(p, re.IGNORECASE) for p in pats] for t, pats in _KEYWORDS.items()}


def keyword_topics(text: str, rating: float) -> List[str]:
    """Complaint topics found by keyword match. Only reviews rated 3.5 or lower count as complaints."""
    if not text or (rating or 3.0) > 3.5:
        return []
    found = [t for t, pats in _COMPILED.items() if any(p.search(text) for p in pats)]
    return found[:3]


def llm_enabled() -> bool:
    """Same gate as services/analysis/analyzer.py: MOCK_LLM must be off and a key configured."""
    mock_flag = os.getenv("MOCK_LLM", "1").lower().strip()
    api_key = os.getenv("GEMINI_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
    return mock_flag in {"0", "false", "no"} and bool(api_key) and "your-" not in api_key


def analyze_topics(reviews: List[dict]) -> List[List[str]]:
    """Complaint topics per review (same order as input). Each review needs `text` and `rating`."""
    if not llm_enabled():
        return [keyword_topics(r.get("text") or "", r.get("rating") or 3.0) for r in reviews]

    from ai.llm_client import LLMClient
    from ai.schemas import ReviewAnalysis

    client = LLMClient()
    template = ANALYSIS_PROMPT.read_text(encoding="utf-8")
    out: List[List[str]] = []
    for i, r in enumerate(reviews):
        text = r.get("text") or ""
        if i >= MAX_LLM_REVIEWS:
            out.append(keyword_topics(text, r.get("rating") or 3.0))
            continue
        prompt = template.replace("{rating}", str(r.get("rating") or 3.0)).replace("{text}", text)
        try:
            analysis = client.generate_json(prompt, ReviewAnalysis)["data"]
            out.append([t for t in analysis.topics if t in TOPICS][:3])
        except Exception:
            out.append(keyword_topics(text, r.get("rating") or 3.0))
    return out
