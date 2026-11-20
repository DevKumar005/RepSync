"""Parse review `posted_at` values: ISO strings, datetimes, or relative text like "6 days ago"."""
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Union

_NUMBER_WORDS = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
}
_UNIT_DAYS = {
    "second": 1 / 86400, "sec": 1 / 86400, "minute": 1 / 1440, "min": 1 / 1440, "hour": 1 / 24, "hr": 1 / 24,
    "day": 1, "din": 1, "week": 7, "hafte": 7, "hafta": 7, "month": 30, "mahine": 30, "mahina": 30,
    "year": 365, "saal": 365,
}
_RELATIVE = re.compile(
    r"^(?P<n>\d+|" + "|".join(_NUMBER_WORDS) + r")\s+"
    r"(?P<unit>second|sec|minute|min|hour|hr|day|week|month|year|din|hafte|hafta|mahine|mahina|saal)s?"
    r"\s+(?:ago|pehle|before)$"
)
_ABSOLUTE_FORMATS = ("%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y", "%d/%m/%Y", "%d-%m-%Y")


def _aware(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def parse_posted_at(
    value: Union[str, datetime, None], collected_at: Optional[datetime] = None
) -> Optional[datetime]:
    """Returns a UTC datetime, or None when the value cannot be understood.

    Relative text is resolved against `collected_at` (when the review was scraped), else now.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return _aware(value)

    base = _aware(collected_at) if collected_at else datetime.now(timezone.utc)
    text = " ".join(str(value).strip().lower().replace("edited", "").split())
    if not text:
        return None

    try:
        return _aware(datetime.fromisoformat(text.upper().replace("Z", "+00:00")))
    except ValueError:
        pass
    for fmt in _ABSOLUTE_FORMATS:
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    if text in {"just now", "now", "today", "moments ago", "a moment ago"}:
        return base
    if text in {"yesterday", "kal"}:
        return base - timedelta(days=1)
    m = re.match(r"^last (week|month|year)$", text)
    if m:
        return base - timedelta(days=_UNIT_DAYS[m.group(1)])

    m = _RELATIVE.match(text)
    if m:
        raw_n = m.group("n")
        n = int(raw_n) if raw_n.isdigit() else _NUMBER_WORDS[raw_n]
        return base - timedelta(days=n * _UNIT_DAYS[m.group("unit")])
    return None
