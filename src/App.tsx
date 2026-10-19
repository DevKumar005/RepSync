import { NavLink, Route, Routes } from 'react-router-dom'
import { isMock } from './api/client'
import { toggleMode, useMode } from './theme'
import Dashboard from './pages/Dashboard'
import Pricing from './pages/Pricing'
import Search from './pages/Search'
import TonePage from './pages/Tone'

const link = ({ isActive }: { isActive: boolean }) => `px-2 py-1 text-sm font-semibold ${isActive ? 'text-brand underline underline-offset-8' : 'text-ink/70'}`

export default function App() {
  const mode = useMode()
  return (
    <>
      <header className="border-b border-line bg-surface">
        <nav className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-3">
          <NavLink to="/" className="mr-auto font-display text-xl font-bold text-brand">RepSync</NavLink>
          {isMock && <span className="chip hidden sm:inline">Demo data</span>}
          <NavLink to="/" end className={link}>Find outlet</NavLink>
          <NavLink to="/tone" className={link}>Reply tone</NavLink>
          <NavLink to="/pricing" className={link}>Pricing</NavLink>
          <button className="btn !py-1" aria-pressed={mode === 'dark'} onClick={toggleMode}>{mode === 'dark' ? 'Light mode' : 'Dark mode'}</button>
        </nav>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">
        <Routes>
          <Route path="/" element={<Search />} />
          <Route path="/outlet/:id" element={<Dashboard />} />
          <Route path="/tone" element={<TonePage />} />
          <Route path="/pricing" element={<Pricing />} />
          <Route path="*" element={<p>Page not found. <NavLink className="underline" to="/">Go to search</NavLink></p>} />
        </Routes>
      </main>
    </>
  )
}
