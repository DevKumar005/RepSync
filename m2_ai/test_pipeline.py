import csv
import json
import os
from llm_client import LLMClient
from loader import load_reviews
from pipeline import detect_language
from pipeline import run_pipeline

os.makedirs("data/output", exist_ok=True)
tone = {"style": "warm",
        "contact": "invite them to call or message us directly on the number listed on our profile."}

# print(detect_language("", "hindi"))              # hinglish
# print(detect_language("रिसेप्शन का व्यवहार खराब था", "hinglish"))       # hindi
# print(detect_language("Food was good", "english"))  

def run(name, reviews, outlet):
    client = LLMClient()
    result = run_pipeline(client, reviews, outlet, tone, on_progress=lambda m: print("  >", m))
    path = f"data/output/pipeline_{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n{name}: saved to {path}")
    print("Summary:", result["summary"])
    print("Fixes:", [(f["title"], f["evidence_count"]) for f in result["fixes"]])
    print("Drafts:", len(result["drafts"]),
          "| with safety flags:", sum(1 for d in result["drafts"] if d["guardrail_flags"]))
    print("Usage:", result["usage"], "\n")


# 1. Real reviews (few negatives, so themes and fixes are skipped)
run("bukhara", load_reviews("data/real/bukhara.json"), {"name": "Bukhara", "category": "restaurant"})

# 2. Synthetic reviews (many negatives, runs the full pipeline)
with open("data/eval/labelled_reviews.csv", encoding="utf-8-sig") as f:
    synthetic = [{"id": r["id"], "platform": "google_maps", "rating": int(r["rating"]),
                  "text": r["text"], "has_owner_reply": False} for r in csv.DictReader(f)]
run("synthetic", synthetic, {"name": "Test Outlet", "category": "restaurant"})