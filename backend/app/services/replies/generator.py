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


def generate_reply_draft(
    review: Review,
    tone: Optional[ToneProfile] = None,
    custom_instruction: Optional[str] = None,
) -> Tuple[str, List[str]]:
    """
    Generates a professional reply tailored to tone profile and validates against guardrails.
    """
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
