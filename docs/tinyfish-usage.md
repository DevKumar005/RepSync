# TinyFish Integration in RepSync

RepSync heavily relies on the **TinyFish SDK** (`Search`, `Fetch`, and `Agent` APIs) as its core ingestion engine. Because our users are local business owners, we need to reliably collect public reviews from platforms like Zomato, Practo, EazyDiner, and Lybrate without getting blocked by anti-bot measures.

## The Smart Escalation Strategy (Cost & Speed Optimized)

To balance speed, reliability, and cost (Agent steps), RepSync implements a **Smart Escalation Pipeline**:

1. **TinyFish Search (Free):** We use `api.search.tinyfish.ai` with category-specific domain allowlists (e.g., `zomato.com`, `practo.com`) to find the exact review page URLs for a given business name and city.
2. **TinyFish Fetch (Free):** We attempt to retrieve the static page using `api.fetch.tinyfish.ai`. If the platform serves server-side HTML (like EazyDiner or Lybrate), Fetch returns clean Markdown. We then pass this Markdown to Gemini (`gemini-3.8-flash`) to extract structured reviews for **$0.00**.
3. **TinyFish Agent (Metered):** If Fetch is blocked (e.g., anti-bot walls) or returns fewer than 6 reviews (e.g., JS-heavy pagination on Zomato or Practo), we dynamically escalate to the TinyFish Web Agent (`agent.tinyfish.ai/v1/automation/run-sse`). The Agent navigates the page, bypasses modals, expands "Read more" buttons, and extracts up to 50 structured reviews as JSON.

### Architecture Diagram
*(Add your Excalidraw diagram here showing the flow: User Input -> Search -> Candidate URLs -> Fetch -> [Extract OR Escalate to Agent] -> Normalise & Dedup -> DB)*

## Per-Source Isolation (Kill-Switch)

We implemented strict per-source isolation. If one platform's anti-bot measures successfully block the Agent (e.g., a hard sign-in wall), the pipeline gracefully catches the failure, logs a `FAILED` status for that specific source, and continues processing the remaining platforms. One failing source **never** crashes the sync job.

## The Activity Log (Proof of Execution)

Every TinyFish call is logged in our database and streamed live to the frontend via Server-Sent Events (SSE). 

Here is a sample of our live Activity Log during a multi-platform sync:

*(Add a screenshot of your M4 UI Activity Log panel here, showing SEARCH, FETCH, and AGENT calls)*

## Unit Economics & Caching

To ensure RepSync is financially viable and scalable for small local outlets, we enforce a strict caching policy alongside a cost-prioritized ingestion pipeline:

* **Caching Layer:** Search, Fetch, and Agent results are cached for 24 hours by `hash(endpoint, input)` in Postgres and local JSON. Cached requests return in <5 ms at **$0.00**.
* **Free Ingestion (Search & Fetch):** Platform discovery and static HTML parsing via `api.search.tinyfish.ai` and `api.fetch.tinyfish.ai` cost **$0.00**[cite: 1]. Markdown extraction runs on free-tier Gemini (`gemini-3.8-flash`) with fallback to Groq (`llama-3.3-70b-versatile`).
* **Metered Agent Step Rate:** **$0.016 per step** (`agent.tinyfish.ai/v1/automation/run-sse`).
* **Measured Initial Onboarding (Cold Sync):** **19.5 steps / $0.312 per outlet** (measured across 4 live outlets: Karim's [19], Indian Accent [12], Apollo Spectra [14], Max Super Speciality [33]).
* **Measured Incremental / Cached Sync:** **7.4 steps / $0.118 per outlet** across 5 outlets with 24-hour cache active.
* **Monthly Recurring Ingestion Cost:** **$1.40 – $2.10 / month per outlet** (Fetch-first daily checks; Agent triggers only when review count changes, using 2–4 steps).
* **Gross Margin (₹999 / $11.80 Growth Plan):** **78% – 82%**, comfortably exceeding the **≥70%** requirement.