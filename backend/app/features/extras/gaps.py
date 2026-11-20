"""Competitor gap matrix: per-theme complaint rates computed in code. No LLM numbers."""
from typing import Dict, List, Optional

MIN_TOTAL_MENTIONS = 3   # skip themes mentioned fewer times than this across all outlets
MIN_GAP_PP = 10.0        # percentage-point difference that counts as "clearly" better/worse
MIN_SIDE_COUNT = 2       # the worse side needs at least this many mentions


def _rate(count: int, n: int) -> Optional[float]:
    return round(100.0 * count / n, 1) if n else None


def compute_gap_matrix(outlets: List[dict]) -> List[dict]:
    """outlets: [{"key": "you" | "A" ..., "name": str, "topics": [[topic, ...] per analysed review]}].

    The first outlet must be the owner's ("you"). Returns rows sorted by gap size, largest first.
    """
    sizes = {o["key"]: len(o["topics"]) for o in outlets}
    counts: Dict[str, Dict[str, int]] = {o["key"]: {} for o in outlets}
    for o in outlets:
        for review_topics in o["topics"]:
            for t in set(review_topics):
                counts[o["key"]][t] = counts[o["key"]].get(t, 0) + 1

    themes = sorted({t for c in counts.values() for t in c})
    rows = []
    for theme in themes:
        total = sum(counts[o["key"]].get(theme, 0) for o in outlets)
        if total < MIN_TOTAL_MENTIONS:
            continue
        cells = [
            {
                "key": o["key"],
                "name": o["name"],
                "count": counts[o["key"]].get(theme, 0),
                "n": sizes[o["key"]],
                "rate": _rate(counts[o["key"]].get(theme, 0), sizes[o["key"]]),
            }
            for o in outlets
        ]
        you_cell = cells[0]
        status, gap_pp, versus = "parity", 0.0, None
        if you_cell["rate"] is not None:
            # Threat: a competitor handles this clearly better than you
            best = None
            for c in cells[1:]:
                if c["rate"] is None:
                    continue
                diff = you_cell["rate"] - c["rate"]
                if diff >= MIN_GAP_PP and you_cell["count"] >= MIN_SIDE_COUNT and (best is None or diff > best[0]):
                    best = (diff, c)
            if best:
                status, gap_pp, versus = "threat", round(best[0], 1), best[1]
            else:
                # Opportunity: a competitor is clearly worse than you
                for c in cells[1:]:
                    if c["rate"] is None:
                        continue
                    diff = c["rate"] - you_cell["rate"]
                    if diff >= MIN_GAP_PP and c["count"] >= MIN_SIDE_COUNT and diff > gap_pp:
                        status, gap_pp, versus = "opportunity", round(diff, 1), c
        rows.append({
            "theme": theme,
            "total_mentions": total,
            "cells": cells,
            "status": status,
            "gap_pp": gap_pp,
            "versus_key": versus["key"] if versus else None,
            "versus_name": versus["name"] if versus else None,
        })

    order = {"threat": 0, "opportunity": 1, "parity": 2}
    rows.sort(key=lambda r: (order[r["status"]], -r["gap_pp"], -r["total_mentions"]))
    return rows


def top_gaps(rows: List[dict], limit: int = 3) -> List[dict]:
    return [r for r in rows if r["status"] != "parity"][:limit]
