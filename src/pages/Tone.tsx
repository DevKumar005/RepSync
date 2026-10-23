import { useEffect, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import type { Tone } from '../types'

const STYLES: { value: Tone['style']; emoji: string; label: string }[] = [
  { value: 'warm', emoji: '🤝', label: 'Warm' },
  { value: 'formal', emoji: '👔', label: 'Formal' },
  { value: 'apologetic', emoji: '🙏', label: 'Apologetic' },
  { value: 'concise', emoji: '⚡', label: 'Concise' },
]

export default function TonePage() {
  const { data } = useQuery({ queryKey: ['tone'], queryFn: api.getTone })
  const [t, setT] = useState<Tone>()
  useEffect(() => { if (data) setT(data) }, [data])
  const save = useMutation({ mutationFn: (x: Tone) => api.putTone(x) })

  if (!t) return (
    <div className="max-w-xl mx-auto pt-16 text-center space-y-3">
      <div className="skeleton h-8 w-48 rounded mx-auto" />
      <div className="skeleton h-4 w-64 rounded mx-auto" />
    </div>
  )

  return (
    <div className="max-w-xl mx-auto pt-6 fade-in">
      <form className="panel p-6 space-y-6" onSubmit={(e) => { e.preventDefault(); save.mutate(t) }}>
        <div className="space-y-1.5">
          <h1 className="text-2xl font-bold tracking-tight">Reply tone</h1>
          <p className="text-sm text-ink/45 leading-relaxed">New drafts follow this. Replies you approve are never changed.</p>
        </div>

        <fieldset className="space-y-3">
          <legend className="text-sm font-medium text-ink/70">Style</legend>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {STYLES.map((s) => (
              <button type="button" key={s.value} aria-pressed={t.style === s.value} onClick={() => setT({ ...t, style: s.value })}
                className={`panel !rounded-xl p-3 text-center transition-all duration-200 cursor-pointer ${t.style === s.value ? '!border-brand !bg-brandsoft shadow-sm' : 'hover:border-brand/30'}`}>
                <span className="text-2xl block mb-1">{s.emoji}</span>
                <span className={`text-sm font-medium ${t.style === s.value ? 'text-brand' : 'text-ink/60'}`}>{s.label}</span>
              </button>
            ))}
          </div>
        </fieldset>

        <label className="block space-y-2">
          <span className="text-sm font-medium text-ink/70">Sample replies you like</span>
          <textarea className="field font-normal" rows={4} value={t.sample_replies}
            onChange={(e) => setT({ ...t, sample_replies: e.target.value })}
            placeholder="Paste one or two replies you have written before" />
        </label>

        <label className="block space-y-2">
          <span className="text-sm font-medium text-ink/70">Words to never use</span>
          <input className="field font-normal" value={t.do_not_say}
            onChange={(e) => setT({ ...t, do_not_say: e.target.value })}
            placeholder="refund, our fault, guarantee" />
        </label>

        <div className="flex items-center gap-3 pt-1">
          <button className="btn btn-primary" disabled={save.isPending}>
            {save.isPending ? 'Saving…' : 'Save tone →'}
          </button>
          {save.isSuccess && <span role="status" className="text-sm text-pos flex items-center gap-1">✓ Saved</span>}
          {save.isError && <span role="alert" className="text-sm text-neg">Could not save: {(save.error as Error).message}</span>}
        </div>
      </form>
    </div>
  )
}
