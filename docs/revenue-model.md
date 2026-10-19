# Revenue Model

Pricing, market size and unit economics for RepSync. All sources were checked on **19 Oct 2026**. Anything marked **[ASSUMPTION]** is a modelling choice, not a measured fact. Anything marked **[TO CONFIRM]** is waiting on a teammate.

## 1. Pricing

| Plan | Price per outlet per month | Includes |
|---|---|---|
| Starter | ₹499 | 1 outlet, 2 platforms, weekly sync, 30 AI replies |
| Growth | ₹999 | 1 outlet, all platforms, daily sync, unlimited replies, alerts, competitor benchmark |
| Pro / Agency | ₹1,999 | Multi-user, white-label PDF reports, priority sync, bulk approvals |

**Lead magnet:** a free reputation audit (one sync, themes, and 5 sample replies).

**Why an owner pays when Google replies are free:** the owner does not have to check four platforms, complaints become a fix list instead of a pile of text, replies go out within hours, and replies come out in the owner's language and tone. One lost table, appointment or salon booking a month costs more than the fee.

## 2. Competitors

Prices are in US dollars, per location per month. The three enterprise vendors **do not publish prices**, so those figures are third-party reports. Before submitting, open each vendor's pricing page and screenshot what it shows today.

| Tool | Price | Platforms | AI reply drafting | Theme / fix insight | India focus |
|---|---|---|---|---|---|
| Birdeye | No public price. Third parties report about $299 to $449, annual contract. Setup reported at $500 to $1,500 | Many review sites | Yes (review AI features) | Analytics and benchmarking. Fix-level advice not confirmed | No India pricing found |
| Podium | No public price. Third parties report about $399 (Core) and $599 (Pro), 12-month contract | Google, Facebook and others | Sources disagree. One reports AI replies as a separate $99 add-on | Messaging-focused | No India pricing found |
| ReviewTrackers | Quote-only. Third-party figures conflict: $49, $69 and $89 | 80+ sources reported | One source says no AI auto-reply | Reporting and analytics suite | No India pricing found |
| Google Business Profile | Free | Google only | Manual reply (free browser add-ons can draft with AI) | Basic stats | Works in India |
| Zomato for Business | Free to use | Zomato only | Owners can respond to reviews | Basic dashboard | Yes |
| Practo Pro | No public price found | Practo only | Doctors can track and answer patient feedback | None found | Yes |

**Cheap AI-reply tools already exist** (prices from the vendors' own marketing):

| Tool | Price |
|---|---|
| ReplyOnTheFly | Free plan with unlimited AI drafts. Pro from $9.99 per month |
| 5S Reviews | $35 per month, includes AI responses |
| FeedbackRobot | $99 per month |

**What this means for our pitch**

1. The enterprise tools are priced in dollars, per location, on annual contracts. Our ₹499 to ₹1,999 range is priced for single outlets. Convert at the current exchange rate before quoting a rupee comparison.
2. **AI reply drafting alone is not a reason to pay.** Free and cheap tools do it. Our case rests on three things: one inbox across platforms that offer no review API, complaint themes turned into a ranked fix list, and Hindi and Hinglish support. We have not checked whether the cheap tools handle Hinglish. Verify before claiming it as unique.
3. Google and Zomato let owners reply for free, but only for their own platform, and they give no cross-platform view.

## 3. Market size

### Top-down

| Segment | Figure | Reliability |
|---|---|---|
| All MSMEs | Over 8.84 crore enterprises registered on the Udyam portals as of 30 June 2026. About 99% are micro enterprises | Good (reply in Parliament). Covers all sectors, so it is not an outlet count |
| Restaurants | NRAI says it represents over 500,000 restaurants. Hyderabad alone has 74,807 restaurants (organised and unorganised), per an NRAI newsletter | Medium. Industry body claim. No Delhi total found |
| Salons | A commercial market report lists about 300,000 players, and over 13,000 organised salons (2024) | **Weak.** Paywalled commercial report, not an official count |
| Doctors (not clinics) | 13,86,157 registered allopathic doctors and 7,51,768 AYUSH practitioners (Lok Sabha reply, Aug 2025). Practo says its network covers 70,000 clinics and hospitals | Good for doctors, but doctors are not clinics. NMC state counts have been disputed |

**Gaps:** no official Delhi restaurant total, no official salon or clinic outlet counts. We treat the restaurant and salon figures as estimates.

### Bottom-up (worked example)

Formula: outlets in a city × share active on 2 or more review platforms × conversion × price.

| | Low | High |
|---|---|---|
| Restaurants (Hyderabad, sourced) | 74,807 | 74,807 |
| Active on 2+ platforms **[ASSUMPTION: 30%]** | 22,442 | 22,442 |
| Conversion **[ASSUMPTION: 1% and 3%]** | 224 | 673 |
| Monthly revenue at ₹999 | about ₹2.2 lakh | about ₹6.7 lakh |
| Yearly revenue | about ₹27 lakh | about ₹81 lakh |

The 30% is unsourced. To replace it with evidence, look up 20 restaurants in one area on Google Maps and Zomato and count how many have reviews on both.

## 4. Unit economics

### What we measured

**TinyFish (M1's stress test), at $0.016 per step.** The cost figures match the step counts (19.5 × $0.016 = $0.312, and 7.4 × $0.016 = $0.118).

| Metric | Cold first sync | Warm incremental check |
|---|---|---|
| Agent steps | 19.5 average (range 12 to 25) | 7.4 average (with 24-hour caching) |
| TinyFish cost per outlet | $0.312 | $0.118 |
| Search and Fetch | $0 (free) | $0 (free) |
| Monthly TinyFish cost | n/a | $1.40 to $2.10 |

The monthly range equals about **12 to 18 Agent checks per outlet per month** ($1.40 ÷ $0.118 and $2.10 ÷ $0.118). So the share of days that need the Agent is an assumption built into that range, not a separate measurement. **[TO CONFIRM with M1: how many runs sit behind the averages, which platforms, and whether 19.5 steps covers both platforms.]**

**LLM tokens (M2).**

| Run | Calls | Tokens in | Tokens out |
|---|---|---|---|
| 10 real reviews (2 negative) | 12 | 7,754 | 439 |
| 30 synthetic reviews (18 negative), Groq-heavy | 50 | 29,367 | 24,278 |

### Prices used

| Item | Price | Source |
|---|---|---|
| TinyFish Agent | $0.016 per step (conservative). The official pricing page shows $0.015 pay-as-you-go | tinyfish.ai/pricing and TinyFish blog |
| Groq gpt-oss-120b | $0.15 per 1M input tokens, $0.60 per 1M output tokens | GroqCloud pricing, Oct 2026 |
| Gemini (our primary) | **[TO CONFIRM]** price for the configured `GEMINI_MODEL`. Groq's price is a conservative stand-in | Google AI pricing page |
| Exchange rate | **₹95 per US$ [ASSUMPTION]**. The latest rate found was about ₹96.5 on 22 Jul 2026 (50-day average ₹95.2). Update with today's rate | pluang.com currency converter |

### LLM cost per outlet

M1's table shows $0.00 because both providers are on free tiers. That is true today, but free tiers have hard limits. Groq's free tier for this model allows 8,000 tokens per minute (our own run hit that limit), and Gemini returned quota errors (429) during our runs. A paid product must budget for paid usage.

At paid Groq prices, the heavy Groq run costs about $0.019 for 30 reviews, or about $0.0006 per review. That run used a reasoning model and a 60% negative mix, so it is pessimistic. For 80 reviews in a first month (50 existing plus 30 new **[ASSUMPTION]**), LLM cost is **about $0.05 per outlet**, and under $0.02 in steady state. **The LLM is not the cost driver.**

### Growth plan margin (₹999 = $10.52 at ₹95 per US$)

Costs per outlet per month: TinyFish as shown, plus LLM $0.05, plus hosting share $1.00 **[ASSUMPTION, M3 to confirm]**.

| Scenario | TinyFish per month | Total cost | Gross margin, all costs | Margin, TinyFish cost only |
|---|---|---|---|---|
| M1 low (about 12 Agent checks) | $1.40 | $2.45 | **77%** | 87% |
| M1 high (about 18 Agent checks) | $2.10 | $3.15 | **70%** | 80% |
| First month, low (adds the $0.312 cold sync) | $1.71 | $2.76 | 74% | 84% |
| First month, high | $2.41 | $3.46 | 67% | 77% |
| Agent runs every day (30 incremental checks) | $3.54 | $4.59 | 56% | 66% |
| Naive: full Agent re-run every day (SRS warning) | $14.40 to $24.00 | $15.45 to $25.05 | −47% to −138% | −37% to −128% |

**What this says**
- On M1's measured numbers, the Growth plan stays at or above the **70% target** in steady state (70% to 77% on all costs, 80% to 87% on TinyFish cost alone). The high end sits right on the line.
- The 70% target holds only up to about **17 Agent checks per month**, which is the key number to protect. The more often Fetch alone is enough, the better the margin.
- The first month is lower (67% to 74%) because of the one-time cold sync.
- **GST.** If ₹999 includes GST (18% on software services, verify), net revenue is about ₹847 ($8.91) and every margin above falls by about 4 to 6 points. Decide whether prices are shown before or after GST. **[DECISION for the team]**
- M1's summary quotes 78.5% to 82.0%. We could not reproduce it from the inputs: we get 80% to 87% on TinyFish cost alone, and 70% to 77% with LLM and hosting. **[TO CONFIRM with M1 how it was calculated.]**

### Starter plan (₹499 = $5.25)

Weekly sync with an incremental Agent check each time, the worst case in this design: 4 × $0.118 = $0.47. With LLM and hosting the total is $1.52, a margin of **about 71%**. Starter must also use incremental syncs. Full weekly re-runs would push the margin well below 50%.

### Pro plan (₹1,999)

Not modelled. Multi-outlet usage, white-label reports and bulk approvals are not measured.

### Break-even

Break-even outlets = fixed monthly cost ÷ (price − variable cost per outlet). For Growth, the contribution per outlet is **$7.37 to $8.07 (about ₹700 to ₹770)**. With an example fixed cost of ₹5,000 per month **[ASSUMPTION: paid hosting tier, domain, monitoring]**, break-even is about **7 to 8 outlets**.

### Upside not used in the table

TinyFish's Starter plan ($15 per month for 1,650 steps) works out to about $0.009 per step. At 89 to 133 steps per outlet per month (12 to 18 checks × 7.4 steps), one subscription covers about 12 to 18 outlets, and Agent cost per outlet falls by roughly 40%. We model pay-as-you-go because it is the conservative case.

## 5. Owner validation

**[TO ADD from M4's conversations with 3 to 5 local owners: what they check today, what they would pay, and one quote.]**

## 6. Go-to-market

- Local marketing agencies who resell the Pro plan.
- Restaurant and salon associations, and clinic networks.
- Free-audit outreach on WhatsApp and Instagram, converting audits into paid plans.

## 7. Legal and ethics (short form)

The owner enters their own business, and we collect public reviews on demand, from public pages only, in small samples and with throttled requests. We store the minimum personal data and let the owner delete an outlet and all its data. Replies are drafts only, and the owner approves and posts every one. The production path for owners' own Google listings is the official Google Business Profile API. TinyFish covers platforms with no API and powers the free audit.

## 8. Still to confirm before submission

| Item | Owner |
|---|---|
| Runs behind the 19.5 and 7.4 step averages, platforms covered, and whether 19.5 covers both platforms | M1 |
| How the 78.5% to 82.0% margin was calculated (we get 80% to 87% on TinyFish cost alone, 70% to 77% with LLM and hosting) | M1 |
| Whether the 12 to 18 Agent checks per month assumption is measured or estimated | M1 |
| Gemini price for the configured model | M2 |
| Hosting cost per outlet and fixed monthly costs | M3 |
| Whether ₹999 includes GST | Team |
| Owner quote | M4 |
| Screenshots of the three vendor pricing pages with today's date | M2 |
| Today's USD to INR rate (this doc uses ₹95) | M2 |

## Sources (checked 19 Oct 2026)

- Birdeye pricing reports: pabau.com/blog/birdeye-pricing, totoslocal.com/birdeye-review, softwarefinder.com/customer-service-software/birdeye
- Podium pricing reports: fieldcamp.ai/reviews/podium, pabau.com/blog/podium-cost, replifast.com/blog/podium-pricing-2026
- ReviewTrackers pricing reports: wiserreview.com/blog/reviewtrackers-alternatives, softwaresuggest.com/reviewtrackers, itqlick.com/reviewtrackers/pricing
- Google Business Profile: google.co.in/business
- Zomato for Business: getapp.co.uk/software/2046703/zomato, g2.com/products/zomato/reviews
- Practo Pro: apps.apple.com/app/id592116111 and apps.apple.com/app/id953772015
- Cheap AI-reply tools: sourceforge.net/software/product/ReplyOnTheFly, 5sreviews.com/blog/podium-pricing-is-it-worth-it, feedbackrobot.com/compare/birdeye-pricing
- MSME counts: knnindia.co.in/news/newsdetails/msme/over-884-crore-msmes-registered-on-udyam-platforms-mos-karandlaje, galific.com/reports/india-msme-udyam-map-2026
- Restaurants: nrai.org, conference.nrai.org/files/uploads/2024/08/april-june-2024-newsletter.pdf
- Salons: kenresearch.com/india-beauty-salon-market
- Doctors: etvbharat.com (Lok Sabha reply, 1 Aug 2025), eparlib.sansad.in (Lok Sabha unstarred question 867, 29 Nov 2024)
- Groq pricing: morphllm.com/groq-pricing, getmaxim.ai/bifrost/llm-cost-calculator/provider/groq/model/gpt-oss-120b
- TinyFish pricing: tinyfish.ai/pricing, tinyfish.ai/blog/firecrawl-pricing
- Exchange rate: pluang.com/en/tools/currency-converter/usd-inr (rate dated 22 Jul 2026)