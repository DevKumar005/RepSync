from llm_client import LLMClient
from replies import draft_reply

client = LLMClient()
outlet = {"name": "Spice Garden", "category": "restaurant"}
review = {"text": "Waited 50 minutes for a table even after booking. Food arrived cold and the manager just shrugged. Never coming back.",
          "rating": 1, "platform": "Google", "language": "english"}
tone = {"style": "warm",
        "contact": "invite them to call or message us directly on the number listed on our profile."}

first = draft_reply(client, review, outlet, tone)
print("ORIGINAL:", first["text"], "\n")

for instruction in ["make it shorter", "offer a callback from the manager", "offer a full refund"]:
    d = draft_reply(client, review, outlet, tone, instruction=instruction, previous=first["text"])
    print(f"INSTRUCTION: {instruction}")
    print("REPLY:", d["text"])
    print("NOTE:", d["note"])
    print(f"   {len(d['text'].split())} words | attempts={d['attempts']} | flags={d['guardrail_flags'] or 'none'}\n")