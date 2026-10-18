import sys
from pathlib import Path

# Ensure backend/ is on the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.services.ingestion.collector import collect
from app.tinyfish.spike import check_wallet

def run_stress_test():
    # 5 Real businesses across all 3 supported categories
    targets = [
        ("Karim's Jama Masjid", "Delhi", "restaurant"),
        ("Indian Accent", "New Delhi", "restaurant"),
        ("Apollo Spectra Hospital", "Karol Bagh", "clinic"),
        ("Max Super Speciality Hospital", "Saket", "clinic"),
        ("Geetanjali Salon", "Connaught Place", "salon"),
    ]

    total_agent_steps = 0
    total_businesses = len(targets)

    print("=== Phase 4: Stress Testing & Unit Economics ===")
    check_wallet()

    for name, city, category in targets:
        print(f"\n--- Testing: {name} ({city}) [{category.upper()}] ---")
        
        # We run the live collection pipeline
        result = collect(
            outlet_name=name,
            city=city,
            category=category,
            use_cache=True,
            on_log=lambda log: print(
                f"  [{log.endpoint.upper()}] status={log.status} | "
                f"items={log.items_returned} | steps={log.steps_used or 0} | {log.duration_ms}ms"
            )
        )
        
        steps = result.total_steps_used
        total_agent_steps += steps
        
        print(f"  -> Result: {len(result.reviews)} reviews collected.")
        print(f"  -> Agent Steps Used: {steps}")

    # Calculate average costs based on the $0.016/step estimate[cite: 1]
    avg_steps = total_agent_steps / total_businesses
    avg_cost = avg_steps * 0.016

    print("\n===============================================")
    print("=== Section 11.4: Unit Economics (Measured) ===")
    print("===============================================")
    print(f"Total Agent Steps for 5 outlets : {total_agent_steps}")
    print(f"Average Steps per Outlet        : {avg_steps:.1f}")
    print(f"Average Cost per Outlet         : ${avg_cost:.3f}")
    print("===============================================")
    
    check_wallet()

if __name__ == "__main__":
    run_stress_test()