import type { ReactNode } from 'react'
import type { DataSource, GapStatus } from './types'

export function SampleBadge({ source, label = 'Sample data' }: { source?: DataSource; label?: string }) {
  if (source !== 'sample') return null
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full border border-warn/30 bg-warnsoft px-2.5 py-0.5 text-[11px] font-semibold text-warn"
      title="Simulated data for demonstration. Not collected live."
    >
      <span className="status-dot status-dot-warn" aria-hidden /> {label}
    </span>
  )
}

const STATUS_STYLE: Record<GapStatus, string> = {
  threat: 'bg-negsoft text-neg border-neg/25',
  opportunity: 'bg-possoft text-pos border-pos/25',
  parity: 'bg-paper text-ink/50 border-line',
}
const STATUS_LABEL: Record<GapStatus, string> = { threat: 'Threat · fix it', opportunity: 'Opportunity · advertise', parity: 'Parity' }

export function StatusChip({ status }: { status: GapStatus }) {
  return (
    <span className={`inline-block whitespace-nowrap rounded-full border px-2 py-0.5 text-[11px] font-semibold ${STATUS_STYLE[status]}`}>
      {STATUS_LABEL[status]}
    </span>
  )
}

export function Panel({ title, action, children }: { title: string; action?: ReactNode; children: ReactNode }) {
  return (
    <section className="panel">
      <div className="flex items-center justify-between gap-3 px-5 pt-5 pb-3">
        <h2 className="text-[13px] font-semibold uppercase tracking-wider text-ink/35">{title}</h2>
        {action}
      </div>
      {children}
    </section>
  )
}

export const ErrorNote = ({ children }: { children: ReactNode }) => (
  <p role="alert" className="px-5 pb-5 text-sm text-neg">{children}</p>
)

// System fonts first, then Devanagari-capable fallbacks so Hindi renders everywhere (incl. poster export)
export const FONT_STACK =
  'system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans", "Noto Sans Devanagari", "Kohinoor Devanagari", "Mangal", "Nirmala UI", sans-serif'
