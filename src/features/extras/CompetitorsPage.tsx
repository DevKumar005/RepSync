import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { SyncEvent } from '../../types'
import { extrasApi } from './api'
import type { CompetitorCandidate, CompetitorResult, GapRow } from './types'
import { ErrorNote, Panel, SampleBadge, StatusChip } from './ui'

const pct = (r: number | null) => (r === null ? '–' : `${r % 1 === 0 ? r : r.toFixed(1)}%`)

function GapGrid({ result }: { result: CompetitorResult }) {
  const outlets = result.outlets ?? []
  const rows = result.matrix ?? []
  if (!rows.length) {
    return <p className="px-5 pb-5 text-sm text-ink/45">No complaint theme was mentioned at least 3 times across these outlets yet.</p>
  }
  const shade = (row: GapRow, rate: number | null) => {
    if (rate === null) return ''
    const max = Math.max(...row.cells.map((c) => c.rate ?? 0), 1)
    const a = Math.round((rate / max) * 30)
    return a ? `rgb(var(--neg) / ${a / 100})` : ''
  }
  return (
    <div className="overflow-x-auto px-5 pb-5">
      <table className="w-full min-w-[560px] text-sm">
        <thead>
          <tr className="text-left text-[12px] text-ink/45">
            <th className="py-2 pr-3 font-medium">Complaint theme</th>
            {outlets.map((o) => (
              <th key={o.key} className="py-2 px-2 font-medium text-center">
                <span className={o.key === 'you' ? 'text-brand font-semibold' : ''}>{o.key === 'you' ? 'You' : o.key}</span>
                <span className="block text-[10px] font-normal text-ink/35 truncate max-w-[120px] mx-auto" title={o.name}>
                  {o.name} · n={o.n}
                </span>
              </th>
            ))}
            <th className="py-2 pl-2 font-medium">Gap</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {rows.map((row) => (
            <tr key={row.theme}>
              <td className="py-2.5 pr-3 font-medium capitalize">{row.theme}</td>
              {row.cells.map((c) => (
                <td key={c.key} className="py-2.5 px-2 text-center tabular-nums" style={{ background: shade(row, c.rate) }}>
                  <span className={`font-semibold ${c.key === 'you' ? 'text-ink' : 'text-ink/80'}`}>{pct(c.rate)}</span>
                  <span className="block text-[10px] text-ink/40">{c.count} of {c.n}</span>
                </td>
              ))}
              <td className="py-2.5 pl-2"><StatusChip status={row.status} /></td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-3 text-[11px] text-ink/40">
        Share of each outlet's analysed public reviews that mention the complaint. Based on {outlets.map((o) => `${o.n}`).join(' / ')} public reviews
        (You / {outlets.slice(1).map((o) => o.key).join(' / ')}). Not star ratings.
      </p>
    </div>
  )
}

function CandidatePicker({ id, onScan, busy }: { id: string; onScan: (p: CompetitorCandidate[]) => void; busy: boolean }) {
  const cands = useQuery({ queryKey: ['extras', 'candidates', id], queryFn: () => extrasApi.candidates(id) })
  const [picked, setPicked] = useState<string[]>([])
  const [custom, setCustom] = useState('')
  const list = cands.data?.candidates ?? []
  useEffect(() => { if (list.length && !picked.length) setPicked(list.slice(0, 3).map((c) => c.name)) }, [list.length])
  const toggle = (n: string) => setPicked((p) => (p.includes(n) ? p.filter((x) => x !== n) : p.length < 3 ? [...p, n] : p))
  const live = cands.data?.source === 'live'

  return (
    <div className="px-5 pb-5 space-y-3">
      {cands.isLoading && <p className="text-sm text-ink/45">Finding nearby competitors…</p>}
      {cands.isError && <p role="alert" className="text-sm text-neg">Could not load competitors: {(cands.error as Error).message}</p>}
      {cands.data?.message && <p className="text-sm text-ink/50">{cands.data.message}</p>}
      {list.length > 0 && (
        <>
          <p className="text-sm text-ink/60">Pick up to 3 competitors to compare. <SampleBadge source={cands.data?.source} /></p>
          <ul className="grid gap-2 sm:grid-cols-2">
            {list.map((c) => (
              <li key={c.name}>
                <label className="flex cursor-pointer items-start gap-2 rounded-xl border border-line px-3 py-2 hover:bg-paper">
                  <input type="checkbox" className="accent-brand mt-1" checked={picked.includes(c.name)} onChange={() => toggle(c.name)} />
                  <span className="min-w-0">
                    <span className="block text-sm font-medium">{c.name}</span>
                    {c.area && <span className="block text-xs text-ink/45 truncate">{c.area}</span>}
                  </span>
                </label>
              </li>
            ))}
          </ul>
        </>
      )}
      {live && (
        <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); const n = custom.trim(); if (n.length > 1 && picked.length < 3) { setPicked([...picked, n]); setCustom('') } }}>
          <input className="field" value={custom} onChange={(e) => setCustom(e.target.value)} placeholder="Swap in another competitor by name" maxLength={100} />
          <button className="btn" disabled={picked.length >= 3}>Add</button>
        </form>
      )}
      {live && picked.some((n) => !list.find((c) => c.name === n)) && (
        <p className="text-xs text-ink/50">Added: {picked.filter((n) => !list.find((c) => c.name === n)).join(', ')}</p>
      )}
      <button
        className="btn btn-primary"
        disabled={busy || !picked.length}
        onClick={() => onScan(picked.map((n) => list.find((c) => c.name === n) ?? { name: n, url: null, area: null }))}
      >
        {busy ? 'Starting…' : `Scan ${picked.length} competitor${picked.length === 1 ? '' : 's'} →`}
      </button>
      <p className="text-[11px] text-ink/40">
        {live
          ? 'Live scans use TinyFish credits: public pages only, at most 50 reviews per competitor, cached for 24 hours.'
          : 'Live scanning is off here, so this replays saved sample data with no network calls.'}
      </p>
    </div>
  )
}

export function CompetitorsSection({ id }: { id: string }) {
  const qc = useQueryClient()
  const [events, setEvents] = useState<SyncEvent[]>([])
  const [picking, setPicking] = useState(false)
  const res = useQuery({
    queryKey: ['extras', 'competitors', id],
    queryFn: () => extrasApi.competitors(id),
    refetchInterval: (q) => (q.state.data?.status === 'running' ? 1200 : false),
  })
  const running = res.data?.status === 'running'

  useEffect(() => {
    if (!running) return
    return extrasApi.streamScan(id, (e) => setEvents((ev) => [...ev.slice(-30), e]))
  }, [id, running])

  useEffect(() => {
    if (res.data?.status === 'done') qc.invalidateQueries({ queryKey: ['extras', 'velocity', id] })
  }, [res.data?.status, res.data?.generated_at, id, qc])

  const scan = useMutation({
    mutationFn: (picks: CompetitorCandidate[]) => extrasApi.scan(id, picks.map(({ name, url }) => ({ name, url }))),
    onSuccess: () => { setEvents([]); setPicking(false); qc.invalidateQueries({ queryKey: ['extras', 'competitors', id] }) },
  })

  const data = res.data
  const showPicker = data?.status === 'none' || data?.status === 'failed' || picking
  const lowSample = (data?.outlets ?? []).filter((o) => o.low_sample)

  return (
    <div className="space-y-6">
      <Panel
        title="Competitor gap matrix"
        action={
          <div className="flex items-center gap-2">
            <SampleBadge source={data?.source} />
            {data?.status === 'done' && !picking && <button className="btn !py-1 !text-xs" onClick={() => setPicking(true)}>Rescan</button>}
          </div>
        }
      >
        {res.isLoading && <p className="px-5 pb-5 text-sm text-ink/45">Loading…</p>}
        {res.isError && <ErrorNote>Could not load the gap matrix: {(res.error as Error).message}</ErrorNote>}
        {data?.status === 'failed' && <ErrorNote>Last scan failed: {data.error}</ErrorNote>}
        {scan.isError && <ErrorNote>Could not start the scan: {(scan.error as Error).message}</ErrorNote>}
        {showPicker && !running && <CandidatePicker id={id} busy={scan.isPending} onScan={(p) => scan.mutate(p)} />}
        {running && (
          <div className="px-5 pb-5" aria-live="polite">
            <p className="text-sm font-medium flex items-center gap-2"><span className="status-dot status-dot-ok pulse-live" /> Scanning competitors…</p>
            <ol className="mt-3 space-y-1 font-mono text-[12px] text-ink/60 max-h-56 overflow-auto">
              {events.map((e, i) => (
                <li key={i}><span className="text-ink/30">{e.type === 'tinyfish_call' ? 'tinyfish' : 'stage'} ·</span> {e.message}</li>
              ))}
            </ol>
          </div>
        )}
        {data?.status === 'done' && !picking && (
          <>
            {lowSample.length > 0 && (
              <p className="mx-5 mb-3 rounded-lg bg-warnsoft px-3 py-2 text-xs text-warn">
                Small sample: {lowSample.map((o) => (o.key === 'you' ? 'your outlet' : o.name)).join(', ')} has fewer than 10 analysed reviews, so treat these rates as rough.
              </p>
            )}
            <GapGrid result={data} />
          </>
        )}
      </Panel>

      {data?.status === 'done' && !picking && (data.advice?.length ?? 0) > 0 && (
        <Panel title="What to do about it">
          <ul className="grid gap-3 px-5 pb-5 md:grid-cols-3">
            {data.advice!.map((a) => (
              <li key={a.theme} className="rounded-2xl border border-line bg-paper p-4 space-y-2">
                <StatusChip status={a.status} />
                <p className="text-sm leading-relaxed">{a.text}</p>
                {(data.quotes?.[a.theme] ?? []).map((q, i) => (
                  <blockquote key={i} className="border-l-2 border-line pl-2 text-xs italic text-ink/50">
                    “{q.text}” <span className="not-italic text-ink/35">· {data.outlets?.find((o) => o.key === q.outlet_key)?.name}</span>
                  </blockquote>
                ))}
              </li>
            ))}
          </ul>
        </Panel>
      )}
    </div>
  )
}

export default function CompetitorsPage() {
  const { id = '' } = useParams()
  return (
    <div className="space-y-6 fade-in">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Competitor Gap Matrix</h1>
        <p className="text-sm text-ink/50 mt-1">
          How often customers complain about each theme at your outlet compared with up to 3 nearby competitors, from public reviews.
        </p>
      </div>
      <CompetitorsSection id={id} />
    </div>
  )
}
