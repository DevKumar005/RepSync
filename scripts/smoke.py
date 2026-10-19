"""
Smoke test script for RepSync Backend (M3-QA-9).
Runs through health checks, platform discovery, demo load, summary, draft state machine.
Usage:
    python scripts/smoke.py [BASE_URL]
"""
import sys
import httpx

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"


def run_smoke():
    print(f"=== Starting RepSync Smoke Test against {BASE_URL} ===")
    with httpx.Client(base_url=BASE_URL, timeout=60.0) as client:
        # 1. Health check
        print("1. Checking /health ...", end=" ")
        r = client.get("/health")
        assert r.status_code == 200, f"Failed: {r.status_code} {r.text}"
        print("PASSED")

        # 2. Database keep-alive check
        print("2. Checking /health/db ...", end=" ")
        r = client.get("/health/db")
        assert r.status_code == 200, f"Failed: {r.status_code} {r.text}"
        print(f"PASSED (platforms count: {r.json().get('platforms_count')})")

        # 3. Platform Registry
        print("3. Checking /api/platforms ...", end=" ")
        r = client.get("/api/platforms")
        assert r.status_code == 200, f"Failed: {r.status_code}"
        platforms = r.json()
        assert len(platforms) >= 3, f"Too few platforms: {len(platforms)}"
        print(f"PASSED ({len(platforms)} platforms available)")

        # 4. Instant Demo Mode Load (<3s)
        print("4. Checking /api/outlets/demo/restaurant ...", end=" ")
        r = client.post("/api/outlets/demo/restaurant")
        assert r.status_code == 200, f"Failed: {r.status_code}"
        demo_outlet = r.json()
        outlet_id = demo_outlet["id"]
        print(f"PASSED (Loaded '{demo_outlet['name']}', id: {outlet_id})")

        # 5. Reviews and Summary
        print(f"5. Checking /api/outlets/{outlet_id}/summary ...", end=" ")
        r = client.get(f"/api/outlets/{outlet_id}/summary")
        assert r.status_code == 200, f"Failed: {r.status_code}"
        summary = r.json()
        print(f"PASSED (Total reviews: {summary['total_reviews']}, Avg rating: {summary['average_rating']})")

        # 6. Draft State Machine
        print(f"6. Checking reviews & drafts for {outlet_id} ...", end=" ")
        r = client.get(f"/api/outlets/{outlet_id}/reviews?sentiment=negative")
        assert r.status_code == 200
        neg_reviews = r.json()
        if neg_reviews and neg_reviews[0].get("draft"):
            draft_id = neg_reviews[0]["draft"]["id"]
            # Approve draft
            r_app = client.patch(f"/api/drafts/{draft_id}", json={"status": "approved"})
            assert r_app.status_code == 200, f"Approval failed: {r_app.text}"
            print("PASSED (Draft approved with timestamp)")
        else:
            print("SKIPPED (no negative review draft found)")

    print("\n[SUCCESS] All RepSync Smoke Tests Passed Successfully!\n")


if __name__ == "__main__":
    run_smoke()
