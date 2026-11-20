import { useState } from 'react'
import { FixesPanel, ThemePanel } from '../../components/Panels'
import { SectionHead } from '../../components/Page'
import { useOutlet } from './OutletLayout'

export default function InsightsPage() {
  const { id } = useOutlet()
  const [theme, setTheme] = useState<string>()
  return (
    <div className="space-y-5">
      <SectionHead title="Insights" sub="What customers keep complaining about, grouped into themes, and the three fixes with the most evidence behind them." />
      <div className="grid gap-5 lg:grid-cols-2">
        <FixesPanel id={id} />
        <ThemePanel id={id} selected={theme} onSelect={setTheme} />
      </div>
    </div>
  )
}
