import { useLayoutEffect } from 'react'
import { NavLink } from 'react-router-dom'
import DotText from '../components/DotText'
import HeroCards, { CardFilterDefs } from '../components/HeroCards'
import { useOpenDemo } from '../components/Page'

const STAGE = {
  widePoster: 'https://d2ol7oe51mr4n9.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/5c3ec08f-2dbf-4c0a-8588-f6106a789443.webp',
  wideSrc: 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260826_125226_45cb4f38-aa7e-47e1-885d-ae0b69745369.mp4',
  narrowPoster: 'https://d2ol7oe51mr4n9.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/0f4926a4-e660-4df2-9195-2bfb3e341bdd.webp',
  narrowSrc: 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260826_125242_daae1570-386d-4bd5-8896-80499e2371e0.mp4',
}

const PILLARS = [
  {
    id: 'collect', tile: 'tile-speed', step: 'Collect',
    title: 'Every public review, in one feed',
    body: 'Small businesses get reviewed on four or five platforms at once, and owners have no time to check them all. RepSync searches Google Maps, Zomato, Practo, Justdial and Tripadvisor for your outlet, reads the public review pages and brings every review into one normalised, de-duplicated inbox.',
    points: ['Search, Fetch and Agent collection with a live activity log', 'Up to 50 reviews per platform per sync, cached for 24 hours', 'Sentiment and severity tagged on every review'],
  },
  {
    id: 'analyse', tile: 'tile-context', step: 'Analyse',
    title: 'What customers keep complaining about',
    body: 'One review is an opinion; ten reviews saying the same thing are a pattern. RepSync groups negative reviews into labelled complaint themes, counts the evidence behind each one, and turns them into the three most useful fixes for your kind of business.',
    points: ['Complaint themes with real quotes and review counts', 'Top 3 fixes ranked by how many reviews support them', 'Understands English, Hindi and Hinglish reviews'],
  },
  {
    id: 'compare', tile: 'tile-connections', step: 'Compare',
    title: 'Where you win and lose against nearby rivals',
    body: 'Reviews of the outlets around you show what customers expect in your area. RepSync compares your complaint rates with up to three nearby competitors, theme by theme, and tells you what to fix first and which strengths to advertise.',
    points: ['Gap matrix: complaint rates with sample sizes, never invented star ratings', 'Threat and opportunity labels computed in code', 'Review velocity shows who is gaining or losing momentum'],
  },
]

const STEPS = [
  { n: '01', title: 'Find your outlet', body: 'Type your business name and city. RepSync looks it up on OpenStreetMap and shows the matching branches so you can confirm the right one.' },
  { n: '02', title: 'Sync reviews', body: 'One click collects reviews from every platform, tags sentiment, groups complaints into themes and drafts a reply for each unanswered negative review.' },
  { n: '03', title: 'Fix, reply, promote', body: 'Read the top fixes, edit and approve the drafts, compare yourself with competitors and turn your best reviews into posters.' },
]

const FEATURES = [
  { tab: '', name: 'Overview', body: 'Rating, review count, share of negative reviews and unanswered complaints at a glance, with snapshots of every tool below.' },
  { tab: 'reviews', name: 'Reviews', body: 'Every review from every platform in one feed. Filter by platform or sentiment and jump to the original listing.' },
  { tab: 'replies', name: 'Replies', body: 'A drafted reply for every unanswered negative review, in your tone. Edit, shorten, offer a callback, approve or reject.' },
  { tab: 'insights', name: 'Insights', body: 'Complaint themes as a chart with real quotes, plus the top three fixes ranked by evidence.' },
  { tab: 'competitors', name: 'Competitors', body: 'Scan up to three nearby competitors and see a theme-by-theme gap matrix with advice for each gap.' },
  { tab: 'velocity', name: 'Velocity', body: 'Reviews per week for twelve weeks, for you and each competitor, with a warning when momentum drops.' },
  { tab: 'posters', name: 'Posters', body: 'Turn any 5-star review into an Instagram post or WhatsApp status image in your brand colour. Hindi included.' },
  { tab: 'ask', name: 'Ask RepSync', body: 'Ask questions about your reviews in English, Hindi or Hinglish. Answers use only your data, and every number is checked.' },
  { tab: 'map', name: 'City map', body: 'See who is rising and who is slipping in your locality on an offline map, with your outlet highlighted.' },
  { tab: 'activity', name: 'Activity', body: 'Every TinyFish Search, Fetch and Agent call, with timing, items found and cache hits, so you know where data came from.' },
]

const TRUST = [
  { title: 'You approve everything', body: 'Replies move from draft to approved only when you say so. Nothing is posted for you.' },
  { title: 'Guardrails on every draft', body: 'No liability admissions, refund promises or blaming the customer. Banned phrases trigger a rewrite.' },
  { title: 'Numbers you can trust', body: 'Counts, percentages and rankings are computed in code. The AI writes words, never statistics.' },
  { title: 'Built for India', body: 'Reads and replies in English, Hindi and Hinglish, on the platforms Indian customers actually use.' },
]

export default function Home() {
  const demo = useOpenDemo()

  // One-shot entrance choreography, with a failsafe so content never stays hidden
  useLayoutEffect(() => {
    const root = document.documentElement
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return
    root.classList.add('entrance-active')
    const failsafe = setTimeout(() => root.classList.remove('entrance-active'), 3200)
    const last = document.querySelector(matchMedia('(max-width: 767px)').matches ? '.card--speed .learn-more' : '.card--connections .learn-more')
    const done = () => { clearTimeout(failsafe); root.classList.remove('entrance-active') }
    last?.addEventListener('animationend', done, { once: true })
    return () => { clearTimeout(failsafe); last?.removeEventListener('animationend', done); root.classList.remove('entrance-active') }
  }, [])

  const scrollTo = (id: string) => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })

  return (
    <div className="rs-home">
      <main className="stage">
        <video className="stage-motion stage-motion--wide" autoPlay muted loop playsInline preload="auto" aria-hidden="true" poster={STAGE.widePoster} src={STAGE.wideSrc} />
        <video className="stage-motion stage-motion--narrow" autoPlay muted loop playsInline preload="none" aria-hidden="true" poster={STAGE.narrowPoster} src={STAGE.narrowSrc} />
        <div className="paper-texture" aria-hidden="true" />
        <CardFilterDefs />

        <div className="masthead">
          <h1 className="headline">
            <span className="headline__line">Built for <span className="dot-word" aria-label="Local"><DotText text="Local" pitchX={4} radius={1.8} /></span></span>
            <span className="headline__line">Reputation</span>
          </h1>
          <p className="intro">
            RepSync collects every public review of your business, shows<br className="desktop-break" /> what customers keep complaining about, and drafts replies you<br className="desktop-break" /> approve, in English, Hindi or Hinglish.
          </p>
        </div>

        <HeroCards onLearnMore={scrollTo} />
      </main>

      {/* ---- What RepSync does ---- */}
      <section className="rs-container pt-16 pb-6 space-y-6">
        <div className="max-w-3xl space-y-3">
          <p className="label-overline">What RepSync does</p>
          <h2 className="rs-title text-[clamp(24px,2.6vw,36px)]">A reputation manager for restaurants, clinics and salons</h2>
          <p className="rs-copy">
            One unanswered 1-star review tells the next customer that nobody is listening. RepSync gives a single-outlet owner the three things they need: every review in one place, a clear list of what to fix, and replies ready to approve.
          </p>
        </div>
        <div className="grid gap-5 lg:grid-cols-3">
          {PILLARS.map((p) => (
            <article key={p.id} id={p.id} className="panel scroll-mt-20 overflow-hidden">
              <div className={`tile ${p.tile} !rounded-none !border-0 px-6 py-5`}>
                <p className="text-xs font-semibold uppercase tracking-[.14em] text-white/80">{p.step}</p>
                <h3 className="mt-1 text-xl font-semibold leading-snug">{p.title}</h3>
              </div>
              <div className="space-y-4 p-6">
                <p className="rs-copy text-[14.5px]">{p.body}</p>
                <ul className="space-y-2 text-sm text-ink/70">
                  {p.points.map((pt) => <li key={pt} className="flex gap-2.5"><span className="mt-[7px] h-1.5 w-1.5 shrink-0 rounded-full bg-brand" />{pt}</li>)}
                </ul>
              </div>
            </article>
          ))}
        </div>
      </section>

      {/* ---- How it works ---- */}
      <section className="rs-container py-10 space-y-6">
        <div className="space-y-2">
          <p className="label-overline">How it works</p>
          <h2 className="rs-title text-[clamp(24px,2.6vw,36px)]">Three steps, a few minutes</h2>
        </div>
        <ol className="grid gap-5 md:grid-cols-3">
          {STEPS.map((s) => (
            <li key={s.n} className="panel p-6 space-y-3">
              <span className="block text-brand"><DotText text={s.n} radius={1.9} height="22px" /></span>
              <h3 className="text-lg font-semibold">{s.title}</h3>
              <p className="rs-copy text-[14.5px]">{s.body}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* ---- Every tool has its own page ---- */}
      <section className="rs-container py-10 space-y-6">
        <div className="flex flex-wrap items-end gap-4">
          <div className="mr-auto max-w-3xl space-y-2">
            <p className="label-overline">Inside your outlet</p>
            <h2 className="rs-title text-[clamp(24px,2.6vw,36px)]">Ten tools, each with its own page</h2>
            <p className="rs-copy">Open the demo restaurant to try any of them with sample data, no sign-up needed.</p>
          </div>
          <NavLink to="/search" className="btn btn-primary !px-5 !py-2.5">Find my business →</NavLink>
        </div>
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {FEATURES.map((f) => (
            <li key={f.name} className="panel flex flex-col p-5">
              <h3 className="font-semibold">{f.name}</h3>
              <p className="mt-2 flex-1 text-[13.5px] leading-relaxed text-ink/60">{f.body}</p>
              <button className="btn mt-4 self-start !py-1.5 !text-xs" disabled={demo.isPending} onClick={() => demo.mutate({ tab: f.tab })}>
                Open in demo
              </button>
            </li>
          ))}
        </ul>
        {demo.isError && <p role="alert" className="text-sm text-neg">Could not open the demo: {(demo.error as Error).message}. The server may be waking up; try again in a few seconds.</p>}
      </section>

      {/* ---- Trust ---- */}
      <section className="rs-container py-10">
        <div className="tile tile-ink grid gap-6 p-8 md:grid-cols-4">
          {TRUST.map((t) => (
            <div key={t.title} className="space-y-2">
              <h3 className="font-semibold">{t.title}</h3>
              <p className="text-sm leading-relaxed text-white/70">{t.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ---- Pricing CTA ---- */}
      <section className="rs-container pt-6 pb-20">
        <div className="panel flex flex-col items-start gap-6 p-8 md:flex-row md:items-center">
          <div className="mr-auto space-y-2">
            <p className="label-overline">Pricing</p>
            <h2 className="rs-title text-[clamp(22px,2.4vw,32px)]">Starts at ₹499 per outlet per month</h2>
            <p className="rs-copy max-w-xl text-[14.5px]">One lost table or appointment a month costs more than the plan. Start with a free reputation audit: one sync, themes and sample replies.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <button className="btn btn-primary !px-5 !py-2.5" disabled={demo.isPending} onClick={() => demo.mutate({})}>
              {demo.isPending ? 'Opening…' : 'Try the demo'}
            </button>
            <NavLink to="/pricing" className="btn !px-5 !py-2.5">View plans</NavLink>
          </div>
        </div>
      </section>
    </div>
  )
}
