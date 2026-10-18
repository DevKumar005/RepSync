import json
import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
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


def extract_reviews_from_markdown(markdown_text: str, platform: str) -> list[dict]:
    """
    Uses Gemini free tier to extract structured customer reviews from TinyFish Fetch Markdown.
    Returns a list of dicts matching the Agent output structure.
    """
    if not markdown_text or len(markdown_text.strip()) < 100:
        return []

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or "your-gemini-key" in api_key:
        print("  [WARN] GEMINI_API_KEY not set; skipping Markdown LLM extraction.")
        return []

    client = genai.Client(api_key=api_key)

    prompt = (
        f"You are extracting real customer reviews from a {platform} page converted to Markdown.\n"
        f"Extract ONLY actual individual customer reviews or patient stories present in the text.\n"
        f"Do NOT invent or hallucinate reviews. If no individual reviews are present in the text, "
        f"return an empty list `[]`.\n\n"
        f"--- PAGE MARKDOWN ---\n{markdown_text[:15000]}"
    )

    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
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
        print(f"  [Extractor Warning] Gemini markdown parse failed: {e}")
        return []