import csv
from llm_client import LLMClient
from replies import draft_reply
from loader import load_reviews

client = LLMClient()

# Placeholder business names, because the synthetic reviews don't have any
OUTLETS = {
    "restaurant": {"name": "Spice Garden", "category": "restaurant"},
    "clinic": {"name": "CityCare Clinic", "category": "clinic"},
    "salon": {"name": "Glow Salon", "category": "salon"},
}
tone = {"style": "warm", "do_not_say": [],
        "contact": "invite them to call or message us directly on the number listed on our profile."}

with open("data/eval/labelled_reviews.csv", encoding="utf-8-sig") as f:
    synthetic = {r["id"]: r for r in csv.DictReader(f)}
real = {r["id"]: r for r in load_reviews("data/real/bukhara.json")}

cases = []
for rid in ["R01", "R05", "C11", "C18", "S24"]:
    r = synthetic[rid]
    cases.append((rid, r["text"], int(r["rating"]), r["language"], OUTLETS[r["category"]]))
for rid in ["G004", "G007"]:
    r = real[rid]
    cases.append((rid, r["text"], r["rating"], "english",
                  {"name": "Bukhara", "category": "restaurant"}))

for rid, text, rating, lang, outlet in cases:
    review = {"text": text, "rating": rating, "platform": "Google", "language": lang}
    d = draft_reply(client, review, outlet, tone)
    print(f"--- {rid} ({outlet['category']}, {lang}, {rating}★)")
    print(f"REVIEW: {text[:100]}")
    print(f"REPLY:  {d['text']}")
    print(f"        {len(d['text'].split())} words | attempts={d['attempts']} | "
          f"flags={d['guardrail_flags'] or 'none'} | {d['provider']}\n")