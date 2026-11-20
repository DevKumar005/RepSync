"""Builds the offline sample fixtures in data/demo/ for the extras features.

Run: python -m backend.app.features.extras.build_fixtures
All outlets and reviews here are fictional sample data (no reviewer names). Topics are
pre-computed with the keyword tagger so the demo works with the network off.
"""
import json
from pathlib import Path

from backend.app.features.extras.topics import keyword_topics

ROOT_DIR = Path(__file__).resolve().parents[4]
DEMO_DIR = ROOT_DIR / "data" / "demo"

R_POSITIVE = [
    "Butter chicken was rich and the naan came out hot. Quick service too.",
    "Food arrived within ten minutes even on a Friday night. Loved the dal.",
    "Paneer tikka was smoky and fresh. Staff were polite.",
    "खाना बहुत स्वादिष्ट था, सर्विस भी जल्दी मिली।",
    "Ekdum mast chole bhature, service bhi fast thi.",
    "Great value thali, generous portions.",
    "Family dinner went smoothly, kids loved the kulfi.",
    "Biryani was fragrant and well cooked. Will come back.",
    "Clean place, friendly waiter, food on time.",
    "Bahut accha khana, staff bhi friendly hai.",
    "Best rajma chawal in the area, quick and tasty.",
    "Tandoori platter was perfectly charred. Good music.",
    "Ordered for office lunch, packed neatly and delivered hot.",
    "Lassi was thick and fresh. Nice seating outside.",
    "Paneer butter masala was creamy, rotis soft.",
    "Polite staff and quick billing. Good experience.",
    "स्टाफ बहुत अच्छा था और खाना गरम मिला।",
    "Value for money, will recommend to friends.",
    "Malai kofta was delicious. Service was prompt.",
    "Nice ambience, dal makhani was the highlight.",
]
R_COMPLAINTS = {
    "hygiene": [
        "Table was dirty and there were flies near the counter.",
        "Washroom had a bad smell, not hygienic at all.",
        "Found a hair in the curry and the plates looked unclean.",
        "Kitchen area looked dirty from the window. Not coming back.",
        "टेबल पर गंदगी थी, किसी ने साफ नहीं किया।",
        "Cutlery was unclean and the floor was sticky.",
    ],
    "overpriced": [
        "Too expensive for such small portions.",
        "Overpriced thali for very average food.",
        "Hidden service charge added to the bill without asking.",
        "Bahut mehnga hai, quantity bhi kam.",
        "Costly drinks and the bill had extra charges.",
        "Prices are way too high for what you get. Overpriced.",
    ],
    "rude staff": [
        "Waiter was rude when we asked for water twice.",
        "Manager shouted at the staff in front of guests, very unprofessional.",
        "Staff was arrogant and did not care about our order.",
        "Badtameez staff, bilkul respect nahi.",
    ],
    "slow service": [
        "Waited 40 minutes for the main course.",
        "Very slow service, we had to remind them three times.",
        "Bill was delayed by 20 minutes on a weekday.",
        "Bahut der lagi khana aane mein.",
    ],
    "food quality": [
        "Dal was bland and the rotis were stale.",
        "Paneer was undercooked and the gravy was oily.",
        "Biryani was cold and tasteless.",
        "खाना ठंडा और बेस्वाद था।",
    ],
    "poor management": [
        "Too crowded, no seating even at lunch time.",
        "Total chaos at the counter on Sunday, orders mixed up.",
        "Booking was not honoured, overcrowded waiting area.",
        "Cramped seating, could not move between tables.",
    ],
}

C_POSITIVE = [
    "Painless root canal, the doctor explained every step.",
    "Clean clinic and on-time appointment.",
    "Doctor was gentle with my kid, very patient.",
    "डॉक्टर ने बहुत अच्छे से समझाया, इलाज बढ़िया था।",
    "Scaling done quickly, no pain at all.",
    "Reception staff were helpful with insurance papers.",
    "Braces consultation was detailed and honest.",
    "Doctor sahab bahut acche hain, dard bilkul nahi hua.",
    "Modern equipment and very hygienic setup.",
    "Got an appointment the same day, great service.",
    "Filling done perfectly, no sensitivity after.",
    "Transparent pricing explained before treatment.",
    "Friendly team, clean waiting area.",
    "Wisdom tooth extraction went smoothly.",
    "Very professional and punctual.",
    "Teeth whitening results are great.",
]
C_COMPLAINTS = {
    "doctor behaviour": [
        "Doctor was rushed and did not listen to my problem.",
        "Doctor barely examined me and wrote a prescription.",
        "Didn't listen to my concerns, the doctor rushed through the check-up.",
        "The doctor was rushing between patients.",
    ],
    "overpriced": [
        "Charges were much higher than quoted on the phone.",
        "Very expensive for a simple cleaning.",
        "Hidden charges for the X-ray added later.",
        "Bahut mehnga hai, normal filling ke liye bhi.",
        "Overpriced treatment, got the same done elsewhere for half.",
        "Costly consultation fee and extra charges for everything.",
        "Expensive, and they push unnecessary treatments.",
    ],
    "hygiene": [
        "Instruments did not look clean, waiting room was dirty.",
        "Washroom was dirty and had a bad smell.",
        "Unhygienic chair, the staff did not change the cover.",
    ],
    "slow service": [
        "Waited an hour past my appointment time.",
        "Appointment was delayed by 40 minutes with no update.",
    ],
    "poor quality work": [
        "Filling fell out within two weeks.",
        "Pain persisted after the root canal, had to redo it.",
    ],
}


def _posted(days: int) -> str:
    """Relative text the way review sites show it."""
    if days == 0:
        return "10 hours ago"
    if days == 1:
        return "yesterday"
    if days == 7:
        return "a week ago"
    if days == 30:
        return "one month ago"
    if days == 60:
        return "2 months ago"
    return f"{days} days ago"


def _competitor(name: str, area: str, complaints: list, positives: list, day_offsets: list, seed: int) -> dict:
    """complaints: [(text, rating)] placed at the start of the timeline mix; positives fill the rest."""
    items = list(complaints)
    pi = seed
    while len(items) < len(day_offsets):
        items.append((positives[pi % len(positives)], 5.0 if pi % 3 else 4.0))
        pi += 1
    # Spread complaints through the timeline instead of clustering them
    items = items[::2] + items[1::2]
    reviews = []
    for (text, rating), days in zip(items, day_offsets):
        reviews.append({
            "text": text,
            "rating": rating,
            "posted_at": _posted(days),
            "topics": keyword_topics(text, rating),
        })
    return {"name": name, "area": area, "reviews": reviews}


def _days(weekly: list) -> list:
    """weekly: review counts per week, newest week first. Returns day offsets."""
    out = []
    for week, n in enumerate(weekly):
        for i in range(n):
            out.append(week * 7 + (i * 7) // max(n, 1))
    return out


def _pick(pool: dict, topic: str, k: int, rating: float = 2.0) -> list:
    return [(t, rating if i % 2 else rating - 1) for i, t in enumerate(pool[topic][:k])]


def build_restaurant() -> dict:
    return {
        "source": "sample",
        "note": "Simulated competitor reviews for the demo. Outlets and reviews are fictional.",
        "category": "restaurant",
        "locality": "Connaught Place, New Delhi",
        "collected_at": None,
        "competitors": [
            _competitor(
                "Tandoor Junction (sample)", "Janpath, New Delhi",
                _pick(R_COMPLAINTS, "hygiene", 5) + _pick(R_COMPLAINTS, "food quality", 1) + _pick(R_COMPLAINTS, "slow service", 1),
                R_POSITIVE, _days([2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]), seed=0,
            ),
            _competitor(
                "Masala Lane (sample)", "Barakhamba Road, New Delhi",
                _pick(R_COMPLAINTS, "overpriced", 6) + _pick(R_COMPLAINTS, "rude staff", 3) + _pick(R_COMPLAINTS, "slow service", 2, 3.0),
                R_POSITIVE, _days([0, 1, 3, 3, 3, 3, 2, 2, 2, 1, 1, 1]), seed=5,
            ),
            _competitor(
                "Hari Bhari Rasoi (sample)", "Gole Market, New Delhi",
                _pick(R_COMPLAINTS, "poor management", 4) + _pick(R_COMPLAINTS, "food quality", 2, 3.0) + [(R_COMPLAINTS["slow service"][3], 2.0)],
                R_POSITIVE, _days([4, 3, 3, 2, 2, 2, 1, 1, 1, 1, 0, 0]), seed=11,
            ),
        ],
    }


def build_clinic() -> dict:
    return {
        "source": "sample",
        "note": "Simulated competitor reviews for the demo. Clinics and reviews are fictional.",
        "category": "clinic",
        "locality": "Bandra West, Mumbai",
        "collected_at": None,
        "competitors": [
            _competitor(
                "Smile Care Dental (sample)", "Linking Road, Mumbai",
                _pick(C_COMPLAINTS, "doctor behaviour", 4) + _pick(C_COMPLAINTS, "poor quality work", 1),
                C_POSITIVE, _days([2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1]), seed=0,
            ),
            _competitor(
                "PearlBright Clinic (sample)", "Hill Road, Mumbai",
                _pick(C_COMPLAINTS, "overpriced", 7) + _pick(C_COMPLAINTS, "hygiene", 3),
                C_POSITIVE, _days([0, 1, 2, 2, 3, 2, 2, 2, 1, 1, 1, 1]), seed=4,
            ),
            _competitor(
                "CityCare Dental (sample)", "Khar West, Mumbai",
                _pick(C_COMPLAINTS, "slow service", 2) + _pick(C_COMPLAINTS, "poor quality work", 1, 3.0),
                C_POSITIVE, _days([3, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 0]), seed=9,
            ),
        ],
    }


# Reviews of the frontend mock outlet (src/api/mock.ts, "Sharma's Kitchen"), newest first
MOCK_OWNER_REVIEWS = [
    ("Waited 50 minutes for butter chicken and it came cold. Staff just shrugged when we asked.", 1.0),
    ("Khana theek tha par service bahut slow hai, 45 min lag gaye order aane me.", 2.0),
    ("Great paneer tikka and quick seating on a Sunday.", 5.0),
    ("Bill me extra service charge add kar diya bina bataye. Not okay.", 1.0),
    ("Good food, a bit loud inside.", 4.0),
    ("Washroom was dirty and the waiter was rude when we mentioned it.", 2.0),
    ("Best dal makhani in Lajpat Nagar!", 5.0),
    ("Average. Nothing special but fine for a quick lunch.", 3.0),
]
FRONTEND_MOCK = ROOT_DIR / "src" / "features" / "extras" / "mockData.ts"


def build_frontend_mock() -> dict:
    """Pre-computed responses for the frontend's offline mock mode (VITE_USE_MOCK)."""
    from datetime import datetime, timedelta, timezone

    from backend.app.features.extras.competitors import build_result
    from backend.app.features.extras.velocity import build_series

    now = datetime.now(timezone.utc)
    owner = [
        {"text": t, "rating": r, "posted_at": now - timedelta(days=i * 2 + 1)}
        for i, (t, r) in enumerate(MOCK_OWNER_REVIEWS)
    ]
    fixture = build_restaurant()
    comps = [{"key": k, "name": c["name"], "url": None, "reviews": c["reviews"]} for k, c in zip("ABC", fixture["competitors"])]
    info = {"name": "Sharma's Kitchen", "category": "restaurant"}
    result = build_result(info, owner, comps, "sample", now)
    result.pop("dates")
    result["generated_at"] = result["collected_at"] = None

    from backend.app.features.extras.dates import parse_posted_at

    series = [build_series("you", info["name"], [r["posted_at"] for r in owner], now)]
    for c in comps:
        series.append(build_series(c["key"], c["name"], [parse_posted_at(r["posted_at"], now) for r in c["reviews"]], now))
    return {"competitors": result, "velocity_series": series}


def write_frontend_mock() -> None:
    data = build_frontend_mock()
    body = (
        "// Generated by backend/app/features/extras/build_fixtures.py. Do not edit by hand.\n"
        "// Offline sample responses for VITE_USE_MOCK mode. All competitor data is fictional.\n"
        "import type { CityMap, CompetitorResult, VelocitySeries } from './types'\n\n"
        f"export const MOCK_COMPETITORS: CompetitorResult = {json.dumps(data['competitors'], ensure_ascii=False, indent=1)}\n\n"
        f"export const MOCK_VELOCITY_SERIES: VelocitySeries[] = {json.dumps(data['velocity_series'], ensure_ascii=False, indent=1)}\n\n"
        f"export const MOCK_CITY_MAP: CityMap = {(DEMO_DIR / 'city_map.json').read_text(encoding='utf-8').strip()}\n"
    )
    FRONTEND_MOCK.write_text(body, encoding="utf-8")
    print(f"wrote {FRONTEND_MOCK.relative_to(ROOT_DIR)}")


if __name__ == "__main__":
    for key, data in (("restaurant", build_restaurant()), ("clinic", build_clinic())):
        path = DEMO_DIR / f"competitors_{key}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT_DIR)}: " + ", ".join(
            f"{c['name']} ({len(c['reviews'])})" for c in data["competitors"]))
    write_frontend_mock()
