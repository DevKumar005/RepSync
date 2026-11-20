import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { api } from '../api/client'
import DotText from './DotText'

/** Page masthead in the stage typography, with an optional LED-dot accent word. */
export function PageTitle({ before, dots, after, sub, eyebrow, action }: {
  before?: string; dots?: string; after?: string; sub?: ReactNode; eyebrow?: string; action?: ReactNode
}) {
  return (
    <header className="flex flex-wrap items-end gap-4 fade-in">
      <div className="mr-auto min-w-0 max-w-3xl space-y-2">
        {eyebrow && <p className="label-overline">{eyebrow}</p>}
        <h1 className="rs-title text-[clamp(26px,3.2vw,42px)]">
          {before}
          {dots && <span className="rs-dot-accent" style={{ marginLeft: before ? '.3em' : 0, marginRight: after ? '.3em' : 0 }}><DotText text={dots} pitchX={4} radius={1.8} height=".74em" /></span>}
          {after}
        </h1>
        {sub && <p className="rs-copy text-[15px] max-w-2xl">{sub}</p>}
      </div>
      {action}
    </header>
  )
}

/** Opens the seeded demo outlet, then a specific outlet tab. */
export function useOpenDemo() {
  const nav = useNavigate()
  return useMutation({
    mutationFn: ({ key = 'restaurant' }: { key?: 'restaurant' | 'clinic'; tab?: string }) => api.demoOutlet(key),
    onSuccess: (o, v) => nav(`/outlet/${o.id}${v.tab ? `/${v.tab}` : ''}`),
  })
}

export const Empty = ({ children }: { children: ReactNode }) => (
  <p className="px-5 py-8 text-center text-sm text-ink/45 leading-relaxed">{children}</p>
)

/** Title row for a tool page inside an outlet. */
export function SectionHead({ title, sub, action }: { title: string; sub?: ReactNode; action?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-end gap-3 fade-in">
      <div className="mr-auto max-w-3xl space-y-1">
        <h2 className="rs-title text-[clamp(22px,2.2vw,30px)]">{title}</h2>
        {sub && <p className="rs-copy text-[14.5px]">{sub}</p>}
      </div>
      {action}
    </div>
  )
}
