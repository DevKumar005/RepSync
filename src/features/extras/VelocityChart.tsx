import { useQuery } from '@tanstack/react-query'
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useMode } from '../../theme'
import { extrasApi } from './api'
import type { VelocityResponse } from './types'
import { ErrorNote, Panel, SampleBadge } from './ui'

const PALETTE = {
  light: { you: '#7C3AED', others: ['#0E7490', '#B45309', '#4D7C0F'], grid: '#E7E5E4', text: '#57534E' },
  dark: { you: '#C4B5FD', others: ['#67E8F9', '#FCD34D', '#BEF264'], grid: '#3A3733', text: '#A8A29E' },
}

const shortDate = (iso: string) => new Date(iso + 'T00:00:00').toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })

export function VelocityView({ data, height = 260 }: { data: VelocityResponse; height?: number }) {
  const p = PALETTE[useMode() === 'dark' ? 'dark' : 'light']
  const rows = data.weeks.map((w, i) => ({
    week: `w/c ${shortDate(w)}`,
    ...Object.fromEntries(data.series.map((s) => [s.key, s.counts[i] ?? 0])),
  }))
  const colour = (key: string, i: number) => (key === 'you' ? p.you : p.others[(i - 1) % p.others.length])
  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={rows} margin={{ top: 8, right: 12, bottom: 0, left: -18 }}>
          <CartesianGrid stroke={p.grid} strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="week" tick={{ fontSize: 10, fill: p.text }} interval={1} />
          <YAxis allowDecimals={false} tick={{ fontSize: 10, fill: p.text }} />
          <Tooltip
            formatter={(v: number, key: string) => [`${v} collected review${v === 1 ? '' : 's'}`, data.series.find((s) => s.key === key)?.name ?? key]}
            contentStyle={{ fontSize: 12, borderRadius: 10 }}
          />
          <Legend formatter={(key: string) => (key === 'you' ? 'You' : data.series.find((s) => s.key === key)?.name ?? key)} wrapperStyle={{ fontSize: 11 }} />
          {data.series.map((s, i) => (
            <Line key={s.key} type="monotone" dataKey={s.key} stroke={colour(s.key, i)} strokeWidth={s.key === 'you' ? 3 : 1.75} dot={false} isAnimationActive={false} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export function VelocityBadges({ data }: { data: VelocityResponse }) {
  return (
    <ul className="flex flex-wrap gap-2">
      {data.series.map((s) => {
        const t = s.trend
        const label = s.key === 'you' ? 'You' : s.name
        if (t.status === 'warning') {
          return (
            <li key={s.key} className="rounded-full border border-neg/25 bg-negsoft px-2.5 py-1 text-[11px] font-semibold text-neg">
              ⚠ {label}: reviews down {Math.abs(t.change_pct ?? 0)}% (last 2 weeks vs previous 4)
            </li>
          )
        }
        return (
          <li key={s.key} className="rounded-full border border-line bg-paper px-2.5 py-1 text-[11px] text-ink/55" title={s.dates_note}>
            {label}: {t.status !== 'ok' ? 'not enough data for a trend' : (t.change_pct ?? 0) >= 15 ? `rising (+${t.change_pct}%)` : `steady (${(t.change_pct ?? 0) > 0 ? '+' : ''}${t.change_pct}%)`} · n={s.sample_size}
          </li>
        )
      })}
    </ul>
  )
}

export default function VelocitySection({ id }: { id: string }) {
  const q = useQuery({ queryKey: ['extras', 'velocity', id], queryFn: () => extrasApi.velocity(id) })
  return (
    <Panel title="Review velocity · last 12 weeks" action={<SampleBadge source={q.data?.source} />}>
      {q.isLoading && <p className="px-5 pb-5 text-sm text-ink/45">Loading…</p>}
      {q.isError && <ErrorNote>Could not load velocity: {(q.error as Error).message}</ErrorNote>}
      {q.data && (
        <div className="space-y-3 px-5 pb-5">
          <VelocityBadges data={q.data} />
          <VelocityView data={q.data} />
          <p className="text-[11px] text-ink/40">{q.data.note}</p>
        </div>
      )}
    </Panel>
  )
}
