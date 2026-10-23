import { NavLink } from 'react-router-dom'

// Feature data drawn from the product's actual capabilities
const FEATURES = [
  {
    emoji: '📥',
    title: 'Unified review inbox',
    body: 'Pulls reviews from Google Maps, Zomato, Practo, JustDial and more into one normalised feed — no dashboard hopping.',
  },
  {
    emoji: '🧩',
    title: 'Complaint themes & top 3 fixes',
    body: 'Clusters negative reviews into labelled themes with evidence counts. Turns patterns into the three most actionable fixes for your business.',
  },
  {
    emoji: '✍️',
    title: 'Tone-aware reply drafts',
    body: 'Drafts a reply for every negative review in your voice — warm, formal, apologetic or concise. Supports English, Hindi and Hinglish.',
  },
  {
    emoji: '🛡️',
    title: 'Guardrails on every draft',
    body: 'No liability admissions, no refund promises, no blaming the reviewer. Banned phrases trigger automatic regeneration before you ever see the draft.',
  },
  {
    emoji: '✅',
    title: 'Owner approval workflow',
    body: 'Every reply goes through Draft → Approved before anything is ready to post. You stay in control — the AI only suggests.',
  },
  {
    emoji: '📊',
    title: 'Live activity log',
    body: 'Every Search, Fetch and Agent call is shown in real time so you can see exactly where your reviews came from and how long it took.',
  },
]

const STEPS = [
  { n: '1', emoji: '🔍', title: 'Find your outlet', body: 'Type your business name and city. RepSync searches across platforms and shows you the matching outlets to confirm.' },
  { n: '2', emoji: '🔄', title: 'Sync reviews', body: 'One click collects reviews from all platforms, classifies sentiment, clusters complaints into themes, and drafts replies.' },
  { n: '3', emoji: '👍', title: 'Review and approve', body: 'Browse your inbox, read the top fixes, edit the AI drafts if needed, and approve the ones you want to post.' },
]

const PLATFORMS = ['Google Maps', 'Zomato', 'Practo', 'JustDial', 'Tripadvisor']

export default function Home() {
  return (
    <div className="space-y-24 py-12">

      {/* ── Hero ─────────────────────────────────────────── */}
      <section className="mx-auto max-w-3xl space-y-7 text-center slide-up">
        <div className="inline-flex items-center gap-2 rounded-full border border-line bg-surface px-4 py-2 text-xs font-medium text-ink/55">
          <span className="status-dot status-dot-ok" />
          Built for KRITICAL HACKS &apos;26 · AI/ML Track
        </div>
        <h1 className="text-[3.2rem] font-bold leading-[1.08] tracking-tight">
          One unanswered 1&#8209;star review<br />
          <span className="text-gradient">can cost you dozens of customers.</span>
        </h1>
        <p className="mx-auto max-w-xl text-lg text-ink/45 leading-relaxed">
          RepSync collects every public review of your business, shows you what to fix, and drafts replies you approve — across all platforms, in one place.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-3 pt-1">
          <NavLink to="/search" className="btn btn-primary px-6 py-3 text-[15px] !rounded-xl">
            Find my business →
          </NavLink>
          <NavLink to="/pricing" className="btn px-6 py-3 text-[15px] !rounded-xl">
            See pricing
          </NavLink>
        </div>
        <div className="flex items-center justify-center gap-3 text-xs text-ink/30">
          {PLATFORMS.map((p, i) => (
            <span key={p} className="flex items-center gap-1.5">
              {i > 0 && <span className="text-line">·</span>}
              {p}
            </span>
          ))}
        </div>
      </section>

      {/* ── Problem ──────────────────────────────────────── */}
      <section className="mx-auto max-w-4xl fade-in">
        <div className="panel p-8 md:p-10">
          <p className="label-overline mb-5">The problem</p>
          <div className="grid gap-8 md:grid-cols-2 md:gap-10">
            <div className="space-y-4">
              <h2 className="text-2xl font-bold tracking-tight leading-snug">
                Your reviews are scattered.<br />You have no time to read them all.
              </h2>
              <p className="text-ink/50 leading-relaxed">
                Small businesses — restaurants, clinics, salons — get reviews on four or five platforms simultaneously. Owners have no time to check four dashboards. An unanswered negative review tells the next customer that nobody cares.
              </p>
            </div>
            <ul className="space-y-3.5 self-start">
              {[
                'Reviews spread across Google, Zomato, Practo, JustDial',
                'No time to read, let alone reply',
                'Recurring complaints go unfixed because nobody spots the pattern',
                'One ignored 1-star can push a 4.6 → 4.3 rating',
              ].map((item) => (
                <li key={item} className="flex items-start gap-3 text-sm text-ink/65 leading-relaxed">
                  <span className="mt-0.5 shrink-0 text-neg text-xs">✕</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* ── How it works ─────────────────────────────────── */}
      <section className="mx-auto max-w-4xl space-y-8">
        <div className="text-center space-y-2">
          <p className="label-overline">How it works</p>
          <h2 className="text-2xl font-bold tracking-tight">Three steps, a few minutes</h2>
        </div>
        <div className="grid gap-5 md:grid-cols-3">
          {STEPS.map((s) => (
            <div key={s.n} className="panel p-6 space-y-4 group hover:border-brand/30 transition-colors duration-300">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{s.emoji}</span>
                <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-brandsoft text-sm font-bold text-brand">
                  {s.n}
                </span>
              </div>
              <h3 className="font-semibold text-ink/90">{s.title}</h3>
              <p className="text-sm text-ink/50 leading-relaxed">{s.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Features ─────────────────────────────────────── */}
      <section className="mx-auto max-w-4xl space-y-8">
        <div className="text-center space-y-2">
          <p className="label-overline">Capabilities</p>
          <h2 className="text-2xl font-bold tracking-tight">Everything a local business needs</h2>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f) => (
            <div key={f.title} className="panel p-5 space-y-3 group hover:border-brand/30 transition-colors duration-300">
              <span className="text-2xl block">{f.emoji}</span>
              <h3 className="font-semibold text-sm text-ink/90">{f.title}</h3>
              <p className="text-sm text-ink/50 leading-relaxed">{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── India callout ────────────────────────────────── */}
      <section className="mx-auto max-w-4xl">
        <div className="panel p-8 md:p-10 flex flex-col md:flex-row items-start md:items-center gap-6 bg-gradient-to-br from-surface to-brandsoft/20">
          <div className="text-4xl shrink-0">🇮🇳</div>
          <div className="space-y-2">
            <h2 className="text-xl font-bold tracking-tight">Built for India</h2>
            <p className="text-ink/50 leading-relaxed text-sm max-w-xl">
              Understands English, Hindi and Hinglish reviews — and replies in the language of the review. Covers the platforms Indian customers actually use. Priced for single-outlet owners, not enterprise chains.
            </p>
          </div>
        </div>
      </section>

      {/* ── Pricing teaser / CTA ─────────────────────────── */}
      <section className="mx-auto max-w-3xl">
        <div className="panel p-8 md:p-10 text-center space-y-6">
          <p className="label-overline">Pricing</p>
          <h2 className="text-3xl font-bold tracking-tight">Starts at ₹499 / outlet / month</h2>
          <p className="text-ink/50 text-sm max-w-md mx-auto leading-relaxed">
            One lost table or appointment a month costs more than the plan. Start with a free reputation audit — one sync, themes and five sample replies, no payment needed.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <NavLink to="/search" className="btn btn-primary px-6 py-3 text-[15px] !rounded-xl">
              Start free audit →
            </NavLink>
            <NavLink to="/pricing" className="btn px-6 py-3 text-[15px] !rounded-xl">
              View all plans
            </NavLink>
          </div>
        </div>
      </section>

    </div>
  )
}
