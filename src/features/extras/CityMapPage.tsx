import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { LngLatBounds, Map as MapLibre, Marker, NavigationControl, setWorkerUrl } from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
import 'maplibre-gl/dist/maplibre-gl.css'
import type { CityMap, CityOutlet } from './types'
import { useCityMap } from './useCityMap'
import { SectionHead } from '../../components/Page'
import { useMode } from '../../theme'
import { ErrorNote, Panel, SampleBadge } from './ui'

setWorkerUrl(workerUrl)

// OpenFreeMap: free OpenStreetMap vector tiles, no key
const STYLE = { light: 'https://tiles.openfreemap.org/styles/positron', dark: 'https://tiles.openfreemap.org/styles/dark' }

type PinKind = 'you' | 'rising' | 'falling' | 'flat' | 'scanned' | 'unscanned'
const kindOf = (o: CityOutlet): PinKind => {
  if (o.is_you) return 'you'
  if (o.rating_change_60d !== null) return o.rating_change_60d > 0.05 ? 'rising' : o.rating_change_60d < -0.05 ? 'falling' : 'flat'
  return o.scanned ? 'scanned' : 'unscanned'
}

/** Polygon approximating a circle of radius_m around the centre, for the search-radius ring. */
function ring(c: { lat: number; lng: number }, radiusM: number) {
  const dLat = radiusM / 111320
  const dLng = dLat / Math.cos((c.lat * Math.PI) / 180)
  const coords = Array.from({ length: 65 }, (_, i) => {
    const a = (i / 64) * 2 * Math.PI
    return [c.lng + dLng * Math.cos(a), c.lat + dLat * Math.sin(a)]
  })
  return { type: 'Feature' as const, properties: {}, geometry: { type: 'Polygon' as const, coordinates: [coords] } }
}

function addRing(map: MapLibre, data: CityMap) {
  if (!data.center || map.getSource('radius')) return
  // Theme tokens are "r g b" triplets; read after the theme class flips, since setStyle reloads the ring
  const brand = `rgb(${getComputedStyle(document.documentElement).getPropertyValue('--brand').trim().split(/\s+/).join(',')})`
  map.addSource('radius', { type: 'geojson', data: ring(data.center, data.radius_m) })
  map.addLayer({ id: 'radius-fill', type: 'fill', source: 'radius', paint: { 'fill-color': brand, 'fill-opacity': 0.06 } })
  map.addLayer({ id: 'radius-line', type: 'line', source: 'radius', paint: { 'line-color': brand, 'line-opacity': 0.5, 'line-width': 1.5, 'line-dasharray': [2, 2] } })
}

function OutletMap({ data, selected, onSelect }: { data: CityMap; selected: string | null; onSelect: (id: string) => void }) {
  const box = useRef<HTMLDivElement>(null)
  const map = useRef<MapLibre | null>(null)
  const mode = useMode()
  const pins = useRef(new Map<string, Marker>())
  const styleMode = useRef(mode)
  const dataRef = useRef(data)
  dataRef.current = data

  useEffect(() => {
    if (!box.current || !data.center) return
    const dLat = data.radius_m / 111320
    const dLng = dLat / Math.cos((data.center.lat * Math.PI) / 180)
    const m = new MapLibre({
      container: box.current,
      style: STYLE[styleMode.current],
      bounds: new LngLatBounds([data.center.lng - dLng, data.center.lat - dLat], [data.center.lng + dLng, data.center.lat + dLat]),
      fitBoundsOptions: { padding: 24 },
      attributionControl: { compact: true },
      dragRotate: false,
      pitchWithRotate: false,
    })
    m.touchZoomRotate.disableRotation()
    m.addControl(new NavigationControl({ showCompass: false }), 'top-right')
    m.on('style.load', () => addRing(m, dataRef.current))
    map.current = m
    return () => { m.remove(); map.current = null; pins.current.clear() }
  }, [data.center?.lat, data.center?.lng])

  useEffect(() => {
    if (!map.current || styleMode.current === mode) return
    styleMode.current = mode
    map.current.setStyle(STYLE[mode])
  }, [mode])

  useEffect(() => {
    const m = map.current
    if (!m) return
    pins.current.forEach((p) => p.remove())
    pins.current.clear()
    // Draw "you" last so it sits on top of nearby pins
    for (const o of [...data.outlets].sort((a, b) => Number(!!a.is_you) - Number(!!b.is_you))) {
      const el = document.createElement('button')
      el.type = 'button'
      el.className = 'map-pin'
      el.dataset.kind = kindOf(o)
      el.title = o.name
      el.setAttribute('aria-label', `${o.name}${o.rating !== null ? `, rating ${o.rating}` : o.scanned ? '' : ', not scanned'}`)
      el.addEventListener('click', (e) => { e.stopPropagation(); onSelect(o.id) })
      pins.current.set(o.id, new Marker({ element: el }).setLngLat([o.lng, o.lat]).addTo(m))
    }
  }, [data.outlets, data.center?.lat, data.center?.lng, onSelect])

  useEffect(() => {
    pins.current.forEach((p, id) => p.getElement().setAttribute('aria-pressed', String(id === selected)))
    const o = data.outlets.find((x) => x.id === selected)
    const m = map.current
    if (!o || !m) return
    // Nearby places often sit metres apart, so zoom in far enough to tell the selected pin from its neighbours
    const crowded = data.outlets.some((x) => x.id !== o.id && Math.abs(x.lat - o.lat) < 0.0006 && Math.abs(x.lng - o.lng) < 0.0006)
    if (crowded && m.getZoom() < 17) m.easeTo({ center: [o.lng, o.lat], zoom: 17 })
    else if (!m.getBounds().contains([o.lng, o.lat])) m.easeTo({ center: [o.lng, o.lat] })
  }, [selected, data.outlets])

  return <div ref={box} className="h-[420px] w-full sm:h-[540px]" role="region" aria-label={`Map of places near ${data.locality}`} />
}

const LEGEND: { kind: PinKind; label: string; sampleOnly?: boolean }[] = [
  { kind: 'you', label: 'Your outlet' },
  { kind: 'rising', label: 'Rating rising', sampleOnly: true },
  { kind: 'falling', label: 'Rating falling', sampleOnly: true },
  { kind: 'flat', label: 'No change', sampleOnly: true },
  { kind: 'scanned', label: 'Scanned competitor' },
  { kind: 'unscanned', label: 'Not scanned' },
]

function Details({ o, data, outletId }: { o: CityOutlet; data: CityMap; outletId: string }) {
  const stat = (label: string, value: string, cls = '') => (
    <div><dt className="text-xs text-ink/45">{label}</dt><dd className={`text-lg font-semibold ${cls}`}>{value}</dd></div>
  )
  const change = o.rating_change_60d
  return (
    <Panel title={o.is_you ? 'Your outlet' : 'Selected place'}>
      <div className="space-y-3 px-5 pb-5">
        <div>
          <p className="font-semibold">{o.name}</p>
          {(o.address || o.distance_m !== undefined) && (
            <p className="text-xs text-ink/45">{[o.address, o.distance_m !== undefined && !o.is_you ? `${o.distance_m} m away` : null].filter(Boolean).join(' · ')}</p>
          )}
        </div>
        {o.scanned ? (
          <dl className="grid grid-cols-2 gap-3 text-sm">
            {stat(data.source === 'sample' ? 'Rating' : 'Avg. review rating', o.rating !== null ? o.rating.toFixed(1) : '–')}
            {change !== null && stat('60-day change', `${change > 0 ? '+' : ''}${change.toFixed(1)}`, change > 0 ? 'text-pos' : change < 0 ? 'text-neg' : '')}
            {o.reviews_per_week !== null && stat('Reviews / week', String(o.reviews_per_week))}
            {o.reviews_analysed != null && stat('Reviews analysed', String(o.reviews_analysed))}
          </dl>
        ) : (
          <div className="space-y-2">
            <p className="text-sm text-ink/60">Not scanned yet, so there are no review numbers for this place.</p>
            <Link className="btn !py-1 !text-xs" to={`/outlet/${outletId}/competitors?add=${encodeURIComponent(o.name)}`}>Add to competitor comparison →</Link>
          </div>
        )}
        {data.source === 'live' && o.scanned && !o.is_you && (
          <p className="text-[11px] text-ink/40">Average of the public reviews RepSync analysed, not the platform's overall rating.</p>
        )}
      </div>
    </Panel>
  )
}

export default function CityMapPage() {
  const { id = '' } = useParams()
  const q = useCityMap(id)
  const data = q.data
  const [selected, setSelected] = useState<string | null>(null)
  const outlets = data?.outlets ?? []
  const sel = outlets.find((o) => o.id === selected) ?? outlets.find((o) => o.is_you)
  const isSample = data?.source === 'sample'
  // Rated places first (best first), then unscanned places nearest first
  const ordered = [...outlets].sort((a, b) =>
    a.rating !== null && b.rating !== null ? b.rating - a.rating : a.rating !== null ? -1 : b.rating !== null ? 1 : (a.distance_m ?? 0) - (b.distance_m ?? 0))
  const nearbyCount = outlets.filter((o) => !o.is_you).length

  return (
    <div className="space-y-5">
      <SectionHead
        title="City reputation map"
        sub={isSample
          ? `Who is rising and who is slipping in ${data?.locality ?? 'your locality'}, over the last 60 days.`
          : `Similar places within ${((data?.radius_m ?? 1500) / 1000).toFixed(1)} km of your outlet${data?.locality ? ` in ${data.locality}` : ''}.`}
        action={<SampleBadge source={data?.source} label="Sample data: simulated competitors" />}
      />
      {q.isError && <ErrorNote>Could not load the map: {(q.error as Error).message}</ErrorNote>}
      {data?.status === 'no_location' && <ErrorNote>{data.note}</ErrorNote>}
      {(q.isLoading || data?.status === 'locating') && (
        <section className="panel flex h-[420px] items-center justify-center sm:h-[540px]" aria-live="polite">
          <p className="flex items-center gap-2 text-sm text-ink/55"><span className="status-dot status-dot-ok pulse-live" /> Finding your outlet and nearby places on OpenStreetMap…</p>
        </section>
      )}
      {data?.status === 'ok' && (
        <div className="grid gap-6 lg:grid-cols-[1fr_300px]">
          <section className="panel self-start overflow-hidden">
            <OutletMap data={data} selected={sel?.id ?? null} onSelect={setSelected} />
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 border-t border-line px-4 py-2.5 text-[11px] text-ink/55">
              {LEGEND.filter((l) => isSample ? l.kind !== 'scanned' && l.kind !== 'unscanned' : !l.sampleOnly).map((l) => (
                <span key={l.kind} className="inline-flex items-center gap-1.5"><span className="map-pin map-pin-legend" data-kind={l.kind} aria-hidden /> {l.label}</span>
              ))}
              {data.places_status === 'loading' && <span className="ml-auto">Loading nearby places…</span>}
              {data.places_status === 'unavailable' && <span className="ml-auto text-warn">Nearby places couldn't load (OpenStreetMap is busy). Try again later.</span>}
            </div>
          </section>
          <div className="space-y-6">
            {sel && <Details o={sel} data={data} outletId={id} />}
            <Panel title={isSample ? 'By rating' : `Nearby (${nearbyCount})`}>
              <ol className="max-h-[360px] divide-y divide-line overflow-y-auto">
                {ordered.map((o) => (
                  <li key={o.id}>
                    <button className={`flex w-full items-center gap-3 px-5 py-2 text-left text-sm hover:bg-ink/[.035] ${sel?.id === o.id ? 'bg-ink/[.04]' : ''}`} onClick={() => setSelected(o.id)}>
                      <span className="map-pin map-pin-legend shrink-0" data-kind={kindOf(o)} aria-hidden />
                      <span className={`flex-1 truncate ${o.is_you ? 'font-semibold text-brand' : ''}`}>{o.name}</span>
                      <span className="tabular-nums text-ink/60">{o.rating !== null ? o.rating.toFixed(1) : o.distance_m !== undefined ? `${o.distance_m} m` : ''}</span>
                    </button>
                  </li>
                ))}
              </ol>
              <p className="border-t border-line px-5 py-2.5 text-[11px] text-ink/40">{data.note}</p>
            </Panel>
          </div>
        </div>
      )}
    </div>
  )
}
