import json
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.tinyfish.client import TinyFishService
from app.services.ingestion.extractor import extract_reviews_from_markdown

tf = TinyFishService()

print("=== 1. Inspecting Practo Doctor Stories Markdown (Already Cached!) ===")
md_doc, _ = tf.fetch("https://www.practo.com/delhi/doctor/dr-mona-juneja-2-dentist/stories")
print(f"Markdown length: {len(md_doc)} chars")
print("Preview:\n", md_doc[:900])

print("\n=== 2. Domain-Filtered Search + FREE Fetch Test (0 Credits!) ===")
domain_tests = [
    ("Restaurant - EazyDiner", "EazyDiner", "eazydiner.com", "Bukhara ITC Maurya Delhi eazydiner.com"),
    ("Restaurant - Magicpin", "Magicpin", "magicpin.in", "Bukhara ITC Maurya Delhi magicpin.in"),
    ("Restaurant - MouthShut", "MouthShut", "mouthshut.com", "Bukhara ITC Maurya Delhi mouthshut.com"),
    ("Restaurant -Dineout/Swiggy", "Swiggy Dineout", "swiggy.com", "Bukhara ITC Maurya Delhi swiggy dineout"),
    ("Clinic - Lybrate", "Lybrate", "lybrate.com", "Clove Dental Delhi lybrate.com"),
    ("Clinic - MouthShut", "MouthShut", "mouthshut.com", "Clove Dental mouthshut.com reviews"),
]

for label, platform, domain, q in domain_tests:
    results, _ = tf.search(q)
    matched_url = None
    for item in results:
        u = item.get("url") or item.get("link") or ""
        if domain in urlparse(u).netloc.lower():
            matched_url = u
            break

    if not matched_url:
        print(f"\n[{label}] No URL matching '{domain}' in top 10. Top URLs were:")
        for item in results[:3]:
            print(f"   - {item.get('url')}")
        continue

    md, log = tf.fetch(matched_url)
    extracted = extract_reviews_from_markdown(md, platform=platform) if md else []
    print(f"\n[{label}] Matched URL: {matched_url}")
    print(f"  -> Fetch status={log.status} | Markdown={len(md)} chars | Gemini Extracted={len(extracted)} reviews")
    if md and not extracted:
        print(f"  -> Markdown snippet: {md[:350]}...")
    elif extracted:
        print(f"  -> First extracted review: {extracted[0]}")