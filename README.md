# RepSync: Local Business Reputation Manager

[![RepSync CI](https://github.com/DevKumar005/RepSync/actions/workflows/ci.yml/badge.svg)](https://github.com/DevKumar005/RepSync/actions)

RepSync synchronizes and unifies fragmented customer review streams across multiple platforms (Google Maps, Zomato, JustDial, Practo, Tripadvisor) into a single actionable dashboard. It provides automated sentiment analysis, operational fix recommendations, and an approval-governed AI reply workflow for business owners.

---

## 🌐 Live Production Deployment

* **Live API Base URL:** `https://repsync-backend.onrender.com`
* **Interactive Swagger UI:** [https://repsync-backend.onrender.com/docs](https://repsync-backend.onrender.com/docs)
* **Health Check Endpoint:** [https://repsync-backend.onrender.com/health](https://repsync-backend.onrender.com/health)
* **Supabase Database:** Hosted on AWS Singapore (`aws-0-ap-southeast-1.pooler.supabase.com:6543`) with direct transaction pooling.

---

## ⚡ Quickstart in 5 Commands

```bash
# 1. Setup virtual environment & install dependencies
make setup

# 2. Configure environment keys
cp .env.example .env

# 3. Create database tables
make migrate

# 4. Seed platform registry, demo user, and demo datasets
make seed

# 5. Start development API server
make dev
```
Open **[http://localhost:8000/docs](http://localhost:8000/docs)** to inspect the interactive OpenAPI documentation.

---

## 🛠️ Supported Platforms Registry

| Platform Key | Display Name | Applicable Categories | Mode |
|---|---|---|---|
| `google_maps` | Google Maps | Restaurant, Clinic, Salon | Search, Fetch & Web Agent |
| `zomato` | Zomato | Restaurant | Search & Fetch |
| `justdial` | JustDial | Salon, Restaurant, Clinic | Search, Fetch & Agent |
| `practo` | Practo | Clinic | Search & Fetch |
| `tripadvisor` | Tripadvisor | Restaurant | Search & Fetch |

---

## 🔒 Approval State Machine (FR-5)

All customer reply drafts follow a strict server-side state machine with audit logging:

```
[draft] ──(edit)──> [edited] ──(approve)──> [approved] ──(post)──> [posted]
   │                   │                         │
   └──(reject)───────> [rejected]                └──(edit)──> [edited] (re-approval needed)
                         │
                         └──(regenerate)──> [draft]
```

Invalid transitions return HTTP `409 Conflict`. Every status change and text edit is captured in the `audit_log` table.

---

## ⚙️ Environment Variables

| Variable | Description | Default / Example |
|---|---|---|
| `DATABASE_URL` | Supabase pooled Postgres or local SQLite URL | `sqlite:///./repsync.db` |
| `SUPABASE_URL` | Supabase project API URL | `https://your-project.supabase.co` |
| `SUPABASE_SERVICE_KEY` | Supabase service role key (backend only) | `your-service-key` |
| `TINYFISH_API_KEY` | TinyFish API key for Search, Fetch & Agent | `sk-tinyfish-...` |
| `GEMINI_API_KEY` | Google Gemini API key | `AIzaSy...` |
| `GROQ_API_KEY` | Groq API key (fallback provider) | `gsk_...` |
| `JWT_SECRET` | Secret key for JWT session tokens | `repsync-secret-dev-jwt` |
| `FRONTEND_ORIGIN` | Allowed CORS frontend URL | `http://localhost:5173` |
| `MOCK_TINYFISH` | Set `1` to run offline/mocked scraping | `0` |
| `MOCK_LLM` | Set `1` to run offline/rule-based analysis | `0` |

---

## 🧪 Testing & Quality Assurance

```bash
# Run complete test suite (state machine, dedup, partial failure, filters, cascade delete)
make test

# Run linter
make lint

# Run end-to-end smoke test against local or deployed server
python scripts/smoke.py http://localhost:8000
```
