# RepSync API Specification & Real-Time SSE Contract

Interactive OpenAPI documentation is live at **`/docs`** (Swagger UI) and **`/redoc`** (ReDoc).

---

## 1. REST Endpoints Overview

| Method | Endpoint | Description | Auth / Rate Limit |
|---|---|---|---|
| `GET` | `/health` | Lightweight service health ping | Public |
| `GET` | `/health/db` | Database touch check (keep-alive) | Public |
| `POST` | `/api/auth/signup` | Register new business owner | Public |
| `POST` | `/api/auth/login` | Login with email and password | Public |
| `POST` | `/api/auth/demo` | Instant login as Demo User | Public |
| `GET` | `/api/platforms` | Platform registry for UI filters | Public |
| `POST` | `/api/outlets/search` | Search candidate URLs for business | 30 req/min |
| `POST` | `/api/outlets` | Register new outlet & init platform sources | Bearer JWT |
| `GET` | `/api/outlets/{id}` | Get outlet metadata and source statuses | Bearer JWT / Demo |
| `POST` | `/api/outlets/demo/{key}` | Instant demo outlet load (<3s) | Public |
| `DELETE`| `/api/outlets/{id}` | Cascade delete outlet and all associated data | Owner Only |
| `POST` | `/api/outlets/{id}/sync` | Start asynchronous review sync pipeline | 10 req/min |
| `GET` | `/api/outlets/{id}/sync/stream` | Server-Sent Events (SSE) live progress stream | Public |
| `GET` | `/api/outlets/{id}/reviews` | Filtered reviews (platform, sentiment, rating) | Public |
| `GET` | `/api/outlets/{id}/themes` | Extracted themes with review counts & percentages | Public |
| `GET` | `/api/outlets/{id}/fixes` | Top 3 ranked operational fixes | Public |
| `GET` | `/api/outlets/{id}/summary` | KPI analytics and per-platform split | Public |
| `GET` | `/api/outlets/{id}/sources` | Source statuses for live UI indicators | Public |
| `GET` | `/api/outlets/{id}/tinyfish-log`| Activity log with agent steps used | Public |
| `POST` | `/api/reviews/{id}/draft` | Regenerate draft with custom instruction | Bearer JWT / Demo |
| `PATCH`| `/api/drafts/{id}` | Edit text or update approval status | Bearer JWT / Demo |
| `PUT` | `/api/tone` | Save brand tone profile & forbidden words | Bearer JWT / Demo |

---

## 2. Server-Sent Events (SSE) Contract (Frozen)

Clients connect to `GET /api/outlets/{id}/sync/stream` to receive real-time events during review collection and analysis:

```json
{
  "type": "source_status | tinyfish_call | stage | done",
  "source": "google_maps | zomato | justdial | practo | tripadvisor",
  "status": "running | success | partial | failed | cached",
  "message": "Agent: Extracted 10 reviews with 2 steps",
  "ts": "2026-10-18T06:00:00Z"
}
```

### Stage Sequence:
1. `searching`: Locates review profile URLs across platforms.
2. `collecting`: Parallel ingestion via TinyFish (Agent concurrency $\le 2$).
3. `normalising`: Language detection, text deduplication, and rating-text mismatch checking.
4. `analysing`: Sentiment scoring, topic theme grouping, and operational fix generation.
5. `drafting`: Generates personalized AI reply drafts for negative reviews with guardrail validation.
6. `done`: Pipeline completed and dashboard ready.

---

## 3. Approval State Machine (FR-5)

The approval status of a customer reply draft is strictly validated server-side on `PATCH /api/drafts/{id}`:

```
[draft] ──(edit)──> [edited] ──(approve)──> [approved] ──(post)──> [posted]
   │                   │                         │
   └──(reject)───────> [rejected]                └──(edit)──> [edited] (re-approval needed)
                         │
                         └──(regenerate)──> [draft]
```

- Transitioning from an unapproved state directly to `posted` returns HTTP **409 Conflict**.
- Updating the draft text of an already approved response automatically resets its status to `edited` and clears `approved_at`.
- All transitions write an immutable entry to `audit_log`.
