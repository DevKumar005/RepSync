import sys
from pathlib import Path

# Ensure backend/ is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.ingestion.collector import collect, discover_outlet_platforms
from app.services.ingestion.schemas import CandidatePlatformUrl, TinyFishCallLog


def print_live_log(log: TinyFishCallLog):
    step_info = f" | steps={log.steps_used}" if log.steps_used is not None else ""
    print(
        f"  [TINYFISH LOG] {log.endpoint.upper():6s} | status={log.status:6s} | "
        f"{log.duration_ms:6d}ms | items={log.items_returned}{step_info} | input={log.input[:65]}"
    )


def main():
    print("=== 1. Testing Outlet Discovery with Domain Allowlist ===")
    candidates, _ = discover_outlet_platforms(
        name="Bukhara ITC Maurya",
        city="Delhi",
        category="restaurant",
        on_log=print_live_log,
    )
    for c in candidates:
        print(f"  -> Matched [{c.platform}]: {c.url} ({c.title[:50]})")

    print("\n=== 2. Testing Full collect(outlet) Pipeline on Zomato ===")
    zomato_only = [c for c in candidates if c.platform == "Zomato"]
    if not zomato_only:
        zomato_only = [
            CandidatePlatformUrl(
                platform="Zomato",
                url="https://www.zomato.com/ncr/bukhara-itc-maurya-chanakyapuri-new-delhi/reviews",
            )
        ]

    result = collect(
        outlet_name="Bukhara ITC Maurya",
        city="Delhi",
        category="restaurant",
        platform_urls=zomato_only,
        use_cache=True,
        on_log=print_live_log,
        on_step=lambda step, msg: print(f"    [Agent Step {step}] {msg}"),
    )

    print("\n=== 3. Collection Result Summary ===")
    print(f"Outlet: {result.outlet_name} ({result.city})")
    print(f"Total Reviews Collected (Deduped): {len(result.reviews)}")
    print(f"Total New Agent Steps Used: {result.total_steps_used}")
    for s in result.sources:
        print(f"Source [{s.platform}]: status={s.status}, count={s.reviews_collected}")

    print("\nSample Normalized Reviews (first 3):")
    for r in result.reviews[:3]:
        print(f"  - [{r.rating}★] {r.author} ({r.posted_at}) [hash={r.dedup_hash[:10]}...]: {r.text[:90]}")


if __name__ == "__main__":
    main()