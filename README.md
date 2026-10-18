<!-- <<<<<<< HEAD
# RepSync
Combines reputation management with multi-platform synchronization. 
It synchronizes/brings together fragmented data streams from multiple distinct platforms (Google, Justdial, TripAdvisor, etc.) into a single unified feed and dashboard
=======
# RepSync frontend (M4)

React 18 + Vite + TypeScript + Tailwind + Recharts + TanStack Query + React Router.

```bash
cp .env.example .env     # VITE_USE_MOCK=true runs with no backend
npm install
npm run dev              # http://localhost:5173
npm run build            # typecheck + production build
```

Switch to the real API: set `VITE_USE_MOCK=false` and `VITE_API_URL` to the FastAPI base URL.
All calls live in `src/api/client.ts`, one function per endpoint in the SRS (section 8).
The sync stream uses `EventSource` and expects default `data:` messages shaped like `SyncEvent` in `src/types.ts`.

Screens: Find outlet and confirm, Dashboard (summary, Top 3 fixes, themes, review feed, reply queue, TinyFish activity), Reply tone, Pricing.

Dark mode: toggle in the header. First visit follows the OS setting, then your choice is remembered. Colours are CSS variables in `src/index.css`, so change a palette in one place.
>>>>>>> b9510f0 (Frontend added.) -->
# RepSync

Combines reputation management with multi-platform synchronization. It synchronizes/brings together fragmented data streams from multiple distinct platforms (Google, Justdial, TripAdvisor, etc.) into a single unified feed and dashboard.

## RepSync frontend (M4)

React 18 + Vite + TypeScript + Tailwind + Recharts + TanStack Query + React Router.

```bash
cp .env.example .env     # VITE_USE_MOCK=true runs with no backend
npm install
npm run dev              # http://localhost:5173
npm run build            # typecheck + production build