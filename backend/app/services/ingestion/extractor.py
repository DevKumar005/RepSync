import json
import os
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
    rating: float
    posted_at: str
    text: str
    owner_reply_text: str | None = None
    has_owner_reply: bool = False


class ExtractedReviewList(BaseModel):
    reviews: list[ExtractedReviewItem]


def _extract_with_groq(markdown_text: str, platform: str) -> list[dict]:
    groq_key = os.getenv("GROQ_API_KEY", "")
    if not groq_key or "your-groq-key" in groq_key:
        return []
    try:
        client = Groq(api_key=groq_key)
        prompt = (
            f"You are extracting real customer reviews from a {platform} page converted to Markdown.\n"
            f"Extract ONLY actual individual customer reviews or patient stories present in the text.\n"
            f"Return a JSON object with key 'reviews' containing a list of objects with keys: "
            f"author, rating (1.0 to 5.0), posted_at, text, owner_reply_text, has_owner_reply.\n"
            f"Do NOT invent or hallucinate reviews. If no individual reviews are present, return {{\"reviews\": []}}.\n\n"
            f"--- PAGE MARKDOWN ---\n{markdown_text[:12000]}"
        )
        model = os.getenv("GROQ_MODEL") or "openai/gpt-oss-120b"
        chat = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            response_format={"type": "json_object"},
            temperature=0.0,
        )
        parsed = json.loads(chat.choices[0].message.content or "{}")
        reviews = parsed.get("reviews", [])
        if reviews:
            print(f"  [Extractor Groq Fallback] Successfully extracted {len(reviews)} reviews via Groq.")
        return reviews
    except Exception as e:
        print(f"  [Extractor Groq Fallback Warning] {e}")
        return []


def extract_reviews_from_markdown(markdown_text: str, platform: str) -> list[dict]:
    """
    Uses Gemini free tier (gemini-3.8-flash) to extract structured customer reviews
    from TinyFish Fetch Markdown. Falls back to Groq on 429/503 errors.
    """
    if not markdown_text or len(markdown_text.strip()) < 100:
        return []

    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if gemini_key and "your-gemini-key" not in gemini_key:
        try:
            client = genai.Client(api_key=gemini_key)
            prompt = (
                f"You are extracting real customer reviews from a {platform} page converted to Markdown.\n"
                f"Extract ONLY actual individual customer reviews or patient stories present in the text.\n"
                f"Do NOT invent or hallucinate reviews. If no individual reviews are present in the text, "
                f"return an empty list `[]`.\n\n"
                f"--- PAGE MARKDOWN ---\n{markdown_text[:15000]}"
            )
            gemini_model = os.getenv("GEMINI_MODEL") or "gemini-3.5-flash"
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
            return parsed.get("reviews", [])
        except Exception as e:
            print(f"  [Extractor Warning] Gemini failed ({e}); attempting Groq fallback...")

    # Fallback to Groq if Gemini is unconfigured, throttled (429), or unavailable (503)
    return _extract_with_groq(markdown_text, platform)
