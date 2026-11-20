import { ActivityLog } from '../../components/Panels'
import { SectionHead } from '../../components/Page'
import { useOutlet } from './OutletLayout'

export default function ActivityPage() {
  const { id, live, syncing } = useOutlet()
  return (
    <div className="space-y-5">
      <SectionHead title="Activity" sub="Every TinyFish Search, Fetch and Agent call made for this outlet, with timing, items found and cache hits." />
      <div className="max-w-3xl"><ActivityLog id={id} live={live} syncing={syncing} /></div>
    </div>
  )
}
