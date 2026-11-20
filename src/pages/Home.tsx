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

const STEPS = [
  { id: 'collect', tile: 'tile-speed', step: '01 · Collect', title: 'Every review, one feed', line: 'Google, Zomato, Practo, Justdial and Tripadvisor.' },
  { id: 'analyse', tile: 'tile-context', step: '02 · Analyse', title: 'Know what to fix', line: 'Complaint themes and your top 3 fixes.' },
  { id: 'compare', tile: 'tile-connections', step: '03 · Compare', title: 'Beat nearby rivals', line: 'Theme-by-theme gaps against 3 competitors.' },
]

const TOOLS = [
  { tab: '', name: 'Overview', line: 'Your reputation at a glance' },
  { tab: 'reviews', name: 'Reviews', line: 'Every platform, one feed' },
  { tab: 'replies', name: 'Replies', line: 'Drafts in your tone' },
  { tab: 'insights', name: 'Insights', line: 'Themes and top fixes' },
  { tab: 'competitors', name: 'Competitors', line: 'Gap matrix with advice' },
  { tab: 'velocity', name: 'Velocity', line: 'Momentum, week by week' },
  { tab: 'posters', name: 'Posters', line: '5-star reviews as images' },
  { tab: 'map', name: 'City map', line: 'Who is rising nearby' },
  { tab: 'activity', name: 'Activity', line: 'Where every review came from' },
  { tab: '', name: 'Ask RepSync', line: 'Chat with your data' },
]

const TRUST = ['You approve every reply', 'Guardrails on every draft', 'Numbers computed, not generated', 'English, Hindi and Hinglish']

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
            Every review in one place, the fixes that matter,<br className="desktop-break" /> and replies you approve.
          </p>
        </div>

        <HeroCards onLearnMore={scrollTo} />
      </main>

      {/* ---- How it works ---- */}
      <section className="rs-container grid gap-4 pt-14 md:grid-cols-3">
        {STEPS.map((st) => (
          <article key={st.id} id={st.id} className={`tile ${st.tile} scroll-mt-24 p-6`}>
            <p className="text-[11px] font-semibold uppercase tracking-[.14em] text-white/75">{st.step}</p>
            <h2 className="mt-2 text-[22px] font-semibold leading-snug">{st.title}</h2>
            <p className="mt-1 text-sm text-white/80">{st.line}</p>
          </article>
        ))}
      </section>

      {/* ---- Tools ---- */}
      <section className="rs-container space-y-5 py-14">
        <div className="flex flex-wrap items-end gap-4">
          <h2 className="rs-title mr-auto text-[clamp(24px,2.4vw,34px)]">Ten tools. Try any of them in the demo.</h2>
          <NavLink to="/search" className="btn btn-primary !px-5 !py-2.5">Find my business</NavLink>
        </div>
        <ul className="grid grid-cols-2 gap-3 md:grid-cols-5">
          {TOOLS.map((t) => (
            <li key={t.name}>
              <button
                className="panel group block h-full w-full p-4 text-left transition-transform duration-200 hover:-translate-y-0.5 disabled:opacity-60"
                disabled={demo.isPending}
                onClick={() => demo.mutate({ tab: t.tab })}
              >
                <span className="block font-semibold">{t.name}</span>
                <span className="mt-1 block text-[13px] text-ink/55">{t.line}</span>
                <span className="mt-3 block text-[12px] font-medium text-brand opacity-0 transition-opacity group-hover:opacity-100">Open in demo</span>
              </button>
            </li>
          ))}
        </ul>
        {demo.isError && <p role="alert" className="text-sm text-neg">Could not open the demo: {(demo.error as Error).message}. Try again in a few seconds.</p>}
      </section>

      {/* ---- Trust + CTA ---- */}
      <section className="rs-container pb-20">
        <div className="tile tile-ink flex flex-col gap-6 p-7 lg:flex-row lg:items-center">
          <ul className="grid flex-1 grid-cols-2 gap-x-6 gap-y-2 text-sm text-white/85 md:grid-cols-4">
            {TRUST.map((t) => <li key={t} className="flex items-center gap-2"><span className="h-1.5 w-1.5 shrink-0 rounded-full bg-[#8aa8f0]" />{t}</li>)}
          </ul>
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-sm text-white/70">From ₹499 / outlet / month</span>
            <button className="btn !px-5 !py-2.5" disabled={demo.isPending} onClick={() => demo.mutate({})}>{demo.isPending ? 'Opening…' : 'Try the demo'}</button>
            <NavLink to="/pricing" className="text-sm font-medium text-white/85 underline-offset-4 hover:underline">View plans</NavLink>
          </div>
        </div>
      </section>
    </div>
  )
}
