import os
import time
from pathlib import Path
from typing import Callable, Optional
from dotenv import load_dotenv
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from tinyfish import TinyFish, CompleteEvent, ProgressEvent

from app.tinyfish.cache import read_cache, write_cache
from app.services.ingestion.schemas import TinyFishCallLog

ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env")

API_KEY = os.getenv("TINYFISH_API_KEY", "")

AGENT_REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "reviews": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "author": {"type": "string"},
                    "rating": {"type": "number"},
                    "posted_at": {"type": "string"},
                    "text": {"type": "string"},
                    "owner_reply_text": {"type": "string", "nullable": True},
                    "has_owner_reply": {"type": "boolean"},
                },
                "required": ["author", "rating", "text"],
            },
        }
    },
    "required": ["reviews"],
}


class TinyFishService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or API_KEY
        if not self.api_key:
            raise ValueError("TINYFISH_API_KEY is missing in .env")
        self.sdk = TinyFish(api_key=self.api_key)
        self.headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4), reraise=True)
    def _raw_search(self, query: str) -> dict:
        resp = httpx.get(
            "https://api.search.tinyfish.ai",
            params={"query": query},
            headers={"X-API-Key": self.api_key},
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json()

    def search(
        self,
        query: str,
        use_cache: bool = True,
        on_log: Optional[Callable[[TinyFishCallLog], None]] = None,
    ) -> tuple[list[dict], TinyFishCallLog]:
        """Free Search endpoint (30 req/min)."""
        if use_cache:
            cached = read_cache("search", query)
            if cached:
                results = cached["data"].get("results") or cached["data"].get("data") or []
                log = TinyFishCallLog(
                    endpoint="search",
                    input=query,
                    status="cached",
                    duration_ms=0,
                    items_returned=len(results),
                    cached=True,
                )
                if on_log:
                    on_log(log)
                return results, log

        t0 = time.time()
        try:
            data = self._raw_search(query)
            duration_ms = int((time.time() - t0) * 1000)
            results = data.get("results") or data.get("data") or []
            write_cache("search", query, data, meta={"duration_ms": duration_ms})
            log = TinyFishCallLog(
                endpoint="search",
                input=query,
                status="ok",
                duration_ms=duration_ms,
                items_returned=len(results),
                cached=False,
            )
            if on_log:
                on_log(log)
            return results, log
        except Exception as e:
            duration_ms = int((time.time() - t0) * 1000)
            log = TinyFishCallLog(
                endpoint="search",
                input=query,
                status="failed",
                duration_ms=duration_ms,
                items_returned=0,
                cached=False,
                error_message=str(e),
            )
            if on_log:
                on_log(log)
            return [], log

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4), reraise=True)
    def _raw_fetch(self, url: str) -> dict:
        resp = httpx.post(
            "https://api.fetch.tinyfish.ai",
            headers=self.headers,
            json={"urls": [url], "format": "markdown"},
            timeout=45.0,
        )
        resp.raise_for_status()
        return resp.json()

    def fetch(
        self,
        url: str,
        use_cache: bool = True,
        on_log: Optional[Callable[[TinyFishCallLog], None]] = None,
    ) -> tuple[str, TinyFishCallLog]:
        """Free Fetch endpoint (150 URLs/min). Returns clean markdown text or empty string if blocked."""
        if use_cache:
            cached = read_cache("fetch", url)
            if cached:
                results = cached["data"].get("results") or []
                text = (results[0].get("text") or results[0].get("markdown") or "") if results else ""
                status = "cached" if text else "failed"
                log = TinyFishCallLog(
                    endpoint="fetch",
                    input=url,
                    status=status,
                    duration_ms=0,
                    items_returned=1 if text else 0,
                    cached=True,
                )
                if on_log:
                    on_log(log)
                return text, log

        t0 = time.time()
        try:
            data = self._raw_fetch(url)
            duration_ms = int((time.time() - t0) * 1000)
            results = data.get("results") or []
            errors = data.get("errors") or []
            text = (results[0].get("text") or results[0].get("markdown") or "") if results else ""

            write_cache("fetch", url, data, meta={"duration_ms": duration_ms})

            if not text or errors:
                err_msg = str(errors[0]) if errors else "empty_content"
                log = TinyFishCallLog(
                    endpoint="fetch",
                    input=url,
                    status="failed",
                    duration_ms=duration_ms,
                    items_returned=0,
                    cached=False,
                    error_message=err_msg,
                )
                if on_log:
                    on_log(log)
                return "", log

            log = TinyFishCallLog(
                endpoint="fetch",
                input=url,
                status="ok",
                duration_ms=duration_ms,
                items_returned=1,
                cached=False,
            )
            if on_log:
                on_log(log)
            return text, log
        except Exception as e:
            duration_ms = int((time.time() - t0) * 1000)
            log = TinyFishCallLog(
                endpoint="fetch",
                input=url,
                status="failed",
                duration_ms=duration_ms,
                items_returned=0,
                cached=False,
                error_message=str(e),
            )
            if on_log:
                on_log(log)
            return "", log

    def run_agent(
        self,
        url: str,
        platform: str,
        max_reviews: int = 10,
        use_cache: bool = True,
        on_log: Optional[Callable[[TinyFishCallLog], None]] = None,
        on_step: Optional[Callable[[int, str], None]] = None,
    ) -> tuple[list[dict], TinyFishCallLog]:
        """
        Metered Web Agent endpoint (SSE stream).
        Escalated ONLY when Fetch is blocked or yields < 10 reviews.
        """
        cache_key = f"{platform}:{url}"
        if use_cache:
            cached = read_cache("agent", cache_key)
            if cached:
                data_obj = cached.get("data") or cached.get("result") or {}
                reviews = data_obj.get("reviews", []) if isinstance(data_obj, dict) else []
                if reviews:
                    log = TinyFishCallLog(
                        endpoint="agent",
                        input=url,
                        status="cached",
                        duration_ms=0,
                        items_returned=len(reviews),
                        steps_used=0,
                        cached=True,
                    )
                    if on_log:
                        on_log(log)
                    return reviews, log

        goal_prompt = (
            f"Open this {platform} URL: {url}. "
            f"Stay strictly on {platform}. If a cookie/consent or login popup appears, dismiss/close it. "
            f"Find the visible customer reviews or patient stories on the page. "
            f"Extract up to {max_reviews} customer reviews with author, rating (1 to 5; if 'I recommend the doctor' "
            f"is shown with no star number, use 5), posted_at, full review text, and owner_reply_text if present. "
            f"Do NOT log in. Submit immediately once you have extracted the visible reviews."
        )

        t0 = time.time()
        steps_logged = 0
        final_result = None
        complete_error = None

        try:
            with self.sdk.agent.stream(
                goal=goal_prompt,
                url=url,
                output_schema=AGENT_REVIEW_SCHEMA,
                browser_profile="stealth",
            ) as stream:
                for event in stream:
                    if isinstance(event, ProgressEvent):
                        steps_logged += 1
                        purpose = getattr(event, "purpose", None) or getattr(event, "message", "Working...")
                        if on_step:
                            on_step(steps_logged, str(purpose))
                    elif isinstance(event, CompleteEvent):
                        final_result = getattr(event, "result_json", None) or getattr(event, "result", None)
                        if not final_result:
                            complete_error = str(event)

            duration_ms = int((time.time() - t0) * 1000)

            if isinstance(final_result, str):
                try:
                    import json
                    final_result = json.loads(final_result)
                except Exception:
                    pass

            if isinstance(final_result, dict):
                reviews = final_result.get("reviews", [])
            elif isinstance(final_result, list):
                reviews = final_result
            else:
                reviews = []

            if reviews:
                write_cache(
                    "agent",
                    cache_key,
                    {"reviews": reviews},
                    meta={"steps_used": steps_logged, "duration_ms": duration_ms},
                )

            log = TinyFishCallLog(
                endpoint="agent",
                input=url,
                status="ok" if reviews else "failed",
                duration_ms=duration_ms,
                items_returned=len(reviews),
                steps_used=steps_logged,
                cached=False,
                error_message=complete_error if not reviews else None,
            )
            if on_log:
                on_log(log)
            return reviews, log

        except Exception as e:
            duration_ms = int((time.time() - t0) * 1000)
            log = TinyFishCallLog(
                endpoint="agent",
                input=url,
                status="failed",
                duration_ms=duration_ms,
                items_returned=0,
                steps_used=steps_logged,
                cached=False,
                error_message=str(e),
            )
            if on_log:
                on_log(log)
            return [], log