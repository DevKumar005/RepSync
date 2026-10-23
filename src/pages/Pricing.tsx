import { useState } from 'react'

const PLANS = [
  { name: 'Starter', price: '499', emoji: '🌱', blurb: 'For one outlet getting started', items: ['1 outlet, 2 platforms', 'Weekly sync', '30 AI replies a month'] },
  { name: 'Growth', price: '999', emoji: '🚀', blurb: 'For owners who want to fix what customers complain about', items: ['1 outlet, all platforms', 'Daily sync and alerts', 'Unlimited replies', 'Competitor benchmark'], featured: true },
  { name: 'Pro / Agency', price: '1,999', emoji: '🏢', blurb: 'For agencies running several outlets', items: ['Multi-user access', 'White-label PDF reports', 'Priority sync', 'Bulk approvals'] },
]

export default function Pricing() {
  const [picked, setPicked] = useState('')
  return (
    <div className="space-y-10 pt-4 max-w-4xl mx-auto fade-in">
      <div className="space-y-2 text-center md:text-left">
        <h1 className="text-3xl font-bold tracking-tight">Priced for one outlet, not a chain</h1>
        <p className="text-ink/45 text-[15px] leading-relaxed">One lost table or appointment a month costs more than the plan. Start with a free reputation audit.</p>
      </div>

      <div className="grid gap-5 md:grid-cols-3">
        {PLANS.map((p) => (
          <section
            key={p.name}
            className={`panel p-6 flex flex-col gap-5 transition-all duration-300 hover:shadow-lg ${p.featured ? 'border-brand/50 shadow-md shadow-brand/10 relative' : 'hover:border-brand/20'}`}
          >
            {p.featured && (
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-brand text-onbrand text-[10px] font-bold uppercase tracking-wider px-3 py-1 rounded-full">
                Most popular
              </span>
            )}
            <div className="space-y-1.5">
              <span className="text-3xl block">{p.emoji}</span>
              <h2 className="text-lg font-semibold">{p.name}</h2>
              <p className="text-sm text-ink/45">{p.blurb}</p>
            </div>
            <p className="flex items-baseline gap-1">
              <span className="text-3xl font-bold tracking-tight">₹{p.price}</span>
              <span className="text-sm text-ink/35">/ outlet / mo</span>
            </p>
            <ul className="space-y-2 text-sm text-ink/65 flex-1">
              {p.items.map((i) => (
                <li key={i} className="flex items-start gap-2.5">
                  <span className="text-pos mt-0.5 shrink-0 text-xs">✓</span>
                  {i}
                </li>
              ))}
            </ul>
            <button
              className={`btn w-full justify-center !py-2.5 ${p.featured ? 'btn-primary' : ''}`}
              onClick={() => setPicked(p.name)}
            >
              Choose {p.name}
            </button>
          </section>
        ))}
      </div>

      {picked && (
        <p role="status" className="panel bg-brandsoft border-brand/20 px-4 py-3 text-sm text-ink/60 text-center fade-in">
          Test mode — no payment taken. You picked <strong className="text-ink">{picked}</strong>. 🎉
        </p>
      )}
    </div>
  )
}
