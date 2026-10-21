import csv
from llm_client import LLMClient
from analysis import build_themes, suggest_fixes

client = LLMClient()

with open("data/eval/results_v1.csv", encoding="utf-8-sig") as f:
    negatives = [{"id": r["id"], "text": r["text"], "topics": r["ai_topics"]}
                 for r in csv.DictReader(f) if r["ai_sentiment"] == "negative"]

result = build_themes(client, negatives)
fixes = suggest_fixes(client, result,
                      business_type="mixed test data: restaurants, clinics and salons")

print(f"\nTOP {len(fixes)} FIXES  (themes from {result['provider']})\n")
for fx in fixes:
    print(f"{fx['rank']}. {fx['title']}")
    print(f"   {fx['rationale']}")
    print(f"   Evidence: main complaint in {fx['evidence_count']} of {fx['total']} negative reviews ({fx['theme']}), {fx['strength']}\n")