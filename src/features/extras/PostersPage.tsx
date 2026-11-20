import { useMemo, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { toPng } from 'html-to-image'
import { api } from '../../api/client'
import type { Review } from '../../types'
import { SectionHead } from '../../components/Page'
import { ErrorNote, FONT_STACK, Panel } from './ui'

const SIZES = {
  square: { w: 1080, h: 1080, label: 'Instagram post · 1080×1080' },
  story: { w: 1080, h: 1920, label: 'WhatsApp status · 1080×1920' },
} as const
type SizeKey = keyof typeof SIZES

const PLATFORM_NAME: Record<string, string> = { google: 'Google', google_maps: 'Google', zomato: 'Zomato', practo: 'Practo', justdial: 'Justdial', tripadvisor: 'Tripadvisor' }

export function truncate(text: string, max = 220): string {
  const t = text.trim().replace(/\s+/g, ' ')
  if (t.length <= max) return t
  const cut = t.slice(0, max - 1)
  const space = cut.lastIndexOf(' ')
  return (space > max * 0.6 ? cut.slice(0, space) : cut).replace(/[\s,.;:!?-]+$/, '') + '…'
}

export function initials(name: string): string {
  return name.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => [...w][0]?.toUpperCase() ?? '').join('') || 'R'
}

/** "Ankit Mehra" -> "Ankit M." ; single word stays as is; empty -> null */
export function firstNameInitial(author: string): string | null {
  const parts = author.replace(/[^\p{L}\p{M}\s.'-]/gu, '').trim().split(/\s+/).filter(Boolean)
  if (!parts.length || /^(anonymous|verified|a google user)/i.test(author)) return null
  return parts.length === 1 ? parts[0] : `${parts[0]} ${[...parts[1]][0]}.`
}

/** Black or white text, whichever reads better on the brand colour */
function textOn(hex: string): string {
  const n = parseInt(hex.replace('#', ''), 16)
  const [r, g, b] = [(n >> 16) & 255, (n >> 8) & 255, n & 255]
  return 0.299 * r + 0.587 * g + 0.114 * b > 160 ? '#111827' : '#ffffff'
}

interface PosterProps { review: Review; size: SizeKey; business: string; logo: string | null; color: string; reviewer: string }

function Poster({ review, size, business, logo, color, reviewer }: PosterProps) {
  const { w, h } = SIZES[size]
  const fg = textOn(color)
  const text = truncate(review.text)
  const tall = size === 'story'
  const fontSize = (text.length <= 80 ? 68 : text.length <= 150 ? 56 : 46) * (tall ? 1.1 : 1)
  return (
    <div
      style={{
        width: w, height: h, fontFamily: FONT_STACK, color: fg, boxSizing: 'border-box',
        background: `linear-gradient(160deg, ${color} 0%, ${color} 55%, ${fg === '#ffffff' ? '#00000055' : '#ffffff88'} 140%)`,
        backgroundColor: color, padding: tall ? '160px 96px' : '96px', display: 'flex', flexDirection: 'column',
        justifyContent: 'space-between',
      }}
    >
      <div style={{ fontSize: 44, letterSpacing: 6, opacity: 0.95 }} aria-label={`${Math.round(review.rating)} out of 5 stars`}>
        {'★★★★★'}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 40 }}>
        <div style={{ fontSize: 180, lineHeight: 0.6, opacity: 0.35, fontFamily: 'Georgia, serif' }}>“</div>
        <p style={{ fontSize, lineHeight: 1.35, fontWeight: 600, margin: 0, wordBreak: 'break-word' }}>{text}</p>
        <p style={{ fontSize: 36, margin: 0, opacity: 0.85 }}>— {reviewer}{PLATFORM_NAME[review.platform] ? ` · on ${PLATFORM_NAME[review.platform]}` : ''}</p>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 28 }}>
        {logo ? (
          <img src={logo} alt="" style={{ width: 120, height: 120, borderRadius: 60, objectFit: 'cover', background: '#fff' }} />
        ) : (
          <div style={{ width: 120, height: 120, borderRadius: 60, background: fg, color, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 48, fontWeight: 700 }}>
            {initials(business)}
          </div>
        )}
        <div style={{ fontSize: 48, fontWeight: 700, lineHeight: 1.15 }}>{business}</div>
      </div>
    </div>
  )
}

function PosterEditor({ review, outletName, onClose }: { review: Review; outletName: string; onClose: () => void }) {
  const [size, setSize] = useState<SizeKey>('square')
  const [business, setBusiness] = useState(outletName)
  const [logo, setLogo] = useState<string | null>(null)
  const [color, setColor] = useState('#4f46e5')
  const [showName, setShowName] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const node = useRef<HTMLDivElement>(null)
  const nameOption = firstNameInitial(review.author)
  const reviewer = showName && nameOption ? nameOption : 'A happy customer'
  const { w, h } = SIZES[size]
  const scale = size === 'square' ? 0.4 : 0.26

  const onLogo = (file?: File) => {
    setError(null)
    if (!file) return
    if (!file.type.startsWith('image/')) return setError('Please choose an image file for the logo.')
    if (file.size > 3 * 1024 * 1024) return setError('Logo is too large. Use an image under 3 MB.')
    // Read locally into a data URL; the logo never leaves the browser
    const reader = new FileReader()
    reader.onload = () => setLogo(String(reader.result))
    reader.onerror = () => setError('Could not read that image.')
    reader.readAsDataURL(file)
  }

  const exportPoster = async () => {
    if (!node.current) return
    setBusy(true)
    setError(null)
    try {
      // fontEmbedCSS '' skips web-font embedding: the poster uses system + Devanagari fonts only
      const dataUrl = await toPng(node.current, { pixelRatio: 2, width: w, height: h, fontEmbedCSS: '', cacheBust: true })
      const fileName = `${business.replace(/[^\p{L}\p{N}]+/gu, '-').toLowerCase() || 'review'}-${size}.png`
      const blob = await (await fetch(dataUrl)).blob()
      const file = new File([blob], fileName, { type: 'image/png' })
      if (navigator.canShare?.({ files: [file] })) {
        try {
          await navigator.share({ files: [file], title: `${business} review` })
          return
        } catch (e) {
          if ((e as Error).name === 'AbortError') return
        }
      }
      const a = document.createElement('a')
      a.href = dataUrl
      a.download = fileName
      a.click()
    } catch (e) {
      setError(`Could not create the image (${(e as Error).message || 'unknown error'}). Try a smaller logo or another browser.`)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Panel title="Create poster" action={<button className="btn !py-1 !text-xs" onClick={onClose}>Close</button>}>
      <div className="grid gap-6 px-5 pb-5 lg:grid-cols-[320px_1fr]">
        <div className="space-y-4">
          <fieldset>
            <legend className="text-sm font-medium text-ink/70 mb-2">Size</legend>
            <div className="flex flex-wrap gap-2">
              {(Object.keys(SIZES) as SizeKey[]).map((k) => (
                <button key={k} type="button" aria-pressed={size === k} onClick={() => setSize(k)} className={`btn !text-xs ${size === k ? 'btn-primary' : ''}`}>
                  {SIZES[k].label}
                </button>
              ))}
            </div>
          </fieldset>
          <label className="block text-sm font-medium text-ink/70">
            Business name
            <input className="field mt-1.5 font-normal" value={business} maxLength={60} onChange={(e) => setBusiness(e.target.value)} />
          </label>
          <label className="block text-sm font-medium text-ink/70">
            Logo <span className="font-normal text-ink/40">(stays on your device)</span>
            <input className="mt-1.5 block w-full text-sm" type="file" accept="image/*" onChange={(e) => onLogo(e.target.files?.[0])} />
          </label>
          {logo && <button className="btn !text-xs" onClick={() => setLogo(null)}>Remove logo (use initials)</button>}
          <label className="flex items-center gap-3 text-sm font-medium text-ink/70">
            Brand colour
            <input type="color" value={color} onChange={(e) => setColor(e.target.value)} className="h-8 w-14 cursor-pointer rounded border border-line" />
          </label>
          <fieldset className="space-y-1.5 text-sm">
            <legend className="font-medium text-ink/70 mb-1">Reviewer shown as</legend>
            <label className="flex items-center gap-2"><input type="radio" className="accent-brand" checked={!showName} onChange={() => setShowName(false)} /> A happy customer</label>
            <label className={`flex items-center gap-2 ${nameOption ? '' : 'opacity-40'}`}>
              <input type="radio" className="accent-brand" disabled={!nameOption} checked={showName} onChange={() => setShowName(true)} />
              First name + initial{nameOption ? ` (${nameOption})` : ' (not available)'}
            </label>
          </fieldset>
          <button className="btn btn-primary w-full" disabled={busy} onClick={exportPoster}>
            {busy ? 'Creating image…' : typeof navigator !== 'undefined' && 'share' in navigator ? 'Share or download PNG' : 'Download PNG'}
          </button>
          {error && <p role="alert" className="text-sm text-neg">{error}</p>}
        </div>
        <div className="overflow-auto rounded-2xl border border-line bg-white/50 p-4">
          <div style={{ width: w * scale, height: h * scale }} className="mx-auto shadow-lg">
            <div style={{ transform: `scale(${scale})`, transformOrigin: 'top left', width: w, height: h }}>
              <div ref={node}>
                <Poster review={review} size={size} business={business || outletName} logo={logo} color={color} reviewer={reviewer} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </Panel>
  )
}

export default function PostersPage() {
  const { id = '' } = useParams()
  const outlet = useQuery({ queryKey: ['outlet', id], queryFn: () => api.outlet(id) })
  const reviews = useQuery({ queryKey: ['extras', 'poster-reviews', id], queryFn: () => api.reviews(id, {}) })
  const [selected, setSelected] = useState<Review | null>(null)
  const fiveStar = useMemo(
    () => (reviews.data ?? []).filter((r) => r.rating >= 5 && r.sentiment !== 'negative' && r.text.trim()),
    [reviews.data],
  )

  return (
    <div className="space-y-5">
      <SectionHead title="Review posters" sub="Turn a 5-star review into a shareable image for an Instagram post or WhatsApp status. The logo you add never leaves your device." />
      {selected && <PosterEditor review={selected} outletName={outlet.data?.name ?? 'Your business'} onClose={() => setSelected(null)} />}
      <Panel title={`5-star reviews (${fiveStar.length})`}>
        {reviews.isLoading && <p className="px-5 pb-5 text-sm text-ink/45">Loading reviews…</p>}
        {reviews.isError && <ErrorNote>Could not load reviews: {(reviews.error as Error).message}</ErrorNote>}
        {reviews.data && !fiveStar.length && <p className="px-5 pb-5 text-sm text-ink/45">No 5-star reviews yet. Press Sync reviews above first.</p>}
        <ul className="divide-y divide-line">
          {fiveStar.map((r) => (
            <li key={r.id} className="flex items-start gap-4 px-5 py-4">
              <div className="min-w-0 flex-1">
                <p className="text-sm leading-relaxed" style={{ fontFamily: FONT_STACK }}>{truncate(r.text)}</p>
                <p className="mt-1 text-xs text-ink/40">{PLATFORM_NAME[r.platform] ?? r.platform} · {r.posted_at}</p>
              </div>
              <button className="btn !text-xs shrink-0" onClick={() => { setSelected(r); window.scrollTo({ top: 0, behavior: 'smooth' }) }}>
                Create poster
              </button>
            </li>
          ))}
        </ul>
      </Panel>
    </div>
  )
}
