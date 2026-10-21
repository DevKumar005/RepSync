import os
from typing import Any, Dict, List, Tuple
from backend.app.models.entities import Review

MOCK_LLM = os.getenv("MOCK_LLM", "0") == "1"


def classify_sentiment(rating: float, text: str) -> Tuple[str, int, bool]:
    """
    Returns (sentiment, severity, rating_text_mismatch).
    """
    lower = text.lower() if text else ""
    negative_words = ["slow", "delayed", "terrible", "bad", "worst", "unacceptable", "cold", "crowded", "rude", "dirty", "overpriced"]
    positive_words = ["great", "amazing", "delicious", "excellent", "best", "wonderful", "hygienic", "friendly", "love"]

    neg_hits = sum(1 for w in negative_words if w in lower)
    pos_hits = sum(1 for w in positive_words if w in lower)

    # Check rating text mismatch
    mismatch = False
    if rating >= 4.0 and neg_hits >= 2 and pos_hits == 0:
        mismatch = True
    elif rating <= 2.0 and pos_hits >= 2 and neg_hits == 0:
        mismatch = True

    if rating <= 2.5 or (neg_hits > pos_hits and rating < 4.0):
        sentiment = "negative"
        severity = 3 if (rating <= 1.0 or "worst" in lower or "terrible" in lower) else 2
    elif rating >= 4.0:
        sentiment = "positive"
        severity = 1
    else:
        sentiment = "neutral"
        severity = 1

    return sentiment, severity, mismatch


def mock_analyze_themes_and_fixes(
    reviews: List[Review],
    category: str,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Mock rule-based theme clustering and fix generator for testing and offline demo."""
    negative_reviews = [r for r in reviews if r.sentiment == "negative"]
    positive_reviews = [r for r in reviews if r.sentiment == "positive"]

    themes: List[Dict[str, Any]] = []
    fixes: List[Dict[str, Any]] = []

    # Category-specific heuristics
    if category == "restaurant":
        themes.append({
            "label": "Food Taste & Authentic Recipes",
            "sentiment": "positive",
            "description": "Customers frequently praise the flavour profile, fresh naans, and rich gravies.",
            "review_ids": [r.id for r in positive_reviews[:3]],
        })
        themes.append({
            "label": "Peak-Hour Table & Order Delays",
            "sentiment": "negative",
            "description": "Extended wait times for order delivery during weekend and peak evening rush.",
            "review_ids": [r.id for r in negative_reviews[:4]],
        })
        themes.append({
            "label": "Packaging & Delivery Temperature",
            "sentiment": "negative",
            "description": "Reports of food temperature drop and gravy leakage during transit.",
            "review_ids": [r.id for r in negative_reviews[4:6]],
        })

        fixes = [
            {
                "rank": 1,
                "title": "Introduce Peak-Hour Kitchen Expediter",
                "rationale": "Assign a dedicated expediter on weekends to coordinate food prep and shave 15 minutes off wait times.",
                "evidence_count": max(len(negative_reviews), 4),
            },
            {
                "rank": 2,
                "title": "Upgrade Insulated Packaging",
                "rationale": "Switch to spill-proof tamper-evident containers with heat-retaining thermal lining for delivery orders.",
                "evidence_count": 3,
            },
            {
                "rank": 3,
                "title": "Real-time Order Status SMS",
                "rationale": "Send automated updates to customers when order enters prep and dispatch to manage expectations.",
                "evidence_count": 2,
            },
        ]
    elif category == "clinic":
        themes.append({
            "label": "Gentle & Professional Care",
            "sentiment": "positive",
            "description": "Patients appreciate clear explanations and painless treatment procedures.",
            "review_ids": [r.id for r in positive_reviews[:3]],
        })
        themes.append({
            "label": "Appointment Delay & Overcrowding",
            "sentiment": "negative",
            "description": "Patients waiting 30-45 minutes past their appointment slot.",
            "review_ids": [r.id for r in negative_reviews[:4]],
        })

        fixes = [
            {
                "rank": 1,
                "title": "Stagger Appointment Buffers",
                "rationale": "Schedule a 10-minute buffer after surgical procedures to prevent appointment backlog.",
                "evidence_count": max(len(negative_reviews), 3),
            },
            {
                "rank": 2,
                "title": "Automated Delay SMS Alert",
                "rationale": "Proactively alert patients via WhatsApp if doctor is delayed by more than 15 minutes.",
                "evidence_count": 3,
            },
            {
                "rank": 3,
                "title": "Transparent Cost Breakdown Sheet",
                "rationale": "Provide printed itemized estimates prior to treatment to eliminate billing confusion.",
                "evidence_count": 2,
            },
        ]
    else:  # salon
        themes.append({
            "label": "Styling & Hospitality",
            "sentiment": "positive",
            "description": "Clients love the courteous stylists and modern hair aesthetics.",
            "review_ids": [r.id for r in positive_reviews[:3]],
        })
        themes.append({
            "label": "Booking Overlap & Waiting Area",
            "sentiment": "negative",
            "description": "Delays for scheduled walk-ins and cramped waiting spaces.",
            "review_ids": [r.id for r in negative_reviews[:4]],
        })

        fixes = [
            {
                "rank": 1,
                "title": "Chair Booking Calendar Sync",
                "rationale": "Enforce strict station assignment in appointment software to prevent double bookings.",
                "evidence_count": max(len(negative_reviews), 3),
            },
            {
                "rank": 2,
                "title": "Consultation First Protocol",
                "rationale": "Standardize 5-minute hair consultation before commencing scissors or chemical work.",
                "evidence_count": 2,
            },
            {
                "rank": 3,
                "title": "Linen Hygiene Checklist",
                "rationale": "Implement single-use fresh laundered aprons and towels per client with visible checklist.",
                "evidence_count": 2,
            },
        ]

    return themes, fixes


def analyze_themes_and_fixes(
    reviews: List[Review],
    category: str,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Dynamic Theme & Fix Recommendation Bridge:
    - If MOCK_LLM=1 (or offline/testing): Uses deterministic mock themes and fixes.
    - If MOCK_LLM=0 and API key is configured: Bridges to the ai.analysis engine.
    """
    mock_flag = os.getenv("MOCK_LLM", "1").lower().strip()
    api_key = os.getenv("GEMINI_API_KEY", "") or os.getenv("GROQ_API_KEY", "")

    # Live Mode: Call the ai module when available
    if mock_flag in {"0", "false", "no"} and api_key and "your-" not in api_key:
        try:
            from ai.llm_client import LLMClient
            from ai.analysis import build_themes, suggest_fixes

            client = LLMClient()
            negatives = [
                {"id": r.id, "text": r.text or "", "topics": r.text or ""}
                for r in reviews if r.sentiment == "negative"
            ]
            if len(negatives) >= 2:
                theme_res = build_themes(client, negatives)
                themes_out: List[Dict[str, Any]] = []
                for t in theme_res.get("themes", []):
                    themes_out.append({
                        "label": t.get("label", "Service Feedback"),
                        "sentiment": "negative",
                        "description": t.get("description", ""),
                        "review_ids": t.get("main_ids", []) + t.get("also_ids", []),
                    })

                fixes_res = suggest_fixes(client, theme_res, business_type=category)
                fixes_out: List[Dict[str, Any]] = []
                for f in fixes_res:
                    fixes_out.append({
                        "rank": f.get("rank", 1),
                        "title": f.get("title", ""),
                        "rationale": f.get("rationale", ""),
                        "evidence_count": f.get("evidence_count", 1),
                    })

                if themes_out and fixes_out:
                    return themes_out, fixes_out
        except Exception as exc:
            print(f"Notice: Live ai analysis unavailable or failed ({exc}), falling back to mock themes.")

    # Mock Mode fallback
    return mock_analyze_themes_and_fixes(reviews, category)

