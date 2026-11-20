import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { ThemePanel } from '../../components/Panels'
import { extrasApi } from './api'
import { GapGrid } from './CompetitorsPage'
import type { AskResponse } from './types'
import { FONT_STACK } from './ui'
import { VelocityView } from './VelocityChart'

const SUGGESTED = ['What should I fix first?', 'How do I compare with competitors?', 'Mera rank kyun gira?']
const SOURCE_LABEL: Record<string, string> = {
  summary: 'Summary', themes: 'Themes', fixes: 'Top fixes', velocity: 'Review velocity', competitor_gaps: 'Competitor gaps',
}

function AnswerChart({ id, chart }: { id: string; chart: AskResponse['chart'] }) {
  const vel = useQuery({ queryKey: ['extras', 'velocity', id], queryFn: () => extrasApi.velocity(id), enabled: chart === 'velocity' })
  const gap = useQuery({ queryKey: ['extras', 'competitors', id], queryFn: () => extrasApi.competitors(id), enabled: chart === 'gap' })
  if (chart === 'themes') return <ThemePanel id={id} onSelect={() => {}} />
  if (chart === 'velocity' && vel.data) return <VelocityView data={vel.data} height={200} />
  if (chart === 'gap' && gap.data?.status === 'done') return <GapGrid result={gap.data} />
  return null
}

interface Turn { q: string; a?: AskResponse; error?: string }

export default function AskDrawer({ id }: { id: string }) {
  const [open, setOpen] = useState(false)
  const [question, setQuestion] = useState('')
  const [turns, setTurns] = useState<Turn[]>([])
  const end = useRef<HTMLDivElement>(null)

  useEffect(() => { setTurns([]) }, [id])
  useEffect(() => { end.current?.scrollIntoView({ behavior: 'smooth' }) }, [turns])
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open])

  const ask = useMutation({
    mutationFn: (q: string) => extrasApi.ask(id, q),
    onMutate: (q) => setTurns((t) => [...t, { q }]),
    onSuccess: (a) => setTurns((t) => t.map((x, i) => (i === t.length - 1 ? { ...x, a } : x))),
    onError: () => setTurns((t) => t.map((x, i) => (i === t.length - 1 ? { ...x, error: 'Sorry, I could not answer right now. Please try again in a moment.' } : x))),
  })
  const send = (q: string) => {
    const text = q.trim().slice(0, 300)
    if (text.length < 2 || ask.isPending) return
    setQuestion('')
    ask.mutate(text)
  }

  return (
    <>
      <button className="btn btn-primary ml-auto shrink-0 !py-1.5 !text-[13px]" onClick={() => setOpen(true)} aria-haspopup="dialog">
        Ask RepSync
      </button>
      {open && (
        <div className="fixed inset-0 z-[60] flex justify-end bg-black/30" onClick={() => setOpen(false)}>
          <aside
            role="dialog"
            aria-label="Ask RepSync"
            className="slide-up flex h-full w-full max-w-md flex-col border-l border-line bg-surface shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <header className="flex items-center justify-between border-b border-line px-5 py-4">
              <div>
                <h2 className="font-semibold">Ask RepSync</h2>
                <p className="text-xs text-ink/45">Answers come only from your collected review data.</p>
              </div>
              <button className="btn !px-2 !py-1" onClick={() => setOpen(false)} aria-label="Close">✕</button>
            </header>
            <div className="flex-1 space-y-5 overflow-y-auto px-5 py-4" style={{ fontFamily: FONT_STACK }}>
              {!turns.length && (
                <div className="space-y-2">
                  <p className="text-sm text-ink/55">Try asking:</p>
                  {SUGGESTED.map((q) => (
                    <button key={q} className="block w-full rounded-xl border border-line px-3 py-2 text-left text-sm hover:bg-paper" onClick={() => send(q)}>
                      {q}
                    </button>
                  ))}
                  <p className="pt-2 text-xs text-ink/40">You can ask in English, Hindi or Hinglish.</p>
                </div>
              )}
              {turns.map((t, i) => (
                <div key={i} className="space-y-2">
                  <p className="ml-auto w-fit max-w-[85%] rounded-2xl rounded-br-sm bg-brand px-3 py-2 text-sm text-onbrand">{t.q}</p>
                  {!t.a && !t.error && <p className="text-sm text-ink/45">Thinking…</p>}
                  {t.error && <p role="alert" className="text-sm text-neg">{t.error}</p>}
                  {t.a && (
                    <div className="space-y-2 rounded-2xl rounded-bl-sm border border-line bg-paper p-3">
                      <p className="text-sm leading-relaxed whitespace-pre-line">{t.a.answer}</p>
                      {t.a.sources.length > 0 && (
                        <div className="flex flex-wrap gap-1.5">
                          {t.a.sources.map((s) => (
                            <span key={s} className="chip !text-[10px]">{SOURCE_LABEL[s] ?? `Review ${s.slice(0, 6)}`}</span>
                          ))}
                        </div>
                      )}
                      {t.a.chart && <div className="-mx-3 pt-1"><AnswerChart id={id} chart={t.a.chart} /></div>}
                    </div>
                  )}
                </div>
              ))}
              <div ref={end} />
            </div>
            <form className="flex gap-2 border-t border-line px-5 py-4" onSubmit={(e) => { e.preventDefault(); send(question) }}>
              <input
                className="field"
                value={question}
                maxLength={300}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask about your reviews…"
                aria-label="Your question"
              />
              <button className="btn btn-primary" disabled={ask.isPending || question.trim().length < 2}>Send</button>
            </form>
          </aside>
        </div>
      )}
    </>
  )
}
