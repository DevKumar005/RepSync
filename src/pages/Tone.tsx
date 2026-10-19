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
  if (!t) return <p className="text-sm text-ink/60">Loading…</p>
  return (
    <form className="panel mx-auto max-w-2xl space-y-4 p-5" onSubmit={(e) => { e.preventDefault(); save.mutate(t) }}>
      <div><h1 className="text-2xl font-bold">How should your replies sound?</h1><p className="text-sm text-ink/60">New drafts follow this. Replies you approve are never changed.</p></div>
      <fieldset><legend className="text-sm font-semibold">Style</legend>
        <div className="mt-1 flex flex-wrap gap-2">{STYLES.map((s) => (
          <button type="button" key={s} aria-pressed={t.style === s} onClick={() => setT({ ...t, style: s })} className={`btn capitalize ${t.style === s ? 'btn-primary' : ''}`}>{s}</button>))}</div></fieldset>
      <label className="block text-sm font-semibold">Sample replies you like
        <textarea className="field mt-1 font-normal" rows={4} value={t.sample_replies} onChange={(e) => setT({ ...t, sample_replies: e.target.value })} placeholder="Paste one or two replies you have written before" /></label>
      <label className="block text-sm font-semibold">Words to never use
        <input className="field mt-1 font-normal" value={t.do_not_say} onChange={(e) => setT({ ...t, do_not_say: e.target.value })} placeholder="refund, our fault, guarantee" /></label>
      <div className="flex items-center gap-3"><button className="btn btn-primary" disabled={save.isPending}>{save.isPending ? 'Saving…' : 'Save tone'}</button>
        {save.isSuccess && <span role="status" className="text-sm text-pos">Tone saved</span>}
        {save.isError && <span role="alert" className="text-sm text-neg">Could not save: {(save.error as Error).message}</span>}</div>
    </form>
  )
}
