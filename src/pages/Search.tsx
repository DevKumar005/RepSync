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
    <div className="mx-auto max-w-2xl space-y-6 pt-6">
      <div><h1 className="text-4xl font-bold leading-tight">One unanswered 1-star review can cost you dozens of customers.</h1>
        <p className="mt-2 text-ink/70">We collect public reviews, show what to fix, and draft replies you approve.</p></div>

      <div className="panel p-5">
      <form className="space-y-3" onSubmit={(e) => { e.preventDefault(); find.mutate() }}>
        <label className="block text-sm font-semibold">Business name
          <input className="field mt-1 font-normal" required value={name} onChange={(e) => setName(e.target.value)} placeholder="Sharma's Kitchen" /></label>
        <label className="block text-sm font-semibold">City
          <input className="field mt-1 font-normal" required value={city} onChange={(e) => setCity(e.target.value)} placeholder="Delhi" /></label>
        <fieldset><legend className="text-sm font-semibold">Type of business</legend>
          <div className="mt-1 flex gap-2">{CATS.map((c) => (
            <button type="button" key={c} aria-pressed={category === c} onClick={() => setCategory(c)}
              className={`btn capitalize ${category === c ? 'btn-primary' : ''}`}>{c}</button>))}</div></fieldset>
        <div className="pt-1"><button className="btn btn-primary" disabled={find.isPending}>{find.isPending ? 'Searching…' : 'Find my business'}</button></div>
        {find.isError && <p role="alert" className="text-sm text-neg">Search failed: {(find.error as Error).message}. Try again, or open a demo outlet above.</p>}
      </form>

      <div className="mt-5 border-t border-dashed border-line pt-4">
        <p className="mb-3 text-center text-xs font-semibold uppercase tracking-wide text-ink/60">Or try a sample outlet</p>
        <div className="grid gap-3 sm:grid-cols-2">
          {DEMOS.map((d) => (
            <button key={d.key} type="button" disabled={demo.isPending} onClick={() => demo.mutate(d.key)}
              className="rounded-lg border border-line bg-surface p-3 text-left hover:border-brand hover:bg-brandsoft disabled:opacity-50">
              <span className="block font-semibold">{demo.isPending && demo.variables === d.key ? 'Loading…' : d.title}</span>
              <span className="block text-xs text-ink/60">{d.blurb}</span>
            </button>
          ))}
        </div>
        {demo.isPending && <p role="status" className="mt-2 text-center text-sm text-ink/60">Loading the sample. If the server was asleep this can take up to a minute.</p>}
        {demo.isError && <p role="alert" className="mt-2 text-center text-sm text-neg">Could not load the demo: {(demo.error as Error).message}. The server may be waking up, wait a few seconds and try again.</p>}
      </div>
      </div>

      {find.data && (
        <section className="panel">
          <h2 className="p-4 text-lg font-bold">Which one is yours?</h2>
          {find.data.length === 0 ? <p className="p-4 text-sm text-ink/60">No matches. Check the spelling or add the area to the city.</p> : (
            <ul className="divide-y divide-line">{find.data.map((c) => (
              <li key={c.id}><label className="flex cursor-pointer items-center gap-3 p-4 hover:bg-paper">
                <input type="radio" name="cand" checked={!!pick && pick.id === c.id} onChange={() => setPick(c)} />
                <span className="flex-1"><span className="block font-semibold">{c.name}</span><span className="text-sm text-ink/60">{c.address}</span></span>
                <span className="chip">{c.source}</span></label></li>))}</ul>)}
          <div className="border-t border-line p-4"><button className="btn btn-primary" disabled={!pick || confirm.isPending} onClick={() => confirm.mutate()}>
            {confirm.isPending ? 'Setting up…' : 'Confirm and collect reviews'}</button></div>
        </section>
      )}
    </div>
  )
}