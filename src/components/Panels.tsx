import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../api/client'
import { useMode } from '../theme'
import type { DraftStatus, Review, ReviewFilters, SyncEvent, Theme, TinyFishCall } from '../types'

const Stars = ({ n: raw }: { n: number }) => {
  const n = Math.max(0, Math.min(5, Math.round(raw)))
  return (
    <span aria-label={`${n} out of 5`} className="tracking-tight text-[15px]">
      {Array.from({ length: 5 }, (_, i) => (
        <span key={i} className={i < n ? 'text-amber-400' : 'text-line'}>{i < n ? '★' : '☆'}</span>
      ))}
    </span>
  )
}

const Empty = ({ icon, children }: { icon?: React.ReactNode; children: React.ReactNode }) => (
  <div className="px-5 py-8 text-center fade-in">
    {icon && <div className="mx-auto mb-3 text-ink/20">{icon}</div>}
    <p className="text-sm text-ink/40 leading-relaxed max-w-xs mx-auto">{children}</p>
  </div>
)

const Loading = () => (
  <div className="px-5 py-6 space-y-3">
    <div className="skeleton h-4 w-3/4 rounded" />
    <div className="skeleton h-4 w-1/2 rounded" />
    <div className="skeleton h-4 w-2/3 rounded" />
  </div>
)

const SectionHeader = ({ children, action }: { children: React.ReactNode; action?: React.ReactNode }) => (
  <div className="flex items-center justify-between px-5 pt-5 pb-3">
    <h2 className="text-[13px] font-semibold uppercase tracking-wider text-ink/35">{children}</h2>
    {action}
  </div>
)

export function SummaryBar({ id }: { id: string }) {
  const { data } = useQuery({ queryKey: ['summary', id], queryFn: () => api.summary(id) })
  const items = data ? [
    { label: 'Average rating', value: data.avg_rating.toFixed(1), icon: '⭐', cls: '' },
    { label: 'Total reviews', value: String(data.total_reviews), icon: '💬', cls: '' },
    { label: 'Negative', value: `${data.pct_negative}%`, icon: '📉', cls: data.pct_negative > 30 ? 'text-neg' : '' },
    { label: 'Unanswered negatives', value: String(data.unanswered_negatives), icon: '⚠️', cls: data.unanswered_negatives > 0 ? 'text-neg' : '' },
  ] : []

  if (!data) {
    return (
      <div className="panel grid grid-cols-2 md:grid-cols-4 divide-y md:divide-y-0 divide-x-0 md:divide-x divide-line">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="px-5 py-5">
            <div className="skeleton h-7 w-16 rounded mb-2" />
            <div className="skeleton h-3 w-24 rounded" />
          </div>
        ))}
      </div>
    )
  }

  const allZero = data.total_reviews === 0

  return (
    <div className="panel grid grid-cols-2 md:grid-cols-4 divide-y md:divide-y-0 divide-x-0 md:divide-x divide-line fade-in">
      {items.map(({ label, value, icon, cls }) => (
        <div key={label} className="px-5 py-4 group">
          <div className="flex items-center gap-2">
            <span className="text-base opacity-70 group-hover:opacity-100 transition-opacity">{icon}</span>
            <span className={`text-2xl font-bold tracking-tight tabular-nums ${cls} ${allZero ? 'text-ink/25' : ''}`}>{value}</span>
          </div>
          <div className="text-[11px] text-ink/35 mt-1 uppercase tracking-wider font-medium">{label}</div>
        </div>
      ))}
      {allZero && (
        <div className="col-span-full px-5 py-3 bg-warnsoft/50 border-t border-warn/20">
          <p className="text-xs text-warn flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v.01"/><path d="M12 8v4"/></svg>
            No review data yet — hit <strong>Sync reviews</strong> to pull in your latest reviews.
          </p>
        </div>
      )}
    </div>
  )
}

export function FixesPanel({ id }: { id: string }) {
  const { data } = useQuery({ queryKey: ['fixes', id], queryFn: () => api.fixes(id) })
  return (
    <section className="panel">
      <SectionHeader>
        <span className="flex items-center gap-1.5">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          Top fixes
        </span>
      </SectionHeader>
      {!data ? <Loading /> : data.length === 0 ? (
        <Empty icon={
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
        }>No issues detected yet. Run a sync and we&apos;ll surface the most impactful things to fix.</Empty>
      ) : (
        <ol className="divide-y divide-line">
          {data.map((f) => (
            <li key={f.rank} className="flex gap-4 px-5 py-4 hover:bg-paper/50 transition-colors duration-150 group">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-brandsoft text-sm font-bold text-brand shrink-0 group-hover:scale-105 transition-transform">{f.rank}</span>
              <div className="min-w-0">
                <div className="font-semibold text-sm text-ink/90">{f.title}</div>
                <p className="text-sm text-ink/50 mt-0.5 leading-relaxed">{f.rationale}</p>
                <span className="chip mt-2 text-[11px]">{f.evidence_count} {f.evidence_count === 1 ? 'review' : 'reviews'}</span>
              </div>
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
  const hot = dark ? '#C4B5FD' : '#7C3AED'
  const dim = dark ? '#3B3060' : '#DDD6FE'
  const text = dark ? '#E8E6E3' : '#1E2022'
  return (
    <section className="panel p-5">
      <h2 className="text-[13px] font-semibold uppercase tracking-wider text-ink/35 flex items-center gap-1.5">
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
        Complaint themes
      </h2>
      <p className="text-xs text-ink/35 mt-1">Click a bar to filter the review feed.</p>
      {!data ? <Loading /> : data.length === 0 ? (
        <Empty icon={
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
        }>No complaint themes yet. Run a sync and we&apos;ll cluster your negative reviews into patterns.</Empty>
      ) : (
        <div className="mt-3">
          <ResponsiveContainer width="100%" height={data.length * 44 + 16}>
            <BarChart data={data} layout="vertical" margin={{ left: 0, right: 24 }}>
              <XAxis type="number" hide /><YAxis type="category" dataKey="label" width={140} tick={{ fontSize: 13, fill: text }} axisLine={false} tickLine={false} />
              <Tooltip formatter={(v) => `${v} reviews`} cursor={{ fill: dark ? '#0F161B' : '#F2F5F6' }}
                contentStyle={{ background: dark ? '#1C1B18' : '#fff', border: `1px solid ${dark ? '#302D28' : '#EAE5DE'}`, borderRadius: 12 }} itemStyle={{ color: text }} />
              <Bar dataKey="count" radius={[0, 6, 6, 0]} onClick={(d: any) => onSelect(d.id === selected ? undefined : d.id)}>
                {data.map((t) => <Cell key={t.id} cursor="pointer" fill={!selected || t.id === selected ? hot : dim} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
      {sel && (
        <ul className="mt-3 space-y-1.5 border-l-2 border-brand/40 pl-3 text-sm italic text-ink/70 fade-in">
          {sel.quotes.map((q) => <li key={q} className="leading-relaxed">&ldquo;{q}&rdquo;</li>)}
        </ul>
      )}
    </section>
  )
}

export function ReviewFeed({ id, theme }: { id: string; theme?: string }) {
  const [f, setF] = useState<ReviewFilters>({})
  const filters = { ...f, theme }
  const { data } = useQuery({ queryKey: ['reviews', id, filters], queryFn: () => api.reviews(id, filters) })
  const sel = (key: keyof ReviewFilters, opts: [string, string][]) => (
    <select aria-label={key} className="field !w-auto !py-1.5 !px-2.5 !text-xs" value={String(f[key] ?? '')} onChange={(e) => setF({ ...f, [key]: e.target.value || undefined })}>
      <option value="">{key[0].toUpperCase() + key.slice(1)}: all</option>{opts.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
    </select>
  )
  return (
    <section className="panel">
      <div className="flex flex-wrap items-center gap-2 px-5 py-4">
        <h2 className="mr-auto text-[13px] font-semibold uppercase tracking-wider text-ink/35 flex items-center gap-1.5">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          Reviews
        </h2>
        {sel('platform', [['google_maps', 'Google Maps'], ['zomato', 'Zomato'], ['practo', 'Practo'], ['justdial', 'JustDial'], ['tripadvisor', 'Tripadvisor']])}
        {sel('sentiment', [['negative', 'Negative'], ['neutral', 'Neutral'], ['positive', 'Positive']])}
      </div>
      {!data ? <Loading /> : data.length === 0 ? (
        <Empty icon={
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
        }>No reviews match these filters. <button className="underline text-brand hover:text-brand/80 transition-colors" onClick={() => setF({})}>Clear filters</button></Empty>
      ) : (
        <ul className="divide-y divide-line">
          {data.map((r) => (
            <li key={r.id} className="p-4 hover:bg-paper/50 transition-colors duration-150">
              <div className="flex flex-wrap items-center gap-2 text-sm">
                <span className="chip text-[11px]">{r.platform.replace(/_/g, ' ')}</span>
                <Stars n={r.rating} />
                <span className="font-semibold text-ink/90">{r.author}</span>
                <span className="text-ink/40 text-xs">{r.posted_at}</span>
                {r.sentiment === 'negative' && (
                  <span className={`chip text-[11px] ${r.has_owner_reply ? '!bg-possoft !text-pos !border-pos/20' : '!bg-negsoft !text-neg !border-neg/20'}`}>
                    {r.has_owner_reply ? '✓ Owner replied' : '⚠ No reply yet'}
                  </span>
                )}
              </div>
              <p className="mt-2 text-[14px] leading-relaxed text-ink/75">{r.text}</p>
              <a className="inline-flex items-center gap-1 mt-2 text-xs text-brand hover:text-brand/70 transition-colors font-medium" href={r.url} target="_blank" rel="noreferrer">
                Open original
                <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
              </a>
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
    <li className="p-4 hover:bg-paper/30 transition-colors duration-150">
      <div className="flex items-center gap-2 text-sm">
        <Stars n={review.rating} />
        <span className="font-semibold text-ink/90">{review.author}</span>
        <span className={`chip ml-auto text-[11px] ${d.status === 'approved' ? '!bg-brandsoft !text-brand !border-brand/20' : d.status === 'rejected' ? '!bg-negsoft !text-neg !border-neg/20' : ''}`}>{d.status}</span>
      </div>
      <p className="mt-1.5 line-clamp-2 text-sm text-ink/60 leading-relaxed">{review.text}</p>
      <textarea aria-label={`Reply to ${review.author}`} className="field mt-3 text-[13px]" rows={4} value={text} disabled={locked} onChange={(e) => setText(e.target.value)} />
      {d.guardrail_flags.length > 0 && (
        <p className="mt-1.5 text-xs text-warn flex items-center gap-1">
          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          Flagged: {d.guardrail_flags.join(', ')}
        </p>
      )}
      {err && <p role="alert" className="mt-1.5 text-xs text-neg">{err}</p>}
      <div className="mt-3 flex flex-wrap gap-2">
        {!locked && <>
          <button className="btn btn-primary !text-xs !py-1.5" disabled={busy} onClick={() => patch.mutate({ text, status: 'approved' })}>✓ Approve</button>
          {text !== d.text && <button className="btn !text-xs !py-1.5" disabled={busy} onClick={() => patch.mutate({ text })}>Save edit</button>}
          <button className="btn !text-xs !py-1.5" disabled={busy} onClick={() => regen.mutate('Make it shorter')}>Shorter</button>
          <button className="btn !text-xs !py-1.5" disabled={busy} onClick={() => regen.mutate('Offer a callback')}>Offer callback</button>
          <button className="btn btn-danger !text-xs !py-1.5" disabled={busy} onClick={() => patch.mutate({ status: 'rejected' })}>Reject</button>
        </>}
        {locked && <>
          <button className="btn btn-primary !text-xs !py-1.5" onClick={() => { navigator.clipboard.writeText(d.text); setCopied(true) }}>{copied ? '✓ Copied' : 'Copy reply'}</button>
          <a className="btn !text-xs !py-1.5" href={review.url} target="_blank" rel="noreferrer">Open review to post</a>
        </>}
        {d.status === 'rejected' && <button className="btn !text-xs !py-1.5" onClick={() => patch.mutate({ status: 'draft' })}>Restore draft</button>}
      </div>
    </li>
  )
}

export function ReplyQueue({ id }: { id: string }) {
  const { data } = useQuery({ queryKey: ['reviews', id, { queue: true }], queryFn: () => api.reviews(id, { sentiment: 'negative' }) })
  const list = data?.filter((r) => r.draft)
  return (
    <section className="panel">
      <div className="px-5 pt-5 pb-3">
        <h2 className="text-[13px] font-semibold uppercase tracking-wider text-ink/35 flex items-center gap-1.5">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>
          Reply queue
        </h2>
        <p className="text-xs text-ink/35 mt-1">Nothing is posted until you approve it.</p>
      </div>
      {!list ? <Loading /> : list.length === 0 ? (
        <Empty icon={
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
        }>All caught up 🎉 New negative reviews will appear here with a draft reply.</Empty>
      ) : (
        <ul className="divide-y divide-line">{list.map((r) => <DraftCard key={r.draft!.id + r.draft!.status + r.draft!.text} review={r} outletId={id} />)}</ul>
      )}
    </section>
  )
}

const tag: Record<TinyFishCall['endpoint'], string> = {
  search: 'bg-brandsoft text-brand border-brand/15',
  fetch: 'bg-fetchbg text-fetchfg border-fetchfg/15',
  agent: 'bg-warnsoft text-warn border-warn/15',
}

export function ActivityLog({ id, live, syncing }: { id: string; live: SyncEvent[]; syncing: boolean }) {
  const { data } = useQuery({ queryKey: ['log', id], queryFn: () => api.log(id) })
  const steps = data?.reduce((s, c) => s + (c.steps_used ?? 0), 0) ?? 0
  return (
    <section className="panel overflow-hidden">
      <div className="flex items-center justify-between px-5 pt-5 pb-3">
        <h2 className="text-[13px] font-semibold uppercase tracking-wider text-ink/35 flex items-center gap-1.5">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20V10"/><path d="M18 20V4"/><path d="M6 20v-4"/></svg>
          TinyFish activity
        </h2>
        {syncing && (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-possoft border border-pos/20 px-2.5 py-0.5 text-[11px] font-semibold text-pos" role="status">
            <span className="status-dot status-dot-ok" />
            Live
          </span>
        )}
      </div>
      {live.length > 0 && (
        <ul className="mx-5 mb-3 space-y-1 border-l-2 border-brand/30 pl-3 font-mono text-xs text-ink/55">
          {live.map((e, i) => (
            <li key={i} className="fade-in leading-relaxed">{e.message}</li>
          ))}
        </ul>
      )}
      {!data ? <Loading /> : data.length === 0 ? (
        <Empty icon={
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20V10"/><path d="M18 20V4"/><path d="M6 20v-4"/></svg>
        }>No calls yet. Sync reviews to see Search, Fetch and Agent at work.</Empty>
      ) : (
        <ul className="divide-y divide-line border-t border-line text-xs">
          {data.map((c) => (
            <li key={c.id} className="flex items-start gap-2.5 px-5 py-3 hover:bg-paper/50 transition-colors duration-150">
              <span className={`chip shrink-0 w-14 text-center !text-[10px] !font-semibold !rounded-md ${tag[c.endpoint]}`}>{c.endpoint}</span>
              <div className="min-w-0 flex-1">
                <div className="truncate text-ink/65 leading-relaxed">{c.input}</div>
                <div className="font-mono text-ink/35 mt-0.5 flex items-center gap-1.5 flex-wrap">
                  <span className={c.status === 'ok' ? 'text-pos' : c.status === 'failed' ? 'text-neg' : 'text-warn'}>{c.status}</span>
                  <span>·</span>
                  <span>{c.items_returned} items</span>
                  <span>·</span>
                  <span>{(c.duration_ms / 1000).toFixed(1)}s</span>
                  {c.cached && <><span>·</span><span className="text-brand">cached</span></>}
                  {c.steps_used ? <><span>·</span><span>{c.steps_used} steps</span></> : null}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
      {steps > 0 && (
        <p className="border-t border-line px-5 py-3 text-xs text-ink/35">
          Agent steps used in this sync: <strong className="text-ink/60">{steps}</strong>
        </p>
      )}
    </section>
  )
}