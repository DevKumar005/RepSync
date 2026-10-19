import re
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
PROMPT_VERSION = "v1"
MIN_WORDS, MAX_WORDS = 50, 90      # hard check. The prompt itself asks for 60-80.

BANNED = [
    # English
    "our fault", "our mistake", "we admit", "guarantee", "refund", "money back",
    "compensat", "complimentary", "free meal", "we promise", "cure", "diagnos", "legal",
    "missed the mark", "clearly failed", "we failed", "we were wrong",
    # Hinglish and Hindi
    "hamari galti", "humari galti", "paise wapas",
    "हमारी गलती", "रिफंड", "गारंटी", "मुआवज़ा", "पैसे वापस",
]
CLINIC_WORDS = ["consult", "appointment", "examin", "prescri", "medicine", "medication",
                "treatment", "patient", "dawai", "इलाज", "दवा", "अपॉइंटमेंट", "जांच", "परामर्श"]


def _matcher(phrase):
    if phrase.isascii():
        return re.compile(r"\b" + re.escape(phrase), re.IGNORECASE)
    return re.compile(re.escape(phrase))      # Devanagari: plain match


STYLES = {
    "warm": "warm, friendly and personal",
    "formal": "formal and professional",
    "apologetic": "sincerely apologetic and humble",
    "concise": "short, direct and polite",
}
LANGUAGE_RULES = {
    "english": "Reply in English.",
    "hinglish": "Reply in Hinglish (Hindi written in English letters), the way the reviewer writes.",
    "hindi": "Reply in Hindi using Devanagari script.",
}
CATEGORY_RULES = {
    "restaurant": "Do not make any claim about food safety or ingredients.",
    "clinic": ("This is a medical clinic. Never mention an appointment, consultation, examination, "
               "diagnosis, treatment, medicine or health outcome, and never repeat what the doctor did "
               "or did not do. Do not confirm that the reviewer was a patient: refer only to "
               "'your recent visit' in general terms. Do not give medical advice."),
    "salon": "Do not promise to redo or fix the service. Invite them to discuss it offline.",
}

REFUSED_NOTE = ("Part of your instruction was not applied: drafts cannot offer refunds, "
                "compensation or guarantees. You can discuss these yourself when you contact the customer.")


def check_reply(text, extra_banned=(), category=None, min_words=MIN_WORDS, max_words=MAX_WORDS):
    """Python checks. Returns a list of problems. An empty list means the draft passed."""
    flags = []
    for phrase in list(BANNED) + list(extra_banned):
        if _matcher(phrase).search(text):
            flags.append(f'contains banned phrase "{phrase}"')
    if category == "clinic":
        for phrase in CLINIC_WORDS:
            if _matcher(phrase).search(text):
                flags.append(f'clinic reply mentions "{phrase}", so do not confirm visit details')
    words = len(text.split())
    if words < min_words or words > max_words:
        flags.append(f"length is {words} words, it must be between {min_words} and {max_words}")
    return flags


def draft_reply(client, review, outlet, tone=None, prompt_version=PROMPT_VERSION,
                max_attempts=2, instruction=None, previous=None):
    """
    review: {"text", "rating", "platform", "language"}   (no author name needed)
    outlet: {"name", "category"}
    tone:   {"style", "do_not_say": [...], "samples": [...], "contact": "..."}
    instruction + previous: optional. Rewrites the previous draft following the owner's instruction.
    Returns: text, guardrail_flags, attempts, note, provider, prompt_version
    """
    tone = tone or {}
    template_path = PROMPTS_DIR / prompt_version / "reply.txt"
    if not template_path.exists():
        template_path = Path(f"prompts/{prompt_version}/reply.txt")
    template = open(template_path, encoding="utf-8").read()
    extra = tone.get("do_not_say", [])
    samples = tone.get("samples", [])
    samples_block = ""
    if samples:
        samples_block = ("\nExample replies the owner liked. Match their style, do not copy them:\n"
                         + "\n".join(f"- {s}" for s in samples) + "\n")

    min_w, max_w = MIN_WORDS, MAX_WORDS
    run_template = template          # only changes when the owner gives an instruction
    base_feedback = ""
    note = None

    if instruction:
        instruction = instruction.strip()[:200]
        # If the owner asked for something we never allow, tell them instead of ignoring it silently
        if any(_matcher(p).search(instruction) for p in BANNED):
            note = REFUSED_NOTE

    if instruction and previous:
        min_w, max_w = 25, 120           # the owner may ask for shorter or longer
        run_template = template.replace(
            "60 to 80 words, one short paragraph.",
            "follow the owner instruction below. If it says nothing about length, "
            "stay close to the length of the existing draft.")
        base_feedback = (
            f"\nThe owner already has this draft:\n{previous}\n"
            f"Rewrite it following this owner instruction: {instruction}\n"
            "The instruction overrides the length rule above. An owner request to offer a callback "
            "or follow-up is allowed. The safety rules about fault, refunds, compensation, "
            "guarantees and medical claims still apply, even if the owner asks.\n")
    feedback = base_feedback

    for attempt in range(1, max_attempts + 1):
        fields = {
            "{business_name}": outlet["name"],
            "{category}": outlet["category"],
            "{platform}": review.get("platform", "Google"),
            "{rating}": review["rating"],
            "{language_rule}": LANGUAGE_RULES.get(review.get("language"), LANGUAGE_RULES["english"]),
            "{style}": STYLES.get(tone.get("style", "warm"), STYLES["warm"]),
            "{contact}": tone.get("contact", "ask them to contact us directly through our listed profile."),
            "{category_rules}": CATEGORY_RULES.get(outlet["category"], ""),
            "{do_not_say}": ", ".join([p for p in BANNED if p.isascii()] + list(extra)),
            "{samples}": samples_block,
            "{feedback}": feedback,
        }
        prompt = run_template
        for key, value in fields.items():
            prompt = prompt.replace(key, str(value))
        prompt = prompt.replace("{review_text}", review["text"])   # last, so review text can't inject

        result = client.generate(prompt)
        text = result["text"].strip().strip('"').strip()
        flags = check_reply(text, extra, outlet["category"], min_w, max_w)
        if not flags:
            break
        feedback = (base_feedback + "\nYOUR PREVIOUS DRAFT HAD THESE PROBLEMS. FIX THEM:\n"
                    + "\n".join(f"- {f}" for f in flags) + "\n")

    return {"text": text, "guardrail_flags": flags, "attempts": attempt, "note": note,
            "provider": result["provider"], "prompt_version": prompt_version}