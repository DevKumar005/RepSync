import { NavLink, Route, Routes } from 'react-router-dom'
import { isMock } from './api/client'
import { toggleMode, useMode } from './theme'
import Dashboard from './pages/Dashboard'
import Home from './pages/Home'
import Pricing from './pages/Pricing'
import Search from './pages/Search'
import TonePage from './pages/Tone'

// Active nav link styles — pill highlight for current route
const link = ({ isActive }: { isActive: boolean }) =>
  `px-2.5 py-1 text-sm font-medium rounded-md transition-colors duration-150 ${
    isActive
      ? 'text-brand bg-brandsoft'
      : 'text-ink/60 hover:text-ink hover:bg-paper'
  }`

export default function App() {
  const mode = useMode()
  return (
    <>
      <header className="border-b border-line bg-surface">
        <nav className="mx-auto flex max-w-6xl items-center gap-1 px-4 py-3">
          <NavLink to="/" className="mr-auto font-display text-[17px] font-bold tracking-tight text-ink">
            Rep<span className="text-brand">Sync</span>
          </NavLink>
          {isMock && <span className="chip hidden sm:inline mr-2">Demo</span>}
          <NavLink to="/search" className={link}>Find outlet</NavLink>
          <NavLink to="/tone" className={link}>Reply tone</NavLink>
          <NavLink to="/pricing" className={link}>Pricing</NavLink>
          <button
            className="btn ml-2 !px-2 !py-1.5"
            aria-label={mode === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            aria-pressed={mode === 'dark'}
            onClick={toggleMode}
          >
            {mode === 'dark' ? (
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>
            )}
          </button>
        </nav>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/search" element={<Search />} />
          <Route path="/outlet/:id" element={<Dashboard />} />
          <Route path="/tone" element={<TonePage />} />
          <Route path="/pricing" element={<Pricing />} />
          <Route path="*" element={<p className="text-ink/60 text-sm">Page not found. <NavLink className="text-brand underline underline-offset-4" to="/">Go home</NavLink></p>} />
        </Routes>
      </main>

      {/* Prototype disclaimer — always visible, non-blocking */}
      <div
        role="note"
        aria-label="Prototype disclaimer"
        className="fixed bottom-4 right-4 z-50 max-w-[280px] rounded-xl border border-warn/40 bg-warnsoft px-3.5 py-2.5 text-xs text-warn shadow-sm"
      >
        <span className="font-semibold">Prototype</span> — data may be simulated or inaccurate. Not for production use.
      </div>
    </>
  )
}
