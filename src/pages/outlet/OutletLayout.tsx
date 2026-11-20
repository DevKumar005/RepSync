import { lazy, Suspense, useCallback, useEffect, useRef, useState } from 'react'
import { NavLink, Outlet, useOutletContext, useParams, useSearchParams } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../api/client'
import type { SyncEvent } from '../../types'
import { extrasEnabled } from '../../features/extras/flags'

const ChatWidget = lazy(() => import('../../features/extras/ChatWidget'))

export interface OutletCtx { id: string; live: SyncEvent[]; syncing: boolean; sync: () => void; openChat: (question?: string) => void }
export const useOutlet = () => useOutletContext<OutletCtx>()

const TABS: { to: string; label: string; extra?: boolean }[] = [
  { to: '', label: 'Overview' },
  { to: 'reviews', label: 'Reviews' },
  { to: 'replies', label: 'Replies' },
  { to: 'insights', label: 'Insights' },
  { to: 'competitors', label: 'Competitors', extra: true },
  { to: 'velocity', label: 'Velocity', extra: true },
  { to: 'posters', label: 'Posters', extra: true },
  { to: 'map', label: 'City map', extra: true },
  { to: 'activity', label: 'Activity' },
]

const tab = ({ isActive }: { isActive: boolean }) =>
  `shrink-0 whitespace-nowrap rounded-full px-3.5 py-1.5 text-[13px] transition-colors duration-200 ${
    isActive ? 'pill-active font-medium' : 'pill-idle'
  }`

export default function OutletLayout() {
  const { id = '' } = useParams()
  const [sp] = useSearchParams()
  const qc = useQueryClient()
  const [live, setLive] = useState<SyncEvent[]>([])
  const [syncing, setSyncing] = useState(false)
  const [err, setErr] = useState('')
  const close = useRef<() => void>()
  const outlet = useQuery({ queryKey: ['outlet', id], queryFn: () => api.outlet(id) })
  const [chatOpen, setChatOpen] = useState(false)
  const [chatSeed, setChatSeed] = useState<string | null>(null)
  const openChat = useCallback((question?: string) => { if (question) setChatSeed(question); setChatOpen(true) }, [])

  const sync = useCallback(async () => {
    setLive([]); setErr(''); setSyncing(true)
    try {
      await api.startSync(id)
      close.current = api.streamSync(id, (e) => {
        if (e.source === 'competitors') return // competitor scans report on their own page
        setLive((l) => [...l, e])
        if (e.type === 'stage' || e.type === 'tinyfish_call') qc.invalidateQueries({ queryKey: ['log', id] })
        if (e.type === 'done') {
          setErr(e.status === 'failed' ? e.message || 'Sync encountered an error. Showing saved results.' : '')
          setSyncing(false)
          close.current?.()
          qc.invalidateQueries()
        }
      }, () => {
        setSyncing(false)
        setErr('Lost connection to the sync. Showing the last saved results.')
        qc.invalidateQueries()
      })
    } catch (e) {
      setSyncing(false)
      setErr((e as Error).message)
    }
  }, [id, qc])

  useEffect(() => { if (sp.get('sync')) sync(); return () => close.current?.() }, [id]) // eslint-disable-line react-hooks/exhaustive-deps

  const o = outlet.data
  return (
    <div className="rs-container space-y-6 pb-20 pt-8">
      <header className="flex flex-wrap items-end gap-4 fade-in">
        <div className="mr-auto min-w-0 space-y-1.5">
          <p className="label-overline">{o ? `${o.category} · ${o.city}` : 'Outlet'}</p>
          <h1 className="rs-title text-[clamp(26px,3.2vw,40px)]">{o?.name ?? <span className="skeleton inline-block h-9 w-64 align-middle" />}</h1>
          {o?.address && <p className="rs-copy text-sm">{o.address}</p>}
        </div>
        <button className="btn btn-primary !px-5 !py-2.5" disabled={syncing} onClick={sync}>
          {syncing ? <><span className="status-dot bg-white" /> Syncing…</> : 'Sync reviews'}
        </button>
      </header>

      {err && (
        <div role="alert" className="panel flex items-start gap-3 !border-neg/30 p-4 text-sm text-neg">
          <p className="flex-1 font-medium">{err}</p>
          <button className="btn btn-danger !px-3 !py-1 !text-xs" onClick={sync}>Try again</button>
        </div>
      )}

      <nav aria-label="Outlet tools" className="panel flex gap-1 overflow-x-auto !rounded-full p-1.5">
        {TABS.filter((t) => !t.extra || extrasEnabled).map((t) => (
          <NavLink key={t.label} end={t.to === ''} to={t.to ? `/outlet/${id}/${t.to}` : `/outlet/${id}`} className={tab}>{t.label}</NavLink>
        ))}
      </nav>

      <Outlet context={{ id, live, syncing, sync, openChat } satisfies OutletCtx} />

      {extrasEnabled && (
        <Suspense fallback={null}>
          <ChatWidget id={id} open={chatOpen} onOpenChange={setChatOpen} seed={chatSeed} onSeedUsed={() => setChatSeed(null)} />
        </Suspense>
      )}
    </div>
  )
}
