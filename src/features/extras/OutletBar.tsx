import { NavLink, useLocation } from 'react-router-dom'
import AskDrawer from './AskDrawer'

const tab = ({ isActive }: { isActive: boolean }) =>
  `px-3 py-1.5 text-[13px] font-medium rounded-lg whitespace-nowrap transition-colors ${
    isActive ? 'text-brand bg-brandsoft' : 'text-ink/55 hover:text-ink hover:bg-paper'
  }`

/** Outlet-level navigation for the extras pages. Renders only on /outlet/:id routes. */
export default function OutletBar() {
  const m = useLocation().pathname.match(/^\/outlet\/([^/]+)/)
  if (!m) return null
  const base = `/outlet/${m[1]}`
  return (
    <nav aria-label="Outlet tools" className="mb-6 flex items-center gap-1 overflow-x-auto rounded-xl border border-line bg-surface p-1">
      <NavLink end to={base} className={tab}>Dashboard</NavLink>
      <NavLink to={`${base}/competitors`} className={tab}>Competitors</NavLink>
      <NavLink to={`${base}/posters`} className={tab}>Posters</NavLink>
      <NavLink to={`${base}/map`} className={tab}>City map</NavLink>
      <AskDrawer id={m[1]} />
    </nav>
  )
}
