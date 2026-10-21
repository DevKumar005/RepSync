import csv
import time
from collections import defaultdict
from llm_client import LLMClient
from schemas import ReviewAnalysis
from pipeline import detect_language

PROMPT_VERSION = "v2"
client = LLMClient()
template = open(f"prompts/{PROMPT_VERSION}/analysis.txt", encoding="utf-8").read()

# 1. Read your labelled reviews
with open("data/eval/labelled_reviews.csv", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

results = []
correct = 0
by_language = defaultdict(lambda: [0, 0])  # language -> [correct, total]
topic_correct = 0
topic_total = 0
lang_correct = 0

# 2. Run the AI on each review
for row in rows:
    prompt = template.replace("{rating}", row["rating"]).replace("{text}", row["text"])
    try:
        out = client.generate_json(prompt, ReviewAnalysis)
        predicted = out["data"].sentiment
        lang = detect_language(row["text"], out["data"].language)
        topic_list = out["data"].topics
        topics = ", ".join(topic_list)
    except Exception as e:
        predicted = "ERROR"
        topic_list = []
        lang = "ERROR"
        topics = str(e)[:60]

    is_correct = predicted == row["sentiment"]
    lang_correct += (lang == row["language"])
    if row["theme"]:                      # only reviews where you labelled a theme
        topic_total += 1
        if row["theme"] in topic_list:
            topic_correct += 1
    correct += is_correct
    by_language[row["language"]][1] += 1
    by_language[row["language"]][0] += is_correct

    mark = "OK " if is_correct else "XX "
    print(f"{mark}{row['id']}  yours={row['sentiment']:<9} ai={predicted:<9} {topics}")

    results.append({**row, "ai_sentiment": predicted, "ai_topics": topics,
                    "correct": is_correct})
    time.sleep(1)  # small pause so free-tier rate limits don't bite

# 3. Print the score
total = len(rows)
print("\n=========== RESULTS ===========")
print(f"Prompt version: {PROMPT_VERSION}")
print(f"Sentiment accuracy: {correct}/{total} = {correct / total:.0%}  (target: 85%+)")
print(f"Topic match: {topic_correct}/{topic_total} = {topic_correct / topic_total:.0%}")
print(f"Language accuracy: {lang_correct}/{total} = {lang_correct / total:.0%}")
for lang, (c, t) in by_language.items():
    print(f"  {lang:<9} {c}/{t}")

print("\nWrong answers:")
for r in results:
    if not r["correct"]:
        print(f"  {r['id']}: yours={r['sentiment']}, ai={r['ai_sentiment']} | {r['text'][:70]}")

# 4. Save everything so you can compare versions later
out_path = f"data/eval/results_{PROMPT_VERSION}.csv"
with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)
print(f"\nSaved to {out_path}")