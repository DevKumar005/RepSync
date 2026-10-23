import json
import os
import re
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from groq import Groq
from pydantic import BaseModel

ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env")


class ExtractedReviewItem(BaseModel):
    author: str
    rating: float = 3.0
    posted_at: str
    text: str
    owner_reply_text: str | None = None
    has_owner_reply: bool = False


class ExtractedReviewList(BaseModel):
    reviews: list[ExtractedReviewItem]


def _extract_with_heuristics(markdown_text: str, platform: str) -> list[dict]:
    """
    Extracts structured reviews directly from platform markdown (e.g. Zomato, TripAdvisor)
    in 1ms with 0 API tokens and 0 external network calls.
    """
    if not markdown_text:
        return []

    lines = [line.strip() for line in markdown_text.splitlines() if line.strip()]
    reviews = []

    # 1. Zomato pattern: Author -> [followers] -> Rating -> DINING/DELIVERY -> Date -> Text -> [Helpful/Votes]
    for i, line in enumerate(lines):
        if line in ("DINING", "DELIVERY"):
            author = None
            rating = 3.0
            date_str = "Recent"

            if i >= 1:
                m = re.match(r"^([1-5](?:\.[0-9])?)$", lines[i - 1])
                if m:
                    rating = float(m.group(1))
                    if i >= 3 and ("review" in lines[i - 2].lower() or "follower" in lines[i - 2].lower()):
                        author = lines[i - 3]
                    elif i >= 2:
                        author = lines[i - 2]
                elif i >= 2:
                    m2 = re.match(r"^([1-5](?:\.[0-9])?)$", lines[i - 2])
                    if m2:
                        rating = float(m2.group(1))
                        author = lines[i - 3] if i >= 3 else None

            if i + 1 < len(lines):
                date_str = lines[i + 1]

            text_parts = []
            j = i + 2
            while j < len(lines):
                l_cur = lines[j]
                if "helpful" in l_cur.lower() or "vote" in l_cur.lower() or l_cur in ("DINING", "DELIVERY", "Comment", "Share"):
                    break
                if j + 3 < len(lines) and lines[j + 3] in ("DINING", "DELIVERY"):
                    break
                text_parts.append(l_cur)
                j += 1

            rev_text = " ".join(text_parts).strip()
            if author and rev_text and len(rev_text) > 5 and not author.startswith("#"):
                reviews.append({
                    "author": author,
                    "rating": rating,
                    "posted_at": date_str,
                    "text": rev_text,
                    "owner_reply_text": None,
                    "has_owner_reply": False,
                })

    if reviews:
        return reviews

    # 2. General review cards with ratings e.g. "★" or "rated X of 5" or "5/5"
    review_blocks = re.split(r"\n(?=#{2,4}\s+|Reviewed\s+|Written\s+)", markdown_text)
    for block in review_blocks:
        b_lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(b_lines) < 2:
            continue
        text_full = " ".join(b_lines)
        r_match = re.search(r"(?:rated\s+|rating:\s*|★\s*)([1-5](?:\.[0-9])?)(?:\s*(?:of\s*5|/5|stars?))?", text_full, re.IGNORECASE)
        rating_val = float(r_match.group(1)) if r_match else None
        if rating_val and len(text_full) > 40:
            author_line = b_lines[0].lstrip("#").strip()
            reviews.append({
                "author": author_line if len(author_line) < 50 else "Customer",
                "rating": rating_val,
                "posted_at": "Recent",
                "text": text_full[:600],
                "owner_reply_text": None,
                "has_owner_reply": False,
            })

    return reviews


def _extract_with_groq(markdown_text: str, platform: str) -> list[dict]:
    groq_key = os.getenv("GROQ_API_KEY", "")
    if not groq_key or "your-groq-key" in groq_key:
        return []
    try:
        client = Groq(api_key=groq_key)
        prompt = (
            f"You are extracting real customer reviews from a {platform} page converted to Markdown.\n"
            f"Extract ONLY actual individual customer reviews present in the text.\n"
            f"Return a JSON object with key 'reviews' containing a list of objects with keys:\n"
            f"author (string), rating (float between 1.0 and 5.0, default 3.0 if not specified), "
            f"posted_at (string), text (full review text), owner_reply_text (string or null), has_owner_reply (boolean).\n"
            f"Do NOT invent reviews. If no individual reviews exist, return {{\"reviews\": []}}.\n\n"
            f"--- PAGE MARKDOWN ---\n{markdown_text[:12000]}"
        )
        model = os.getenv("GROQ_MODEL") or "openai/gpt-oss-20b"
        chat = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        parsed = json.loads(chat.choices[0].message.content or "{}")
        raw_list = parsed.get("reviews", [])
        clean_list = []
        for r in raw_list:
            t = (r.get("text") or "").strip()
            if not t:
                continue
            try:
                rt = float(r.get("rating") or 3.0)
            except (ValueError, TypeError):
                rt = 3.0
            clean_list.append({
                "author": (r.get("author") or "Customer").strip(),
                "rating": max(1.0, min(5.0, rt)),
                "posted_at": str(r.get("posted_at") or "Recent"),
                "text": t,
                "owner_reply_text": r.get("owner_reply_text"),
                "has_owner_reply": bool(r.get("has_owner_reply", False)),
            })
        if clean_list:
            print(f"  [Extractor Groq Fallback] Successfully extracted {len(clean_list)} reviews via Groq.")
        return clean_list
    except Exception as e:
        print(f"  [Extractor Groq Fallback Warning] {e}")
        return []


def extract_reviews_from_markdown(markdown_text: str, platform: str) -> list[dict]:
    """
    1. Runs fast 1ms pattern heuristics (0 API tokens, 0 network calls).
    2. Falls back to Groq / Gemini with strict 8s timeout to protect Google quota.
    """
    if not markdown_text or len(markdown_text.strip()) < 80:
        return []

    # 1. Fast Heuristic extraction
    heuristic_reviews = _extract_with_heuristics(markdown_text, platform)
    if heuristic_reviews:
        print(f"  [Extractor Heuristics] Extracted {len(heuristic_reviews)} reviews from {platform} markdown instantly.")
        return heuristic_reviews

    # 2. Check if Gemini is in cooldown
    try:
        from ai.llm_client import LLMClient
        if time.time() < LLMClient._gemini_down_until:
            return _extract_with_groq(markdown_text, platform)
    except Exception:
        pass

    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if gemini_key and "your-gemini-key" not in gemini_key:
        try:
            # Strict 8s timeout to prevent SSL hang or deadline expiry from eating quota
            client = genai.Client(api_key=gemini_key, http_options={"timeout": 8.0})
            prompt = (
                f"You are extracting real customer reviews from a {platform} page converted to Markdown.\n"
                f"Extract ONLY actual individual customer reviews present in the text.\n"
                f"Do NOT invent reviews. If no individual reviews are present in the text, return empty list `[]`.\n\n"
                f"--- PAGE MARKDOWN ---\n{markdown_text[:12000]}"
            )
            gemini_model = os.getenv("GEMINI_MODEL") or "gemini-3.8-flash"
            response = client.models.generate_content(
                model=gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ExtractedReviewList,
                    temperature=0.0,
                ),
            )
            parsed = json.loads(response.text)
            extracted = parsed.get("reviews", [])
            if extracted:
                return extracted
        except Exception as e:
            print(f"  [Extractor Warning] Gemini unavailable ({e}); failing over to Groq and marking Gemini down for 30m...")
            try:
                from ai.llm_client import LLMClient
                LLMClient._gemini_down_until = time.time() + 1800
            except Exception:
                pass

    return _extract_with_groq(markdown_text, platform)
