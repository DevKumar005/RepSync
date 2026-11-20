import { useEffect, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import type { Tone } from '../types'

const STYLES: { value: Tone['style']; label: string; hint: string }[] = [
  { value: 'warm', label: 'Warm', hint: 'Friendly and personal' },
  { value: 'formal', label: 'Formal', hint: 'Polite and precise' },
  { value: 'apologetic', label: 'Apologetic', hint: 'Owns the problem' },
  { value: 'concise', label: 'Concise', hint: 'Short and direct' },
]

export default function TonePage() {
  const { data } = useQuery({ queryKey: ['tone'], queryFn: api.getTone })
  const [t, setT] = useState<Tone>()
  useEffect(() => { if (data) setT(data) }, [data])
  const save = useMutation({ mutationFn: (x: Tone) => api.putTone(x) })

  if (!t) return (
    <div className="rs-container pt-16 text-center space-y-3">
      <div className="skeleton h-8 w-48 rounded mx-auto" />
      <div className="skeleton h-4 w-64 rounded mx-auto" />
    </div>
  )

  return (
    <div className="rs-container pt-10 pb-20 fade-in">
      <form className="panel grid gap-8 p-6 lg:grid-cols-2 lg:gap-12 lg:p-10" onSubmit={(e) => { e.preventDefault(); save.mutate(t) }}>
        <div className="space-y-6">
        <div className="space-y-1.5">
          <p className="label-overline">Reply tone</p>
          <h1 className="rs-title text-[clamp(28px,3.2vw,44px)]">How your replies should sound</h1>
          <p className="rs-copy text-sm">New drafts follow this style. Replies you have already approved are never changed.</p>
        </div>

        <fieldset className="space-y-3">
          <legend className="text-sm font-medium text-ink/70">Style</legend>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {STYLES.map((s) => (
              <button type="button" key={s.value} aria-pressed={t.style === s.value} onClick={() => setT({ ...t, style: s.value })}
                className={`rounded-2xl p-3 text-center transition-all duration-200 cursor-pointer ${t.style === s.value ? 'tile tile-speed' : 'border border-ink/[.08] bg-ink/[.03] hover:bg-ink/[.06]'}`}>
                <span className={`block text-sm font-semibold ${t.style === s.value ? 'text-white' : 'text-ink/80'}`}>{s.label}</span>
                <span className={`mt-0.5 block text-[11px] ${t.style === s.value ? 'text-white/75' : 'text-ink/45'}`}>{s.hint}</span>
              </button>
            ))}
          </div>
        </fieldset>
        </div>

        <div className="space-y-6">
        <label className="block space-y-2">
          <span className="text-sm font-medium text-ink/70">Sample replies you like</span>
          <textarea className="field font-normal" rows={6} value={t.sample_replies}
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
        </div>
      </form>
    </div>
  )
}
