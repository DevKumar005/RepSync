import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { api } from '../api/client'
import type { Candidate, Category } from '../types'

const CATS: Category[] = ['restaurant', 'clinic', 'salon']
const DEMOS = [
  { key: 'restaurant', title: 'Demo: Restaurant', blurb: 'Kake Da Dhaba · reviews, themes, replies' },
  { key: 'clinic', title: 'Demo: Clinic', blurb: 'Dental clinic · patient feedback, replies' },
] as const

export default function Search() {
  const nav = useNavigate()
  const [name, setName] = useState('')
  const [city, setCity] = useState('')
  const [category, setCategory] = useState<Category>('restaurant')
  const [pick, setPick] = useState<Candidate>()
  const find = useMutation({ mutationFn: () => api.searchOutlets(name.trim(), city.trim(), category), onSuccess: () => setPick(undefined) })
  const confirm = useMutation({ mutationFn: () => api.createOutlet(pick!, city.trim(), category), onSuccess: (o) => nav(`/outlet/${o.id}?sync=1`) })
  const demo = useMutation({ mutationFn: (key: 'restaurant' | 'clinic') => api.demoOutlet(key), onSuccess: (o) => nav(`/outlet/${o.id}`) })

  return (
    <div className="mx-auto max-w-xl space-y-8 pt-10">
      <div className="space-y-2">
        <h1 className="text-[2rem] font-bold leading-tight tracking-tight">
          One unanswered 1-star review<br />can cost you dozens of customers.
        </h1>
        <p className="text-ink/50 text-[15px]">
          We collect public reviews, surface what to fix, and draft replies you approve.
        </p>
      </div>

      <div className="panel p-6 space-y-5">
        <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); find.mutate() }}>
          <label className="block text-sm font-medium text-ink/80">
            Business name
            <input className="field mt-1.5 font-normal" required value={name} onChange={(e) => setName(e.target.value)} placeholder="Sharma's Kitchen" />
          </label>
          <label className="block text-sm font-medium text-ink/80">
            City
            <input className="field mt-1.5 font-normal" required value={city} onChange={(e) => setCity(e.target.value)} placeholder="Delhi" />
          </label>
          <fieldset>
            <legend className="text-sm font-medium text-ink/80">Type of business</legend>
            <div className="mt-2 flex gap-2">
              {CATS.map((c) => (
                <button type="button" key={c} aria-pressed={category === c} onClick={() => setCategory(c)}
                  className={`btn capitalize ${category === c ? 'btn-primary' : ''}`}>{c}</button>
              ))}
            </div>
          </fieldset>
          <button className="btn btn-primary w-full" disabled={find.isPending}>
            {find.isPending ? 'Searching…' : 'Find my business'}
          </button>
          {find.isError && <p role="alert" className="text-sm text-neg">{(find.error as Error).message}. Try again, or open a demo below.</p>}
        </form>

        <div className="border-t border-line pt-4 space-y-3">
          <p className="label-overline text-center">Or try a sample outlet</p>
          <div className="grid gap-2.5 sm:grid-cols-2">
            {DEMOS.map((d) => (
              <button key={d.key} type="button" disabled={demo.isPending} onClick={() => demo.mutate(d.key)}
                className="rounded-xl border border-line bg-paper p-3.5 text-left hover:border-brand hover:bg-brandsoft transition-colors duration-150 disabled:opacity-50">
                <span className="block text-sm font-semibold text-ink">
                  {demo.isPending && demo.variables === d.key ? 'Loading…' : d.title}
                </span>
                <span className="block text-xs text-ink/50 mt-0.5">{d.blurb}</span>
              </button>
            ))}
          </div>
          {demo.isPending && <p role="status" className="text-center text-xs text-ink/50">Loading sample — if the server was asleep this can take up to a minute.</p>}
          {demo.isError && <p role="alert" className="text-center text-sm text-neg">Could not load demo: {(demo.error as Error).message}. Wait a few seconds and try again.</p>}
        </div>
      </div>

      {find.data && (
        <section className="panel">
          <h2 className="px-5 pt-5 pb-3 text-base font-semibold">Which one is yours?</h2>
          {find.data.length === 0
            ? <p className="px-5 pb-5 text-sm text-ink/50">No matches. Check the spelling or add the area to the city name.</p>
            : (
              <ul className="divide-y divide-line">
                {find.data.map((c) => (
                  <li key={c.id}>
                    <label className="flex cursor-pointer items-center gap-3 px-5 py-3.5 hover:bg-paper transition-colors duration-150">
                      <input type="radio" name="cand" checked={!!pick && pick.id === c.id} onChange={() => setPick(c)} className="accent-brand" />
                      <span className="flex-1 min-w-0">
                        <span className="block font-medium text-sm">{c.name}</span>
                        <span className="text-xs text-ink/50">{c.address}</span>
                      </span>
                      <span className="chip">{c.source}</span>
                    </label>
                  </li>
                ))}
              </ul>
            )
          }
          <div className="border-t border-line px-5 py-4">
            <button className="btn btn-primary" disabled={!pick || confirm.isPending} onClick={() => confirm.mutate()}>
              {confirm.isPending ? 'Setting up…' : 'Confirm and collect reviews'}
            </button>
          </div>
        </section>
      )}
    </div>
  )
}