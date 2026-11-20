"""Reviews-per-week series and a simple drop warning, computed from collected review dates."""
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Sequence

WEEKS = 12
RECENT_WEEKS = 2
PRIOR_WEEKS = 4
DROP_THRESHOLD = 0.30
MIN_PRIOR_REVIEWS = 8    # below this the prior window is too small to call a trend


def weekly_counts(dates: Sequence[Optional[datetime]], now: datetime, weeks: int = WEEKS) -> List[int]:
    """Counts per week, oldest first. Week i covers (now - (weeks-i)*7d, now - (weeks-i-1)*7d]."""
    counts = [0] * weeks
    for d in dates:
        if d is None:
            continue
        age_days = (now - d).total_seconds() / 86400
        if age_days < 0:
            age_days = 0
        idx = weeks - 1 - int(age_days // 7)
        if 0 <= idx < weeks:
            counts[idx] += 1
    return counts


def trend(counts: List[int]) -> dict:
    recent = counts[-RECENT_WEEKS:]
    prior = counts[-(RECENT_WEEKS + PRIOR_WEEKS):-RECENT_WEEKS]
    recent_avg = round(sum(recent) / RECENT_WEEKS, 2)
    prior_avg = round(sum(prior) / PRIOR_WEEKS, 2)
    if sum(prior) < MIN_PRIOR_REVIEWS:
        return {"status": "insufficient_data", "recent_avg": recent_avg, "prior_avg": prior_avg, "change_pct": None}
    change_pct = round(100 * (recent_avg - prior_avg) / prior_avg)
    status = "warning" if (prior_avg - recent_avg) / prior_avg >= DROP_THRESHOLD else "ok"
    return {"status": status, "recent_avg": recent_avg, "prior_avg": prior_avg, "change_pct": change_pct}


def build_series(key: str, name: str, dates: Sequence[Optional[datetime]], now: datetime) -> dict:
    counts = weekly_counts(dates, now)
    known = [d for d in dates if d is not None]
    series = {"key": key, "name": name, "counts": counts, "sample_size": len(known), "trend": trend(counts)}
    # Some collectors stamp every review with the scrape time; a single-day spread is not a real trend
    if len(known) >= 5 and (max(known) - min(known)) < timedelta(days=1):
        series["trend"] = {**series["trend"], "status": "insufficient_data", "change_pct": None}
        series["dates_note"] = "Review dates were not available from the source, so they all show the collection day."
    return series


SAMPLE_NOTE = (
    "Counts come from the reviews RepSync collected (up to 50 per platform), not the total number of reviews. "
    "Relative dates like \"one month ago\" are approximate."
)


def week_labels(now: datetime, weeks: int = WEEKS) -> List[str]:
    return [(now - timedelta(days=7 * (weeks - i))).date().isoformat() for i in range(weeks)]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
