import { api, isMock } from '../../api/client'
import type { SyncEvent } from '../../types'
import { MOCK_COMPETITORS, MOCK_VELOCITY_SERIES } from './mockData'
import type { AskResponse, CandidatesResponse, CompetitorResult, VelocityResponse } from './types'

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

const mockScanDone = () => mockScanStartedAt !== null && Date.now() - mockScanStartedAt >= MOCK_SCAN_MS
const weekLabels = (weeks = 12) =>
  Array.from({ length: weeks }, (_, i) => new Date(Date.now() - 7 * (weeks - i) * 86400000).toISOString().slice(0, 10))

/** Offline mock answers: same rule shapes as the backend fallback, numbers from mock data only. */
async function mockAsk(id: string, question: string): Promise<AskResponse> {
  const q = question.toLowerCase()
  const s = await api.summary(id)
  const themes = await api.themes(id)
  const top = [...themes].sort((a, b) => b.count - a.count)[0]
  const hinglish = /\b(kya|kyu|kyun|mera|meri|kaise|hai|gira)\b/.test(q)
  const rating = `Your average rating is ${s.avg_rating} from ${s.total_reviews} collected reviews, and ${s.pct_negative}% are negative.`
  if (/rank|position|रैंक/.test(q)) {
    return {
      answer: hinglish
        ? `RepSync search rank ya map position track nahi karta, isliye rank kyun badla yeh main nahi bata sakta. Aapki average rating ${s.avg_rating} hai (${s.total_reviews} reviews), aur ${s.pct_negative}% negative hain.${top ? ` Sabse badi shikayat "${top.label}" hai.` : ''}`
        : `RepSync does not track search rank or map position, so I can't say why your rank changed. ${rating}${top ? ` The biggest complaint theme is "${top.label}".` : ''}`,
      sources: ['summary', 'velocity', 'themes'], chart: 'velocity', grounded: true,
    }
  }
  if (/competit|compare|gap|\bvs\b/.test(q)) {
    if (!mockScanDone()) return { answer: 'There is no competitor scan yet. Open the Competitors tab and run a scan, then ask again.', sources: [], chart: null, grounded: true }
    return { answer: MOCK_COMPETITORS.advice?.[0]?.text ?? 'You are at parity with these competitors.', sources: ['competitor_gaps'], chart: 'gap', grounded: true }
  }
  if (/fix|complain|problem|improve|shikayat/.test(q) && top) {
    return { answer: `The biggest complaint theme is "${top.label}" (${top.count} reviews).`, sources: ['themes'], chart: 'themes', grounded: true }
  }
  return { answer: rating, sources: ['summary'], chart: null, grounded: true }
}

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
  velocity: (id: string): Promise<VelocityResponse> =>
    isMock
      ? wait({
          weeks: weekLabels(),
          series: mockScanDone() ? MOCK_VELOCITY_SERIES : MOCK_VELOCITY_SERIES.slice(0, 1),
          source: 'sample',
          note: 'Counts come from the reviews RepSync collected (up to 50 per platform), not the total number of reviews. Relative dates like "one month ago" are approximate.',
        })
      : call('GET', `/api/outlets/${id}/velocity`),
  ask: (id: string, question: string): Promise<AskResponse> =>
    isMock ? wait(null, 500).then(() => mockAsk(id, question)) : call('POST', `/api/outlets/${id}/ask`, { question }),
  call,
}
