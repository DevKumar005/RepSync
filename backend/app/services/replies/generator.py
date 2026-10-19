import os
from typing import List, Optional, Tuple
from backend.app.models.entities import Review, ToneProfile


def check_guardrails(reply_text: str, do_not_say: List[str]) -> List[str]:
    """
    Scans reply draft for forbidden words and defensive framing.
    """
    flags = []
    lower = reply_text.lower()

    # 1. Check custom do_not_say
    for forbidden in do_not_say:
        if forbidden.lower() in lower:
            flags.append(f"Forbidden phrase detected: '{forbidden}'")

    # 2. Check general defensive phrasing
    defensive_phrases = ["not our fault", "as per our terms", "you should have", "we are very busy"]
    for phrase in defensive_phrases:
        if phrase in lower:
            flags.append(f"Defensive phrasing detected: '{phrase}'")

    return flags


def mock_generate_reply_draft(
    review: Review,
    tone: Optional[ToneProfile] = None,
    custom_instruction: Optional[str] = None,
) -> Tuple[str, List[str]]:
    """Deterministic mock reply generator for test isolation and offline demo."""
    author = review.author or "valued customer"
    style = tone.style if tone else "warm"
    do_not_say = tone.do_not_say if tone else []

    if style == "empathetic":
        base_reply = (
            f"Dear {author}, we are truly sorry to hear that your experience did not meet expectations. "
            f"Your comfort and peace of mind are our absolute priority. "
            f"We are actively reviewing our procedures with the team. "
            f"Please reach out to us directly so we can personally ensure your next visit is seamless."
        )
    elif style == "professional":
        base_reply = (
            f"Dear {author}, thank you for taking the time to share your feedback. "
            f"We hold our standards to the highest level and regret the inconvenience caused. "
            f"Our management team has noted your remarks regarding service turnaround. "
            f"Please contact our management desk so we may address this promptly."
        )
    elif style == "witty":
        base_reply = (
            f"Hey {author}, ouch! That is definitely not the standard we pride ourselves on. "
            f"We dropped the ball this time, and we want to make it up to you. "
            f"Give us another shot to show you how we really roll—reach out to us directly!"
        )
    else:  # warm (default)
        base_reply = (
            f"Dear {author}, thank you for sharing your candid feedback. "
            f"We deeply regret the delay and frustration you experienced during your visit. "
            f"We are taking immediate steps with our floor team to address peak-hour delays. "
            f"Please give us the opportunity to make this right on your next visit."
        )

    if custom_instruction:
        base_reply += f" [Note: {custom_instruction}]"

    # Evaluate guardrails
    flags = check_guardrails(base_reply, do_not_say)

    return base_reply, flags


def generate_reply_draft(
    review: Review,
    tone: Optional[ToneProfile] = None,
    custom_instruction: Optional[str] = None,
    previous: Optional[str] = None,
) -> Tuple[str, List[str]]:
    """
    Dynamic Reply Drafting Bridge:
    - If MOCK_LLM=1 (or offline/testing): Uses deterministic mock reply templates.
    - If MOCK_LLM=0 and API key is set: Bridges to Param's m2_ai.replies engine with multi-lingual guardrails.
    """
    mock_flag = os.getenv("MOCK_LLM", "1").lower().strip()
    api_key = os.getenv("GEMINI_API_KEY", "") or os.getenv("GROQ_API_KEY", "")

    # Live Mode: Call Param's m2_ai module when available on main
    if mock_flag in {"0", "false", "no"} and api_key and "your-" not in api_key:
        try:
            from m2_ai.llm_client import LLMClient
            from m2_ai.replies import draft_reply

            client = LLMClient()
            review_dict = {
                "text": review.text or "",
                "rating": float(review.rating or 3.0),
                "platform": review.platform or "Google Maps",
                "language": review.language or "english",
            }
            outlet_dict = {
                "name": "Local Business",
                "category": "restaurant",
            }
            tone_dict = {
                "style": tone.style if tone else "warm",
                "do_not_say": tone.do_not_say if tone else [],
                "samples": tone.samples if tone else [],
            }
            res = draft_reply(
                client=client,
                review=review_dict,
                outlet=outlet_dict,
                tone=tone_dict,
                instruction=custom_instruction,
                previous=previous,
            )
            return res.get("text", ""), res.get("guardrail_flags", [])
        except Exception as exc:
            print(f"Notice: Live m2_ai reply draft unavailable or failed ({exc}), falling back to mock reply.")

    # Mock Mode fallback
    return mock_generate_reply_draft(review, tone, custom_instruction)

