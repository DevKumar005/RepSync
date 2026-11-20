import { lazy, Suspense, useState } from 'react'
import { NavLink, Route, Routes } from 'react-router-dom'
import { isMock } from './api/client'
import DotText from './components/DotText'
import { extrasEnabled } from './features/extras/flags'
import { toggleMode, useMode } from './theme'
import Home from './pages/Home'

// Route-level code splitting keeps the first load small (charts and image export load on demand)
const Search = lazy(() => import('./pages/Search'))
const TonePage = lazy(() => import('./pages/Tone'))
const Pricing = lazy(() => import('./pages/Pricing'))
const OutletLayout = lazy(() => import('./pages/outlet/OutletLayout'))
const Overview = lazy(() => import('./pages/outlet/Overview'))
const ReviewsPage = lazy(() => import('./pages/outlet/ReviewsPage'))
const RepliesPage = lazy(() => import('./pages/outlet/RepliesPage'))
const InsightsPage = lazy(() => import('./pages/outlet/InsightsPage'))
const ActivityPage = lazy(() => import('./pages/outlet/ActivityPage'))
const CompetitorsPage = lazy(() => import('./features/extras/CompetitorsPage'))
const VelocityPage = lazy(() => import('./features/extras/VelocityChart'))
const PostersPage = lazy(() => import('./features/extras/PostersPage'))
const CityMapPage = lazy(() => import('./features/extras/CityMapPage'))

const link = ({ isActive }: { isActive: boolean }) =>
  `whitespace-nowrap rounded-full px-2.5 py-1.5 text-[12.5px] sm:px-3.5 sm:text-[13.5px] transition-colors duration-200 ${
    isActive ? 'pill-active' : 'pill-idle'
  }`

const PageFallback = () => (
  <div className="rs-container space-y-4 py-10">
    <div className="skeleton h-9 w-72" />
    <div className="skeleton h-40 w-full" />
  </div>
)

const NotFound = () => (
  <div className="mx-auto max-w-xl px-4 py-24 text-center">
    <span className="inline-block text-brand"><DotText text="404" radius={1.9} height="40px" /></span>
    <p className="rs-copy mt-4">This page does not exist. <NavLink className="text-brand underline underline-offset-4" to="/">Go home</NavLink></p>
  </div>
)

export default function App() {
  const mode = useMode()
  const [noteHidden, setNoteHidden] = useState(() => { try { return localStorage.getItem('hide-prototype-note') === '1' } catch { return false } })
  const hideNote = () => { setNoteHidden(true); try { localStorage.setItem('hide-prototype-note', '1') } catch { } }
  return (
    <>
      <header className="sticky top-0 z-40 h-[var(--header-h)] border-b border-ink/[.07] bg-[var(--header-bg)] backdrop-blur-xl">
        <nav className="rs-container flex h-full items-center gap-0.5 sm:gap-1">
          <NavLink to="/" className="mr-auto flex items-center gap-2 text-[17px] font-semibold tracking-tight text-ink" aria-label="RepSync home">
            Rep<span className="text-brand"><DotText text="Sync" pitchX={4} radius={1.8} height="15px" /></span>
          </NavLink>
          {isMock && <span className="chip mr-2 hidden !text-[10px] sm:inline">Demo data</span>}
          <NavLink to="/search" className={link}>Find outlet</NavLink>
          <NavLink to="/tone" className={link}>Reply tone</NavLink>
          <NavLink to="/pricing" className={link}>Pricing</NavLink>
          <button
            className="ml-1 flex h-8 w-8 items-center justify-center rounded-full text-ink/65 hover:bg-ink/[.06] hover:text-ink"
            onClick={toggleMode}
            aria-label={mode === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            aria-pressed={mode === 'dark'}
          >
            {mode === 'dark' ? (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></svg>
            ) : (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" /></svg>
            )}
          </button>
        </nav>
      </header>

      <Suspense fallback={<PageFallback />}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/search" element={<Search />} />
          <Route path="/tone" element={<TonePage />} />
          <Route path="/pricing" element={<Pricing />} />
          <Route path="/outlet/:id" element={<OutletLayout />}>
            <Route index element={<Overview />} />
            <Route path="reviews" element={<ReviewsPage />} />
            <Route path="replies" element={<RepliesPage />} />
            <Route path="insights" element={<InsightsPage />} />
            <Route path="activity" element={<ActivityPage />} />
            {extrasEnabled && <>
              <Route path="competitors" element={<CompetitorsPage />} />
              <Route path="velocity" element={<VelocityPage />} />
              <Route path="posters" element={<PostersPage />} />
              <Route path="map" element={<CityMapPage />} />
            </>}
          </Route>
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>

      {!noteHidden && <div
        role="note"
        aria-label="Prototype disclaimer"
        className="fixed bottom-3 left-3 z-30 hidden sm:block max-w-[230px] rounded-2xl border border-ink/[.08] bg-[var(--glass-bg)] px-3 py-2 text-[11px] text-ink/60 shadow-sm backdrop-blur-md"
      >
        <span className="font-semibold text-ink/80">Prototype</span> · data may be simulated.
        <button className="ml-1.5 align-middle text-ink/45 hover:text-ink" onClick={hideNote} aria-label="Dismiss prototype note">
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" aria-hidden="true"><path d="M18 6 6 18M6 6l12 12" /></svg>
        </button>
      </div>}
    </>
  )
}
