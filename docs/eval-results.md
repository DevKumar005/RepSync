# Evaluation Results

What we measured, how, and what the numbers do and do not show.

## 1. The eval set

30 hand-labelled reviews in `data/eval/labelled_reviews.csv`.

| Dimension | Split |
|---|---|
| Language | 10 English, 10 Hinglish, 10 Hindi (Devanagari) |
| Category | 10 restaurant, 10 clinic, 10 salon |
| Sentiment (our labels) | 10 positive, 4 neutral, 16 negative (17 if R04 is relabelled, see section 3) |

It includes deliberately tricky cases: sarcasm with 5 stars (R03, S24), a 1-star review with positive text (C14), mixed reviews (R04, C17, S30), very short reviews ("Worst.", "Okay food. Nothing special."), and clinic reviews that mention medical outcomes (C12, C16, C19).

**Important:** every review in this set is **synthetic**. We wrote them to mimic real reviews and labelled them ourselves. The `source` column says so. A separate test on real reviews is in section 4.

## 2. Results by prompt version

Run with `python run_eval.py`. Each version's per-review results are saved in `data/eval/results_<version>.csv`.

| Prompt | Sentiment accuracy | Topic match | Language accuracy | Misses |
|---|---|---|---|---|
| v0 (first draft) | **97%** (29/30) | not measured | not measured | R04 |
| v1 (fixed topic vocabulary, mixed-review rule) | **93%** (28/30) | **94%** (15/16) | not measured | R04, S30 |
| v2 (adds language, two new topic labels, "don't guess" rule) | **97%** (29/30) | **94%** (15/16) | **100%** (30/30) | R04 |

Sentiment by language, v2: English 9/10, Hinglish 10/10, Hindi 10/10.

**Metric definitions**
- **Sentiment accuracy:** the AI's sentiment equals our label.
- **Topic match:** counted only on the 16 reviews where we labelled a theme. A match means our theme appears in the AI's topic list for that review.
- **Language accuracy:** the language after the code-level script check equals our label.

**What each version taught us**
- **v0 → v1:** v0 scored well on sentiment, but the topics were inconsistent: one problem was named four different ways. v1 added a fixed topic vocabulary. Sentiment dipped to 93% because the new mixed-review rule exposed two reviews (R04, S30) where the rule and our labels disagreed.
- **v1 → v2:** a test on real reviews (section 4) showed that average food was labelled "cold food" and a crowding complaint was labelled "overpriced, slow service". v2 added `food quality` and `poor management` and a rule not to guess complaints the customer did not mention. v2 also moved the Hindi / Hinglish decision into code, because the AI labelled several Hinglish reviews as Hindi.

## 3. The R04 note

R04: "Food was great but the service was terrible. Paid 600 for a thali that took forever." We labelled it neutral. The AI says negative in every version.

Our written rule says a strong complaint word (such as "terrible") makes a mixed review negative. Under that rule the AI is right and our label is arguable. We did **not** change the label after seeing the results, to avoid tuning the test to the answer. If R04 were relabelled negative, v2 sentiment would be 30/30. We report 97%.

## 4. Test on real reviews

10 real Google Maps reviews of one Delhi restaurant (Bukhara), collected by the TinyFish agent.

| Check | Result |
|---|---|
| Sentiment vs our labels | 10/10 (8 positive, 2 negative) |
| Tricky cases | A 3-star review reading "The food was a disappointment" was correctly negative. Very short reviews ("Great", "AMAZINGG!!") were positive with no invented topics. A mixed English / Hindi-word review was positive. |
| Topics on the 2 negatives | **Wrong under v1, corrected under v2** (see section 2) |

**Caveat:** the two negative reviews were used to write v2, so they are development examples, not a clean test. Eight of the ten reviews were easy positives. This test shows the pipeline works on real data. It does not give a reliable accuracy figure.

## 5. Other checks

**Theme stability.** Complaint grouping was run three times, across both Gemini and Groq. The top theme, slow service, came out identical every time (8 of 16 negative reviews, same review ids). Minor themes varied slightly between runs, which led us to count the primary theme as the headline number and to show secondary mentions separately.

**Reply guardrails.**
- In a full run on the 30-review set, all 17 drafts passed the automated check on the first attempt (no banned phrase, correct length, no clinic privacy words).
- Reading the drafts by hand still found problems the automated check cannot detect: quoting the review word for word, mentioning a wait the review never described, and clinic replies that confirmed a consultation. These led to the stricter v1 reply prompt and the clinic word list.
- **Regenerate with an instruction.** "Make it shorter" cut a reply from about 74 to 43 words. "Offer a callback" produced a callback offer with no invented name or number. "Offer a full refund" produced a reply with **no refund promise**, plus a note telling the owner the request was not applied.

**Language.** After the script check, language accuracy was 30/30. Before it, several Hinglish reviews were labelled Hindi, so replies came out in Devanagari instead of Hinglish.

## 6. Not measured

We did not measure these, and we do not report a figure:

| Metric | SRS target | Status |
|---|---|---|
| Reply checklist pass rate (specific, on-tone, no banned phrase) | 90% | Not measured. The automated check passed 17 of 17 drafts, but that is a rule check, not a quality score. |
| Theme coherence (manual rating, 1 to 5) | 4 or more | Not measured |
| Repeated eval runs with a range | n/a | Single run per version. Results can shift by a review or two between runs, so a 1-review difference (3.3%) is within noise. |

## 7. Limitations

- **Synthetic set, tuned on.** The prompts were adjusted while looking at these same 30 reviews, so 97% is a development number, not a production estimate.
- **Small sample.** One review is 3.3% of the score.
- **Real-data test is thin.** Ten reviews, two negative, partly used for tuning.
- **Labels are our judgement.** Mixed reviews are borderline, and we applied one rule consistently.
- **The reply check is a safety net, not a guarantee.** The owner approves every reply and posts it themselves.

## 8. Reproducing

```bash
cd ai
cp .env.example .env     # add your Gemini and Groq keys and model names
python run_eval.py       # set PROMPT_VERSION at the top: "v0", "v1" or "v2"
```

Results print to the terminal and save to `data/eval/results_<version>.csv`.
