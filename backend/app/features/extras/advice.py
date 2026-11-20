"""One-line advice per top gap. The LLM writes only the action phrase; code writes every number."""
import re
from typing import List, Optional

from pydantic import BaseModel

from backend.app.features.extras.topics import llm_enabled

_DIGITS = re.compile(r"\d")

FALLBACK_TIPS = {
    ("threat", "slow service"): "Add a peak-hour floor captain so orders and bills move faster.",
    ("threat", "food quality"): "Run a daily taste and temperature check before dishes leave the kitchen.",
    ("threat", "overpriced"): "Explain portion sizes and taxes clearly on the menu and bill.",
    ("threat", "hygiene"): "Put a visible cleaning schedule on tables and washrooms every hour.",
    ("threat", "rude staff"): "Hold a short courtesy briefing for front-of-house staff each shift.",
    ("threat", "poor management"): "Use a simple token or booking system at peak times.",
    ("threat", "doctor behaviour"): "Block enough time per consultation so patients never feel rushed.",
    ("threat", "poor quality work"): "Add a final quality check before the customer leaves.",
    ("opportunity", "slow service"): "Promote your quick service in replies and on your listing.",
    ("opportunity", "food quality"): "Show fresh, hot dishes in photos and highlight them in replies.",
    ("opportunity", "overpriced"): "Highlight your fair prices and value portions in posters and replies.",
    ("opportunity", "hygiene"): "Share photos of your clean kitchen and tables on your listing.",
    ("opportunity", "rude staff"): "Feature your friendly team in posters and thank them in replies.",
    ("opportunity", "poor management"): "Advertise easy seating or bookings at peak times.",
    ("opportunity", "doctor behaviour"): "Highlight unhurried, careful consultations in replies and posters.",
    ("opportunity", "poor quality work"): "Showcase before-and-after results with customer permission.",
}


class AdviceItem(BaseModel):
    theme: str
    tip: str


class AdviceResult(BaseModel):
    items: List[AdviceItem]


def _fallback_tip(status: str, theme: str) -> str:
    if status == "opportunity":
        return FALLBACK_TIPS.get((status, theme), "Customers notice this gap, so mention your strength here in replies.")
    return FALLBACK_TIPS.get((status, theme), f"Make {theme} your first fix this month.")


def _numbers_sentence(gap: dict) -> str:
    you = gap["cells"][0]
    other = next(c for c in gap["cells"] if c["key"] == gap["versus_key"])
    return (
        f"{gap['theme'].capitalize()}: {you['rate']:g}% of your reviews ({you['count']} of {you['n']}) "
        f"vs {other['rate']:g}% at {other['name']} ({other['count']} of {other['n']})."
    )


def _llm_tips(gaps: List[dict], category: str) -> dict:
    from ai.llm_client import LLMClient

    lines = []
    for g in gaps:
        you = g["cells"][0]
        other = next(c for c in g["cells"] if c["key"] == g["versus_key"])
        lines.append(
            f'- theme "{g["theme"]}", status {g["status"]}: you {you["rate"]}% of reviews, '
            f'{other["name"]} {other["rate"]}% of reviews'
        )
    prompt = (
        f"You advise the owner of a small {category} in India.\n"
        "For each gap below, write ONE short action sentence (max 18 words).\n"
        "threat = customers complain about this more at the owner's outlet than at a competitor: suggest a fix.\n"
        "opportunity = a competitor gets more complaints about this: suggest how to advertise the owner's strength.\n"
        "Do NOT write any numbers, digits, percentages or competitor names. Plain English.\n"
        'Return ONLY JSON: {"items": [{"theme": "<theme exactly as given>", "tip": "<sentence>"}]}\n\n'
        + "\n".join(lines)
    )
    result = LLMClient().generate_json(prompt, AdviceResult)["data"]
    return {i.theme: i.tip.strip() for i in result.items}


def build_advice(gaps: List[dict], category: str, use_llm: Optional[bool] = None) -> List[dict]:
    if not gaps:
        return []
    tips: dict = {}
    if use_llm if use_llm is not None else llm_enabled():
        try:
            tips = _llm_tips(gaps, category)
        except Exception as e:
            print(f"Notice: advice LLM failed ({e}); using fallback tips.")

    out = []
    for g in gaps:
        tip = tips.get(g["theme"], "")
        # Reject anything the LLM wrote with a number in it, or empty text
        if not tip or _DIGITS.search(tip) or len(tip) > 160:
            tip = _fallback_tip(g["status"], g["theme"])
        out.append({
            "theme": g["theme"],
            "status": g["status"],
            "text": f"{_numbers_sentence(g)} {tip}",
        })
    return out
