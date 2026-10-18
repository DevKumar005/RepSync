import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../api/client'
import { useMode } from '../theme'
import type { DraftStatus, Review, ReviewFilters, SyncEvent, Theme, TinyFishCall } from '../types'

const Stars = ({ n: raw }: { n: number }) => { const n = Math.max(0, Math.min(5, Math.round(raw))); return <span aria-label={`${n} out of 5`} className="text-warn">{'★'.repeat(n)}<span className="text-line">{'★'.repeat(5 - n)}</span></span> }
const Empty = ({ children }: { children: React.ReactNode }) => <p className="p-5 text-sm text-ink/60">{children}</p>
const Loading = () => <p className="p-5 text-sm text-ink/60">Loading…</p>

export function SummaryBar({ id }: { id: string }) {
  const { data } = useQuery({ queryKey: ['summary', id], queryFn: () => api.summary(id) })
  const items = data ? [
    ['Average rating', data.avg_rating.toFixed(1), ''], ['Total reviews', String(data.total_reviews), ''],
    ['Negative', `${data.pct_negative}%`, ''], ['Negatives with no reply', String(data.unanswered_negatives), data.unanswered_negatives ? 'text-neg' : ''],
  ] : []
  return (
    <div className="panel grid grid-cols-2 md:grid-cols-4 divide-line md:divide-x">
      {!data && <Loading />}
      {items.map(([label, value, cls]) => (
        <div key={label} className="p-4"><div className={`font-display text-3xl font-bold ${cls}`}>{value}</div><div className="text-sm text-ink/60">{label}</div></div>
      ))}
    </div>
  )
}

export function FixesPanel({ id }: { id: string }) {
  const { data } = useQuery({ queryKey: ['fixes', id], queryFn: () => api.fixes(id) })
  return (
    <section className="panel">
      <h2 className="px-4 pt-4 text-lg font-bold">Top 3 fixes</h2>
      {!data ? <Loading /> : (
        <ol className="divide-y divide-line">
          {data.map((f) => (
            <li key={f.rank} className="flex gap-3 p-4">
              <span className="font-display text-2xl font-bold text-brand">{f.rank}</span>
              <div><div className="font-semibold">{f.title}</div><p className="text-sm text-ink/70">{f.rationale}</p>
                <span className="chip mt-1">{f.evidence_count} {f.evidence_count === 1 ? 'review' : 'reviews'}</span></div>
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}

export function ThemePanel({ id, selected, onSelect }: { id: string; selected?: string; onSelect: (t?: string) => void }) {
  const { data } = useQuery({ queryKey: ['themes', id], queryFn: () => api.themes(id) })
  const sel: Theme | undefined = data?.find((t) => t.id === selected)
  const dark = useMode() === 'dark'
  const hot = dark ? '#F08068' : '#B93A26'
  const dim = dark ? '#5E342D' : '#E6B8AE'
  const text = dark ? '#E6EDF1' : '#16222B'
  return (
    <section className="panel p-4">
      <h2 className="text-lg font-bold">What customers complain about</h2>
      <p className="text-sm text-ink/60">Select a theme to filter the review feed.</p>
      {!data ? <Loading /> : data.length === 0 ? <Empty>No complaint themes yet. Run a sync to find them.</Empty> : (
        <ResponsiveContainer width="100%" height={data.length * 44 + 16}>
          <BarChart data={data} layout="vertical" margin={{ left: 0, right: 24 }}>
            <XAxis type="number" hide /><YAxis type="category" dataKey="label" width={140} tick={{ fontSize: 13, fill: text }} axisLine={false} tickLine={false} />
            <Tooltip formatter={(v) => `${v} reviews`} cursor={{ fill: dark ? '#0F161B' : '#F2F5F6' }}
              contentStyle={{ background: dark ? '#162027' : '#fff', border: `1px solid ${dark ? '#2C3A44' : '#D9E0E4'}`, borderRadius: 6 }} itemStyle={{ color: text }} />
            <Bar dataKey="count" radius={[0, 4, 4, 0]} onClick={(d: any) => onSelect(d.id === selected ? undefined : d.id)}>
              {data.map((t) => <Cell key={t.id} cursor="pointer" fill={!selected || t.id === selected ? hot : dim} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
      {sel && <ul className="mt-2 space-y-1 border-l-2 border-neg pl-3 text-sm italic text-ink/80">{sel.quotes.map((q) => <li key={q}>“{q}”</li>)}</ul>}
    </section>
  )
}

export function ReviewFeed({ id, theme }: { id: string; theme?: string }) {
  const [f, setF] = useState<ReviewFilters>({})
  const filters = { ...f, theme }
  const { data } = useQuery({ queryKey: ['reviews', id, filters], queryFn: () => api.reviews(id, filters) })
  const sel = (key: keyof ReviewFilters, opts: [string, string][]) => (
    <select aria-label={key} className="field !w-auto" value={String(f[key] ?? '')} onChange={(e) => setF({ ...f, [key]: e.target.value || undefined })}>
      <option value="">{key[0].toUpperCase() + key.slice(1)}: all</option>{opts.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
    </select>
  )
  return (
    <section className="panel">
      <div className="flex flex-wrap items-center gap-2 p-4">
        <h2 className="mr-auto text-lg font-bold">Reviews</h2>
        {sel('platform', [['google_maps', 'Google Maps'], ['zomato', 'Zomato'], ['practo', 'Practo'], ['justdial', 'JustDial'], ['tripadvisor', 'Tripadvisor']])}
        {sel('sentiment', [['negative', 'Negative'], ['neutral', 'Neutral'], ['positive', 'Positive']])}
      </div>
      {!data ? <Loading /> : data.length === 0 ? (
        <Empty>No reviews match these filters. <button className="underline" onClick={() => setF({})}>Clear filters</button></Empty>
      ) : (
        <ul className="divide-y divide-line">
          {data.map((r) => (
            <li key={r.id} className="p-4">
              <div className="flex flex-wrap items-center gap-2 text-sm">
                <span className="chip">{r.platform.replace(/_/g, ' ')}</span><Stars n={r.rating} /><span className="font-semibold">{r.author}</span>
                <span className="text-ink/50">{r.posted_at}</span>
                {r.sentiment === 'negative' && <span className={`chip ${r.has_owner_reply ? '' : '!bg-negsoft !text-neg'}`}>{r.has_owner_reply ? 'Owner replied' : 'No reply yet'}</span>}
              </div>
              <p className="mt-1">{r.text}</p>
              <a className="text-sm text-brand underline" href={r.url} target="_blank" rel="noreferrer">Open original review</a>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

function DraftCard({ review, outletId }: { review: Review; outletId: string }) {
  const d = review.draft!
  const qc = useQueryClient()
  const [text, setText] = useState(d.text)
  const [err, setErr] = useState('')
  const [copied, setCopied] = useState(false)
  const done = () => qc.invalidateQueries({ queryKey: ['reviews', outletId] })
  const patch = useMutation({ mutationFn: (b: { text?: string; status?: DraftStatus }) => api.patchDraft(d.id, b), onSuccess: () => { setErr(''); done() }, onError: (e: Error) => setErr(e.message) })
  const regen = useMutation({ mutationFn: (i?: string) => api.draftFor(review.id, i), onSuccess: (n) => { setText(n.text); done() }, onError: (e: Error) => setErr(e.message) })
  const locked = d.status === 'approved' || d.status === 'posted'
  const busy = patch.isPending || regen.isPending
  return (
    <li className="p-4">
      <div className="flex items-center gap-2 text-sm"><Stars n={review.rating} /><span className="font-semibold">{review.author}</span>
        <span className={`chip ml-auto ${d.status === 'approved' ? '!bg-brandsoft !text-brand' : d.status === 'rejected' ? '!bg-negsoft !text-neg' : ''}`}>{d.status}</span></div>
      <p className="mt-1 line-clamp-2 text-sm text-ink/70">{review.text}</p>
      <textarea aria-label={`Reply to ${review.author}`} className="field mt-2" rows={4} value={text} disabled={locked} onChange={(e) => setText(e.target.value)} />
      {d.guardrail_flags.length > 0 && <p className="mt-1 text-sm text-warn">Flagged: {d.guardrail_flags.join(', ')}</p>}
      {err && <p role="alert" className="mt-1 text-sm text-neg">{err}</p>}
      <div className="mt-2 flex flex-wrap gap-2">
        {!locked && <>
          <button className="btn btn-primary" disabled={busy} onClick={() => patch.mutate({ text, status: 'approved' })}>Approve</button>
          {text !== d.text && <button className="btn" disabled={busy} onClick={() => patch.mutate({ text })}>Save edit</button>}
          <button className="btn" disabled={busy} onClick={() => regen.mutate('Make it shorter')}>Shorter</button>
          <button className="btn" disabled={busy} onClick={() => regen.mutate('Offer a callback')}>Offer a callback</button>
          <button className="btn btn-danger" disabled={busy} onClick={() => patch.mutate({ status: 'rejected' })}>Reject</button>
        </>}
        {locked && <>
          <button className="btn btn-primary" onClick={() => { navigator.clipboard.writeText(d.text); setCopied(true) }}>{copied ? 'Copied' : 'Copy reply'}</button>
          <a className="btn" href={review.url} target="_blank" rel="noreferrer">Open review to post</a>
        </>}
        {d.status === 'rejected' && <button className="btn" onClick={() => patch.mutate({ status: 'draft' })}>Restore draft</button>}
      </div>
    </li>
  )
}

export function ReplyQueue({ id }: { id: string }) {
  const { data } = useQuery({ queryKey: ['reviews', id, { queue: true }], queryFn: () => api.reviews(id, { sentiment: 'negative' }) })
  const list = data?.filter((r) => r.draft)
  return (
    <section className="panel">
      <h2 className="px-4 pt-4 text-lg font-bold">Reply queue</h2>
      <p className="px-4 text-sm text-ink/60">Nothing is ready to post until you approve it.</p>
      {!list ? <Loading /> : list.length === 0 ? <Empty>All caught up. New negative reviews will show up here with a draft reply.</Empty> : (
        <ul className="divide-y divide-line">{list.map((r) => <DraftCard key={r.draft!.id + r.draft!.status + r.draft!.text} review={r} outletId={id} />)}</ul>
      )}
    </section>
  )
}

const tag: Record<TinyFishCall['endpoint'], string> = { search: 'bg-brandsoft text-brand', fetch: 'bg-fetchbg text-fetchfg', agent: 'bg-warnsoft text-warn' }
export function ActivityLog({ id, live, syncing }: { id: string; live: SyncEvent[]; syncing: boolean }) {
  const { data } = useQuery({ queryKey: ['log', id], queryFn: () => api.log(id) })
  const steps = data?.reduce((s, c) => s + (c.steps_used ?? 0), 0) ?? 0
  return (
    <section className="panel overflow-hidden">
      <div className="flex items-center justify-between p-4"><h2 className="text-lg font-bold">TinyFish activity</h2>
        {syncing && <span className="chip !bg-brandsoft !text-brand" role="status">Live</span>}</div>
      {live.length > 0 && <ul className="mx-4 mb-3 space-y-1 border-l-2 border-brand pl-3 font-mono text-xs">{live.map((e, i) => <li key={i}>{e.message}</li>)}</ul>}
      {!data ? <Loading /> : data.length === 0 ? <Empty>No calls yet. Sync reviews to see Search, Fetch and Agent at work.</Empty> : (
        <ul className="divide-y divide-line border-t border-line text-sm">
          {data.map((c) => (
            <li key={c.id} className="flex items-start gap-2 p-3">
              <span className={`chip w-14 shrink-0 text-center ${tag[c.endpoint]}`}>{c.endpoint}</span>
              <div className="min-w-0 flex-1"><div className="truncate">{c.input}</div>
                <div className="font-mono text-xs text-ink/60">{c.status} · {c.items_returned} items · {(c.duration_ms / 1000).toFixed(1)}s{c.cached ? ' · cached' : ''}{c.steps_used ? ` · ${c.steps_used} steps` : ''}</div></div>
            </li>
          ))}
        </ul>
      )}
      {steps > 0 && <p className="border-t border-line p-3 text-xs text-ink/60">Agent steps used in this sync: {steps}</p>}
    </section>
  )
}