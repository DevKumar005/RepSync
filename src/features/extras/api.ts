import { api, isMock } from '../../api/client'
import type { SyncEvent } from '../../types'
import { MOCK_COMPETITORS } from './mockData'
import type { CandidatesResponse, CompetitorResult } from './types'

// Same base URL rule as src/api/client.ts
const BASE: string = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function call<T>(method: string, path: string, body?: unknown): Promise<T> {
  const r = await fetch(BASE + path, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (!r.ok) {
    let msg = r.statusText
    try { const j = await r.json(); msg = typeof j.error === 'string' ? j.error : JSON.stringify(j.detail ?? j) } catch { }
    throw new Error(msg || `Request failed (${r.status})`)
  }
  return r.json() as Promise<T>
}

const wait = <T,>(v: T, ms = 300) => new Promise<T>((res) => setTimeout(() => res(v), ms))

// ---- offline mock mode: replays committed sample data ----
let mockScanStartedAt: number | null = null
const MOCK_SCAN_MS = 2600
const mockStages = [
  '[Sample] Loading saved reviews for Tandoor Junction (sample)…',
  '[Sample] Tandoor Junction (sample): 24 sample reviews (no live TinyFish call)',
  '[Sample] Loading saved reviews for Masala Lane (sample)…',
  '[Sample] Masala Lane (sample): 22 sample reviews (no live TinyFish call)',
  '[Sample] Loading saved reviews for Hari Bhari Rasoi (sample)…',
  '[Sample] Hari Bhari Rasoi (sample): 20 sample reviews (no live TinyFish call)',
  'Competitor scan: analysing complaints and computing gaps…',
  'Competitor scan complete',
]

export const extrasApi = {
  competitors: (id: string): Promise<CompetitorResult> => {
    if (!isMock) return call('GET', `/api/outlets/${id}/competitors`)
    if (mockScanStartedAt === null) return wait({ status: 'none', live: false, sample_available: true })
    if (Date.now() - mockScanStartedAt < MOCK_SCAN_MS) return wait({ status: 'running' })
    return wait({ ...MOCK_COMPETITORS, generated_at: new Date(mockScanStartedAt + MOCK_SCAN_MS).toISOString() })
  },
  candidates: (id: string): Promise<CandidatesResponse> =>
    isMock
      ? wait({ source: 'sample', candidates: (MOCK_COMPETITORS.outlets ?? []).slice(1).map((o) => ({ name: o.name, url: null, area: null })) })
      : call('GET', `/api/outlets/${id}/competitors/candidates`),
  scan: (id: string, picks: { name: string; url?: string | null }[]): Promise<{ status: string }> => {
    if (!isMock) return call('POST', `/api/outlets/${id}/competitors/scan`, { competitors: picks })
    mockScanStartedAt = Date.now()
    return wait({ status: 'started' })
  },
  /** Live scan progress: filters the existing outlet SSE stream to competitor events. */
  streamScan: (id: string, on: (e: SyncEvent) => void): (() => void) => {
    if (!isMock) return api.streamSync(id, (e) => { if (e.source === 'competitors') on(e) })
    const timers = mockStages.map((message, i) =>
      setTimeout(() => on({ type: i % 2 && i < 6 ? 'tinyfish_call' : 'stage', source: 'competitors', message, ts: new Date().toISOString() }), (i + 1) * 300))
    return () => timers.forEach(clearTimeout)
  },
  call,
}
