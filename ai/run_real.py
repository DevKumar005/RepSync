import time
from llm_client import LLMClient
from schemas import ReviewAnalysis
from loader import load_reviews
from analysis import build_themes, suggest_fixes

PROMPT_VERSION = "v2"
MIN_NEGATIVES_FOR_THEMES = 5

# My guesses for the right answers. Check them and change any you disagree with.
MY_LABELS = {
    "G001": "positive", "G002": "positive", "G003": "positive",
    "G004": "negative", "G005": "positive", "G006": "positive",
    "G007": "negative", "G008": "positive", "G009": "positive",
    "G010": "positive",
}

client = LLMClient()
template = open(f"prompts/{PROMPT_VERSION}/analysis.txt", encoding="utf-8").read()
reviews = load_reviews("data/real/bukhara.json")

correct = 0
negatives = []
for r in reviews:
    prompt = template.replace("{rating}", str(r["rating"])).replace("{text}", r["text"])
    try:
        a = client.generate_json(prompt, ReviewAnalysis)["data"]
    except Exception as e:
        print(f"ERROR {r['id']}: {str(e)[:60]}")
        continue

    r["sentiment"] = a.sentiment
    r["topics"] = ", ".join(a.topics)
    mine = MY_LABELS.get(r["id"])
    ok = (mine == a.sentiment)
    correct += ok
    print(f'{"OK " if ok else "XX "}{r["id"]} {r["rating"]}★ yours={mine} ai={a.sentiment} '
          f'sev={a.severity} | {r["topics"] or "-"} | {r["text"][:45]}')
    if a.sentiment == "negative":
        negatives.append({"id": r["id"], "text": r["text"], "topics": r["topics"]})
    time.sleep(1)

print(f"\nSentiment on real reviews: {correct}/{len(reviews)}")
print(f"Negative reviews found: {len(negatives)}")

if len(negatives) < MIN_NEGATIVES_FOR_THEMES:
    print("Too few negative reviews to find a pattern. We need more reviews from M1.")
else:
    result = build_themes(client, negatives)
    fixes = suggest_fixes(client, result, business_type="fine-dining Indian restaurant")
    for fx in fixes:
        print(f"{fx['rank']}. {fx['title']} ({fx['evidence_count']} of {fx['total']}, {fx['strength']})")
        print(f"   {fx['rationale']}")