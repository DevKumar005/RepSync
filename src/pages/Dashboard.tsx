import { useCallback, useEffect, useRef, useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'
import type { SyncEvent } from '../types'
import { ActivityLog, FixesPanel, ReplyQueue, ReviewFeed, SummaryBar, ThemePanel } from '../components/Panels'

export default function Dashboard() {
  const { id = '' } = useParams()
  const [sp] = useSearchParams()
  const qc = useQueryClient()
  const [live, setLive] = useState<SyncEvent[]>([])
  const [syncing, setSyncing] = useState(false)
  const [theme, setTheme] = useState<string>()
  const [err, setErr] = useState('')
  const [retryCount, setRetryCount] = useState(0)
  const close = useRef<() => void>()
  const outlet = useQuery({ queryKey: ['outlet', id], queryFn: () => api.outlet(id) })

  const sync = useCallback(async () => {
    setLive([]); setErr(''); setSyncing(true); setRetryCount(0)
    try {
      await api.startSync(id)
      close.current = api.streamSync(id, (e) => {
        setLive((l) => [...l, e])
        if (e.type === 'stage' || e.type === 'tinyfish_call') qc.invalidateQueries({ queryKey: ['log', id] })
        if (e.type === 'done') {
          if (e.status === 'failed') {
            setErr(e.message || 'Sync encountered an error. Showing saved results.')
          } else {
            setErr('')
          }
          setSyncing(false)
          close.current?.()
          qc.invalidateQueries()
        }
      }, () => {
        setSyncing(false)
        setErr('Lost connection to the sync. Showing the last saved results.')
        // Invalidate all queries to re-fetch whatever data made it through
        qc.invalidateQueries()
      })
    } catch (e) {
      setSyncing(false)
      setErr((e as Error).message)
    }
  }, [id, qc])

  const handleRetry = useCallback(() => {
    setRetryCount((c) => c + 1)
    sync()
  }, [sync])

  useEffect(() => { if (sp.get('sync')) sync(); return () => close.current?.() }, [id]) // eslint-disable-line

  return (
    <div className="space-y-5 fade-in">
      {/* Header */}
      <div className="flex flex-wrap items-end gap-3">
        <div className="mr-auto">
          <h1 className="text-2xl font-bold tracking-tight">
            {outlet.data?.name ?? (
              <span className="inline-flex items-center gap-2">
                <span className="skeleton h-7 w-48 inline-block" />
              </span>
            )}
          </h1>
          {outlet.data && (
            <p className="text-sm text-ink/50 mt-0.5 flex items-center gap-1.5">
              <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>
              {outlet.data.address} · {outlet.data.category}
            </p>
          )}
        </div>
        <button className="btn btn-primary" disabled={syncing} onClick={sync}>
          {syncing ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
              Syncing…
            </span>
          ) : (
            <span className="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
              Sync reviews
            </span>
          )}
        </button>
      </div>

      {/* Error banner */}
      {err && (
        <div role="alert" className="panel border-neg/40 bg-negsoft p-4 text-sm text-neg fade-in flex items-start gap-3">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="shrink-0 mt-0.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          <div className="flex-1">
            <p className="font-medium">{err}</p>
            {retryCount > 0 && (
              <p className="text-neg/70 mt-1 text-xs">Retry attempt {retryCount} — if this keeps happening, the backend might be down.</p>
            )}
          </div>
          <button className="btn btn-danger !py-1 !px-3 text-xs shrink-0" onClick={handleRetry}>
            Try again
          </button>
        </div>
      )}

      <SummaryBar id={id} />

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
        <div className="space-y-5">
          <FixesPanel id={id} />
          <ThemePanel id={id} selected={theme} onSelect={setTheme} />
          <ReviewFeed id={id} theme={theme} />
        </div>
        <div className="space-y-5">
          <ReplyQueue id={id} />
          <ActivityLog id={id} live={live} syncing={syncing} />
        </div>
      </div>
    </div>
  )
}
