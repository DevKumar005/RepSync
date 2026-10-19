from llm_client import LLMClient
from schemas import ReviewAnalysis

client = LLMClient()

template = open("prompts/v0/analysis.txt").read()

reviews = [
    (1, "Khana bilkul thanda tha aur waiter ne baat bhi nahi suni."),
    (5, "Amazing biryani, will come again!"),
    (5, "Waited 50 minutes for a table. Great, just great."),
]

for rating, text in reviews:
    prompt = template.replace("{rating}", str(rating)).replace("{text}", text)
    out = client.generate_json(prompt, ReviewAnalysis)
    print(out["provider"], out["data"])