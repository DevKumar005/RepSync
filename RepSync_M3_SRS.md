# RepSync: M3 Role SRS (Backend, Database, DevOps, QA)

**Project:** RepSync, Local Business Reputation Manager (KRITICAL HACKS'26, AI/ML Track)
**Owner:** M3
**Based on:** RepSync SRS v2.0 (16 Oct 2026)
**Document version:** M3-1.0, written Sun 18 Oct 2026
**Database:** Supabase (managed Postgres, free tier)
**Online round deadline:** Tue 20 Oct 2026 (confirm exact time on Unstop)
**Feature freeze:** Mon 19 Oct, 12:00

---

## 0. How to read this document

- Day 1 and Day 2 work (repo, contracts, models, endpoints, approval state machine, SSE) is listed as **Phase 1 and 2, carried-in status**. Tick what is truly done, and anything unticked rolls into Phase 3 today.
- Phases 3 to 5 are the live plan from now to submission.
- Every task has an ID (`M3-x.y`), a priority (**P0** must, **P1** should, **F** finale) and an acceptance check.
- Dependency on other members is stated explicitly (M1 ingestion, M2 AI, M4 frontend).

---

## 1. M3 Scope and Responsibilities

| Area | M3 owns | Primary SRS refs |
|---|---|---|
| Repo and CI | Public repo, layout, Makefile, `.env.example`, GitHub Actions, PR hygiene | Judging: Working GitHub (20 pts) |
| Database | Supabase project, schema, migrations, seed data, indexes, RLS decision | Section 7 |
| Backend API | FastAPI app, all REST endpoints, validation, rate limiting, OpenAPI docs | Section 8 |
| Pipeline orchestration | Async sync job that wires M1 collection, M2 analysis, drafting, persistence | FR-2, FR-3, FR-4 |
| Real-time | SSE stream for stage, source status and TinyFish call events | FR-2.6, NFR-1 |
| Approval workflow | Draft state machine enforced server-side, audit log | FR-5 |
| Auth | Seeded demo user (P0), email and password with JWT (P1), Google OAuth (F) | FR-7 |
| Deployment | Backend on Render, frontend on Vercel, keep-alive, secrets, rollback tag | NFR-4, Risk register |
| QA | Pytest suite, mocked TinyFish client, E2E checklist, bug bash, secrets audit | Section 10 |
| Docs | README setup steps, API docs, deployment notes | Section 16.1 |

**Out of M3 scope:** scraping logic and extraction (M1), LLM prompts and eval (M2), UI screens (M4). M3 provides the interfaces they plug into.

---

## 2. Multi-Platform Review Collection: Backend Design

Collection must work across several distinct platforms, not just two hardcoded ones. M1 builds the per-platform collection logic; M3 builds the **platform-agnostic backend** that stores, tracks and serves it.

### 2.1 Supported platforms (registry)

| Platform key | Display name | Applies to categories | Typical TinyFish path | Prototype status |
|---|---|---|---|---|
| `google_maps` | Google Maps | restaurant, clinic, salon | Search, Fetch, Agent (scroll, more reviews) | Primary for all categories |
| `justdial` | JustDial | salon, restaurant, clinic | Search, Fetch, Agent if JS-heavy | Primary for salons; optional elsewhere |
| `tripadvisor` | Tripadvisor | restaurant | Search, Fetch, Agent if needed | Optional for restaurants |
| `zomato` | Zomato | restaurant | Search, Fetch | Primary for restaurants |
| `practo` | Practo | clinic | Search, Fetch | Primary for clinics |

Final use or skip verdicts per platform come from M1's feasibility matrix (SRS v2.0 Section 4.5). M3 must not hardcode the list.

### 2.2 Backend requirements for multi-platform support

| ID | Requirement | Pri |
|---|---|---|
| M3-MP-1 | A `platform` registry table (or config) listing key, display name, enabled flag, applicable categories, per-platform review cap (default 50) | P0 |
| M3-MP-2 | One `Source` row per outlet per platform, holding URL, status (`pending`, `running`, `success`, `partial`, `failed`, `skipped`), error text, review count, last synced time, agent steps used | P0 |
| M3-MP-3 | The sync job reads the enabled platforms for the outlet's category and runs the collector for each in parallel, with a concurrency limit of 2 for Agent runs | P0 |
| M3-MP-4 | A collector interface that M1 implements per platform: `collect(outlet, platform) -> CollectionResult` where the result contains reviews, status, steps used and TinyFish call records | P0 |
| M3-MP-5 | One failed platform never fails the whole job (per-source try/except, retry with exponential backoff via `tenacity`) | P0 |
| M3-MP-6 | Dedup at insert using the `hash_for_dedup` unique constraint (platform + author + date + first 100 characters) | P0 |
| M3-MP-7 | The platform field is stored on every review, and filtering by platform works in `GET /reviews` | P0 |
| M3-MP-8 | `GET /summary` returns a per-platform breakdown (count, average rating, % negative) | P1 |
| M3-MP-9 | Adding a new platform requires only a registry row plus an M1 collector, with no schema or API changes | P1 |
| M3-MP-10 | Platform enabled flag can be toggled via env or admin script without redeploy | F |

### 2.3 Collector contract (agree with M1 today)

```python
class CollectionResult(BaseModel):
    platform: str
    status: Literal["success", "partial", "failed"]
    reviews: list[ReviewIn]          # normalised, pre-dedup
    agent_steps_used: int = 0
    tinyfish_calls: list[TinyFishCallIn] = []
    error: str | None = None

class Collector(Protocol):
    platform: str
    async def collect(self, outlet: OutletRead, emit: EventEmitter) -> CollectionResult: ...
```

M3 passes an `emit` callback so each collector can stream `tinyfish_call` and `source_status` events straight to SSE and the Activity Log.

---

## 3. Supabase Database Specification

### 3.1 Setup decisions

| Decision | Choice | Reason |
|---|---|---|
| Hosting | Supabase free project | Managed Postgres, survives backend restarts, dashboard for demo debugging |
| Access from backend | Direct Postgres connection via SQLModel/SQLAlchemy using the **pooled connection string** (port 6543, transaction mode) | Free backends open many short connections; pooler avoids exhaustion |
| Migrations | Alembic migrations committed to repo (or SQL files in `backend/migrations/`) | Reproducible, judges can run them |
| Local dev | SQLite or a second Supabase project, selected by `DATABASE_URL` | Keeps local setup under 10 minutes |
| Row Level Security | **Off for prototype** (backend is the only client, uses the service role or direct DB credentials); document this honestly. On with per-user policies at Finale if the frontend ever talks to Supabase directly | Avoids policy debugging in a 4-day sprint |
| Supabase Auth | Not used in prototype (own JWT). Revisit for Google OAuth at Finale | Keeps one auth path |
| Secrets | `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` in env only. The service key never goes to the frontend or git | NFR-4 |

> **Free-tier cautions (verify on your Supabase dashboard):** free projects can be paused after a period of inactivity, and have storage and connection limits. Open the project daily, and keep the keep-alive ping hitting a lightweight DB-touching endpoint so the project stays active until submission.

### 3.2 Schema (Postgres DDL outline)

```sql
-- users
create table app_user (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  email text unique not null,
  password_hash text,
  created_at timestamptz default now()
);

create table tone_profile (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references app_user(id) on delete cascade,
  style text not null default 'warm',
  sample_replies jsonb default '[]',
  do_not_say jsonb default '[]'
);

create table outlet (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references app_user(id) on delete cascade,
  name text not null,
  category text not null check (category in ('restaurant','clinic','salon')),
  city text not null,
  address text,
  tone_profile_id uuid references tone_profile(id),
  is_demo boolean default false,
  created_at timestamptz default now()
);

create table platform (
  key text primary key,                -- google_maps, justdial, tripadvisor, zomato, practo
  display_name text not null,
  enabled boolean default true,
  categories text[] not null,
  review_cap int default 50
);

create table source (
  id uuid primary key default gen_random_uuid(),
  outlet_id uuid references outlet(id) on delete cascade,
  platform text references platform(key),
  url text,
  status text not null default 'pending',
  error text,
  review_count int default 0,
  agent_steps_used int default 0,
  last_synced_at timestamptz,
  unique (outlet_id, platform)
);

create table review (
  id uuid primary key default gen_random_uuid(),
  outlet_id uuid references outlet(id) on delete cascade,
  source_id uuid references source(id) on delete cascade,
  platform text not null,
  author text,
  rating numeric(2,1),
  text text,
  language text,
  posted_at timestamptz,
  url text,
  owner_reply_text text,
  has_owner_reply boolean default false,
  sentiment text check (sentiment in ('positive','neutral','negative')),
  severity int check (severity between 1 and 3),
  rating_text_mismatch boolean default false,
  hash_for_dedup text not null,
  unique (outlet_id, hash_for_dedup)
);
create index on review (outlet_id, platform);
create index on review (outlet_id, sentiment);

create table theme (
  id uuid primary key default gen_random_uuid(),
  outlet_id uuid references outlet(id) on delete cascade,
  label text not null,
  description text,
  created_at timestamptz default now()
);

create table review_theme (
  review_id uuid references review(id) on delete cascade,
  theme_id uuid references theme(id) on delete cascade,
  confidence real,
  primary key (review_id, theme_id)
);

create table fix_suggestion (
  id uuid primary key default gen_random_uuid(),
  outlet_id uuid references outlet(id) on delete cascade,
  rank int not null,
  title text not null,
  rationale text,
  evidence_count int
);

create table reply_draft (
  id uuid primary key default gen_random_uuid(),
  review_id uuid references review(id) on delete cascade,
  text text not null,
  status text not null default 'draft'
    check (status in ('draft','edited','approved','rejected','posted')),
  version int default 1,
  prompt_version text,
  guardrail_flags jsonb default '[]',
  edited_by uuid references app_user(id),
  approved_at timestamptz
);

create table audit_log (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references app_user(id),
  action text not null,
  entity text not null,
  entity_id uuid,
  timestamp timestamptz default now()
);

create table tinyfish_call (
  id uuid primary key default gen_random_uuid(),
  outlet_id uuid references outlet(id) on delete cascade,
  platform text,
  endpoint text not null check (endpoint in ('search','fetch','agent')),
  input jsonb,
  status text,
  duration_ms int,
  items_returned int,
  steps_used int default 0,
  cached boolean default false,
  created_at timestamptz default now()
);

create table cache_entry (
  cache_key text primary key,          -- hash of (endpoint, input)
  payload jsonb not null,
  created_at timestamptz default now(),
  expires_at timestamptz
);
```

Notes:
- `platform`, `source.review_count`, `source.agent_steps_used`, `tinyfish_call.platform/steps_used` and `review.rating_text_mismatch` are small additions over SRS v2.0 to support multi-platform tracking and the Agent cost policy. Announce them to M1, M2 and M4 as a contract change.
- Deleting an outlet cascades to all its data (NFR-5).

### 3.3 Database tasks and acceptance

| ID | Task | Pri | Acceptance |
|---|---|---|---|
| M3-DB-1 | Create Supabase project, store credentials in a shared password manager (not chat or git) | P0 | All 4 members can connect with their own `.env` |
| M3-DB-2 | Run schema migration, commit migration files | P0 | `make migrate` creates all tables on an empty DB |
| M3-DB-3 | Seed `platform` registry rows and the demo user | P0 | `make seed` is idempotent |
| M3-DB-4 | Seed two demo outlets from M1's cached datasets in `data/demo` | P0 | Demo mode loads in under 3 s with all external APIs disabled |
| M3-DB-5 | Indexes and unique constraints for dedup | P0 | Re-running sync does not create duplicate reviews |
| M3-DB-6 | Pooled connection string and sane pool size for Render | P0 | No "too many connections" under 3 concurrent syncs |
| M3-DB-7 | Daily DB touch via keep-alive | P1 | Project not paused before submission |
| M3-DB-8 | Optional RLS policies | F | Documented, off for prototype |

---

## 4. Backend API Requirements

All endpoints from SRS v2.0 Section 8 remain. M3 adds the multi-platform and ops items below.

### 4.1 Endpoint checklist

| Method | Endpoint | Pri | Notes |
|---|---|---|---|
| POST | `/api/outlets/search` | P0 | Calls M1 `search_candidates(name, city, category)` |
| POST | `/api/outlets` | P0 | Creates outlet and one `source` row per enabled platform for the category |
| POST | `/api/outlets/demo/{key}` | P0 | Loads cached demo data, no external calls |
| POST | `/api/outlets/{id}/sync` | P0 | Returns a job id immediately, then runs in background |
| GET | `/api/outlets/{id}/sync/stream` | P0 | SSE, see 4.2 |
| GET | `/api/outlets/{id}/reviews` | P0 | Filters: platform (multi), rating, sentiment, theme, has_owner_reply; pagination |
| GET | `/api/outlets/{id}/themes` | P0 | Counts, percentages, quotes |
| GET | `/api/outlets/{id}/fixes` | P0 | Top 3 |
| GET | `/api/outlets/{id}/summary` | P0 | Avg rating, total, % negative, unanswered negatives, per-platform split (P1) |
| GET | `/api/outlets/{id}/sources` | P0 | Per-platform status for the live progress UI |
| GET | `/api/outlets/{id}/tinyfish-log` | P0 | Activity Log entries including steps used |
| GET | `/api/platforms` | P1 | Platform registry for UI filters |
| POST | `/api/reviews/{id}/draft` | P0 | Optional instruction for regenerate (P1) |
| PATCH | `/api/drafts/{id}` | P0 | Edit or status change, with transition validation |
| PUT | `/api/tone` | P0 | Save tone profile |
| POST | `/api/auth/signup`, `/api/auth/login` | P1 | bcrypt and JWT |
| DELETE | `/api/outlets/{id}` | P0 | Cascade delete |
| GET | `/health` | P0 | Cheap, no DB (for uptime pings) |
| GET | `/health/db` | P1 | Touches Supabase (keep-alive target) |

### 4.2 SSE event contract (frozen)

```json
{ "type": "source_status|tinyfish_call|stage|done",
  "source": "google_maps",
  "status": "running|success|partial|failed",
  "message": "Fetch: JustDial OK, 38 reviews",
  "ts": "2026-10-18T06:00:00Z" }
```

Stages in order: `searching`, `collecting`, `normalising`, `analysing`, `drafting`, `done`. Include `platform` on every collection event so the UI can light up each source individually.

### 4.3 Approval state machine (FR-5)

| From | To (allowed) |
|---|---|
| draft | edited, approved, rejected |
| edited | edited, approved, rejected |
| approved | posted, edited (re-approval required afterwards) |
| rejected | draft (via regenerate) |
| posted | none |

Rules: transitions are validated in the API layer (return 409 on invalid). Only `PATCH` with explicit `status=approved` can approve. Regeneration resets status to `draft` and bumps `version`. Every transition writes an `audit_log` row.

### 4.4 Cross-cutting backend requirements

| ID | Requirement | Pri |
|---|---|---|
| M3-API-1 | Pydantic v2 request and response models; OpenAPI at `/docs` | P0 |
| M3-API-2 | CORS limited to the deployed frontend origin and localhost | P0 |
| M3-API-3 | Consistent error shape `{error, detail, code}` | P0 |
| M3-API-4 | Rate limiting (for example `slowapi`) on sync and search endpoints | P1 |
| M3-API-5 | Prevent concurrent syncs for the same outlet (return the existing job) | P0 |
| M3-API-6 | Input validation: name and city length, category enum | P0 |
| M3-API-7 | Request logging with a correlation id; no secrets in logs | P1 |
| M3-API-8 | Agent step budget guard: refuse live Agent runs when the daily cap is reached and fall back to cache | P1 |

---

## 5. Pipeline Orchestration (Sync Job)

```
POST /sync
  -> create job (in-memory registry + DB status)
  -> stage: searching     (M1: find review URLs per platform, update source.url)
  -> stage: collecting    (parallel per platform, Agent concurrency <= 2)
        each collector: Fetch -> count -> escalate to Agent if needed
        persist reviews with dedup, update source status, log TinyFish calls
  -> stage: normalising   (language detect, cleanup; M2/M1 utilities)
  -> stage: analysing     (M2: sentiment, topics, themes, fixes) -> persist
  -> stage: drafting      (M2: draft per negative review) -> persist with guardrail flags
  -> stage: done
```

| ID | Requirement | Pri |
|---|---|---|
| M3-PIPE-1 | Job runs as `asyncio` task via FastAPI `BackgroundTasks`, with no Celery or Redis | P0 |
| M3-PIPE-2 | Each stage emits events and persists output before the next stage begins (crash-safe, partial results usable) | P0 |
| M3-PIPE-3 | First partial results appear within 20 s, full dashboard within 60 to 90 s (NFR-1) | P0 |
| M3-PIPE-4 | If live collection fails for all sources, fall back to the cached dataset and mark the run as cached | P0 |
| M3-PIPE-5 | Re-sync is idempotent (dedup prevents duplicates) and skips analysis if no new reviews arrived | P1 |
| M3-PIPE-6 | Cache lookups use `cache_entry` keyed by hash of (endpoint, input) with 24 h TTL for Agent results | P0 |
| M3-PIPE-7 | Job state survives a page refresh: `GET /sources` plus `GET /sync/stream` can rejoin a running job | P1 |
| M3-PIPE-8 | Mocked collector and mocked LLM selectable by env flag (`MOCK_TINYFISH=1`, `MOCK_LLM=1`) for CI and demo mode | P0 |

---

## 6. Authentication and Security

| ID | Requirement | Pri |
|---|---|---|
| M3-SEC-1 | Seeded demo user and a simple "continue as demo" login | P0 |
| M3-SEC-2 | Email and password signup/login, bcrypt hashing, JWT with expiry | P1 |
| M3-SEC-3 | Every outlet endpoint checks the outlet belongs to the caller (demo outlets readable by the demo user) | P1 |
| M3-SEC-4 | Secrets only in env vars, `.env.example` lists all keys with dummy values | P0 |
| M3-SEC-5 | Secrets audit before submission: scan git history (for example `gitleaks`) and rotate anything that leaked | P0 |
| M3-SEC-6 | HTTPS only in deployment, security headers, request size limits | P1 |
| M3-SEC-7 | Delete-outlet endpoint removes all related data (privacy, DPDP awareness) | P0 |
| M3-SEC-8 | Google OAuth | F |

---

## 7. DevOps, Repository and Deployment

### 7.1 Repository and CI

| ID | Requirement | Pri |
|---|---|---|
| M3-OPS-1 | Public repo with the agreed layout, all 4 members' commits visible daily | P0 |
| M3-OPS-2 | Makefile targets: `setup`, `dev`, `test`, `lint`, `migrate`, `seed` | P0 |
| M3-OPS-3 | GitHub Actions: ruff, pytest (mocked TinyFish and LLM), frontend build; CI badge in README | P0 |
| M3-OPS-4 | Branch protection: PRs with at least one reviewer, small commits with clear messages | P0 |
| M3-OPS-5 | `.env.example` with `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `TINYFISH_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`, `JWT_SECRET`, `FRONTEND_ORIGIN`, `MOCK_TINYFISH`, `MOCK_LLM` | P0 |

### 7.2 Deployment

| ID | Requirement | Pri |
|---|---|---|
| M3-DEP-1 | Backend on Render free web service, start command via Uvicorn, env vars set in the dashboard | P0 |
| M3-DEP-2 | Frontend on Vercel, auto-deploy from `main`, API base URL via env | P0 |
| M3-DEP-3 | Keep-alive: an external pinger (for example UptimeRobot or a GitHub Actions cron) hits `/health` every ~10 minutes, plus `/health/db` daily to keep Supabase active | P0 |
| M3-DEP-4 | Warm up the backend and open Supabase before every rehearsal and recording | P0 |
| M3-DEP-5 | Rollback tag (`v0.9-stable`) on the last known good commit before freeze | P0 |
| M3-DEP-6 | Local backup run (`make dev` with demo mode) ready if the hosted backend misbehaves | P0 |

---

## 8. Quality Assurance Requirements

| ID | Test | Pri | Maps to acceptance criterion |
|---|---|---|---|
| M3-QA-1 | Pytest: approval state machine (all valid and invalid transitions, API-level) | P0 | #4 |
| M3-QA-2 | Pytest: dedup (same review twice yields one row; same text on different platforms yields two) | P0 | FR-2.5 |
| M3-QA-3 | Pytest: sync job with mocked collectors, where one platform fails and the run still completes with that source marked `failed` | P0 | #6 |
| M3-QA-4 | Pytest: filters on `/reviews`, summary metrics, unanswered negatives calculation | P0 | FR-6 |
| M3-QA-5 | Pytest: delete outlet cascades | P1 | NFR-5 |
| M3-QA-6 | Demo mode works with all external APIs disabled | P0 | #7 |
| M3-QA-7 | Manual E2E checklist on the deployed site using 3 fresh outlets across categories | P0 | #1 |
| M3-QA-8 | Kill-switch test: disable one platform's collector and confirm UI shows status and no crash | P0 | #6 |
| M3-QA-9 | Smoke test script (`scripts/smoke.sh`) hitting health, demo load, summary, drafts | P1 | #7 |
| M3-QA-10 | Bug bash with the other three members, logged as GitHub issues | P0 | all |

---

## 9. Phase-wise Plan (M3)

### Phase 1: Foundation (Fri 16 Oct, Day 1) — carried-in status

| Task | Status |
|---|---|
| Public repo, layout, Makefile, `.env.example`, CI skeleton | ☑ completed |
| Data model and API contract frozen and announced | ☑ completed |
| Stub endpoints returning mock JSON, OpenAPI live | ☑ completed |
| Supabase project created, credentials shared securely | ☑ completed |

**Gate (was Fri 10 pm):** repo public, contract frozen.

### Phase 2: Core backend (Sat 17 Oct, Day 2) — carried-in status

| Task | Status |
|---|---|
| Tables created on Supabase, platform registry seeded | ☑ completed |
| Outlet, review, theme, draft endpoints on real DB | ☑ completed |
| SSE stream working with mock events | ☑ completed |
| Approval state machine with tests | ☑ completed |
| Demo-mode endpoint | ☑ completed |
| First deploy started | ☑ completed |


**Anything unticked moves to the top of Phase 3.** Approval state machine, DB on Supabase and demo mode are the non-negotiables.

---

### Phase 3: Integration and first deployment (TODAY, Sun 18 Oct, Day 3)

**Goal:** by 10 pm, entering a business name on the deployed site shows reviews from multiple platforms, themes, fixes and drafts, and demo mode works offline.

| Time (IST) | Task | ID | Depends on | Deliverable |
|---|---|---|---|---|
| 11:30 to 12:30 | Close any Phase 2 gaps; run migrations on Supabase; seed `platform` registry and demo user | M3-DB-2/3 | none | Clean DB with seed data |
| 12:30 to 13:30 | Agree collector contract (Section 2.3) and `CollectionResult` with M1; add per-platform fields (`steps_used`, `platform`) to `tinyfish_call` and `source` | M3-MP-4 | M1 | Contract note posted to the team |
| 13:30 to 16:00 | Build the sync orchestrator: per-category platform selection, parallel collectors, Agent concurrency of 2, retries, per-source status, persistence with dedup | M3-PIPE-1/2, M3-MP-3/5/6 | M1 collectors (use mocks until ready) | `POST /sync` end to end on mocks |
| 16:00 to 17:00 | Wire M2 analysis and drafting into stages; persist themes, fixes and drafts with guardrail flags | M3-PIPE-2 | M2 functions | Full pipeline on mocked collectors |
| 17:00 to 18:00 | SSE events from every stage and every collector call; `GET /sources`, `GET /tinyfish-log` | 4.2 | M4 (consumes it) | M4 can render live progress |
| 18:00 to 19:30 | Load M1's cached demo datasets into Supabase via `make seed`; verify demo mode with all external APIs off | M3-DB-4, M3-QA-6 | M1 datasets | Demo mode under 3 s |
| 19:30 to 21:00 | Deploy backend on Render and frontend on Vercel; set env vars; CORS; keep-alive pinger; `/health` and `/health/db` | M3-DEP-1/2/3, M3-API-2 | M4 build | Deployed E2E link |
| 21:00 to 22:00 | Smoke test on the deployed link, filters, audit log, fix the top blockers; tag `v0.8-integration` | M3-QA-9 | all | **Gate passed** |

**Phase 3 exit criteria**
- [x] Deployed site: name + city, confirm, sync runs, at least 2 distinct platforms show per-source status
- [x] Reviews, themes, fixes, drafts visible in the UI
- [x] Failed platform does not crash the run
- [x] Demo mode works offline
- [x] Supabase tables hold the data (verify in the Supabase table editor)


**Phase 3 risks and fallbacks**
| Risk | Fallback |
|---|---|
| M1 collector for a platform is not ready | Run the pipeline with the collectors that exist, mark others `skipped`, and keep the registry flag off |
| Render build or cold-start issues | Deploy a minimal `/health` first, then add routes; keep local run as backup |
| Supabase connection errors | Use the pooled string, `sslmode=require`, and reduce pool size |
| Pipeline too slow | Cap reviews per platform (50), run platforms in parallel, stream partial results |

---

### Phase 4: Harden, freeze, record (Mon 19 Oct, Day 4)

**Feature freeze: 12:00.** After that, only bug fixes and submission assets.

| Time (IST) | Task | ID | Deliverable |
|---|---|---|---|
| 09:00 to 10:00 | Morning stand-up; triage Day 3 bugs; finish unfinished P0 items | all | Bug list |
| 10:00 to 12:00 | P1 items if time: email/password auth with JWT, ownership checks, per-platform summary split, rate limiting, concurrent-sync guard, Agent step budget guard | M3-SEC-2/3, M3-MP-8, M3-API-4/5/8 | Auth and guards merged |
| **12:00** | **Feature freeze.** Tag `v0.9-stable` | M3-DEP-5 | Rollback point |
| 12:00 to 14:00 | Pytest suite complete (QA-1 to QA-5), CI green, coverage on state machine, dedup, partial failure | M3-QA-1..5 | Green CI badge |
| 14:00 to 15:30 | Bug bash with the team on 5+ real businesses across categories and platforms; log issues and triage | M3-QA-7/10 | Issue list closed or deferred |
| 15:30 to 16:30 | Kill-switch test per platform; demo mode with APIs disabled; cold-start check | M3-QA-6/8 | Test notes |
| 16:30 to 17:30 | Secrets audit (gitleaks on full history); rotate anything exposed; verify `.env.example` | M3-SEC-5 | Audit clean |
| 17:30 to 19:00 | README setup steps (5 commands), env variable table, deployment notes, API docs link, supported platforms table | Section 10 below | README merged |
| 19:00 to 20:00 | Final deploy of stable build; verify Supabase seed, keep-alive and CORS on production | M3-DEP-* | Production stable |
| 20:00 to 22:00 | Support M4 on the video and pricing page; two full rehearsals with warmed-up backend | M3-DEP-4 | **Gate: everything submittable exists; public links tested in incognito** |

**Phase 4 exit criteria**
- [x] CI green, tests cover approval transitions, dedup and partial failure
- [x] No secrets in git history
- [x] README lets a stranger run the project in under 10 minutes
- [x] Rollback tag exists; local demo-mode backup runs
- [x] Smoke test and documentation deliverables in docs/


---

### Phase 5: Submit (Tue 20 Oct, Day 5)

| Time (IST) | Task | Deliverable |
|---|---|---|
| 08:00 | Warm up Render and Supabase; open the deployed site in an incognito window | Warm backend |
| 08:30 to 09:30 | Final smoke test (`scripts/smoke.sh`): health, demo load, one live sync on a fresh outlet, approve a draft, delete an outlet | Smoke test pass |
| 09:30 to 10:30 | Confirm repo is public, README renders, CI badge green, all 4 members have visible commits, license and screenshots present | Repo checklist |
| 10:30 | Keep rollback ready; **no new features or risky deploys** | Stable |
| Before noon | Support M4 submission on Unstop; confirm all links open in incognito | Submitted |
| After submit | Keep the pinger running until results; watch Render and Supabase dashboards | Monitoring |

Target: submit before noon, well ahead of the deadline hour.

---

### Phase 6: Finale (21 Oct to 1 Nov, only if shortlisted)

| Task | ID | Pri |
|---|---|---|
| Google OAuth (Supabase Auth or own flow) | M3-SEC-8 | F |
| Scheduled re-sync (cron endpoint or Supabase scheduled function) with incremental sync | FR-2.9 | F |
| New 1-2 star review alerts (in-app or email), weekly digest | FR-8.* | F |
| Multi-outlet switcher and agency view endpoints | FR-7.3/7.4 | F |
| Test-mode billing endpoints | FR-7.2 | F |
| Row Level Security policies and security review | M3-DB-8 | F |
| Additional platform onboarding via registry only | M3-MP-9/10 | F |
| Hour 0 to 2 of finale: agree the one big feature; Hour 2 to 16: keep `main` deployable and own the demo environment | | F |

---

## 10. Documentation Deliverables (M3)

| Item | Content |
|---|---|
| README sections | Setup in 5 commands (`make setup`, set `.env`, `make migrate`, `make seed`, `make dev`), env variable table, demo mode, deployment guide, supported platforms table, CI badge |
| `docs/architecture.png` | Excalidraw diagram of frontend, FastAPI, Supabase, TinyFish, LLM (co-owned with M1) |
| `docs/api.md` or OpenAPI link | Endpoint list and SSE contract |
| `docs/database.md` | ER diagram, table descriptions, Supabase notes, RLS stance |
| `docs/testing.md` | How to run tests, manual E2E checklist, smoke script |

---

## 11. Dependencies and Handoffs

| From / To | What M3 needs or provides | By when |
|---|---|---|
| M1 to M3 | `Collector` implementations per platform, cached demo datasets, `search_candidates()` | Today 16:00 (mocks until then) |
| M2 to M3 | `analyze()`, `generate_reply()`, guardrail check function signatures | Today 16:00 |
| M3 to M4 | Stable API base URL, SSE contract, sample responses, `GET /platforms` | Today 12:30 |
| M3 to all | Supabase credentials (secure channel), schema change notices | Today morning |
| M3 to M4 | Deployed URLs for video and submission | Today 21:00 |

**Rule:** any schema or contract change is announced to all four before merging.

---

## 12. Risks (M3-specific)

| Risk | Impact | Mitigation |
|---|---|---|
| Supabase free project pauses or hits limits | Demo breaks | Daily DB touch, pooled connection, local SQLite and demo-data fallback |
| Render cold start | App looks frozen | Keep-alive pings, warm-up before demos, local backup |
| A platform (for example JustDial or Tripadvisor) blocks collection | Missing data | Registry flag to disable it, per-source status, cached demo data, M1's feasibility verdicts |
| Collector contract mismatch with M1 | Integration delay | Agree `CollectionResult` today, use mocks until M1 ships |
| Agent credits spent by mistake | No live demo | Step budget guard, 24 h cache, `MOCK_TINYFISH` for development |
| Secrets leaked in git | Credibility and security | Gitleaks audit, rotate keys, `.env` in `.gitignore` |
| Late deploy bugs | Missed submission | Freeze at Mon 12:00, rollback tag, no Tuesday risky changes |

**Drop order if time runs out (M3 items):** Google OAuth, per-platform summary split, rate limiting, email/password auth (keep demo login), then `/health/db` extras. Never drop: Supabase persistence, approval state machine, partial-failure handling, demo mode, secrets audit, README.

---

## 13. Final M3 Acceptance Checklist

- [ ] Public repo with commits from M3 every day, CI badge green
- [ ] Supabase holds all tables; `make migrate` and `make seed` work on an empty DB
- [ ] Platform registry drives collection; at least 2 distinct platforms collected per outlet, with per-source status
- [ ] A failed platform does not break the run
- [ ] Dedup verified by test
- [ ] Draft cannot be approved except via explicit approve (API test)
- [ ] SSE streams stage, source status and TinyFish call events
- [ ] Activity Log endpoint returns Search, Fetch and Agent calls with steps used
- [ ] Deployed backend and frontend working on a fresh outlet; demo mode works with external APIs disabled
- [ ] Delete outlet removes all data
- [ ] No secrets in git history; `.env.example` complete
- [ ] README setup works for a stranger in under 10 minutes
- [ ] Rollback tag exists

---

*End of M3 SRS. Update the status boxes in Phases 1 and 2 first, then work top to bottom through Phase 3.*
