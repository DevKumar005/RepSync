import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { api } from '../api/client'
import type { Candidate, Category } from '../types'
import DotText from '../components/DotText'

const CATS: Category[] = ['restaurant', 'clinic', 'salon']
const DEMOS = [
  { key: 'restaurant', label: 'Restaurant demo' },
  { key: 'clinic', label: 'Clinic demo' },
] as const

const Spinner = () => (
  <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" aria-hidden="true">
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
  </svg>
)

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
    <div className="rs-container space-y-6 pt-12 pb-20 fade-in">
      <header className="space-y-2">
        <h1 className="rs-title text-[clamp(30px,3.6vw,52px)]">
          Find your <span className="rs-dot-accent ml-[.25em]"><DotText text="outlet" pitchX={4} radius={1.8} height=".74em" /></span>
        </h1>
        <p className="rs-copy">Search by name and city. We collect the reviews.</p>
      </header>

      <form className="panel grid gap-4 p-5 md:p-6 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)_auto_auto] lg:items-end" onSubmit={(e) => { e.preventDefault(); find.mutate() }}>
        <label className="block text-[13px] font-medium text-ink/65">
          Business name
          <input className="field mt-1.5 !py-3 text-[15px]" required value={name} onChange={(e) => setName(e.target.value)} placeholder="Sharma's Kitchen" />
        </label>
        <label className="block text-[13px] font-medium text-ink/65">
          City
          <input className="field mt-1.5 !py-3 text-[15px]" required value={city} onChange={(e) => setCity(e.target.value)} placeholder="Delhi" />
        </label>
        <fieldset>
          <legend className="mb-1.5 text-[13px] font-medium text-ink/65">Type</legend>
          <div className="flex rounded-full border border-ink/[.08] bg-ink/[.03] p-1" role="radiogroup">
            {CATS.map((c) => (
              <button
                type="button" key={c} role="radio" aria-checked={category === c} onClick={() => setCategory(c)}
                className={`rounded-full px-4 py-2 text-sm capitalize transition-colors ${category === c ? 'pill-active font-medium' : 'pill-idle'}`}
              >
                {c}
              </button>
            ))}
          </div>
        </fieldset>
        <button className="btn btn-primary !px-7 !py-3 text-[15px]" disabled={find.isPending}>
          {find.isPending ? <><Spinner /> Searching…</> : 'Search'}
        </button>
      </form>
      {find.isError && <p role="alert" className="text-sm text-neg">{(find.error as Error).message}. Try again, or open a demo.</p>}

      {find.data && (
        <section className="panel fade-in">
          <div className="flex flex-wrap items-center gap-3 px-5 pt-5 pb-4">
            <h2 className="mr-auto text-base font-semibold">{find.data.length ? 'Pick your branch' : 'No matches'}</h2>
            {find.data.length > 0 && (
              <button className="btn btn-primary" disabled={!pick || confirm.isPending} onClick={() => confirm.mutate()}>
                {confirm.isPending ? 'Setting up…' : 'Collect reviews'}
              </button>
            )}
          </div>
          {find.data.length === 0
            ? <p className="px-5 pb-5 text-sm text-ink/50">Check the spelling, or add the area to the city.</p>
            : (
              <ul className="grid gap-3 px-5 pb-5 sm:grid-cols-2 xl:grid-cols-3" role="radiogroup">
                {find.data.map((c) => {
                  const on = !!pick && pick.id === c.id
                  return (
                    <li key={c.id}>
                      <label className={`flex h-full cursor-pointer items-start gap-3 rounded-2xl border p-4 transition-colors ${on ? 'border-brand/60 bg-brand/[.06]' : 'border-ink/[.08] hover:bg-ink/[.03]'}`}>
                        <input type="radio" name="cand" checked={on} onChange={() => setPick(c)} className="mt-0.5 h-4 w-4 accent-brand" />
                        <span className="min-w-0">
                          <span className="block text-sm font-medium">{c.name}</span>
                          <span className="block text-xs text-ink/50">{c.address}</span>
                        </span>
                      </label>
                    </li>
                  )
                })}
              </ul>
            )}
          {confirm.isError && <p role="alert" className="px-5 pb-5 text-sm text-neg">{(confirm.error as Error).message}</p>}
        </section>
      )}

      <div className="flex flex-wrap items-center gap-2 text-sm text-ink/55">
        <span>No account? Try a demo:</span>
        {DEMOS.map((d) => (
          <button key={d.key} className="btn !py-1.5" disabled={demo.isPending} onClick={() => demo.mutate(d.key)}>
            {demo.isPending && demo.variables === d.key ? 'Opening…' : d.label}
          </button>
        ))}
        {demo.isError && <span role="alert" className="text-neg">Could not open the demo. The server may be waking up; try again.</span>}
      </div>
    </div>
  )
}
