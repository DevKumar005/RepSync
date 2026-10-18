import hashlib
import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv
import httpx
from tinyfish import TinyFish, CompleteEvent, ProgressEvent

# Load .env from repo root
ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env")

API_KEY = os.getenv("TINYFISH_API_KEY")
CACHE_DIR = ROOT_DIR / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

if not API_KEY or "your-key-here" in API_KEY:
    raise ValueError("Please set your real TINYFISH_API_KEY in the .env file!")

client = TinyFish(api_key=API_KEY)
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}


def get_cache_path(endpoint: str, key: str) -> Path:
    h = hashlib.sha256(f"{endpoint}:{key}".encode()).hexdigest()[:16]
    return CACHE_DIR / f"{endpoint}_{h}.json"


def check_wallet():
    print("=== 1. Checking TinyFish Wallet / Credits ===")
    try:
        wallet = client.wallet.get()
        print(f"Available Balance: {wallet.available_balance} {wallet.currency}")
    except Exception as e:
        print(f"Wallet check note (may be on credit plan): {e}")


def tinyfish_search(query: str) -> dict:
    """Free Search endpoint (30 req/min). Caches results in data/cache/."""
    cache_file = get_cache_path("search", query)
    if cache_file.exists():
        print(f"  [CACHE HIT] Search: '{query}'")
        return json.loads(cache_file.read_text(encoding="utf-8"))

    print(f"  [LIVE CALL] Search: '{query}'")
    t0 = time.time()
    resp = httpx.get(
        "https://api.search.tinyfish.ai",
        params={"query": query},
        headers={"X-API-Key": API_KEY},
        timeout=30.0,
    )
    resp.raise_for_status()
    data = resp.json()
    duration_ms = int((time.time() - t0) * 1000)

    payload = {"query": query, "duration_ms": duration_ms, "data": data}
    cache_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def tinyfish_fetch(url: str) -> dict:
    """Free Fetch endpoint (150 URLs/min). Converts page to clean Markdown."""
    cache_file = get_cache_path("fetch", url)
    if cache_file.exists():
        print(f"  [CACHE HIT] Fetch: {url}")
        return json.loads(cache_file.read_text(encoding="utf-8"))

    print(f"  [LIVE CALL] Fetch: {url}")
    t0 = time.time()
    resp = httpx.post(
        "https://api.fetch.tinyfish.ai",
        headers=HEADERS,
        json={"urls": [url], "format": "markdown"},
        timeout=45.0,
    )
    resp.raise_for_status()
    data = resp.json()
    duration_ms = int((time.time() - t0) * 1000)

    payload = {"url": url, "duration_ms": duration_ms, "data": data}
    cache_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def tinyfish_agent_extract_reviews(url: str, platform: str, max_reviews: int = 10) -> dict:
    """
    Metered Web Agent endpoint (SSE stream).
    Only run when Fetch returns <10 reviews or needs scrolling/JS expansion.
    Cached for 24h so we never waste credits on the same URL twice.
    """
    cache_file = get_cache_path("agent", f"{platform}:{url}")
    if cache_file.exists():
        print(f"  [CACHE HIT] Agent: {url}")
        return json.loads(cache_file.read_text(encoding="utf-8"))

    print(f"  [LIVE AGENT RUN - METERED] {platform} -> {url}")
    goal_prompt = (
        f"Open this {platform} page. Navigate to or scroll the customer reviews section. "
        f"Expand truncated review texts ('Read more' / 'More') if visible. "
        f"Extract up to {max_reviews} real customer reviews. "
        f"Do NOT log in. Stop immediately once you have {max_reviews} reviews."
    )

    output_schema = {
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

    t0 = time.time()
    steps_logged = 0
    final_result = None

    with client.agent.stream(
        goal=goal_prompt,
        url=url,
        output_schema=output_schema,
        browser_profile="stealth",
    ) as stream:
        for event in stream:
            if isinstance(event, ProgressEvent):
                steps_logged += 1
                print(f"    [Agent Step {steps_logged}] { getattr(event, 'message', event) }")
            elif isinstance(event, CompleteEvent):
                final_result = event.result_json

    duration_ms = int((time.time() - t0) * 1000)
    payload = {
        "platform": platform,
        "url": url,
        "steps_used": steps_logged,
        "duration_ms": duration_ms,
        "result": final_result,
    }
    cache_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def run_feasibility_spike():
    check_wallet()

    # 3 Sample Businesses across categories (Restaurant, Clinic, Salon)
    sample_queries = [
        ("Restaurant", "Zomato", "Bukhara ITC Maurya Delhi zomato reviews"),
        ("Restaurant", "Tripadvisor", "Karim's Jama Masjid Delhi tripadvisor reviews"),
        ("Clinic", "Practo", "Clove Dental Connaught Place Delhi practo"),
        ("Salon", "JustDial", "Geetanjali Salon Connaught Place Delhi justdial"),
    ]

    print("\n=== 2. Running Search + Fetch Feasibility Spike (FREE) ===")
    for category, platform, query in sample_queries:
        print(f"\n--- Testing [{category}] on [{platform}] ---")
        try:
            search_res = tinyfish_search(query)
            # Extract first URL from search response
            results_list = (
                search_res["data"].get("results")
                or search_res["data"].get("data")
                or []
            )
            if not results_list:
                print(f"  Search raw keys: {list(search_res['data'].keys())}")
                continue

            top_url = results_list[0].get("url") or results_list[0].get("link")
            print(f"  Found Top URL ({search_res['duration_ms']}ms): {top_url}")

            if top_url:
                fetch_res = tinyfish_fetch(top_url)
                raw_str = json.dumps(fetch_res["data"])
                print(
                    f"  Fetch Response ({fetch_res['duration_ms']}ms): "
                    f"Length = {len(raw_str)} chars"
                )
                print(f"  Snippet: {raw_str[:300]}...\n")
        except Exception as e:
            print(f"  [ERROR] {platform}: {e}")


if __name__ == "__main__":
    run_feasibility_spike()
