import { useEffect, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import type { Tone } from '../types'

const STYLES: Tone['style'][] = ['warm', 'formal', 'apologetic', 'concise']

export default function TonePage() {
  const { data } = useQuery({ queryKey: ['tone'], queryFn: api.getTone })
  const [t, setT] = useState<Tone>()
  useEffect(() => { if (data) setT(data) }, [data])
  const save = useMutation({ mutationFn: (x: Tone) => api.putTone(x) })
  if (!t) return <p className="text-sm text-ink/40 pt-10 text-center">Loading…</p>
  return (
    <div className="max-w-xl mx-auto pt-6">
      <form className="panel p-6 space-y-6" onSubmit={(e) => { e.preventDefault(); save.mutate(t) }}>
        <div className="space-y-1">
          <h1 className="text-2xl font-bold tracking-tight">Reply tone</h1>
          <p className="text-sm text-ink/50">New drafts follow this. Replies you approve are never changed.</p>
        </div>

        <fieldset className="space-y-2">
          <legend className="text-sm font-medium text-ink/80">Style</legend>
          <div className="flex flex-wrap gap-2">
            {STYLES.map((s) => (
              <button type="button" key={s} aria-pressed={t.style === s} onClick={() => setT({ ...t, style: s })}
                className={`btn capitalize ${t.style === s ? 'btn-primary' : ''}`}>{s}</button>
            ))}
          </div>
        </fieldset>

        <label className="block space-y-1.5">
          <span className="text-sm font-medium text-ink/80">Sample replies you like</span>
          <textarea className="field font-normal" rows={4} value={t.sample_replies}
            onChange={(e) => setT({ ...t, sample_replies: e.target.value })}
            placeholder="Paste one or two replies you have written before" />
        </label>

        <label className="block space-y-1.5">
          <span className="text-sm font-medium text-ink/80">Words to never use</span>
          <input className="field font-normal" value={t.do_not_say}
            onChange={(e) => setT({ ...t, do_not_say: e.target.value })}
            placeholder="refund, our fault, guarantee" />
        </label>

        <div className="flex items-center gap-3 pt-1">
          <button className="btn btn-primary" disabled={save.isPending}>
            {save.isPending ? 'Saving…' : 'Save tone'}
          </button>
          {save.isSuccess && <span role="status" className="text-sm text-pos">Saved</span>}
          {save.isError && <span role="alert" className="text-sm text-neg">Could not save: {(save.error as Error).message}</span>}
        </div>
      </form>
    </div>
  )
}
