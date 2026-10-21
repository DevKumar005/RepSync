import json


def load_reviews(path, platform="google_maps"):
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    items = raw["reviews"] if isinstance(raw, dict) else raw

    out = []
    for n, r in enumerate(items, 1):
        out.append({
            "id": f"G{n:03d}",
            "platform": r.get("platform") or platform,
            "author": r.get("author") or "",
            "rating": int(round(float(r["rating"]))),
            "text": (r.get("text") or "").strip(),
            "posted_at": r.get("posted_at") or "",
            "url": r.get("url") or "",
            "owner_reply_text": r.get("owner_reply_text") or "",
            "has_owner_reply": bool(r.get("has_owner_reply")),
        })
    # reviews with only stars and no text can't be analysed
    return [r for r in out if r["text"]]