import csv
from llm_client import LLMClient
from schemas import ThemeAssignmentResult

PROMPT_VERSION = "v2"
MIN_THEME_SIZE = 2   # a theme needs at least this many mentions (main + also)

client = LLMClient()
template = open(f"prompts/{PROMPT_VERSION}/themes.txt", encoding="utf-8").read()

with open("data/eval/results_v1.csv", encoding="utf-8-sig") as f:
    negatives = [r for r in csv.DictReader(f) if r["ai_sentiment"] == "negative"]

with_topics = [r for r in negatives if r["ai_topics"].strip()]
no_detail = [r for r in negatives if not r["ai_topics"].strip()]
by_id = {r["id"]: r for r in with_topics}
total = len(with_topics)

lines = [f'{r["id"]} | {r["ai_topics"]}' for r in with_topics]
prompt = template.replace("{reviews}", "\n".join(lines))
out = client.generate_json(prompt, ThemeAssignmentResult)
data = out["data"]
descriptions = {t.label: t.description for t in data.themes}

# Python builds both lists from the assignments
main = {label: [] for label in descriptions}   # main complaint
also = {label: [] for label in descriptions}   # secondary mention
for a in data.assignments:
    if a.review_id not in by_id:
        continue                                # ignore invented ids
    if a.primary in main and a.review_id not in main[a.primary]:
        main[a.primary].append(a.review_id)
    if (a.secondary and a.secondary in also and a.secondary != a.primary
            and a.review_id not in also[a.secondary]):
        also[a.secondary].append(a.review_id)

# Keep themes with enough mentions; everything else goes to "Other issues"
kept = {l: (main[l], also[l]) for l in descriptions
        if len(main[l]) + len(also[l]) >= MIN_THEME_SIZE}
placed = {i for m, _ in kept.values() for i in m}
leftover = sorted(set(by_id) - placed)

print(f"Provider: {out['provider']}   Negative reviews with details: {total}\n")
used_quotes = set()
ordered = sorted(kept.items(), key=lambda x: (len(x[1][0]), len(x[1][1])), reverse=True)
for label, (m, a) in ordered:
    extra = f", +{len(a)} also mention it" if a else ""
    print(f"{label}: {len(m)} main complaints ({len(m) / total:.0%}){extra}")
    print(f"  main: {', '.join(m) or '-'}" + (f"   also: {', '.join(a)}" if a else ""))
    print(f"  {descriptions[label]}")
    pool = [by_id[i]["text"] for i in m + a if len(by_id[i]["text"]) >= 25]
    fresh = [q for q in pool if q not in used_quotes] or pool
    for q in sorted(fresh, key=len)[:2]:
        used_quotes.add(q)
        print(f'  "{q}"')
    print()

if leftover:
    print(f"Other issues: {len(leftover)} main complaint(s) ({len(leftover) / total:.0%})   ids: {', '.join(leftover)}")
if no_detail:
    print(f"{len(no_detail)} negative review(s) with no detail: {[r['id'] for r in no_detail]}")

main_total = sum(len(m) for m, _ in kept.values()) + len(leftover)
print(f"\nCheck: main complaints add up to {main_total} of {total} reviews")