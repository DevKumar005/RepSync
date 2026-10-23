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
  `px-3 py-1.5 text-sm font-medium rounded-lg transition-all duration-200 ${
    isActive
      ? 'text-brand bg-brandsoft'
      : 'text-ink/50 hover:text-ink hover:bg-paper'
  }`

export default function App() {
  const mode = useMode()
  return (
    <>
      <header className="sticky top-0 z-40 border-b border-line/80 bg-surface/90 backdrop-blur-lg">
        <nav className="mx-auto flex max-w-6xl items-center gap-1.5 px-4 py-3">
          <NavLink to="/" className="mr-auto font-display text-[17px] font-bold tracking-tight text-ink flex items-center gap-1.5">
            <span className="inline-flex items-center justify-center h-7 w-7 rounded-lg bg-brand text-onbrand text-xs font-bold">R</span>
            Rep<span className="text-brand">Sync</span>
          </NavLink>
          {isMock && <span className="chip hidden sm:inline mr-2 !text-[10px]">Demo</span>}
          <NavLink to="/search" className={link}>Find outlet</NavLink>
          <NavLink to="/tone" className={link}>Reply tone</NavLink>
          <NavLink to="/pricing" className={link}>Pricing</NavLink>
          <button
            className="btn ml-2 !px-2 !py-1.5 !border-transparent"
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
          <Route path="*" element={
            <div className="text-center py-20 fade-in">
              <p className="text-5xl mb-4">🔍</p>
              <p className="text-ink/60 text-sm">Page not found. <NavLink className="text-brand underline underline-offset-4 hover:text-brand/70 transition-colors" to="/">Go home</NavLink></p>
            </div>
          } />
        </Routes>
      </main>

      {/* Prototype disclaimer — subtle, non-blocking */}
      <div
        role="note"
        aria-label="Prototype disclaimer"
        className="fixed bottom-3 right-3 z-50 max-w-[260px] rounded-xl border border-warn/20 bg-warnsoft/90 backdrop-blur-sm px-3 py-2 text-[11px] text-warn/90 shadow-sm"
      >
        <span className="font-semibold">Prototype</span> — data may be simulated. Not for production use.
      </div>
    </>
  )
}
