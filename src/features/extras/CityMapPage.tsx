import { useMemo, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { extrasApi } from './api'
import type { CityOutlet } from './types'
import { ErrorNote, Panel, SampleBadge } from './ui'

const W = 800
const H = 560
const PAD = 60
const MIN_ZOOM = 1
const MAX_ZOOM = 6

type View = { k: number; x: number; y: number }

/** Equirectangular projection of lat/lng into the SVG box, keeping aspect ratio. */
function useProjection(outlets: CityOutlet[]) {
  return useMemo(() => {
    if (!outlets.length) return () => ({ x: W / 2, y: H / 2 })
    const lats = outlets.map((o) => o.lat)
    const lngs = outlets.map((o) => o.lng)
    const midLat = ((Math.min(...lats) + Math.max(...lats)) / 2) * (Math.PI / 180)
    const minX = Math.min(...lngs) * Math.cos(midLat)
    const maxX = Math.max(...lngs) * Math.cos(midLat)
    const minY = Math.min(...lats)
    const maxY = Math.max(...lats)
    const scale = Math.min((W - 2 * PAD) / (maxX - minX || 1), (H - 2 * PAD) / (maxY - minY || 1))
    const offX = (W - (maxX - minX) * scale) / 2
    const offY = (H - (maxY - minY) * scale) / 2
    return (o: { lat: number; lng: number }) => ({
      x: offX + (o.lng * Math.cos(midLat) - minX) * scale,
      y: H - (offY + (o.lat - minY) * scale),
    })
  }, [outlets])
}

const trendOf = (o: CityOutlet) => (o.rating_change_60d > 0.05 ? 'rising' : o.rating_change_60d < -0.05 ? 'falling' : 'flat')
const PIN = { rising: 'rgb(var(--pos))', falling: 'rgb(var(--neg))', flat: 'rgb(var(--ink) / 0.45)' }

export default function CityMapPage() {
  const { id = '' } = useParams()
  const q = useQuery({ queryKey: ['extras', 'city-map', id], queryFn: () => extrasApi.cityMap(id) })
  const outlets = q.data?.outlets ?? []
  const project = useProjection(outlets)
  const [view, setView] = useState<View>({ k: 1, x: 0, y: 0 })
  const [selected, setSelected] = useState<string | null>(null)
  const svg = useRef<SVGSVGElement>(null)
  const pointers = useRef(new Map<number, { x: number; y: number }>())
  const lastPinch = useRef<number | null>(null)
  const dragged = useRef(false)

  const toSvg = (clientX: number, clientY: number) => {
    const r = svg.current!.getBoundingClientRect()
    return { x: ((clientX - r.left) / r.width) * W, y: ((clientY - r.top) / r.height) * H }
  }
  const zoomAt = (factor: number, cx = W / 2, cy = H / 2) =>
    setView((v) => {
      const k = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, v.k * factor))
      const f = k / v.k
      return k === MIN_ZOOM ? { k, x: 0, y: 0 } : { k, x: cx - (cx - v.x) * f, y: cy - (cy - v.y) * f }
    })

  const onWheel = (e: React.WheelEvent) => {
    const p = toSvg(e.clientX, e.clientY)
    zoomAt(e.deltaY < 0 ? 1.2 : 1 / 1.2, p.x, p.y)
  }
  const onPointerDown = (e: React.PointerEvent) => {
    pointers.current.set(e.pointerId, { x: e.clientX, y: e.clientY })
    dragged.current = false
  }
  const onPointerMove = (e: React.PointerEvent) => {
    const prev = pointers.current.get(e.pointerId)
    if (!prev) return
    pointers.current.set(e.pointerId, { x: e.clientX, y: e.clientY })
    const pts = [...pointers.current.values()]
    if (pts.length === 2) {
      // Pinch zoom around the midpoint of both fingers
      const dist = Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y)
      if (lastPinch.current) {
        const mid = toSvg((pts[0].x + pts[1].x) / 2, (pts[0].y + pts[1].y) / 2)
        zoomAt(dist / lastPinch.current, mid.x, mid.y)
      }
      lastPinch.current = dist
      dragged.current = true
      return
    }
    const r = svg.current!.getBoundingClientRect()
    const dx = ((e.clientX - prev.x) / r.width) * W
    const dy = ((e.clientY - prev.y) / r.height) * H
    if (Math.abs(dx) + Math.abs(dy) > 1) dragged.current = true
    setView((v) => (v.k === 1 ? v : { ...v, x: v.x + dx, y: v.y + dy }))
  }
  const onPointerUp = (e: React.PointerEvent) => {
    pointers.current.delete(e.pointerId)
    if (pointers.current.size < 2) lastPinch.current = null
  }

  const sel = outlets.find((o) => o.id === selected) ?? outlets.find((o) => o.is_you)
  const ranked = [...outlets].sort((a, b) => b.rating - a.rating)

  return (
    <div className="space-y-6 fade-in">
      <div className="flex flex-wrap items-center gap-3">
        <div className="mr-auto">
          <h1 className="text-2xl font-bold tracking-tight">City Reputation Map</h1>
          <p className="text-sm text-ink/50 mt-1">Who is rising and who is slipping in {q.data?.locality ?? 'your locality'}, over the last 60 days.</p>
        </div>
        <SampleBadge source={q.data?.source} label="Sample data: simulated locality" />
      </div>
      {q.isError && <ErrorNote>Could not load the map: {(q.error as Error).message}</ErrorNote>}
      <div className="grid gap-6 lg:grid-cols-[1fr_300px]">
        <section className="panel relative self-start overflow-hidden">
          <svg
            ref={svg}
            viewBox={`0 0 ${W} ${H}`}
            className="block h-auto w-full touch-none select-none"
            style={{ cursor: view.k > 1 ? 'grab' : 'default' }}
            onWheel={onWheel}
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
            onPointerCancel={onPointerUp}
            role="img"
            aria-label={`Map of ${outlets.length} outlets in ${q.data?.locality ?? 'the locality'}`}
          >
            <rect width={W} height={H} fill="rgb(var(--paper))" />
            <g transform={`translate(${view.x} ${view.y}) scale(${view.k})`}>
              {Array.from({ length: 9 }, (_, i) => (
                <g key={i} stroke="rgb(var(--line))" strokeWidth={1 / view.k}>
                  <line x1={(i * W) / 8} y1={0} x2={(i * W) / 8} y2={H} />
                  <line x1={0} y1={(i * H) / 8} x2={W} y2={(i * H) / 8} />
                </g>
              ))}
              {[80, 150, 220].map((r) => (
                <circle key={r} cx={W / 2} cy={H / 2} r={r} fill="none" stroke="rgb(var(--line))" strokeWidth={6 / view.k} />
              ))}
              <text x={W / 2} y={H / 2 + 4} textAnchor="middle" fontSize={13 / view.k} fill="rgb(var(--ink) / 0.3)">{q.data?.locality}</text>
              {outlets.map((o) => {
                const p = project(o)
                const r = (o.is_you ? 13 : 9) / Math.sqrt(view.k)
                const active = sel?.id === o.id
                return (
                  <g
                    key={o.id}
                    transform={`translate(${p.x} ${p.y})`}
                    className="cursor-pointer"
                    onClick={() => { if (!dragged.current) setSelected(o.id) }}
                    role="button"
                    tabIndex={0}
                    aria-label={`${o.name}, rating ${o.rating}`}
                    onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setSelected(o.id) }}
                  >
                    {o.is_you && <circle r={r + 7 / Math.sqrt(view.k)} fill="none" stroke="rgb(var(--brand))" strokeWidth={3 / Math.sqrt(view.k)} />}
                    <circle r={r} fill={PIN[trendOf(o)]} stroke={active ? 'rgb(var(--ink))' : 'rgb(var(--surface))'} strokeWidth={(active ? 3 : 2) / Math.sqrt(view.k)} />
                    {(view.k >= 1.8 || o.is_you) && (
                      <text y={-r - 6 / view.k} textAnchor="middle" fontSize={12 / Math.sqrt(view.k)} fontWeight={o.is_you ? 700 : 500} fill="rgb(var(--ink))">
                        {o.name}
                      </text>
                    )}
                  </g>
                )
              })}
            </g>
          </svg>
          <div className="absolute right-3 top-3 flex flex-col gap-1">
            <button className="btn !px-2.5 !py-1 bg-surface" aria-label="Zoom in" onClick={() => zoomAt(1.4)}>+</button>
            <button className="btn !px-2.5 !py-1 bg-surface" aria-label="Zoom out" onClick={() => zoomAt(1 / 1.4)}>−</button>
            <button className="btn !px-2 !py-1 bg-surface !text-[10px]" aria-label="Reset view" onClick={() => setView({ k: 1, x: 0, y: 0 })}>Reset</button>
          </div>
          <div className="flex flex-wrap gap-4 border-t border-line px-4 py-2.5 text-[11px] text-ink/55">
            <span><span className="status-dot status-dot-ok" /> Rating rising</span>
            <span><span className="status-dot status-dot-neg" /> Rating falling</span>
            <span><span className="status-dot" style={{ background: PIN.flat }} /> Flat</span>
            <span className="text-brand font-semibold">◯ Your outlet</span>
            <span className="ml-auto">Scroll or pinch to zoom, drag to pan</span>
          </div>
        </section>
        <div className="space-y-6">
          {sel && (
            <Panel title={sel.is_you ? 'Your outlet' : 'Selected outlet'}>
              <div className="space-y-3 px-5 pb-5">
                <p className="font-semibold">{sel.name}</p>
                <dl className="grid grid-cols-2 gap-3 text-sm">
                  <div><dt className="text-xs text-ink/45">Rating</dt><dd className="text-lg font-semibold">{sel.rating.toFixed(1)}</dd></div>
                  <div>
                    <dt className="text-xs text-ink/45">60-day change</dt>
                    <dd className={`text-lg font-semibold ${sel.rating_change_60d > 0 ? 'text-pos' : sel.rating_change_60d < 0 ? 'text-neg' : ''}`}>
                      {sel.rating_change_60d > 0 ? '+' : ''}{sel.rating_change_60d.toFixed(1)}
                    </dd>
                  </div>
                  <div><dt className="text-xs text-ink/45">Reviews / week</dt><dd className="text-lg font-semibold">{sel.reviews_per_week}</dd></div>
                  <div><dt className="text-xs text-ink/45">Rating order (sample)</dt><dd className="text-lg font-semibold">#{ranked.findIndex((o) => o.id === sel.id) + 1} of {ranked.length}</dd></div>
                </dl>
                <p className="text-[11px] text-ink/40">{q.data?.note}</p>
              </div>
            </Panel>
          )}
          <Panel title="By rating">
            <ol className="divide-y divide-line">
              {ranked.map((o, i) => (
                <li key={o.id}>
                  <button className={`flex w-full items-center gap-3 px-5 py-2 text-left text-sm hover:bg-paper ${sel?.id === o.id ? 'bg-paper' : ''}`} onClick={() => setSelected(o.id)}>
                    <span className="w-5 text-ink/35 tabular-nums">{i + 1}</span>
                    <span className={`flex-1 truncate ${o.is_you ? 'font-semibold text-brand' : ''}`}>{o.name}</span>
                    <span className="tabular-nums">{o.rating.toFixed(1)}</span>
                    <span className="status-dot" style={{ background: PIN[trendOf(o)] }} />
                  </button>
                </li>
              ))}
            </ol>
          </Panel>
        </div>
      </div>
    </div>
  )
}
