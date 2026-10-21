// In-memory mock API — prototype data only, not connected to any backend.
import type { Api, Draft, DraftStatus, Review, SyncEvent, Theme, TinyFishCall, Tone } from '../types'

const wait = <T,>(v: T, ms = 250) => new Promise<T>((r) => setTimeout(() => r(v), ms))
const now = () => new Date().toISOString()
const OUTLET = { id: 'demo-restaurant', name: "Sharma's Kitchen", category: 'restaurant' as const, city: 'Delhi', address: 'Lajpat Nagar II, New Delhi' }

const mk = (id: string, platform: Review['platform'], rating: number, author: string, text: string, sentiment: Review['sentiment'],
  theme_ids: string[], language: Review['language'] = 'en', has_owner_reply = false): Review => ({
  id, platform, rating, author, text, sentiment, theme_ids, language, has_owner_reply,
  posted_at: `2026-10-${String(18 - Number(id.slice(1))).padStart(2, '0')}`, url: `https://example.com/review/${id}`,
})

let reviews: Review[] = [
  mk('r1', 'google', 1, 'Ankit M.', 'Waited 50 minutes for butter chicken and it came cold. Staff just shrugged when we asked.', 'negative', ['slow', 'staff']),
  mk('r2', 'zomato', 2, 'Priya S.', 'Khana theek tha par service bahut slow hai, 45 min lag gaye order aane me.', 'negative', ['slow'], 'hinglish'),
  mk('r3', 'google', 5, 'Rohit K.', 'Great paneer tikka and quick seating on a Sunday.', 'positive', []),
  mk('r4', 'zomato', 1, 'Neha G.', 'Bill me extra service charge add kar diya bina bataye. Not okay.', 'negative', ['billing'], 'hinglish'),
  mk('r5', 'google', 4, 'Vikram T.', 'Good food, a bit loud inside.', 'positive', []),
  mk('r6', 'google', 2, 'Sana A.', 'Washroom was dirty and the waiter was rude when we mentioned it.', 'negative', ['hygiene', 'staff'], 'en', true),
  mk('r7', 'zomato', 5, 'Deepak R.', 'Best dal makhani in Lajpat Nagar!', 'positive', []),
  mk('r8', 'google', 3, 'Meera P.', 'Average. Nothing special but fine for a quick lunch.', 'neutral', []),
]
const replies: Record<string, string> = {
  r1: "Hi Ankit, a cold dish after a 50 minute wait is not the experience we want. We have shared this with our floor team. Please call us on 98xxxxxx10 so we can make your next visit right.",
  r2: "Priya ji, 45 minute ka wait kaafi lamba hai, humein iska afsos hai. Hum kitchen aur floor staff ke saath ise sudhar rahe hain. Aap humein 98xxxxxx10 par call kar sakti hain.",
  r4: "Hi Neha, thank you for flagging the service charge. It should always be shown clearly before billing. Please call us on 98xxxxxx10 with your bill details and our manager will look into it.",
  r6: "Hi Sana, thank you for telling us about the washroom and how the waiter responded. We are reviewing both with the team. We would value a call on 98xxxxxx10 to hear more.",
}
let drafts: Draft[] = Object.entries(replies).map(([rid, text]) => ({ id: 'd' + rid, review_id: rid, text, status: 'draft', guardrail_flags: [] }))

const themes: Theme[] = [
  { id: 'slow', label: 'Slow service', count: 2, pct: 50, quotes: ['Waited 50 minutes for butter chicken', 'service bahut slow hai, 45 min lag gaye'] },
  { id: 'staff', label: 'Staff behaviour', count: 2, pct: 50, quotes: ['Staff just shrugged when we asked', 'the waiter was rude when we mentioned it'] },
  { id: 'billing', label: 'Billing surprises', count: 1, pct: 25, quotes: ['extra service charge add kar diya bina bataye'] },
  { id: 'hygiene', label: 'Washroom hygiene', count: 1, pct: 25, quotes: ['Washroom was dirty'] },
]
const calls: TinyFishCall[] = [
  { id: 'c1', endpoint: 'search', input: "Sharma's Kitchen Delhi reviews", status: 'ok', duration_ms: 1200, items_returned: 6, cached: false, created_at: now() },
  { id: 'c2', endpoint: 'fetch', input: 'zomato.com/.../sharmas-kitchen/reviews', status: 'ok', duration_ms: 2400, items_returned: 38, cached: false, created_at: now() },
  { id: 'c3', endpoint: 'agent', input: 'Google Maps: scroll and expand reviews', status: 'ok', duration_ms: 81000, items_returned: 50, cached: false, steps_used: 22, created_at: now() },
]
let tone: Tone = { style: 'warm', sample_replies: '', do_not_say: 'refund, our fault, guarantee' }

const ALLOWED: Record<DraftStatus, DraftStatus[]> = {
  draft: ['edited', 'approved', 'rejected'], edited: ['edited', 'approved', 'rejected'],
  approved: ['posted', 'rejected'], rejected: ['draft'], posted: [],
}
const withDraft = (r: Review): Review => ({ ...r, draft: drafts.find((d) => d.review_id === r.id) })

export const mockApi: Api = {
  searchOutlets: (name, city) => wait([
    { id: 'c-1', name, address: `Main Market, ${city}`, source: 'Google Maps' },
    { id: 'c-2', name: `${name} (Branch 2)`, address: `Sector 14, ${city}`, source: 'Zomato' },
    { id: 'c-3', name: `${name} Express`, address: `Metro Station Road, ${city}`, source: 'Google Maps' },
  ], 600),
  createOutlet: (c, city, category) => wait({ ...OUTLET, name: c.name, address: c.address, city, category }),
  demoOutlet: () => wait(OUTLET),
  outlet: () => wait(OUTLET, 100),
  startSync: () => wait(undefined, 100),
  streamSync: (_id, on) => {
    const t = now()
    const ev: SyncEvent[] = [
      { type: 'stage', message: 'Looking for review pages', ts: t },
      { type: 'tinyfish_call', message: 'Search: found 6 candidate pages', ts: t },
      { type: 'source_status', source: 'zomato', status: 'success', message: 'Fetch: Zomato OK, 38 reviews', ts: t },
      { type: 'tinyfish_call', message: 'Agent: Google Maps scrolling, 50 reviews', ts: t },
      { type: 'source_status', source: 'google', status: 'success', message: 'Google Maps done, 50 reviews', ts: t },
      { type: 'stage', message: 'Finding themes and drafting replies', ts: t },
      { type: 'done', message: 'Dashboard ready', ts: t },
    ]
    let i = 0
    const id = setInterval(() => { on({ ...ev[i], ts: now() }); if (++i >= ev.length) clearInterval(id) }, 800)
    return () => clearInterval(id)
  },
  reviews: (_id, f) => wait(reviews.filter((r) =>
    (!f.platform || r.platform === f.platform) && (!f.sentiment || r.sentiment === f.sentiment) &&
    (!f.rating || r.rating === f.rating) && (!f.theme || r.theme_ids.includes(f.theme))).map(withDraft)),
  themes: () => wait(themes),
  fixes: () => wait([
    { rank: 1, title: 'Cut wait time at peak hours', rationale: 'Two reviews on two platforms mention 45 to 50 minute waits.', evidence_count: 2 },
    { rank: 2, title: 'Brief staff on handling complaints', rationale: 'Staff shrugging or being rude shows up in 2 of 4 negative reviews.', evidence_count: 2 },
    { rank: 3, title: 'Show service charge on the menu', rationale: 'A surprise charge turned a visit into a 1-star review.', evidence_count: 1 },
  ]),
  summary: () => {
    const neg = reviews.filter((r) => r.sentiment === 'negative')
    return wait({
      avg_rating: Math.round((reviews.reduce((s, r) => s + r.rating, 0) / reviews.length) * 10) / 10,
      total_reviews: reviews.length, pct_negative: Math.round((neg.length / reviews.length) * 100),
      unanswered_negatives: neg.filter((r) => !r.has_owner_reply).length,
    })
  },
  log: () => wait(calls, 150),
  draftFor: (rid, instruction) => {
    const d = drafts.find((x) => x.review_id === rid)!
    const text = instruction?.toLowerCase().includes('short') ? d.text.split('. ').slice(0, 2).join('. ').replace(/\.?$/, '.')
      : instruction?.toLowerCase().includes('callback') ? d.text + ' We will also call you back within a day.' : d.text
    Object.assign(d, { text, status: 'draft' })
    return wait({ ...d })
  },
  patchDraft: (id, b) => {
    const d = drafts.find((x) => x.id === id)
    if (!d) return Promise.reject(new Error('Draft not found'))
    const next: DraftStatus = b.status ?? (b.text !== undefined ? 'edited' : d.status)
    if (next !== d.status && !ALLOWED[d.status].includes(next)) return Promise.reject(new Error(`Cannot move a ${d.status} draft to ${next}`))
    drafts = drafts.map((x) => (x.id === id ? { ...x, text: b.text ?? x.text, status: next } : x))
    return wait(drafts.find((x) => x.id === id)!, 150)
  },
  getTone: () => wait(tone, 100),
  putTone: (t) => { tone = t; return wait(tone, 200) },
}
