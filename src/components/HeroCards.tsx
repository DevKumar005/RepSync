import DotText, { dotLayout } from './DotText'

const CDN = 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P'
const STILLS = 'https://d2ol7oe51mr4n9.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P'
const MEDIA = {
  speed: { poster: `${STILLS}/167977c6-8539-46b1-9a15-8dba566f50b8.png`, src: `${CDN}/hf_20260826_130045_1a612b69-4854-4b34-8043-ccb91f2c60af.mp4` },
  context: { poster: `${STILLS}/0446d1d5-e65e-4db5-8090-3e30d09afc43.png`, src: `${CDN}/hf_20260826_130054_dd005674-d693-4d81-80a5-357f7f10b3a3.mp4` },
  connections: { poster: `${STILLS}/da8d0242-4dee-4f6d-813f-a5887e86ad77.png`, src: `${CDN}/hf_20260826_130103_7550f407-f14b-40a6-9616-7a26d7a8bd9f.mp4` },
}

// "118" spans 31.2% of the card in the reference; keep the same dot size for any number
const numberWidth = (text: string) => `${dotLayout(text).width * (31.2 / 70)}%`

const Grain = () => (
  <svg className="card__grain" viewBox="0 0 429 554" preserveAspectRatio="none" aria-hidden="true">
    <rect width="429" height="554" filter="url(#cardNoise)" />
  </svg>
)

function Metric({ kind, value, unit, radius }: { kind: string; value: string; unit: string; radius: number }) {
  return (
    <div className={`metric metric--${kind}`}>
      <span className="dot-number" style={{ width: numberWidth(value) }}>
        <DotText text={value} radius={radius} />
      </span>
      <span className="metric__unit">{unit}</span>
    </div>
  )
}

const ticks = Array.from({ length: 23 }, (_, i) => {
  const a = ((190 + i * 5) * Math.PI) / 180
  const inner = i % 5 === 0 ? 129 : 133
  return { x1: 163 + Math.cos(a) * 142, y1: 163 + Math.sin(a) * 142, x2: 163 + Math.cos(a) * inner, y2: 163 + Math.sin(a) * inner, w: i % 5 === 0 ? 1.5 : 1 }
})

function Gauge() {
  return (
    <svg className="gauge" viewBox="0 0 326 326" aria-hidden="true">
      <defs>
        <linearGradient id="gaugeArc" gradientUnits="userSpaceOnUse" x1="7" y1="136" x2="312" y2="109">
          <stop offset="0" stopColor="#ff9ab7" stopOpacity=".06" /><stop offset=".08" stopColor="#ff8caf" stopOpacity=".44" />
          <stop offset=".34" stopColor="#ff6796" stopOpacity=".94" /><stop offset=".58" stopColor="#ff6796" stopOpacity="1" />
          <stop offset=".82" stopColor="#ffe7ed" stopOpacity=".74" /><stop offset=".94" stopColor="#fff8fa" stopOpacity=".28" />
          <stop offset="1" stopColor="#fff" stopOpacity="0" />
        </linearGradient>
        <linearGradient id="gaugeShadow" gradientUnits="userSpaceOnUse" x1="11" y1="136" x2="308" y2="110">
          <stop offset="0" stopColor="#6e1639" stopOpacity=".04" /><stop offset=".09" stopColor="#6e1639" stopOpacity=".17" />
          <stop offset=".52" stopColor="#72163d" stopOpacity=".18" /><stop offset=".78" stopColor="#7b1a43" stopOpacity=".1" />
          <stop offset="1" stopColor="#7b1a43" stopOpacity="0" />
        </linearGradient>
        <radialGradient id="radarBeam" gradientUnits="userSpaceOnUse" cx="163" cy="163" r="145">
          <stop offset=".3" stopColor="#650f35" stopOpacity="0" /><stop offset=".45" stopColor="#650f35" stopOpacity=".025" />
          <stop offset=".7" stopColor="#650f35" stopOpacity=".065" /><stop offset=".9" stopColor="#650f35" stopOpacity=".08" />
          <stop offset="1" stopColor="#650f35" stopOpacity=".05" />
        </radialGradient>
        <linearGradient id="radarBeamEdge" gradientUnits="userSpaceOnUse" x1="238" y1="33" x2="190.5" y2="115.4">
          <stop offset="0" stopColor="#ffe7ef" stopOpacity=".19" /><stop offset=".48" stopColor="#ffd1df" stopOpacity=".11" />
          <stop offset=".82" stopColor="#ffc6d7" stopOpacity=".045" /><stop offset="1" stopColor="#ffc6d7" stopOpacity="0" />
        </linearGradient>
        <filter id="radarSoft"><feGaussianBlur stdDeviation="1.35" /></filter>
        <filter id="radarHalo"><feGaussianBlur stdDeviation="5.2" /></filter>
        <filter id="gaugeBlur"><feGaussianBlur stdDeviation="11" /></filter>
      </defs>
      <path d="M11.34 136.26A154 154 0 0 1 307.71 110.33" fill="none" strokeWidth="3.2" strokeLinecap="round" stroke="url(#gaugeShadow)" />
      <path d="M6.91 135.48A158.5 158.5 0 0 1 311.94 108.79" fill="none" strokeWidth="2.2" strokeLinecap="round" stroke="url(#gaugeArc)" />
      <path d="M19.22 137.65A146 146 0 0 1 236 36.56" fill="none" strokeWidth="1.15" stroke="rgba(255,166,194,.31)" />
      <path d="M238 33.1A150 150 0 0 1 277.9 66.6L199.8 119.5A55 55 0 0 0 190.5 115.4Z" fill="#6a1238" opacity=".022" filter="url(#radarHalo)" />
      <path d="M238 33.1A150 150 0 0 1 277.9 66.6L199.8 119.5A55 55 0 0 0 190.5 115.4Z" fill="url(#radarBeam)" filter="url(#radarSoft)" />
      <path d="M238 33.1L190.5 115.4" stroke="url(#radarBeamEdge)" strokeWidth="1.25" strokeLinecap="round" filter="url(#radarSoft)" />
      <g>{ticks.map((t, i) => <line key={i} className="tick" x1={t.x1} y1={t.y1} x2={t.x2} y2={t.y2} strokeWidth={t.w} />)}</g>
      <ellipse cx="225" cy="166" rx="92" ry="76" fill="#fff" opacity=".055" filter="url(#gaugeBlur)" />
    </svg>
  )
}

function TileWall() {
  return (
    <div className="context-glow" aria-hidden="true">
      <svg className="context-backdrop" viewBox="0 0 429 554" preserveAspectRatio="none">
        <defs>
          <linearGradient id="tTLf" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#d4b0ee" stopOpacity=".05" /><stop offset="1" stopColor="#c6bbff" stopOpacity=".18" /></linearGradient>
          <linearGradient id="tTCf" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#d5c2ff" stopOpacity=".22" /><stop offset=".4" stopColor="#e0bdff" stopOpacity=".26" />
            <stop offset=".75" stopColor="#f2a0ee" stopOpacity=".32" /><stop offset="1" stopColor="#ff96da" stopOpacity=".34" />
          </linearGradient>
          <linearGradient id="tTRf" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#ffe8da" stopOpacity=".56" /><stop offset=".5" stopColor="#f9c6d0" stopOpacity=".26" /><stop offset="1" stopColor="#eba4bf" stopOpacity=".08" /></linearGradient>
          <linearGradient id="tMLf" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#c9b8ff" stopOpacity=".3" /><stop offset="1" stopColor="#a678d8" stopOpacity=".12" /></linearGradient>
          <linearGradient id="tMCf" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#e7b8f2" stopOpacity=".22" /><stop offset="1" stopColor="#d993c9" stopOpacity=".14" /></linearGradient>
          <linearGradient id="tMRf" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#e858b8" stopOpacity=".52" /><stop offset=".55" stopColor="#e6459c" stopOpacity=".46" /><stop offset="1" stopColor="#de74ba" stopOpacity=".16" /></linearGradient>
          <linearGradient id="deepX" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor="#6e2238" stopOpacity=".5" /><stop offset=".35" stopColor="#e47d73" stopOpacity=".34" />
            <stop offset=".7" stopColor="#f0a2c4" stopOpacity=".3" /><stop offset="1" stopColor="#9aa8f0" stopOpacity=".28" />
          </linearGradient>
          <linearGradient id="sheen" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#fff" stopOpacity=".28" /><stop offset="1" stopColor="#fff" stopOpacity="0" /></linearGradient>
          <filter id="tileSoft"><feGaussianBlur stdDeviation="3.4" /></filter>
          <filter id="groutSoft"><feGaussianBlur stdDeviation="6.5" /></filter>
        </defs>
        <g filter="url(#tileSoft)">
          <rect x="-24" y="22" width="106" height="149" rx="15" fill="url(#tTLf)" />
          <rect x="88" y="22" width="247" height="150" rx="15" fill="url(#tTCf)" />
          <rect x="88" y="22" width="247" height="46" rx="15" fill="url(#sheen)" />
          <rect x="346" y="22" width="111" height="147" rx="15" fill="url(#tTRf)" />
          <rect x="346" y="22" width="111" height="46" rx="15" fill="url(#sheen)" />
          <rect x="-24" y="177" width="108" height="174" rx="15" fill="url(#tMLf)" />
          <rect x="-24" y="177" width="108" height="52" rx="15" fill="url(#sheen)" />
          <rect x="88" y="177" width="247" height="174" rx="15" fill="url(#tMCf)" />
          <rect x="344" y="175" width="113" height="176" rx="15" fill="url(#tMRf)" />
          <rect x="-24" y="384" width="480" height="170" rx="15" fill="url(#deepX)" />
        </g>
        <g filter="url(#groutSoft)" opacity=".5">
          <rect x="81" y="30" width="8" height="150" fill="#5c1f55" opacity=".35" />
          <rect x="338" y="30" width="8" height="322" fill="#6b1d58" opacity=".35" />
          <rect x="0" y="167" width="429" height="12" fill="#5d2257" opacity=".3" />
        </g>
        <ellipse cx="352" cy="86" rx="70" ry="54" fill="#ffe3ec" opacity=".22" filter="url(#groutSoft)" />
        <ellipse cx="75" cy="150" rx="41" ry="27" fill="#fff" opacity=".12" filter="url(#groutSoft)" />
        <ellipse cx="8" cy="334" rx="38" ry="29" fill="#3d1640" opacity=".16" filter="url(#groutSoft)" />
        <ellipse cx="56" cy="215" rx="28" ry="31" fill="#9b7bff" opacity=".16" filter="url(#groutSoft)" />
      </svg>
    </div>
  )
}

const NETWORK_WHITE: [number, string][] = [
  [0.2, 'M0 5H128c27 0 36 7 39 26 2 16 9 22 24 22h106c16 0 23-8 25-25 2-16 10-23 31-23h76'],
  [0.3, 'M0 117h46c15 0 22 8 26 25 5 23 12 31 31 31h174c18 0 25-8 30-31 4-17 11-25 26-25h96'],
  [0.34, 'M0 173h87c15 0 22 7 27 25 4 15 11 22 28 22h140c17 0 25-7 29-22 5-18 12-25 28-25h90'],
  [0.16, 'M0 228h120c17 0 25-5 28-18 4-15 10-20 28-20h81c18 0 25 6 28 20 4 13 11 18 28 18h116'],
  [0.26, 'M0 5H429M0 61H429M0 117H429'],
  [0.09, 'M0 173H429'],
]
const NETWORK_WARM: [number, string][] = [
  [0.52, 'M0 61h95c14 0 22-6 27-20 4-13 12-20 27-20h115c15 0 23 6 27 20 5 14 13 20 28 20h110'],
  [0.94, 'M0 117h88c15 0 22-8 25-25 4-24 12-31 31-31h129c20 0 27 7 31 31 3 17 10 25 26 25h99'],
]
const NODES: [number, number, string][] = [[45, 117, '#fff'], [133, 61, '#fff4a7'], [189, 61, '#fff1a4'], [319, 61, '#fff4a6'], [319, 117, '#fff2a0']]

function NetworkMap() {
  return (
    <svg className="connections-map" viewBox="0 0 429 238" preserveAspectRatio="none" aria-hidden="true">
      {NETWORK_WHITE.map(([o, d], i) => <path key={i} d={d} fill="none" stroke="#fff" strokeWidth="1" opacity={o} />)}
      {NETWORK_WARM.map(([o, d], i) => <path key={i} d={d} fill="none" stroke="#fff8dd" strokeWidth="1.15" opacity={o} />)}
      {NODES.map(([cx, cy, f]) => <circle key={`${cx}-${cy}`} cx={cx} cy={cy} r="6.5" fill={f} />)}
    </svg>
  )
}

const Video = ({ kind }: { kind: keyof typeof MEDIA }) => (
  <video className="card__media" autoPlay muted loop playsInline preload="auto" aria-hidden="true" poster={MEDIA[kind].poster} src={MEDIA[kind].src} />
)

export function CardFilterDefs() {
  return (
    <svg className="filter-defs" aria-hidden="true" focusable="false">
      <filter id="cardNoise" x="0" y="0" width="100%" height="100%">
        <feTurbulence type="fractalNoise" baseFrequency=".54" numOctaves="3" seed="27" stitchTiles="stitch" />
        <feColorMatrix type="saturate" values="0" />
        <feComponentTransfer>
          <feFuncR type="linear" slope="1.8" intercept="-.25" />
          <feFuncG type="linear" slope="1.8" intercept="-.25" />
          <feFuncB type="linear" slope="1.8" intercept="-.25" />
          <feFuncA type="table" tableValues="0 .52" />
        </feComponentTransfer>
      </filter>
    </svg>
  )
}

export default function HeroCards({ onLearnMore }: { onLearnMore: (section: 'collect' | 'analyse' | 'compare') => void }) {
  return (
    <section className="cards" aria-label="RepSync capabilities">
      <article className="card card--speed">
        <Video kind="speed" />
        <div className="card__inner">
          <Grain />
          <Gauge />
          <h3 className="card__title">Review Collection<br />Every Platform, One Feed</h3>
          <Metric kind="speed" value="5" unit="platforms" radius={2.05} />
          <p className="caption">Google, Zomato, Practo,<br />Justdial, Tripadvisor</p>
          <button type="button" className="learn-more" onClick={() => onLearnMore('collect')}>Learn More</button>
        </div>
      </article>
      <article className="card card--context">
        <Video kind="context" />
        <div className="card__inner">
          <Grain />
          <TileWall />
          <div className="context-window" aria-hidden="true">
            <div className="window-lines"><span /><span /><span /></div>
          </div>
          <h3 className="card__title">Complaint Analysis<br />Themes &amp; Top Fixes</h3>
          <Metric kind="context" value="3" unit="fixes" radius={2.32} />
          <p className="caption">Ranked actions drawn<br />from your reviews</p>
          <button type="button" className="learn-more" onClick={() => onLearnMore('analyse')}>Learn More</button>
        </div>
      </article>
      <article className="card card--connections">
        <Video kind="connections" />
        <div className="card__inner">
          <Grain />
          <NetworkMap />
          <h3 className="card__title">Competitor Insight<br />Cross-Outlet Gaps</h3>
          <Metric kind="connections" value="3" unit="rivals" radius={1.55} />
          <p className="caption">Nearby competitors<br />compared by theme</p>
          <button type="button" className="learn-more" onClick={() => onLearnMore('compare')}>Learn More</button>
        </div>
      </article>
    </section>
  )
}
