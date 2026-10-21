import { useState } from 'react'

const PLANS = [
  { name: 'Starter', price: '499', blurb: 'For one outlet getting started', items: ['1 outlet, 2 platforms', 'Weekly sync', '30 AI replies a month'] },
  { name: 'Growth', price: '999', blurb: 'For owners who want to fix what customers complain about', items: ['1 outlet, all platforms', 'Daily sync and alerts', 'Unlimited replies', 'Competitor benchmark'], featured: true },
  { name: 'Pro / Agency', price: '1,999', blurb: 'For agencies running several outlets', items: ['Multi-user access', 'White-label PDF reports', 'Priority sync', 'Bulk approvals'] },
]

export default function Pricing() {
  const [picked, setPicked] = useState('')
  return (
    <div className="space-y-10 pt-4 max-w-4xl mx-auto">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight">Priced for one outlet, not a chain</h1>
        <p className="text-ink/50 text-[15px]">One lost table or appointment a month costs more than the plan. Start with a free reputation audit.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {PLANS.map((p) => (
          <section
            key={p.name}
            className={`panel p-6 flex flex-col gap-5 ${p.featured ? 'border-brand/60 shadow-sm shadow-brand/10' : ''}`}
          >
            <div className="space-y-0.5">
              {p.featured && <span className="label-overline text-brand">Most popular</span>}
              <h2 className="text-lg font-semibold">{p.name}</h2>
              <p className="text-sm text-ink/50">{p.blurb}</p>
            </div>
            <p className="flex items-baseline gap-1">
              <span className="text-3xl font-bold tracking-tight">₹{p.price}</span>
              <span className="text-sm text-ink/40">/ outlet / mo</span>
            </p>
            <ul className="space-y-1.5 text-sm text-ink/70 flex-1">
              {p.items.map((i) => (
                <li key={i} className="flex items-start gap-2">
                  <svg className="mt-0.5 shrink-0 text-pos" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                  {i}
                </li>
              ))}
            </ul>
            <button
              className={`btn w-full justify-center ${p.featured ? 'btn-primary' : ''}`}
              onClick={() => setPicked(p.name)}
            >
              Choose {p.name}
            </button>
          </section>
        ))}
      </div>

      {picked && (
        <p role="status" className="panel bg-brandsoft border-brand/30 px-4 py-3 text-sm text-ink/70">
          Test mode — no payment taken. You picked <strong className="text-ink">{picked}</strong>.
        </p>
      )}
    </div>
  )
}
