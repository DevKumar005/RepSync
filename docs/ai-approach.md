# AI Approach

How RepSync turns raw public reviews into themes, fixes and owner-approved replies, and how we keep the AI honest.

## 1. Design principle

**The AI makes judgement calls. Plain Python guarantees the facts.**

| The AI decides | Python guarantees |
|---|---|
| Sentiment, topics and severity of a review | Output shape (Pydantic schemas, one retry on bad JSON) |
| Which complaints belong together | Counts, percentages, rankings and quotes (taken from the real reviews, never written by the AI) |
| The wording of a fix or a reply | The top 3 fixes (ranked by count), the evidence numbers, and the strong / early-signal tag |
| Whether a reply sounds warm | Banned phrases, clinic privacy words, length limits, reply language script |

A prompt is only a request. The AI can ignore it, so every rule that must hold is also enforced in code.

## 2. Pipeline

`run_pipeline(client, reviews, outlet, tone, on_progress)` in `pipeline.py` runs five stages and returns one result.

1. **Analysis** (`prompts/v2/analysis.txt`): one call per review returns language, sentiment, topics and severity. Output is validated against `ReviewAnalysis`. Star rating is a hint only. The text decides, so a 5-star sarcastic review is still negative.
2. **Language fix**: `detect_language()` overrides the AI using the script. Devanagari means Hindi. Hindi words in English letters means Hinglish. The AI had labelled several Hinglish reviews as Hindi, which made replies come out in the wrong script.
3. **Themes** (`prompts/v2/themes.txt`): one call groups negative reviews into 3 to 7 themes, starting from a fixed vocabulary (slow service, food quality, overpriced, hygiene, rude staff, poor management, doctor behaviour, poor quality work). Each review gets one primary theme and at most one secondary theme, so a review can never be counted three times. Python then does the counting, adds any review the AI forgot (using its own topics), folds themes with fewer than 2 mentions into "Other issues", and picks real quotes. Reviews with no detail ("Worst.") are reported separately.
4. **Top 3 fixes** (`prompts/v2/fixes.txt`): Python picks the top 3 themes by main-complaint count. The AI writes a specific action for each and is told not to write numbers. Python adds the evidence count ("8 of 16") and tags each fix `strong` (3 or more) or `early signal` (fewer than 3).
5. **Reply drafts** (`prompts/v1/reply.txt`): one call per negative review without an owner reply, then the guardrail check (section 5).

If fewer than 5 negative reviews exist, themes and fixes are skipped on purpose, because a pattern from 2 reviews is not a pattern.

## 3. Provider layer (`llm_client.py`)

All AI calls go through one `LLMClient`.

- **Gemini first, Groq as fallback.** Model names live in `.env`, so changing a model needs no code change.
- **Failure handling:** 2 tries on Gemini, then Groq. After a Gemini failure the client skips Gemini for 5 minutes. On a Groq rate limit (429) it waits for the time Groq reports and retries up to 4 times.
- **Observed in testing:** Gemini returned 503 (server busy) and 429 (free-tier quota). The fallback kept every run alive.
- **Usage log:** every call records provider, tokens in, tokens out and seconds. `usage_summary()` feeds the unit economics.

## 4. Prompt versions and what each taught us

Prompts are versioned in `prompts/v0`, `v1` and `v2`. Reply drafts store `prompt_version`.

| Version | Change | Result on 30 labelled reviews |
|---|---|---|
| v0 | First draft: sentiment, free-text topics | Sentiment 97% (29/30). Topics inconsistent: one problem got four names ("long wait", "long wait time", "slow service"). |
| v1 | Fixed topic vocabulary, explicit mixed-review rule | Sentiment 93% (28/30), topic match 94% (15/16). The dip exposed two cases where our stated rule and our labels disagreed. |
| v2 | Added `language`, plus `food quality` and `poor management` labels, plus a "do not guess a complaint the customer did not mention" rule | Sentiment 97%, topic match 94%, language 100% |

**The real-data lesson.** v1's vocabulary was written from our synthetic reviews. On 10 real reviews from TinyFish (Bukhara, Delhi), sentiment was 10/10, but the two negative reviews got wrong topics. "The food was a disappointment" was labelled `cold food`. A review about crowding and mismanagement was labelled `overpriced, slow service`. We had no label for average food or for crowding, and no rule against guessing. v2 fixed both.

## 5. Reply guardrails

A reply goes out in the owner's name, in public. We assume the AI will sometimes get it wrong, so there are three layers.

1. **Prompt rules:** 60 to 80 words, mention one specific detail from the review, no admission of fault, no refund or compensation promise, no medical claims, no blaming the reviewer, no invented facts, invite them to continue offline.
2. **Python check (`check_reply`):**
   - Banned phrases in English, Hinglish and Hindi ("our fault", "refund", "guarantee", "compensat", "we failed", and others). Matching starts at a word boundary, so "cure" is caught but "secure" is not.
   - Clinic words (consultation, appointment, examination, treatment, patient, and Hindi equivalents). Mentioning them would confirm that the reviewer was a patient.
   - A length range.
3. **Automatic retry:** if the check fails, the AI gets one more attempt with the exact problems named. If it still fails, the draft is returned with `guardrail_flags` so the owner sees a warning.

**Owner instructions cannot bypass the rules.** "Regenerate with instruction" takes an owner instruction ("shorter", "offer a callback"). The same check runs on the new draft. In our test, "offer a full refund" produced a reply with no refund promise, and the result carried a `note` telling the owner the request was not applied.

**What the checker cannot catch.** All 17 drafts in a full run passed with no flags, but reading them by hand found problems: a reply that quoted the review word for word, clinic replies that repeated "consultation" and "appointment", a reply that assumed a long customer history, and a reply that mentioned a wait the review never described. These led to the stricter v1 reply prompt and the clinic word list. Some problems (an invented detail) still need a human, which is why **the owner approves every reply and posts it themselves**.

## 6. Language handling

English, Hindi (Devanagari) and Hinglish are detected per review. Replies match the review's language. Script detection is done in code, not by the AI (section 2, stage 2). On the 30-review set, language accuracy is 100% (30/30).

## 7. Evaluation

- **Set:** 30 hand-labelled reviews (10 English, 10 Hinglish, 10 Hindi; 10 restaurant, 10 clinic, 10 salon), including sarcasm, 1-star-positive, mixed and very short reviews. **The set is synthetic.** Labels were written by the team.
- **Run:** `python run_eval.py` scores sentiment, topic match and language and writes `data/eval/results_<version>.csv`.

| Metric | Target | v2 result |
|---|---|---|
| Sentiment accuracy | 85% or more | 97% (29/30) |
| Topic match | n/a | 94% (15/16) |
| Language accuracy | n/a | 100% (30/30) |
| Reply checklist pass rate | 90% or more | [FILL IN: measure on about 20 drafts] |
| Theme coherence (manual, 1 to 5) | 4 or more | [FILL IN] |

[FILL IN after rerun: R04 and S21 labels corrected to match the stated rules, and the 3-run range for each metric.]

## 8. Limitations (stated honestly)

- **The eval set is synthetic and was used while tuning prompts.** Treat 97% as a development number, not a production estimate. The real-data test (10 Bukhara reviews) was small and mostly positive, with only 2 negatives.
- **Results vary slightly between runs and between providers.** One borderline review (C17, a parking complaint) flipped between neutral and negative across runs. One review is 3.3% of the set.
- **Minor themes are less stable than the top theme.** The top theme (slow service, 8 of 16) was identical across three runs and both providers.
- **Fixes from 2 reviews are weak evidence.** They are tagged `early signal`.
- **A sync is slow on free tiers** (minutes for 30 to 50 reviews) and can hit quota limits. The demo uses cached data.
- **The banned-phrase list is a safety net, not a guarantee.** A reworded promise can slip through, so every reply needs owner approval.

## 9. Cost tracking

Every call logs tokens. Measured so far:

| Run | Calls | Tokens in | Tokens out |
|---|---|---|---|
| 10 real reviews (2 negative) | 12 | about 7,800 | about 400 |
| 30 synthetic reviews (17 negative), mostly Gemini | 49 | about 29,100 | about 10,500 |

A realistic outlet is closer to the first run (about 800 tokens per review). A first sync costs money mainly where the TinyFish Agent is used, so unit economics are in `docs/revenue-model.md`.
