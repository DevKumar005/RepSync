import { useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ThemePanel } from '../../components/Panels'
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
  if (chart === 'velocity' && vel.data) return <VelocityView data={vel.data} height={180} />
  if (chart === 'gap' && gap.data?.status === 'done') return <GapGrid result={gap.data} />
  return null
}

const ChatIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M21 12a8 8 0 0 1-11.6 7.1L4 20.5l1.4-4.9A8 8 0 1 1 21 12Z" /><path d="M8.5 12h.01M12 12h.01M15.5 12h.01" />
  </svg>
)

interface Turn { q: string; a?: AskResponse; error?: string }

interface Props {
  id: string
  open: boolean
  onOpenChange: (open: boolean) => void
  /** A question handed over from elsewhere (for example the Overview ask box) */
  seed: string | null
  onSeedUsed: () => void
}

/** Floating "Ask RepSync" assistant, available on every outlet page. */
export default function ChatWidget({ id, open, onOpenChange, seed, onSeedUsed }: Props) {
  const [question, setQuestion] = useState('')
  const [turns, setTurns] = useState<Turn[]>([])
  const [pending, setPending] = useState(false)
  const latest = useRef<HTMLDivElement>(null)
  const input = useRef<HTMLInputElement>(null)

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

  useEffect(() => { setTurns([]) }, [id])
  useEffect(() => { if (seed && open) { onSeedUsed(); send(seed) } }, [seed, open]) // eslint-disable-line react-hooks/exhaustive-deps
  // Keep the start of the newest exchange in view, so long answers with charts are read from the top
  useEffect(() => { if (open) latest.current?.scrollIntoView({ block: 'start' }) }, [turns, open])
  useEffect(() => {
    if (!open) return
    input.current?.focus()
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onOpenChange(false) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onOpenChange])

  return (
    <>
      {open && (
        <section
          role="dialog"
          aria-label="Ask RepSync"
          className="panel fixed bottom-24 right-4 z-50 flex h-[min(620px,calc(100svh-140px))] w-[min(420px,calc(100vw-32px))] flex-col overflow-hidden slide-up"
        >
          <header className="tile tile-speed !rounded-none !border-0 flex items-center gap-3 px-5 py-4">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white/15"><ChatIcon /></span>
            <div className="mr-auto min-w-0">
              <h2 className="text-[15px] font-semibold leading-tight">Ask RepSync</h2>
              <p className="text-[11.5px] text-white/75">Answers use only your review data</p>
            </div>
            <button className="rounded-full p-1.5 text-white/80 hover:bg-white/15 hover:text-white" onClick={() => onOpenChange(false)} aria-label="Close chat">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true"><path d="M18 6 6 18M6 6l12 12" /></svg>
            </button>
          </header>

          <div className="flex-1 space-y-4 overflow-y-auto px-4 py-4" style={{ fontFamily: FONT_STACK }}>
            {!turns.length && (
              <div className="space-y-2">
                <p className="text-sm text-ink/55">Ask in English, Hindi or Hinglish. For example:</p>
                {SUGGESTED.map((q) => (
                  <button key={q} className="block w-full rounded-xl border border-ink/[.08] bg-ink/[.025] px-3 py-2 text-left text-sm hover:bg-ink/[.05]" onClick={() => send(q)}>
                    {q}
                  </button>
                ))}
              </div>
            )}
            {turns.map((t, i) => (
              <div key={i} ref={i === turns.length - 1 ? latest : undefined} className="scroll-mt-3 space-y-2">
                <p className="ml-auto w-fit max-w-[85%] rounded-2xl rounded-br-md bg-gradient-to-b from-[#3a5cc0] to-[#1b2f6b] px-3.5 py-2 text-sm text-white">{t.q}</p>
                {!t.a && !t.error && <p className="text-sm text-ink/45">Thinking…</p>}
                {t.error && <p role="alert" className="text-sm text-neg">{t.error}</p>}
                {t.a && (
                  <div className="max-w-[95%] space-y-2.5 rounded-2xl rounded-bl-md border border-ink/[.08] bg-ink/[.03] p-3.5">
                    <p className="whitespace-pre-line text-[14px] leading-relaxed">{t.a.answer}</p>
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
          </div>

          <form className="flex gap-2 border-t border-ink/[.07] p-3" onSubmit={(e) => { e.preventDefault(); send(question) }}>
            <input ref={input} className="field !py-2" value={question} maxLength={300} onChange={(e) => setQuestion(e.target.value)} placeholder="Ask about your reviews…" aria-label="Your question" />
            <button className="btn btn-primary !px-4" disabled={pending || question.trim().length < 2}>Send</button>
          </form>
        </section>
      )}

      <button
        className="fixed bottom-4 right-4 z-50 flex h-14 items-center gap-2 rounded-full bg-gradient-to-b from-[#3a5cc0] to-[#1b2f6b] px-5 text-white shadow-[0_10px_30px_rgba(27,47,107,.35)] transition-transform duration-200 hover:-translate-y-0.5"
        onClick={() => onOpenChange(!open)}
        aria-expanded={open}
        aria-label={open ? 'Close Ask RepSync' : 'Open Ask RepSync'}
      >
        {open
          ? <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true"><path d="M18 6 6 18M6 6l12 12" /></svg>
          : <ChatIcon />}
        <span className="text-sm font-medium">{open ? 'Close' : 'Ask RepSync'}</span>
      </button>
    </>
  )
}
