import { NavLink } from 'react-router-dom'

// Feature data drawn from the product's actual capabilities
const FEATURES = [
  {
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
    ),
    title: 'Unified review inbox',
    body: 'Pulls reviews from Google Maps, Zomato, Practo, JustDial and more into one normalised feed — no dashboard hopping.',
  },
  {
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"/></svg>
    ),
    title: 'Complaint themes & top 3 fixes',
    body: 'Clusters negative reviews into labelled themes with evidence counts. Turns patterns into the three most actionable fixes for your business.',
  },
  {
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>
    ),
    title: 'Tone-aware reply drafts',
    body: 'Drafts a reply for every negative review in your voice — warm, formal, apologetic or concise. Supports English, Hindi and Hinglish.',
  },
  {
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
    ),
    title: 'Guardrails on every draft',
    body: 'No liability admissions, no refund promises, no blaming the reviewer. Banned phrases trigger automatic regeneration before you ever see the draft.',
  },
  {
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
    ),
    title: 'Owner approval workflow',
    body: 'Every reply goes through Draft → Approved before anything is ready to post. You stay in control — the AI only suggests.',
  },
  {
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
    ),
    title: 'Live activity log',
    body: 'Every Search, Fetch and Agent call is shown in real time so you can see exactly where your reviews came from and how long it took.',
  },
]

const STEPS = [
  { n: '1', title: 'Find your outlet', body: 'Type your business name and city. RepSync searches across platforms and shows you the matching outlets to confirm.' },
  { n: '2', title: 'Sync reviews', body: 'One click collects reviews from all platforms, classifies sentiment, clusters complaints into themes, and drafts replies.' },
  { n: '3', title: 'Review and approve', body: 'Browse your inbox, read the top fixes, edit the AI drafts if needed, and approve the ones you want to post.' },
]

const PLATFORMS = ['Google Maps', 'Zomato', 'Practo', 'JustDial', 'Tripadvisor']

export default function Home() {
  return (
    <div className="space-y-20 py-10">

      {/* ── Hero ─────────────────────────────────────────── */}
      <section className="mx-auto max-w-3xl space-y-6 text-center">
        <div className="inline-flex items-center gap-2 rounded-full border border-line bg-surface px-3.5 py-1.5 text-xs font-medium text-ink/60">
          <span className="h-1.5 w-1.5 rounded-full bg-pos" />
          Built for KRITICAL HACKS '26 · AI/ML Track
        </div>
        <h1 className="text-5xl font-bold leading-[1.1] tracking-tight">
          One unanswered 1-star review<br />can cost you dozens of customers.
        </h1>
        <p className="mx-auto max-w-xl text-lg text-ink/50 leading-relaxed">
          RepSync collects every public review of your business, shows you what to fix, and drafts replies you approve — across all platforms, in one place.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-3">
          <NavLink to="/search" className="btn btn-primary px-5 py-2.5 text-[15px]">
            Find my business
          </NavLink>
          <NavLink to="/pricing" className="btn px-5 py-2.5 text-[15px]">
            See pricing
          </NavLink>
        </div>
        <p className="text-xs text-ink/30">
          Covers {PLATFORMS.join(' · ')}
        </p>
      </section>

      {/* ── Problem ──────────────────────────────────────── */}
      <section className="mx-auto max-w-4xl">
        <div className="panel p-8 md:p-10">
          <p className="label-overline mb-4">The problem</p>
          <div className="grid gap-6 md:grid-cols-2 md:gap-10">
            <div className="space-y-3">
              <h2 className="text-2xl font-bold tracking-tight">
                Your reviews are scattered. You have no time to read them all.
              </h2>
              <p className="text-ink/55 leading-relaxed">
                Small businesses — restaurants, clinics, salons — get reviews on four or five platforms simultaneously. Owners have no time to check four dashboards. An unanswered negative review tells the next customer that nobody cares.
              </p>
            </div>
            <ul className="space-y-3 self-start">
              {[
                'Reviews spread across Google, Zomato, Practo, JustDial',
                'No time to read, let alone reply',
                'Recurring complaints go unfixed because nobody spots the pattern',
                'One ignored 1-star can push a 4.6 → 4.3 rating',
              ].map((item) => (
                <li key={item} className="flex items-start gap-2.5 text-sm text-ink/70">
                  <svg className="mt-0.5 shrink-0 text-neg" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* ── How it works ─────────────────────────────────── */}
      <section className="mx-auto max-w-4xl space-y-6">
        <div className="text-center space-y-1">
          <p className="label-overline">How it works</p>
          <h2 className="text-2xl font-bold tracking-tight">Three steps, a few minutes</h2>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {STEPS.map((s) => (
            <div key={s.n} className="panel p-6 space-y-3">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brandsoft text-sm font-bold text-brand">
                {s.n}
              </span>
              <h3 className="font-semibold">{s.title}</h3>
              <p className="text-sm text-ink/55 leading-relaxed">{s.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Features ─────────────────────────────────────── */}
      <section className="mx-auto max-w-4xl space-y-6">
        <div className="text-center space-y-1">
          <p className="label-overline">Capabilities</p>
          <h2 className="text-2xl font-bold tracking-tight">Everything a local business needs</h2>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f) => (
            <div key={f.title} className="panel p-5 space-y-2.5">
              <span className="text-brand">{f.icon}</span>
              <h3 className="font-semibold text-sm">{f.title}</h3>
              <p className="text-sm text-ink/55 leading-relaxed">{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── India callout ────────────────────────────────── */}
      <section className="mx-auto max-w-4xl">
        <div className="panel p-8 md:p-10 flex flex-col md:flex-row items-start md:items-center gap-6">
          <div className="text-4xl shrink-0">🇮🇳</div>
          <div className="space-y-1.5">
            <h2 className="text-xl font-bold tracking-tight">Built for India</h2>
            <p className="text-ink/55 leading-relaxed text-sm max-w-xl">
              Understands English, Hindi and Hinglish reviews — and replies in the language of the review. Covers the platforms Indian customers actually use. Priced for single-outlet owners, not enterprise chains.
            </p>
          </div>
        </div>
      </section>

      {/* ── Pricing teaser / CTA ─────────────────────────── */}
      <section className="mx-auto max-w-3xl">
        <div className="panel p-8 md:p-10 text-center space-y-5">
          <p className="label-overline">Pricing</p>
          <h2 className="text-2xl font-bold tracking-tight">Starts at ₹499 / outlet / month</h2>
          <p className="text-ink/55 text-sm max-w-md mx-auto leading-relaxed">
            One lost table or appointment a month costs more than the plan. Start with a free reputation audit — one sync, themes and five sample replies, no payment needed.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <NavLink to="/search" className="btn btn-primary px-5 py-2.5 text-[15px]">
              Start free audit
            </NavLink>
            <NavLink to="/pricing" className="btn px-5 py-2.5 text-[15px]">
              View all plans
            </NavLink>
          </div>
        </div>
      </section>

    </div>
  )
}
