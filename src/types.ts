export type Platform = 'google' | 'zomato' | 'practo' | 'justdial'
export type Sentiment = 'positive' | 'neutral' | 'negative'
export type Category = 'restaurant' | 'clinic' | 'salon'
export type DraftStatus = 'draft' | 'edited' | 'approved' | 'rejected' | 'posted'

export interface Candidate { id: string; name: string; address: string; source: string }
export interface Outlet { id: string; name: string; category: Category; city: string; address: string }
export interface Draft { id: string; review_id: string; text: string; status: DraftStatus; guardrail_flags: string[] }
export interface Review {
  id: string; platform: Platform; author: string; rating: number; text: string
  language: 'en' | 'hi' | 'hinglish'; posted_at: string; url: string
  sentiment: Sentiment; has_owner_reply: boolean; theme_ids: string[]
  draft?: Draft // contract ask: backend nests the draft inside the review
}
export interface Theme { id: string; label: string; count: number; pct: number; quotes: string[] }
export interface Fix { rank: number; title: string; rationale: string; evidence_count: number }
export interface Summary { avg_rating: number; total_reviews: number; pct_negative: number; unanswered_negatives: number }
export interface TinyFishCall {
  id: string; endpoint: 'search' | 'fetch' | 'agent'; input: string; status: 'ok' | 'partial' | 'failed'
  duration_ms: number; items_returned: number; cached: boolean; steps_used?: number; created_at: string
}
export interface Tone { style: 'warm' | 'formal' | 'apologetic' | 'concise'; sample_replies: string; do_not_say: string }
export interface SyncEvent { type: 'source_status' | 'tinyfish_call' | 'stage' | 'done'; source?: string; status?: string; message: string; ts: string }
export interface ReviewFilters { platform?: string; sentiment?: string; rating?: number; theme?: string }

export interface Api {
  searchOutlets(name: string, city: string, category: Category): Promise<Candidate[]>
  createOutlet(c: Candidate, city: string, category: Category): Promise<Outlet>
  demoOutlet(key: string): Promise<Outlet>
  outlet(id: string): Promise<Outlet>
  startSync(id: string): Promise<void>
  streamSync(id: string, on: (e: SyncEvent) => void, onError?: () => void): () => void
  reviews(id: string, f: ReviewFilters): Promise<Review[]>
  themes(id: string): Promise<Theme[]>
  fixes(id: string): Promise<Fix[]>
  summary(id: string): Promise<Summary>
  log(id: string): Promise<TinyFishCall[]>
  draftFor(reviewId: string, instruction?: string): Promise<Draft>
  patchDraft(id: string, b: { text?: string; status?: DraftStatus }): Promise<Draft>
  getTone(): Promise<Tone>
  putTone(t: Tone): Promise<Tone>
}
