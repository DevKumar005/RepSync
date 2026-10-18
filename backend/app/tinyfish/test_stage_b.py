import json
from spike import (
    tinyfish_fetch,
    tinyfish_agent_extract_reviews,
    check_wallet,
)


def test_practo_clinic_fetch():
    print("=== 1. Testing Direct Practo Clinic URL via Fetch (FREE) ===")
    practo_url = "https://www.practo.com/delhi/clinic/clove-dental-karol-bagh-1"
    f_res = tinyfish_fetch(practo_url)
    res_list = f_res["data"].get("results", [])
    if res_list:
        text = res_list[0].get("text") or ""
        print(f"  -> Practo Fetch OK! Text length: {len(text)} chars")
        print(f"  -> Preview:\n{text[:800]}...\n")
    else:
        print(f"  -> Practo Fetch Error: {f_res['data'].get('errors')}")


def test_one_agent_run():
    print("=== 2. Running 1 Metered TinyFish Agent Call on Zomato ===")
    zomato_url = "https://www.zomato.com/ncr/bukhara-itc-maurya-chanakyapuri-new-delhi/reviews"
    agent_res = tinyfish_agent_extract_reviews(
        url=zomato_url,
        platform="Zomato",
        max_reviews=10,
    )
    print(
        f"\nAgent Finished in {agent_res['duration_ms']}ms | "
        f"Steps used: {agent_res['steps_used']}"
    )
    print("Extracted JSON Reviews:")
    print(json.dumps(agent_res["result"], indent=2, ensure_ascii=False))
    check_wallet()


if __name__ == "__main__":
    test_practo_clinic_fetch()
    test_one_agent_run()
