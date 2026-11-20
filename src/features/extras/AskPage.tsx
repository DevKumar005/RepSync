import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ThemePanel } from '../../components/Panels'
import { SectionHead } from '../../components/Page'
import { useOutlet } from '../../pages/outlet/OutletLayout'
import { extrasApi } from './api'
import { GapGrid } from './CompetitorsPage'
import type { AskResponse } from './types'
import { FONT_STACK } from './ui'
import { VelocityView } from './VelocityChart'

const SUGGESTED = ['What should I fix first?', 'How do I compare with competitors?', 'Are my reviews slowing down?', 'Mera rank kyun gira?']
const SOURCE_LABEL: Record<string, string> = {
  summary: 'Summary', themes: 'Themes', fixes: 'Top fixes', velocity: 'Review velocity', competitor_gaps: 'Competitor gaps',
}

function AnswerChart({ id, chart }: { id: string; chart: AskResponse['chart'] }) {
  const vel = useQuery({ queryKey: ['extras', 'velocity', id], queryFn: () => extrasApi.velocity(id), enabled: chart === 'velocity' })
  const gap = useQuery({ queryKey: ['extras', 'competitors', id], queryFn: () => extrasApi.competitors(id), enabled: chart === 'gap' })
  if (chart === 'themes') return <ThemePanel id={id} onSelect={() => {}} />
  if (chart === 'velocity' && vel.data) return <VelocityView data={vel.data} height={220} />
  if (chart === 'gap' && gap.data?.status === 'done') return <GapGrid result={gap.data} />
  return null
}

interface Turn { q: string; a?: AskResponse; error?: string }

export default function AskPage() {
  const { id } = useOutlet()
  const [sp, setSp] = useSearchParams()
  const [question, setQuestion] = useState('')
  const [turns, setTurns] = useState<Turn[]>([])
  const [pending, setPending] = useState(false)
  const end = useRef<HTMLDivElement>(null)
  const handedOver = useRef(sp.get('q'))

  // Plain async state (not useMutation) so an in-flight answer survives StrictMode re-mounts
  const send = async (q: string) => {
    const text = q.trim().slice(0, 300)
    if (text.length < 2 || pending) return
    setQuestion('')
    setPending(true)
    const idx = turns.length
    setTurns((t) => [...t, { q: text }])
    const settle = (patch: Partial<Turn>) => setTurns((t) => t.map((x, i) => (i === idx ? { ...x, ...patch } : x)))
    try {
      settle({ a: await extrasApi.ask(id, text) })
    } catch {
      settle({ error: 'Sorry, I could not answer right now. Please try again in a moment.' })
    } finally {
      setPending(false)
    }
  }

  // A question handed over from the Overview page (asked once)
  useEffect(() => {
    const q = handedOver.current
    if (!q) return
    handedOver.current = null
    setSp({}, { replace: true })
    send(q)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { if (turns.length) end.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }) }, [turns])

  return (
    <div className="space-y-5">
      <SectionHead title="Ask RepSync" sub="Ask about your reviews in English, Hindi or Hinglish. Answers come only from your collected data, and every number is checked against it." />
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_280px]">
        <section className="panel flex min-h-[460px] flex-col">
          <div className="flex-1 space-y-5 p-5" style={{ fontFamily: FONT_STACK }}>
            {!turns.length && <p className="py-16 text-center text-sm text-ink/45">Pick a suggested question or type your own below.</p>}
            {turns.map((t, i) => (
              <div key={i} className="space-y-2">
                <p className="ml-auto w-fit max-w-[80%] rounded-2xl rounded-br-md bg-gradient-to-b from-[#bd4468] to-[#8c1320] px-4 py-2 text-sm text-white">{t.q}</p>
                {!t.a && !t.error && <p className="text-sm text-ink/45">Thinking…</p>}
                {t.error && <p role="alert" className="text-sm text-neg">{t.error}</p>}
                {t.a && (
                  <div className="max-w-[92%] space-y-3 rounded-2xl rounded-bl-md border border-white/80 bg-white/70 p-4">
                    <p className="whitespace-pre-line text-[14.5px] leading-relaxed">{t.a.answer}</p>
                    {t.a.sources.length > 0 && (
                      <div className="flex flex-wrap gap-1.5">
                        {t.a.sources.map((s) => <span key={s} className="chip !text-[10px]">{SOURCE_LABEL[s] ?? `Review ${s.slice(0, 6)}`}</span>)}
                      </div>
                    )}
                    {t.a.chart && <div className="-mx-2"><AnswerChart id={id} chart={t.a.chart} /></div>}
                  </div>
                )}
              </div>
            ))}
            <div ref={end} />
          </div>
          <form className="flex gap-2 border-t border-white/70 p-4" onSubmit={(e) => { e.preventDefault(); send(question) }}>
            <input className="field" value={question} maxLength={300} onChange={(e) => setQuestion(e.target.value)} placeholder="Ask about your reviews…" aria-label="Your question" />
            <button className="btn btn-primary !px-5" disabled={pending || question.trim().length < 2}>Send</button>
          </form>
        </section>
        <aside className="panel h-fit space-y-2 p-5">
          <p className="label-overline mb-2">Try asking</p>
          {SUGGESTED.map((q) => (
            <button key={q} className="block w-full rounded-xl border border-white/80 bg-white/50 px-3 py-2 text-left text-sm hover:bg-white" onClick={() => send(q)}>{q}</button>
          ))}
          <p className="pt-2 text-xs leading-relaxed text-ink/45">RepSync has no search-rank data, so rank questions are answered with your rating, review velocity and complaint themes instead.</p>
        </aside>
      </div>
    </div>
  )
}
