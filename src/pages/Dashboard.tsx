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
  const close = useRef<() => void>()
  const outlet = useQuery({ queryKey: ['outlet', id], queryFn: () => api.outlet(id) })

  const sync = useCallback(async () => {
    setLive([]); setErr(''); setSyncing(true)
    try {
      await api.startSync(id)
      close.current = api.streamSync(id, (e) => {
        setLive((l) => [...l, e])
        if (e.type === 'stage' || e.type === 'tinyfish_call') qc.invalidateQueries({ queryKey: ['log', id] })
        if (e.type === 'done') { setErr(''); setSyncing(false); close.current?.(); qc.invalidateQueries() }
      }, () => { setSyncing(false); setErr('Lost connection to the sync. Showing the last saved results.') })
    } catch (e) { setSyncing(false); setErr((e as Error).message) }
  }, [id, qc])

  useEffect(() => { if (sp.get('sync')) sync(); return () => close.current?.() }, [id]) // eslint-disable-line

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-3">
        <div className="mr-auto"><h1 className="text-2xl font-bold">{outlet.data?.name ?? 'Loading outlet…'}</h1>
          <p className="text-sm text-ink/60">{outlet.data && `${outlet.data.address} · ${outlet.data.category}`}</p></div>
        <button className="btn btn-primary" disabled={syncing} onClick={sync}>{syncing ? 'Syncing…' : 'Sync reviews'}</button>
      </div>
      {err && <p role="alert" className="panel border-neg/40 bg-negsoft p-3 text-sm text-neg">{err} <button className="underline" onClick={sync}>Try again</button></p>}
      <SummaryBar id={id} />
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
        <div className="space-y-4"><FixesPanel id={id} /><ThemePanel id={id} selected={theme} onSelect={setTheme} /><ReviewFeed id={id} theme={theme} /></div>
        <div className="space-y-4"><ReplyQueue id={id} /><ActivityLog id={id} live={live} syncing={syncing} /></div>
      </div>
    </div>
  )
}
