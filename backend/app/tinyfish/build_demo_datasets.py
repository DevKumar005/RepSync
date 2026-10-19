import asyncio
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_DIR))

from app.services.ingestion.sync_job import DEMO_DIR, load_demo_dataset, stream_outlet_sync
from app.tinyfish.spike import check_wallet


async def build_one_demo(filename: str, name: str, city: str, category: str):
    print(f"\n=======================================================")
    print(f"Building Demo Dataset: {name} ({city}) [{category.upper()}]")
    print(f"=======================================================")

    final_payload = None
    async for sse_event in stream_outlet_sync(
        outlet_name=name,
        city=city,
        category=category,
        use_cache=True,
    ):
        print(f"  [SSE -> {sse_event['type']:13s}] {sse_event['message']}")
        if sse_event["type"] == "done":
            final_payload = sse_event["data"]

    if final_payload:
        out_path = DEMO_DIR / filename
        out_path.write_text(
            json.dumps(final_payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"\n[SAVED] {out_path}")
        print(f"  -> Sources: {[s['platform'] + ':' + s['status'] + '(' + str(s['reviews_collected']) + ')' for s in final_payload['sources']]}")
        print(f"  -> Total Deduplicated Reviews: {len(final_payload['reviews'])}")
        print(f"  -> Total Activity Log Events: {len(final_payload['tinyfish_calls'])}")


async def main():
    check_wallet()

    # Demo Outlet 1: Restaurant (Zomato is already cached = 0 steps; JustDial will run 1 Agent call)
    await build_one_demo(
        filename="demo_restaurant.json",
        name="Bukhara ITC Maurya",
        city="Delhi",
        category="restaurant",
    )

    # Demo Outlet 2: Clinic (Practo + JustDial)
    await build_one_demo(
        filename="demo_clinic.json",
        name="Clove Dental Karol Bagh",
        city="Delhi",
        category="clinic",
    )

    print("\n=== Verifying Offline Demo Loader (< 3s requirement, NFR-1) ===")
    for key in ["restaurant", "clinic"]:
        loaded = load_demo_dataset(key)
        print(
            f"  [OFFLINE LOAD OK] key='{key}' -> {loaded.outlet_name}: "
            f"{len(loaded.reviews)} reviews across {[s.platform for s in loaded.sources]}"
        )

    check_wallet()


if __name__ == "__main__":
    asyncio.run(main())