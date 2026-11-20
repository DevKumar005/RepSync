import { lazy, Suspense } from 'react'
import { NavLink, Route, Routes } from 'react-router-dom'
import { isMock } from './api/client'
import DotText from './components/DotText'
import { extrasEnabled } from './features/extras/flags'
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
const AskPage = lazy(() => import('./features/extras/AskPage'))
const CityMapPage = lazy(() => import('./features/extras/CityMapPage'))

const link = ({ isActive }: { isActive: boolean }) =>
  `whitespace-nowrap rounded-full px-2.5 py-1.5 text-[12.5px] sm:px-3.5 sm:text-[13.5px] transition-colors duration-200 ${
    isActive ? 'bg-white text-ink shadow-[0_1px_3px_rgba(58,25,39,.12)]' : 'text-ink/60 hover:text-ink hover:bg-white/60'
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
  return (
    <>
      <header className="sticky top-0 z-40 h-[var(--header-h)] border-b border-white/60 bg-[rgba(236,236,235,.72)] backdrop-blur-xl">
        <nav className="rs-container flex h-full items-center gap-0.5 sm:gap-1">
          <NavLink to="/" className="mr-auto flex items-center gap-2 text-[17px] font-semibold tracking-tight text-ink" aria-label="RepSync home">
            Rep<span className="text-brand"><DotText text="Sync" pitchX={4} radius={1.8} height="15px" /></span>
          </NavLink>
          {isMock && <span className="chip mr-2 hidden !text-[10px] sm:inline">Demo data</span>}
          <NavLink to="/search" className={link}>Find outlet</NavLink>
          <NavLink to="/tone" className={link}>Reply tone</NavLink>
          <NavLink to="/pricing" className={link}>Pricing</NavLink>
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
              <Route path="ask" element={<AskPage />} />
              <Route path="map" element={<CityMapPage />} />
            </>}
          </Route>
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>

      <div
        role="note"
        aria-label="Prototype disclaimer"
        className="fixed bottom-3 right-3 z-30 max-w-[240px] rounded-2xl border border-white/70 bg-white/70 px-3 py-2 text-[11px] text-ink/60 shadow-sm backdrop-blur-md"
      >
        <span className="font-semibold text-ink/80">Prototype</span> · data may be simulated. Not for production use.
      </div>
    </>
  )
}
