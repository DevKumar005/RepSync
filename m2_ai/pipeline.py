import time
from schemas import ReviewAnalysis
from analysis import build_themes, suggest_fixes
from replies import draft_reply

ANALYSIS_VERSION = "v2"

def detect_language(text, ai_guess):
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return ai_guess or "english"
    deva = sum(1 for c in letters if "\u0900" <= c <= "\u097F")
    if deva / len(letters) >= 0.5:
        return "hindi"
    if ai_guess == "hindi":          # Hindi words, but in English letters
        return "hinglish"
    return ai_guess or "english"


def analyze_reviews(client, reviews, prompt_version=ANALYSIS_VERSION, pause=1.0):
    template = open(f"prompts/{prompt_version}/analysis.txt", encoding="utf-8").read()
    out = []
    for r in reviews:
        prompt = template.replace("{rating}", str(r["rating"])).replace("{text}", r["text"])
        try:
            a = client.generate_json(prompt, ReviewAnalysis)["data"]
            out.append({**r, "language": detect_language(r["text"], a.language) , "sentiment": a.sentiment,
                        "topics": a.topics, "severity": a.severity, "analysis_failed": False})
        except Exception:
            out.append({**r, "language": detect_language(r["text"], None), "sentiment": "neutral",
                        "topics": [], "severity": 1, "analysis_failed": True})
        time.sleep(pause)
    return out


def summarize(reviews):
    total = len(reviews)
    neg = [r for r in reviews if r["sentiment"] == "negative"]
    return {
        "total_reviews": total,
        "average_rating": round(sum(r["rating"] for r in reviews) / total, 2) if total else 0,
        "negative_count": len(neg),
        "percent_negative": round(100 * len(neg) / total) if total else 0,
        "unanswered_negatives": sum(1 for r in neg if not r.get("has_owner_reply")),
        "analysis_failed": sum(1 for r in reviews if r.get("analysis_failed")),
    }


def run_pipeline(client, reviews, outlet, tone=None, on_progress=None,
                 min_negatives_for_themes=5):
    """
    reviews: list of dicts with id, platform, rating, text, has_owner_reply (see loader.py)
    outlet:  {"name": "...", "category": "restaurant" | "clinic" | "salon"}
    """
    def say(msg):
        if on_progress:
            on_progress(msg)

    say(f"Analysing {len(reviews)} reviews")
    analyzed = analyze_reviews(client, reviews)
    negatives = [r for r in analyzed if r["sentiment"] == "negative"]

    themes, fixes = None, []
    if len(negatives) >= min_negatives_for_themes:
        say("Grouping complaints into themes")
        themes = build_themes(client, [
            {"id": r["id"], "text": r["text"], "topics": ", ".join(r["topics"])}
            for r in negatives])
        say("Writing top fixes")
        fixes = suggest_fixes(client, themes, business_type=outlet["category"])
    else:
        say("Too few negative reviews to find a pattern")

    to_answer = [r for r in negatives if not r.get("has_owner_reply")]   # skip already-answered
    drafts = []
    for n, r in enumerate(to_answer, 1):
        say(f"Drafting reply {n} of {len(to_answer)}")
        review = {"text": r["text"], "rating": r["rating"],
                  "platform": r.get("platform", "Google"), "language": r["language"]}
        try:
            d = draft_reply(client, review, outlet, tone)
        except Exception as e:
            d = {"text": "", "guardrail_flags": ["draft failed, please regenerate"],
                 "attempts": 0, "provider": "none", "prompt_version": "v0"}
        drafts.append({"review_id": r["id"], **d})
        time.sleep(1)

    say("Done")
    return {"summary": summarize(analyzed), "reviews": analyzed, "themes": themes,
            "fixes": fixes, "drafts": drafts, "usage": client.usage_summary()}