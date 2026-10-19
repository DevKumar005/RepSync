import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from sqlmodel import Session, select
from backend.app.db import engine, init_db
from backend.app.models.entities import (
    AppUser,
    FixSuggestion,
    Outlet,
    Platform,
    ReplyDraft,
    Review,
    ReviewTheme,
    Source,
    Theme,
    TinyFishCall,
    ToneProfile,
)


def compute_dedup_hash(platform: str, author: str, date_str: str, text: str) -> str:
    norm = f"{platform.lower()}:{(author or '').strip().lower()}:{date_str}:{(text or '')[:100].strip().lower()}"
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


def seed_platforms(session: Session) -> None:
    platforms_data = [
        {
            "key": "google_maps",
            "display_name": "Google Maps",
            "enabled": True,
            "categories": ["restaurant", "clinic", "salon"],
            "review_cap": 50,
        },
        {
            "key": "justdial",
            "display_name": "JustDial",
            "enabled": True,
            "categories": ["salon", "restaurant", "clinic"],
            "review_cap": 50,
        },
        {
            "key": "tripadvisor",
            "display_name": "Tripadvisor",
            "enabled": True,
            "categories": ["restaurant"],
            "review_cap": 50,
        },
        {
            "key": "zomato",
            "display_name": "Zomato",
            "enabled": True,
            "categories": ["restaurant"],
            "review_cap": 50,
        },
        {
            "key": "practo",
            "display_name": "Practo",
            "enabled": True,
            "categories": ["clinic"],
            "review_cap": 50,
        },
    ]

    for p in platforms_data:
        existing = session.exec(select(Platform).where(Platform.key == p["key"])).first()
        if not existing:
            session.add(Platform(**p))
        else:
            existing.categories = p["categories"]
            existing.display_name = p["display_name"]
            existing.enabled = p["enabled"]
            session.add(existing)
    session.commit()
    print("Platforms seeded and updated successfully.")


def seed_demo_user(session: Session) -> AppUser:
    demo_email = "demo@repsync.local"
    user = session.exec(select(AppUser).where(AppUser.email == demo_email)).first()
    if not user:
        user = AppUser(
            id=str(uuid.uuid4()),
            name="Demo Owner",
            email=demo_email,
            password_hash=None,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    print(f"Demo user ready: {user.email} (id: {user.id})")
    return user


def seed_demo_outlets(session: Session, user: AppUser) -> None:
    demo_specs = [
        {
            "name": "Kake Da Dhaba",
            "category": "restaurant",
            "city": "New Delhi",
            "address": "Connaught Place, Outer Circle, New Delhi",
            "platforms": ["google_maps", "zomato", "tripadvisor"],
            "style": "warm",
            "sample_replies": [
                "Thank you so much for dining with us! We look forward to serving you our signature Dal Makhani again soon.",
                "We sincerely apologize for the delay you experienced. Please reach out to us at care@kakedadhaba.in so we can make this right.",
            ],
            "do_not_say": ["not our fault", "we are very busy", "check terms"],
            "themes": [
                ("Authentic Taste & Flavours", "positive", "Customers praise the rich gravy, Dal Makhani, and tandoori rotis."),
                ("Slow Service During Peak Hours", "negative", "Several weekend diners faced a 25-30 minute wait for main course."),
                ("Cramped Seating Space", "negative", "Rush hour seating feels crowded and noisy."),
            ],
            "fixes": [
                (1, "Deploy Weekend Expediter", "Assign a dedicated floor captain between 7 PM - 10 PM to cut order turnaround time by 40%.", 6),
                (2, "Streamline Table Layout", "Re-arrange corner tables to improve aisle space and comfort during high footfall.", 4),
                (3, "Digital Bill Settlement", "Introduce QR code settlement at table to reduce checkout wait time by 5 minutes.", 3),
            ],
            "reviews": [
                ("google_maps", "Aman Verma", 5.0, "Legendary butter chicken and fresh garlic naan. The flavours are unforgettable! Will visit again.", "positive", None, False),
                ("google_maps", "Rohan Gupta", 2.0, "Food was tasty but waited 35 minutes for our order on Saturday night. Staff seemed overwhelmed.", "negative", 2, True),
                ("zomato", "Priya Sharma", 4.0, "Great Mughlai food. Dal makhani is rich and creamy. Slightly crowded ambience.", "positive", None, False),
                ("zomato", "Vikram Malhotra", 1.0, "Terrible service yesterday. Waiter forgot our beverage order twice and bill was delayed.", "negative", 3, False),
                ("tripadvisor", "Sarah Jenkins", 5.0, "Incredible authentic Indian culinary experience! The mutton rogan josh was cooked to perfection.", "positive", None, False),
            ],
        },
        {
            "name": "The White Dental Clinic",
            "category": "clinic",
            "city": "Mumbai",
            "address": "Bandra West, Mumbai",
            "platforms": ["google_maps", "practo", "justdial"],
            "style": "empathetic",
            "sample_replies": [
                "Thank you for trusting us with your dental health! We are glad your visit was painless.",
                "We truly appreciate your feedback regarding wait times. We are refining our appointment slots.",
            ],
            "do_not_say": ["teeth are complex", "not our mistake"],
            "themes": [
                ("Gentle & Painless Care", "positive", "Patients commend the gentle root canal and cleaning procedures."),
                ("Appointment Delay", "negative", "Patients waiting past scheduled appointment slot."),
            ],
            "fixes": [
                (1, "Buffer Slot Scheduling", "Add a 10-minute buffer after complex procedures to keep appointment times on schedule.", 5),
                (2, "SMS Delay Alert", "Send automated WhatsApp/SMS notifications if doctor is running >15 minutes late.", 4),
                (3, "Reception Greeting Protocol", "Standardize reception check-in process to acknowledge arrivals promptly.", 2),
            ],
            "reviews": [
                ("practo", "Dr. Shalini Mehta", 5.0, "Dr. Kapoor was so gentle during my tooth extraction. Absolutely zero pain!", "positive", None, False),
                ("practo", "Rajesh Iyer", 2.0, "Appointment was at 4 PM, got called in at 4:45 PM. Please respect patients' time.", "negative", 2, False),
                ("google_maps", "Sneha Patil", 5.0, "Clean clinic and very professional staff. Highly recommend for children's dental care.", "positive", None, False),
                ("justdial", "Kunal Shah", 2.0, "Charges felt slightly higher than quoted on the phone. Procedure was decent though.", "neutral", 1, False),
            ],
        },
    ]

    for spec in demo_specs:
        existing = session.exec(select(Outlet).where(Outlet.name == spec["name"])).first()
        if existing:
            continue

        tone = ToneProfile(
            user_id=user.id,
            style=spec["style"],
            sample_replies=spec["sample_replies"],
            do_not_say=spec["do_not_say"],
        )
        session.add(tone)
        session.commit()
        session.refresh(tone)

        outlet = Outlet(
            user_id=user.id,
            name=spec["name"],
            category=spec["category"],
            city=spec["city"],
            address=spec["address"],
            tone_profile_id=tone.id,
            is_demo=True,
        )
        session.add(outlet)
        session.commit()
        session.refresh(outlet)

        # Sources
        sources_map = {}
        for plt_key in spec["platforms"]:
            src = Source(
                outlet_id=outlet.id,
                platform=plt_key,
                url=f"https://www.{plt_key}.com/{spec['name'].lower().replace(' ', '-')}",
                status="success",
                review_count=len([r for r in spec["reviews"] if r[0] == plt_key]),
                agent_steps_used=2 if plt_key == "google_maps" else 0,
                last_synced_at=datetime.now(timezone.utc),
            )
            session.add(src)
            session.commit()
            session.refresh(src)
            sources_map[plt_key] = src

        # Themes
        themes_map = {}
        for label, sentiment, desc in spec["themes"]:
            thm = Theme(
                outlet_id=outlet.id,
                label=label,
                sentiment=sentiment,
                description=desc,
            )
            session.add(thm)
            session.commit()
            session.refresh(thm)
            themes_map[label] = thm

        # Fix suggestions
        for rank, title, rationale, ev_count in spec["fixes"]:
            fix = FixSuggestion(
                outlet_id=outlet.id,
                rank=rank,
                title=title,
                rationale=rationale,
                evidence_count=ev_count,
            )
            session.add(fix)
        session.commit()

        # Reviews & Drafts
        for idx, (plt, author, rating, text, sentiment, severity, has_reply) in enumerate(spec["reviews"]):
            src = sources_map.get(plt)
            posted_date = datetime.now(timezone.utc) - timedelta(days=idx * 2 + 1)
            h = compute_dedup_hash(plt, author, posted_date.strftime("%Y-%m-%d"), text)

            rev = Review(
                outlet_id=outlet.id,
                source_id=src.id if src else None,
                platform=plt,
                author=author,
                rating=rating,
                text=text,
                language="en",
                posted_at=posted_date,
                url=src.url if src else None,
                has_owner_reply=has_reply,
                sentiment=sentiment,
                severity=severity,
                hash_for_dedup=h,
            )
            session.add(rev)
            session.commit()
            session.refresh(rev)

            # Link first matching theme
            matched_theme = None
            if sentiment == "positive" and spec["themes"]:
                matched_theme = themes_map.get(spec["themes"][0][0])
            elif sentiment == "negative" and len(spec["themes"]) > 1:
                matched_theme = themes_map.get(spec["themes"][1][0])

            if matched_theme:
                rt = ReviewTheme(review_id=rev.id, theme_id=matched_theme.id, confidence=0.92)
                session.add(rt)
                session.commit()

            # Create Reply Draft for negative reviews
            if sentiment == "negative":
                reply_text = (
                    f"Dear {author}, thank you for bringing this to our attention. "
                    f"We deeply regret the delay and inconvenience you experienced. "
                    f"Our management team is actively addressing peak-hour staffing. "
                    f"Please contact us directly so we can make this right on your next visit."
                )
                draft = ReplyDraft(
                    review_id=rev.id,
                    text=reply_text,
                    status="draft",
                    version=1,
                    prompt_version="v2",
                    guardrail_flags=[],
                )
                session.add(draft)
                session.commit()

        # Activity Log / TinyFish Calls
        t_calls = [
            TinyFishCall(
                outlet_id=outlet.id,
                platform="google_maps",
                endpoint="search",
                input={"query": f"{spec['name']} {spec['city']}"},
                status="success",
                duration_ms=420,
                items_returned=1,
                steps_used=0,
                cached=True,
            ),
            TinyFishCall(
                outlet_id=outlet.id,
                platform="google_maps",
                endpoint="fetch",
                input={"url": f"https://maps.google.com/?q={spec['name']}"},
                status="success",
                duration_ms=650,
                items_returned=len(spec["reviews"]),
                steps_used=0,
                cached=True,
            ),
            TinyFishCall(
                outlet_id=outlet.id,
                platform="google_maps",
                endpoint="agent",
                input={"goal": f"Extract more customer reviews for {spec['name']}"},
                status="success",
                duration_ms=1800,
                items_returned=5,
                steps_used=2,
                cached=True,
            ),
        ]
        for tc in t_calls:
            session.add(tc)
        session.commit()

    print("Demo outlets seeded successfully.")


def run_seed() -> None:
    init_db()
    with Session(engine) as session:
        seed_platforms(session)
        user = seed_demo_user(session)
        seed_demo_outlets(session, user)
    print("Database seeding completed.")


if __name__ == "__main__":
    run_seed()
