from pathlib import Path

try:
    from ai.schemas import ThemeAssignmentResult, FixResult
except ImportError:
    from schemas import ThemeAssignmentResult, FixResult

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def _read_prompt(prompt_version: str, filename: str) -> str:
    path = PROMPTS_DIR / prompt_version / filename
    if not path.exists():
        path = Path(f"prompts/{prompt_version}/{filename}")
    return open(path, encoding="utf-8").read()


def build_themes(client, negatives, prompt_version="v2", min_size=2):
    """negatives: list of dicts with keys id, text, topics (comma-separated string)."""
    with_topics = [r for r in negatives if r["topics"].strip()]
    no_detail = [r["id"] for r in negatives if not r["topics"].strip()]
    by_id = {r["id"]: r for r in with_topics}
    total = len(with_topics)

    template = _read_prompt(prompt_version, "themes.txt")
    lines = [f'{r["id"]} | {r["topics"]}' for r in with_topics]
    out = client.generate_json(template.replace("{reviews}", "\n".join(lines)),
                               ThemeAssignmentResult)
    data = out["data"]
    descriptions = {t.label: t.description for t in data.themes}

    main = {l: [] for l in descriptions}
    also = {l: [] for l in descriptions}
    for a in data.assignments:
        if a.review_id not in by_id:
            continue                                  # ignore invented ids
        if a.primary in main and a.review_id not in main[a.primary]:
            main[a.primary].append(a.review_id)
        if (a.secondary and a.secondary in also and a.secondary != a.primary
                and a.review_id not in also[a.secondary]):
            also[a.secondary].append(a.review_id)
            # Safety net: the AI sometimes forgets a review, so place it using its own topics
        placed_now = {i for ids in main.values() for i in ids}
        label_lookup = {l.lower(): l for l in descriptions}
        for i, r in by_id.items():
            if i in placed_now:
                continue
            for t in r["topics"].split(","):
                label = label_lookup.get(t.strip().lower())
                if label:
                    main[label].append(i)
                    break

    kept = [l for l in descriptions if len(main[l]) + len(also[l]) >= min_size]
    placed = {i for l in kept for i in main[l]}
    leftover = sorted(set(by_id) - placed)

    used, themes = set(), []
    for l in sorted(kept, key=lambda l: (len(main[l]), len(also[l])), reverse=True):
        pool = [by_id[i]["text"] for i in main[l] + also[l] if len(by_id[i]["text"]) >= 25]
        fresh = [q for q in pool if q not in used] or pool
        quotes = sorted(fresh, key=len)[:2]
        used.update(quotes)
        themes.append({"label": l, "description": descriptions[l],
                       "main_ids": main[l], "also_ids": also[l], "quotes": quotes})

    return {"themes": themes, "leftover": leftover, "no_detail": no_detail,
            "total": total, "provider": out["provider"]}


def suggest_fixes(client, result, business_type, prompt_version="v2"):
    total = result["total"]
    top = [t for t in result["themes"] if t["main_ids"]][:3]   # Python picks the top 3
    if not top:
        return []

    blocks = []
    for t in top:
        quotes = " / ".join(f'"{q}"' for q in t["quotes"])
        blocks.append(f'- {t["label"]}: affects {len(t["main_ids"])} of {total} '
                      f'negative reviews. Examples: {quotes}')

    template = _read_prompt(prompt_version, "fixes.txt")
    prompt = (template.replace("{business_type}", business_type)
                      .replace("{themes}", "\n".join(blocks)))
    out = client.generate_json(prompt, FixResult)

    by_label = {t["label"]: t for t in top}
    fixes, seen = [], set()
    for f in out["data"].fixes:
        t = by_label.get(f.theme)
        if not t or f.theme in seen:                  # ignore invented or repeated themes
            continue
        seen.add(f.theme)
        fixes.append({"theme": f.theme, "title": f.title, "rationale": f.rationale,
                "evidence_count": len(t["main_ids"]), "total": total,
                "strength": "strong" if len(t["main_ids"]) >= 3 else "early signal"})

    fixes.sort(key=lambda x: x["evidence_count"], reverse=True)
    for n, fx in enumerate(fixes, 1):
        fx["rank"] = n
    return fixes