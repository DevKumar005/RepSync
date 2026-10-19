import type { Api,Candidate, Draft, Outlet, Review, ReviewFilters } from '../types'
import { mockApi } from './mock'

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== 'false'
const BASE: string = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(BASE + path, { headers: { 'Content-Type': 'application/json' }, ...init })
  if (!r.ok) throw new Error((await r.text()) || r.statusText)
  return r.json() as Promise<T>
}
const send = <T,>(method: string, path: string, body?: unknown) =>
  req<T>(path, { method, body: body === undefined ? undefined : JSON.stringify(body) })
const qs = (f: ReviewFilters) => {
  const p = new URLSearchParams()
  Object.entries(f).forEach(([k, v]) => v !== undefined && v !== '' && p.set(k, String(v)))
  const s = p.toString()
  return s ? `?${s}` : ''
}

// ---- adapters: backend field names -> frontend types (check against /docs and adjust if a field differs) ----
const low = (v: unknown) => String(v ?? '').toLowerCase()
const normOutlet = (o: any): Outlet => ({
  id: String(o.id ?? o.outlet_id), name: o.name ?? o.outlet_name ?? 'Your outlet',
  category: o.category ?? 'restaurant', city: o.city ?? '', address: o.address ?? '',
})
const cacheOutlet = (o: Outlet) => { try { sessionStorage.setItem('outlet:' + o.id, JSON.stringify(o)) } catch { /* ignore */ } return o }
const normDraft = (d: any): Draft => ({ id: String(d.id ?? d.draft_id), review_id: String(d.review_id), text: d.text ?? '', status: low(d.status || 'draft') as Draft['status'], guardrail_flags: d.guardrail_flags ?? [] })
const nestedDraft = (r: any): Draft | undefined => {
  const hit = r.draft ?? r.drafts ?? r.reply_draft ?? r.draft_reply ?? Object.entries(r).find(([k, v]) => /draft/i.test(k) && v && typeof v === 'object')?.[1]
  const d: any = Array.isArray(hit) ? hit[0] : hit
  return d ? normDraft({ review_id: r.id, ...d }) : undefined
}
const normReview = (r: any): Review => ({
  id: String(r.id), platform: low(r.platform) as Review['platform'], author: r.author ?? 'Anonymous', rating: Number(r.rating ?? 0),
  text: r.text ?? '', language: r.language ?? 'en', posted_at: String(r.posted_at ?? '').slice(0, 10), url: r.url ?? '#',
  sentiment: low(r.sentiment) as Review['sentiment'], has_owner_reply: Boolean(r.has_owner_reply), theme_ids: r.theme_ids ?? [],
  draft: nestedDraft(r),
})

const pick = (o: any, ...keys: string[]) => { for (const k of keys) if (o?.[k] !== undefined && o?.[k] !== null) return o[k]; return undefined }
const list = (x: any, ...keys: string[]): any[] => (Array.isArray(x) ? x : pick(x, ...keys, 'items', 'data', 'results') ?? [])
const normSummary = (raw: any) => {
  const s = raw?.summary ?? raw
  const total = Number(pick(s, 'total_reviews', 'review_count', 'total', 'count') ?? 0)
  const negCount = pick(s, 'negative_count', 'negative_reviews', 'negatives')
  const pctNeg = pick(s, 'pct_negative', 'negative_percentage', 'negative_pct', 'percent_negative', 'negative_percent')
  return {
    avg_rating: Number(pick(s, 'avg_rating', 'average_rating', 'avg', 'rating_avg', 'average', 'rating') ?? 0),
    total_reviews: total,
    pct_negative: Math.round(Number(pctNeg ?? (negCount !== undefined && total ? (Number(negCount) / total) * 100 : 0))),
    unanswered_negatives: Number(pick(s, 'unanswered_negatives', 'unanswered_negative_count', 'unanswered', 'unreplied_negatives') ?? 0),
  }
}
const normTheme = (t: any, i: number) => ({
  id: String(pick(t, 'id', 'theme_id', 'label', 'name') ?? i), label: String(pick(t, 'label', 'name', 'title') ?? 'Theme'),
  count: Number(pick(t, 'count', 'review_count', 'frequency', 'member_count') ?? 0), pct: Number(pick(t, 'pct', 'percentage') ?? 0),
  quotes: (pick(t, 'quotes', 'representative_quotes', 'examples') ?? []).map((q: any) => (typeof q === 'string' ? q : String(q?.text ?? q?.quote ?? ''))),
})
const normFix = (f: any, i: number) => ({
  rank: Number(pick(f, 'rank') ?? i + 1), title: String(pick(f, 'title', 'name') ?? 'Fix'),
  rationale: String(pick(f, 'rationale', 'description', 'reason') ?? ''), evidence_count: Number(pick(f, 'evidence_count', 'count') ?? 0),
})
const asText = (v: unknown): string =>
  typeof v === 'string' ? v : v && typeof v === 'object' ? String(pick(v, 'query', 'url', 'goal', 'text') ?? JSON.stringify(v)) : String(v ?? '')
const normCall = (c: any, i: number) => {
  const st = low(c.status)
  return {
    id: String(c.id ?? i), endpoint: low(pick(c, 'endpoint', 'type', 'tool')) as 'search' | 'fetch' | 'agent', input: asText(pick(c, 'input', 'query', 'url', 'goal')),
    status: (st === 'success' ? 'ok' : st === 'failed' || st === 'error' ? 'failed' : st === 'partial' ? 'partial' : 'ok') as 'ok' | 'partial' | 'failed',
    duration_ms: Number(c.duration_ms ?? 0), items_returned: Number(c.items_returned ?? 0), cached: Boolean(c.cached),
    steps_used: c.steps_used ?? undefined, created_at: String(c.created_at ?? ''),
  }
}
const normCandidate = (c: any, i: number): Candidate => ({
  ...c, id: String(pick(c, 'id', 'place_id', 'candidate_id', 'url') ?? i), name: String(pick(c, 'name', 'title') ?? 'Unnamed business'),
  address: String(pick(c, 'address', 'location', 'snippet') ?? ''), source: String(pick(c, 'source', 'platform', 'domain') ?? ''),
})
const realApi: Api = {
 searchOutlets: async (name, city, category) => list(await send('POST', '/api/outlets/search', { name, city, category }), 'candidates').map(normCandidate),
  createOutlet: async (c, city, category) => cacheOutlet(normOutlet(await send('POST', '/api/outlets', { ...c, name: c.name, address: c.address, city, category }))),
  demoOutlet: async (key) => cacheOutlet(normOutlet(await send('POST', `/api/outlets/demo/${key}`))),
  outlet: async (id) => {
    try { return normOutlet(await send('GET', `/api/outlets/${id}`)) } catch {
      const saved = sessionStorage.getItem('outlet:' + id)
      return saved ? (JSON.parse(saved) as Outlet) : normOutlet({ id })
    }
  },
  startSync: (id) => send('POST', `/api/outlets/${id}/sync`),
  streamSync: (id, on, onError) => {
    const es = new EventSource(`${BASE}/api/outlets/${id}/sync/stream`)
    es.onmessage = (m) => on(JSON.parse(m.data))
    es.onerror = () => { es.close(); onError?.() }
    return () => es.close()
  },
  reviews: async (id, f) => {
    const rs = list(await send<any>('GET', `/api/outlets/${id}/reviews${qs(f)}`), 'reviews')
    return rs.map(normReview).filter((r) =>
      (!f.platform || r.platform === f.platform) && (!f.sentiment || r.sentiment === f.sentiment) && (!f.rating || r.rating === f.rating))
  },
  themes: async (id) => list(await send('GET', `/api/outlets/${id}/themes`), 'themes').map(normTheme),
  fixes: async (id) => list(await send('GET', `/api/outlets/${id}/fixes`), 'fixes').map(normFix),
  summary: async (id) => normSummary(await send('GET', `/api/outlets/${id}/summary`)),
  log: async (id) => list(await send('GET', `/api/outlets/${id}/tinyfish-log`), 'calls', 'logs').map(normCall),
  draftFor: async (rid, instruction) => normDraft({ review_id: rid, ...(await send<any>('POST', `/api/reviews/${rid}/draft`, { instruction })) }),
  patchDraft: async (id, b) => normDraft(await send<any>('PATCH', `/api/drafts/${id}`, b)),
  getTone: async () => {
    try { return await send('GET', '/api/tone') } catch {
      try { const t = localStorage.getItem('tone'); if (t) return JSON.parse(t) } catch { /* ignore */ }
      return { style: 'warm', sample_replies: '', do_not_say: '' }
    }
  },
  putTone: async (t) => {
    try { localStorage.setItem('tone', JSON.stringify(t)) } catch { /* ignore */ }
    await send('PUT', '/api/tone', t)
    return t
  },
}

export const api: Api = USE_MOCK ? mockApi : realApi
export const isMock = USE_MOCK