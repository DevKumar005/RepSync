import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator, Optional

from app.services.ingestion.collector import collect
from app.services.ingestion.schemas import (
    CandidatePlatformUrl,
    CollectionResult,
    TinyFishCallLog,
)

ROOT_DIR = Path(__file__).resolve().parents[3]
DEMO_DIR = ROOT_DIR / "data" / "demo"
DEMO_DIR.mkdir(parents=True, exist_ok=True)


def make_sse_event(
    event_type: str,
    message: str,
    source: Optional[str] = None,
    status: Optional[str] = None,
    payload: Optional[dict] = None,
) -> dict:
    """
    Matches exact Section 8 SSE contract:
    {type: "source_status"|"tinyfish_call"|"stage"|"done", source?, status?, message, ts}
    """
    evt = {
        "type": event_type,
        "message": message,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    if source is not None:
        evt["source"] = source
    if status is not None:
        evt["status"] = status
    if payload is not None:
        evt["data"] = payload
    return evt


def load_demo_dataset(demo_key: str) -> CollectionResult:
    """
    FR-1.5 / FR-2.7 / NFR-1: Loads pre-cached real TinyFish dataset from data/demo/
    in under 3 seconds with zero external API calls.
    Supported keys: 'restaurant' (or 'bukhara'), 'clinic' (or 'clove').
    """
    key_map = {
        "restaurant": "demo_restaurant.json",
        "bukhara": "demo_restaurant.json",
        "clinic": "demo_clinic.json",
        "clove": "demo_clinic.json",
    }
    filename = key_map.get(demo_key.lower().strip(), f"demo_{demo_key.lower()}.json")
    path = DEMO_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Demo dataset not found at {path}")

    raw = json.loads(path.read_text(encoding="utf-8"))
    return CollectionResult.model_validate(raw)


async def stream_outlet_sync(
    outlet_name: str,
    city: str,
    category: str,
    platform_urls: Optional[list[CandidatePlatformUrl]] = None,
    use_cache: bool = True,
) -> AsyncGenerator[dict, None]:
    """
    Streams live SSE events while running M1's TinyFish ingestion pipeline in a worker thread.
    Falls back automatically to Demo Dataset if live collection fails completely (FR-2.7).
    """
    queue: asyncio.Queue[dict] = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def on_log(log: TinyFishCallLog):
        msg = (
            f"TinyFish {log.endpoint.upper()}: {log.status.upper()} "
            f"({log.items_returned} items, {log.duration_ms}ms)"
        )
        evt = make_sse_event(
            event_type="tinyfish_call",
            status=log.status,
            message=msg,
            payload=log.model_dump(),
        )
        loop.call_soon_threadsafe(queue.put_nowait, evt)

    def on_step(step_num: int, purpose: str):
        evt = make_sse_event(
            event_type="tinyfish_call",
            status="running",
            message=f"TinyFish Agent Step {step_num}: {purpose}",
            payload={"endpoint": "agent", "step": step_num, "purpose": purpose},
        )
        loop.call_soon_threadsafe(queue.put_nowait, evt)

    yield make_sse_event(
        event_type="stage",
        status="running",
        message=f"Starting TinyFish collection for {outlet_name} ({city})...",
    )

    task = asyncio.create_task(
        asyncio.to_thread(
            collect,
            outlet_name=outlet_name,
            city=city,
            category=category,
            platform_urls=platform_urls,
            use_cache=use_cache,
            on_log=on_log,
            on_step=on_step,
        )
    )

    while not task.done():
        try:
            evt = await asyncio.wait_for(queue.get(), timeout=0.25)
            yield evt
        except asyncio.TimeoutError:
            continue

    while not queue.empty():
        yield queue.get_nowait()

    try:
        result: CollectionResult = await task
    except Exception as e:
        # FR-2.7: Automatic fallback to cached demo dataset if live run crashes
        yield make_sse_event(
            event_type="stage",
            status="fallback",
            message=f"Live sync encountered an error ({e}); loading cached fallback dataset...",
        )
        result = load_demo_dataset(category)

    # Emit per-source final statuses (FR-2.6)
    for src in result.sources:
        yield make_sse_event(
            event_type="source_status",
            source=src.platform,
            status=src.status,
            message=f"{src.platform}: {src.status.upper()} ({src.reviews_collected} reviews)",
            payload=src.model_dump(),
        )

    yield make_sse_event(
        event_type="done",
        status="ok",
        message=f"Collection complete: {len(result.reviews)} deduplicated reviews across {len(result.sources)} sources.",
        payload=result.model_dump(),
    )
