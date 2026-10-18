import { useState } from 'react'

const PLANS = [
  { name: 'Starter', price: '499', blurb: 'For one outlet getting started', items: ['1 outlet, 2 platforms', 'Weekly sync', '30 AI replies a month'] },
  { name: 'Growth', price: '999', blurb: 'For owners who want to fix what customers complain about', items: ['1 outlet, all platforms', 'Daily sync and alerts', 'Unlimited replies', 'Competitor benchmark'], featured: true },
  { name: 'Pro / Agency', price: '1,999', blurb: 'For agencies running several outlets', items: ['Multi-user access', 'White-label PDF reports', 'Priority sync', 'Bulk approvals'] },
]

export default function Pricing() {
  const [picked, setPicked] = useState('')
  return (
    <div className="space-y-6 pt-4">
      <div><h1 className="text-3xl font-bold">Priced for one outlet, not a chain</h1>
        <p className="mt-1 text-ink/70">One lost table or appointment a month costs more than the plan. Start with a free reputation audit.</p></div>
      <div className="grid gap-4 md:grid-cols-3">
        {PLANS.map((p) => (
          <section key={p.name} className={`panel p-5 ${p.featured ? 'border-brand ring-2 ring-brand' : ''}`}>
            <h2 className="text-xl font-bold">{p.name}</h2><p className="text-sm text-ink/60">{p.blurb}</p>
            <p className="my-3"><span className="font-display text-4xl font-bold">₹{p.price}</span><span className="text-ink/60"> / outlet / month</span></p>
            <ul className="mb-4 space-y-1 text-sm">{p.items.map((i) => <li key={i}>{i}</li>)}</ul>
            <button className={`btn w-full ${p.featured ? 'btn-primary' : ''}`} onClick={() => setPicked(p.name)}>Choose {p.name}</button>
          </section>
        ))}
      </div>
      {picked && <p role="status" className="panel bg-brandsoft p-3 text-sm">Test mode: no payment was taken. You picked {picked}.</p>}
    </div>
  )
}
