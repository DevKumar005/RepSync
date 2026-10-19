import json
import re
import os
import time
import warnings
from dotenv import load_dotenv
from google import genai
from groq import Groq
from pydantic import ValidationError

warnings.filterwarnings("ignore")
load_dotenv()


class LLMClient:
    def __init__(self):
        gemini_key = os.getenv("GEMINI_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")

        self.gemini = genai.Client(api_key=gemini_key) if gemini_key else None
        self.groq = Groq(api_key=groq_key) if groq_key else None
        self.gemini_model = os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
        self.groq_model = os.getenv("GROQ_MODEL") or "llama-3.3-70b-versatile"
        self.gemini_down_until = 0
        self.usage = []          # one entry per successful call

    def _call_gemini(self, prompt):
        response = self.gemini.models.generate_content(
            model=self.gemini_model, contents=prompt)
        meta = response.usage_metadata
        tokens_in = getattr(meta, "prompt_token_count", 0) or 0
        total = getattr(meta, "total_token_count", 0) or 0
        return response.text, tokens_in, max(total - tokens_in, 0)

    def _call_groq(self, prompt):
        response = self.groq.chat.completions.create(
            model=self.groq_model,
            messages=[{"role": "user", "content": prompt}])
        u = response.usage
        return (response.choices[0].message.content,
                getattr(u, "prompt_tokens", 0) or 0,
                getattr(u, "completion_tokens", 0) or 0)

    def _record(self, provider, tokens_in, tokens_out, started):
        self.usage.append({"provider": provider, "tokens_in": tokens_in,
                           "tokens_out": tokens_out,
                           "seconds": round(time.time() - started, 2)})

    def usage_summary(self):
        out = {"calls": len(self.usage), "tokens_in": 0, "tokens_out": 0, "by_provider": {}}
        for u in self.usage:
            out["tokens_in"] += u["tokens_in"]
            out["tokens_out"] += u["tokens_out"]
            out["by_provider"][u["provider"]] = out["by_provider"].get(u["provider"], 0) + 1
        return out

    def _groq_wait_time(self, error):
        # Groq's error says things like "try again in 397.5ms" or "try again in 2.4s"
        m = re.search(r"try again in ([\d.]+)(ms|s)", str(error))
        if not m:
            return 10.0
        value = float(m.group(1))
        seconds = value / 1000 if m.group(2) == "ms" else value
        return min(seconds + 1.0, 60.0)      # small buffer, never more than a minute

    def generate(self, prompt):
        if self.gemini and time.time() > self.gemini_down_until:
            for attempt in range(2):
                started = time.time()
                try:
                    text, t_in, t_out = self._call_gemini(prompt)
                    self._record("gemini", t_in, t_out, started)
                    return {"text": text, "provider": "gemini"}
                except Exception as e:
                    print(f"Gemini failed (attempt {attempt + 1}): {type(e).__name__} {str(e)[:150]}")
                    time.sleep(2)
            self.gemini_down_until = time.time() + 300   # skip Gemini for 5 minutes

        if self.groq:
            last_error = None
            for attempt in range(4):
                started = time.time()
                try:
                    text, t_in, t_out = self._call_groq(prompt)
                    self._record("groq", t_in, t_out, started)
                    return {"text": text, "provider": "groq"}
                except Exception as e:
                    last_error = e
                    if "429" in str(e) or "rate_limit" in str(e).lower():
                        wait = self._groq_wait_time(e)
                        print(f"Groq rate limit, waiting {wait:.0f}s")
                        time.sleep(wait)
                    else:
                        break                      # a different error, so retrying won't help
            raise RuntimeError(f"Groq failed: {last_error}")

        raise RuntimeError("No working LLM provider available. Please set a valid GEMINI_API_KEY or GROQ_API_KEY.")

    def generate_json(self, prompt, schema):
        last_error = None
        for attempt in range(2):
            result = self.generate(prompt)
            raw = result["text"].strip()
            if raw.startswith("```"):
                raw = raw.strip("`")
                if raw.lower().startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()
            try:
                data = json.loads(raw)
                return {"data": schema(**data), "provider": result["provider"]}
            except (json.JSONDecodeError, ValidationError, TypeError) as e:
                last_error = e
                print(f"Bad JSON (attempt {attempt + 1}): {type(e).__name__}")
        raise ValueError(f"AI did not return valid JSON after 2 tries: {last_error}")