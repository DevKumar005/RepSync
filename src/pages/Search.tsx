import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { api } from '../api/client'
import type { Candidate, Category } from '../types'

const CATS: Category[] = ['restaurant', 'clinic', 'salon']
const CAT_EMOJI: Record<Category, string> = { restaurant: '🍽️', clinic: '🏥', salon: '💇' }
const DEMOS = [
  { key: 'restaurant', title: 'Demo: Restaurant', blurb: 'Kake Da Dhaba · reviews, themes, replies', emoji: '🍛' },
  { key: 'clinic', title: 'Demo: Clinic', blurb: 'Dental clinic · patient feedback, replies', emoji: '🦷' },
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
    <div className="mx-auto max-w-xl space-y-8 pt-10 fade-in">
      <div className="space-y-3">
        <h1 className="text-[2rem] font-bold leading-tight tracking-tight">
          One unanswered 1&#8209;star review<br /><span className="text-gradient">can cost you dozens of customers.</span>
        </h1>
        <p className="text-ink/45 text-[15px] leading-relaxed">
          We collect public reviews, surface what to fix, and draft replies you approve.
        </p>
      </div>

      <div className="panel p-6 space-y-5">
        <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); find.mutate() }}>
          <label className="block text-sm font-medium text-ink/70">
            Business name
            <input className="field mt-1.5 font-normal" required value={name} onChange={(e) => setName(e.target.value)} placeholder="Sharma's Kitchen" />
          </label>
          <label className="block text-sm font-medium text-ink/70">
            City
            <input className="field mt-1.5 font-normal" required value={city} onChange={(e) => setCity(e.target.value)} placeholder="Delhi" />
          </label>
          <fieldset>
            <legend className="text-sm font-medium text-ink/70 mb-2">Type of business</legend>
            <div className="flex gap-2">
              {CATS.map((c) => (
                <button type="button" key={c} aria-pressed={category === c} onClick={() => setCategory(c)}
                  className={`btn capitalize flex items-center gap-1.5 ${category === c ? 'btn-primary' : ''}`}>
                  <span>{CAT_EMOJI[c]}</span>{c}
                </button>
              ))}
            </div>
          </fieldset>
          <button className="btn btn-primary w-full !py-2.5" disabled={find.isPending}>
            {find.isPending ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
                Searching…
              </span>
            ) : 'Find my business →'}
          </button>
          {find.isError && (
            <p role="alert" className="text-sm text-neg flex items-center gap-1.5">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
              {(find.error as Error).message}. Try again, or open a demo below.
            </p>
          )}
        </form>

        <div className="border-t border-line pt-5 space-y-4">
          <p className="label-overline text-center">Or try a sample outlet</p>
          <div className="grid gap-3 sm:grid-cols-2">
            {DEMOS.map((d) => (
              <button key={d.key} type="button" disabled={demo.isPending} onClick={() => demo.mutate(d.key)}
                className="rounded-2xl border border-line bg-paper p-4 text-left hover:border-brand/40 hover:shadow-sm transition-all duration-200 disabled:opacity-50 group">
                <span className="text-2xl block mb-2">{d.emoji}</span>
                <span className="block text-sm font-semibold text-ink/90 group-hover:text-brand transition-colors">
                  {demo.isPending && demo.variables === d.key ? 'Loading…' : d.title}
                </span>
                <span className="block text-xs text-ink/45 mt-0.5">{d.blurb}</span>
              </button>
            ))}
          </div>
          {demo.isPending && <p role="status" className="text-center text-xs text-ink/40">Loading sample — if the server was asleep this can take up to a minute.</p>}
          {demo.isError && <p role="alert" className="text-center text-sm text-neg">Could not load demo: {(demo.error as Error).message}. Wait a few seconds and try again.</p>}
        </div>
      </div>

      {find.data && (
        <section className="panel fade-in">
          <h2 className="px-5 pt-5 pb-3 text-base font-semibold">Which one is yours?</h2>
          {find.data.length === 0
            ? <p className="px-5 pb-5 text-sm text-ink/45">No matches. Check the spelling or add the area to the city name.</p>
            : (
              <ul className="divide-y divide-line">
                {find.data.map((c) => (
                  <li key={c.id}>
                    <label className="flex cursor-pointer items-center gap-3 px-5 py-4 hover:bg-paper transition-colors duration-150">
                      <input type="radio" name="cand" checked={!!pick && pick.id === c.id} onChange={() => setPick(c)} className="accent-brand h-4 w-4" />
                      <span className="flex-1 min-w-0">
                        <span className="block font-medium text-sm">{c.name}</span>
                        <span className="text-xs text-ink/45">{c.address}</span>
                      </span>
                      <span className="chip !text-[10px]">{c.source}</span>
                    </label>
                  </li>
                ))}
              </ul>
            )
          }
          <div className="border-t border-line px-5 py-4">
            <button className="btn btn-primary" disabled={!pick || confirm.isPending} onClick={() => confirm.mutate()}>
              {confirm.isPending ? 'Setting up…' : 'Confirm and collect reviews →'}
            </button>
          </div>
        </section>
      )}
    </div>
  )
}