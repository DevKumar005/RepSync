import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'
import { FixesPanel, SummaryBar } from '../../components/Panels'
import { extrasApi } from '../../features/extras/api'
import { extrasEnabled } from '../../features/extras/flags'
import { SampleBadge, StatusChip } from '../../features/extras/ui'
import { useCityMap } from '../../features/extras/useCityMap'
import { useOutlet } from './OutletLayout'

function Card({ title, to, cta, children, badge }: { title: string; to: string; cta: string; children: React.ReactNode; badge?: React.ReactNode }) {
  return (
    <section className="panel flex flex-col">
      <div className="flex items-center gap-2 px-5 pt-5 pb-3">
        <h2 className="mr-auto text-[13px] font-semibold uppercase tracking-[.1em] text-ink/45">{title}</h2>
        {badge}
      </div>
      <div className="flex-1 px-5 pb-4">{children}</div>
      <div className="border-t border-ink/[.07] px-5 py-3">
        <NavLink to={to} className="text-[13px] font-medium text-brand hover:underline underline-offset-4">{cta} →</NavLink>
      </div>
    </section>
  )
}

function RepliesSnapshot({ id }: { id: string }) {
  const { data } = useQuery({ queryKey: ['reviews', id, { queue: true }], queryFn: () => api.reviews(id, { sentiment: 'negative' }) })
  const waiting = data?.filter((r) => r.draft && ['draft', 'edited'].includes(r.draft.status)).length
  return (
    <Card title="Reply queue" to={`/outlet/${id}/replies`} cta="Review drafts">
      {waiting === undefined ? <div className="skeleton h-10 w-32" /> : (
        <p className="text-sm text-ink/65"><span className="mr-1 text-3xl font-semibold text-ink tabular-nums">{waiting}</span> draft {waiting === 1 ? 'reply is' : 'replies are'} waiting for your approval.</p>
      )}
    </Card>
  )
}

function CompetitorSnapshot({ id }: { id: string }) {
  const { data } = useQuery({ queryKey: ['extras', 'competitors', id], queryFn: () => extrasApi.competitors(id) })
  const rows = (data?.matrix ?? []).filter((r) => r.status !== 'parity').slice(0, 3)
  return (
    <Card title="Competitor gaps" to={`/outlet/${id}/competitors`} cta={data?.status === 'done' ? 'Open gap matrix' : 'Scan competitors'} badge={<SampleBadge source={data?.source} />}>
      {!data ? <div className="skeleton h-16 w-full" /> : data.status !== 'done' ? (
        <p className="text-sm text-ink/60">{data.status === 'running' ? 'A competitor scan is running…' : 'No scan yet. Compare your complaint rates with up to three nearby competitors.'}</p>
      ) : rows.length === 0 ? (
        <p className="text-sm text-ink/60">You are at parity with your competitors on every theme with enough mentions.</p>
      ) : (
        <ul className="space-y-2.5">
          {rows.map((r) => (
            <li key={r.theme} className="flex flex-wrap items-center gap-x-3 gap-y-0.5 text-sm">
              <span className="flex-1 capitalize">{r.theme}</span>
              <span className="order-last w-full tabular-nums text-xs text-ink/55 sm:order-none sm:w-auto sm:text-sm">you {r.cells[0].rate ?? 0}% · {r.versus_name?.replace(' (sample)', '')} {r.cells.find((c) => c.key === r.versus_key)?.rate ?? 0}%</span>
              <StatusChip status={r.status} />
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}

function VelocitySnapshot({ id }: { id: string }) {
  const { data } = useQuery({ queryKey: ['extras', 'velocity', id], queryFn: () => extrasApi.velocity(id) })
  const you = data?.series.find((s) => s.key === 'you')
  const warnings = data?.series.filter((s) => s.trend.status === 'warning') ?? []
  return (
    <Card title="Review velocity" to={`/outlet/${id}/velocity`} cta="Open chart" badge={<SampleBadge source={data?.source} />}>
      {!data || !you ? <div className="skeleton h-12 w-full" /> : (
        <div className="space-y-2 text-sm text-ink/65">
          <div className="flex h-10 items-end gap-[3px]" aria-label="Your reviews per week, last 12 weeks">
            {you.counts.map((c, i) => {
              const max = Math.max(...you.counts, 1)
              return <span key={i} className="flex-1 rounded-sm bg-brand/70" style={{ height: `${Math.max(6, (c / max) * 100)}%`, opacity: c ? 1 : 0.25 }} title={`${c} reviews`} />
            })}
          </div>
          <p>
            {you.trend.status === 'warning' ? `Your new reviews are down ${Math.abs(you.trend.change_pct ?? 0)}%.` : you.trend.status === 'ok' ? 'Your review flow is steady.' : 'Not enough dated reviews for a trend yet.'}
            {warnings.filter((w) => w.key !== 'you').length > 0 && ` ${warnings.filter((w) => w.key !== 'you').map((w) => w.name.replace(' (sample)', '')).join(', ')} slowing down.`}
          </p>
        </div>
      )}
    </Card>
  )
}

function AskSnapshot() {
  const { openChat } = useOutlet()
  const [q, setQ] = useState('')
  const go = (text: string) => { openChat(text); setQ('') }
  return (
    <section className="panel flex flex-col">
      <div className="px-5 pt-5 pb-3">
        <h2 className="text-[13px] font-semibold uppercase tracking-[.1em] text-ink/45">Ask RepSync</h2>
      </div>
      <div className="flex-1 px-5 pb-5">
      <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); if (q.trim().length > 1) go(q.trim()) }}>
        <input className="field !py-2" value={q} maxLength={300} onChange={(e) => setQ(e.target.value)} placeholder="What should I fix first?" aria-label="Ask a question" />
        <button className="btn btn-primary !py-2" disabled={q.trim().length < 2}>Ask</button>
      </form>
      <div className="mt-3 flex flex-wrap gap-1.5">
        {['How do I compare with competitors?', 'Mera rank kyun gira?'].map((s) => (
          <button key={s} className="chip hover:bg-ink/[.05]" onClick={() => go(s)}>{s}</button>
        ))}
      </div>
      </div>
    </section>
  )
}

function PostersSnapshot({ id }: { id: string }) {
  const { data } = useQuery({ queryKey: ['extras', 'poster-reviews', id], queryFn: () => api.reviews(id, {}) })
  const n = data?.filter((r) => r.rating >= 5 && r.sentiment !== 'negative').length
  return (
    <Card title="Review posters" to={`/outlet/${id}/posters`} cta="Create a poster">
      <p className="text-sm text-ink/65">
        {n === undefined ? 'Loading…' : n ? <><span className="mr-1 text-3xl font-semibold text-ink tabular-nums">{n}</span> five-star {n === 1 ? 'review is' : 'reviews are'} ready to share on Instagram or WhatsApp.</> : 'No five-star reviews yet. Sync to find some.'}
      </p>
    </Card>
  )
}

function MapSnapshot({ id }: { id: string }) {
  const { data } = useCityMap(id)
  const outlets = data?.outlets ?? []
  const rated = outlets.filter((o) => o.rating !== null).sort((a, b) => b.rating! - a.rating!)
  const pos = rated.findIndex((o) => o.is_you)
  const rising = outlets.filter((o) => (o.rating_change_60d ?? 0) > 0.05).length
  const nearby = outlets.filter((o) => !o.is_you).length
  return (
    <Card title="City map" to={`/outlet/${id}/map`} cta="Open map" badge={<SampleBadge source={data?.source} label="Sample" />}>
      {!data ? <div className="skeleton h-10 w-full" /> : (
        <p className="text-sm text-ink/65">
          {data.status === 'locating' ? 'Finding your outlet on the map…'
            : data.status === 'no_location' ? "We couldn't find your address on the map yet."
            : data.source === 'sample' ? <>In {data.locality}, you are <strong className="text-ink">#{pos + 1} of {rated.length}</strong> by rating. {rising} outlets are rising over the last 60 days.</>
            : <><strong className="text-ink">{nearby}</strong> similar {nearby === 1 ? 'place' : 'places'} within {(data.radius_m / 1000).toFixed(1)} km of you.{' '}
              {rated.length > 1 && pos >= 0 ? <>You are <strong className="text-ink">#{pos + 1} of {rated.length}</strong> among scanned places by review rating.</> : 'Scan competitors to compare ratings.'}</>}
        </p>
      )}
    </Card>
  )
}

export default function Overview() {
  const { id } = useOutlet()
  return (
    <div className="space-y-6">
      <SummaryBar id={id} />
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1.25fr)_minmax(0,1fr)]">
        <div className="space-y-5">
          <FixesPanel id={id} />
          {extrasEnabled && <CompetitorSnapshot id={id} />}
        </div>
        <div className="space-y-5">
          <RepliesSnapshot id={id} />
          {extrasEnabled && <VelocitySnapshot id={id} />}
        </div>
      </div>
      {extrasEnabled && (
        <div className="grid gap-5 md:grid-cols-3">
          <AskSnapshot />
          <PostersSnapshot id={id} />
          <MapSnapshot id={id} />
        </div>
      )}
    </div>
  )
}
