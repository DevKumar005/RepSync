export type DataSource = 'live' | 'sample'
export type GapStatus = 'threat' | 'opportunity' | 'parity'

export interface GapCell { key: string; name: string; count: number; n: number; rate: number | null }
export interface GapRow {
  theme: string; total_mentions: number; cells: GapCell[]; status: GapStatus
  gap_pp: number; versus_key: string | null; versus_name: string | null
}
export interface CompetitorOutlet { key: string; name: string; n: number; url: string | null; low_sample?: boolean }
export interface Advice { theme: string; status: GapStatus; text: string }
export interface CompetitorResult {
  status: 'done' | 'running' | 'none' | 'failed'
  source?: DataSource
  generated_at?: string | null
  collected_at?: string | null
  outlets?: CompetitorOutlet[]
  matrix?: GapRow[]
  advice?: Advice[]
  quotes?: Record<string, { outlet_key: string; text: string }[]>
  error?: string
  live?: boolean
  sample_available?: boolean
}
export interface CompetitorCandidate { name: string; url: string | null; area: string | null }
export interface CandidatesResponse { source: DataSource; candidates: CompetitorCandidate[]; message?: string }

export interface Trend { status: 'ok' | 'warning' | 'insufficient_data'; recent_avg: number; prior_avg: number; change_pct: number | null }
export interface VelocitySeries { key: string; name: string; counts: number[]; sample_size: number; trend: Trend; dates_note?: string }
export interface VelocityResponse { weeks: string[]; series: VelocitySeries[]; source: DataSource; note: string }

export type ChartKind = 'themes' | 'velocity' | 'gap'
export interface AskResponse { answer: string; sources: string[]; chart: ChartKind | null; grounded: boolean }

export interface CityOutlet {
  id: string; name: string; lat: number; lng: number; address?: string; distance_m?: number
  /** Average stars of the reviews RepSync analysed; null when the place has not been scanned */
  rating: number | null
  /** Only known for sample data until rating history is collected */
  rating_change_60d: number | null
  reviews_per_week: number | null
  reviews_analysed?: number | null
  is_you?: boolean
  scanned?: boolean
}
export interface CityMap {
  source: DataSource; status: 'ok' | 'locating' | 'no_location'; locality: string; city: string; note: string
  center: { lat: number; lng: number } | null; radius_m: number
  places_status?: 'ok' | 'loading' | 'unavailable'
  outlets: CityOutlet[]
}
