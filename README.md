# RepSync

> **Turn messy multi-platform customer reviews into actionable operational fixes and tone-aware, owner-approved replies in minutes.**

Built for **KRITICAL HACKS '26** (AI/ML Track) · Powered by **TinyFish Web AI** & **Gemini 2.5/3.8 Flash**.

---

## The Problem
Small local business owners (restaurants, clinics, salons) lose customers due to negative reviews scattered across Zomato, Practo, EazyDiner, and Lybrate. Owners lack the time to monitor fragmented websites, cannot afford enterprise tools ($100+/mo), and struggle to draft polite, contextual replies that protect their brand.

## What RepSync Does
* **Multi-Platform Ingestion:** Enter business name and city to aggregate reviews across public platforms without API keys.
* **Smart Themes & Sentiment:** Clusters complaints into actionable operational buckets (e.g., *wait time, billing, hygiene, staff behavior*) with exact quotes and counts.
* **Top 3 Fixes:** Recommends prioritized operational improvements backed by review evidence counts.
* **Tone-Aware AI Reply Drafts:** Generates contextual replies matching the customer's language (English/Hindi/Hinglish) with strict safety guardrails (no liability, no medical advice).
* **Owner-in-the-Loop:** Explicit approve, edit, or reject workflow before anything is posted.
* **Live TinyFish Activity Log:** Real-time visibility into every web automation step via Server-Sent Events (SSE).

---

## Unit Economics & Business Model

| Tier | Price / Month | Ideal For |
| :--- | :--- | :--- |
| **Starter** | ₹499 (~$6) | 1 outlet, weekly sync, core dashboard |
| **Growth** | ₹999 (~$12) | 1 outlet, daily sync, Top 3 fixes, AI reply drafts |
| **Multi / Agency** | ₹1,999 (~$24) | Up to 3 outlets, priority sync, audit logs |

* **Metered Agent Rate:** $0.016 / step
* **Measured Cold Sync:** 19.5 steps ($0.312) per outlet onboarding
* **Measured Warm / Re-sync:** 7.4 steps ($0.118) with 24-hour cache active
* **Recurring Data Ingestion Cost:** ~$1.40 – $2.10 / month per outlet
* **Gross Margin:** **78% – 82%** on the ₹999 Growth Plan (comfortably exceeding the ≥70% requirement).

---

## Tech Stack

* **Frontend:** React 18, Vite, TypeScript, Tailwind CSS, shadcn/ui, Recharts
* **Backend:** Python 3.12, FastAPI, Uvicorn, SQLModel / SQLAlchemy, Pydantic v2
* **Web Automation:** TinyFish SDK (`tinyfish`)
* **LLM Engine:** Gemini API (`gemini-3.8-flash`) with Groq fallback (`llama-3.3-70b-versatile`)
* **Streaming & Jobs:** Server-Sent Events (`sse-starlette`), `asyncio` background tasks
* **Database:** SQLite (local development) / Neon PostgreSQL (production)

---

## Legal & Compliance Stance

- **Public Data Only:** RepSync accesses only publicly viewable customer reviews.
- **Zero Credential Scraping:** No login-gated data or user accounts are accessed.
- **Owner-Initiated:** Audits and collection runs are triggered solely by the business owner.
- **Owner-Approved Output:** AI-generated replies are suggestions only. No reply is posted automatically without explicit owner sign-off.

---

## 👥 Team — Fine Shyts

| # | Member | Domain | Contributions |
|:---:|:---|:---|:---|
| 1 | **[Dev](https://github.com/DevKumar005)** | Team Lead & TinyFish Data Engineer |  |
| 2 | **[M2](https://github.com/)** | AI/LLM Engineer & Business Analyst |  |
| 3 | **[M3](https://github.com/)** | Backend, Database & DevOps Engineer |  |
| 4 | **[M4](https://github.com/)** | Frontend, UI/UX & Product Storyteller|  |

---