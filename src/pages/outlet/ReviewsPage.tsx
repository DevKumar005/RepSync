import { useState } from 'react'
import { ReviewFeed, ThemePanel } from '../../components/Panels'
import { SectionHead } from '../../components/Page'
import { useOutlet } from './OutletLayout'

export default function ReviewsPage() {
  const { id } = useOutlet()
  const [theme, setTheme] = useState<string>()
  return (
    <div className="space-y-5">
      <SectionHead title="Reviews" sub="Every collected review from every platform. Click a complaint theme to filter the feed." />
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.6fr)]">
        <div className="lg:sticky lg:top-[calc(var(--header-h)+16px)] lg:self-start"><ThemePanel id={id} selected={theme} onSelect={setTheme} /></div>
        <ReviewFeed id={id} theme={theme} />
      </div>
    </div>
  )
}
