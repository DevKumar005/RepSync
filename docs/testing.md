# RepSync Quality Assurance & Testing Guide

This document describes the automated and manual testing procedures for **RepSync** (M3 Role).

---

## 1. Automated Test Suite (Pytest)

The Pytest suite in `backend/tests/test_backend.py` contains 13 focused tests covering all SRS Section 8 requirements:

```bash
# Run pytest with verbose reporting
make test
```

### Coverage Matrix:

| Test Name | SRS Ref | Acceptance Criterion Verified |
|---|---|---|
| `test_approval_state_machine_valid_transitions` | M3-QA-1, FR-5 | Valid transitions (`draft` $\rightarrow$ `edited` $\rightarrow$ `approved` $\rightarrow$ `posted`) |
| `test_approval_state_machine_invalid_transitions_409` | M3-QA-1, FR-5 | Invalid transitions (e.g. `draft` $\rightarrow$ `posted`) return HTTP 409 |
| `test_dedup_hash_logic` | M3-QA-2, FR-2.5 | Identical reviews produce identical hash; cross-platform produces distinct hashes |
| `test_dedup_database_insertion` | M3-QA-2, FR-2.5 | Re-running sync does not insert duplicate review rows |
| `test_partial_failure_sync_pipeline` | M3-QA-3, #6 | A failed platform marks source `failed` without failing the overall sync |
| `test_reviews_filtering` | M3-QA-4, FR-6 | Filtering `/reviews` by platform and sentiment |
| `test_summary_metrics_and_platform_split` | M3-QA-4, M3-MP-8 | Total reviews, avg rating, % negative, and per-platform split |
| `test_cascade_delete_outlet` | M3-QA-5, NFR-5 | Deleting an outlet cascade-cleans reviews, themes, drafts, and sources |
| `test_demo_mode_endpoint_offline` | M3-QA-6, #7 | Demo endpoint returns seeded outlet with external APIs disabled (<3s) |
| `test_health_endpoints` | M3-DEP-3 | `/health` and `/health/db` return 200 OK |
| `test_correlation_id_middleware` | M3-API-7 | Every response returns `X-Correlation-ID` header |
| `test_outlet_ownership_forbidden_for_different_user` | M3-SEC-3 | Modifying another owner's private outlet returns 403 Forbidden |
| `test_agent_step_budget_guard` | M3-API-8 | When daily step budget is exhausted, live agent runs are skipped safely |

---

## 2. Smoke Testing

Run the automated smoke test script against a running local or deployed server:

```bash
# Local test
python scripts/smoke.py http://localhost:8000

# Remote Render deployment test
python scripts/smoke.py https://repsync-backend.onrender.com
```

The smoke test validates:
1. `/health` ping
2. `/health/db` database keep-alive touch
3. Platform registry lookup
4. Instant demo mode load (<3s)
5. Reviews and KPI summary metrics
6. Draft approval state transition

---

## 3. Secrets Audit

Run the secrets audit script before pushing code:

```bash
make audit
# or: python scripts/audit_secrets.py
```

Scans the working tree and the last 30 commits in git history for accidental leaks of OpenAI/TinyFish keys, Gemini API keys, Groq API keys, or database credentials.

---

## 4. Manual E2E Checklist

Before rehearsals and submission recordings, execute this manual flow:

- [ ] **Warm-up**: Ping `/health` to verify Render backend is active.
- [ ] **Demo Mode**: Click "Try Demo Mode" on frontend $\rightarrow$ verify *Kake Da Dhaba* loads under 3s with reviews, themes, and drafts.
- [ ] **Live Sync**: Register a new outlet $\rightarrow$ start sync $\rightarrow$ verify SSE progress updates (stages 1 to 5) and sources light up.
- [ ] **Filter Check**: Select "Google Maps" filter $\rightarrow$ confirm only Google Maps reviews appear.
- [ ] **Draft Action**: Edit a reply draft $\rightarrow$ status changes to "edited" $\rightarrow$ click "Approve" $\rightarrow$ status changes to "approved".
- [ ] **Delete Outlet**: Delete the test outlet $\rightarrow$ confirm it disappears from dashboard with no orphaned records in database.
