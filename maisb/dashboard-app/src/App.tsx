import { BrowserRouter, Navigate, Outlet, Route, Routes } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Topbar from './components/Topbar'
import { getApiKey } from './lib/auth'
import ApiKeys from './pages/ApiKeys'
import Billing from './pages/Billing'
import Certify from './pages/Certify'
import Dashboard from './pages/Dashboard'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Pricing from './pages/Pricing'
import Privacy from './pages/Privacy'
import Refund from './pages/Refund'
import Settings from './pages/Settings'
import Signup from './pages/Signup'
import SocConsole from './pages/SocConsole'
import Terms from './pages/Terms'
import Usage from './pages/Usage'

const host = window.location.hostname.toLowerCase()
const isPublicHost = host === 'maisb.app' || host === 'www.maisb.app'
const isAppHost = host === 'app.maisb.app' || host === 'localhost' || host === '127.0.0.1'

function RootRedirect() {
  if (isPublicHost) return <Navigate to="/" replace />
  return <Navigate to={getApiKey() ? '/dashboard' : '/login'} replace />
}

function RequireApiKey() {
  return getApiKey() ? <Outlet /> : <Navigate to="/login" replace />
}

function AppLayout() {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="app-main">
        <Topbar />
        <main className="app-content"><Outlet /></main>
      </div>
    </div>
  )
}

function PublicRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/pricing" element={<Pricing />} />
      <Route path="/terms" element={<Terms />} />
      <Route path="/privacy" element={<Privacy />} />
      <Route path="/refund" element={<Refund />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<RootRedirect />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/pricing" element={<Pricing />} />
      <Route path="/terms" element={<Terms />} />
      <Route path="/privacy" element={<Privacy />} />
      <Route path="/refund" element={<Refund />} />
      <Route element={<RequireApiKey />}>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/api-keys" element={<ApiKeys />} />
          <Route path="/usage" element={<Usage />} />
          <Route path="/billing" element={<Billing />} />
          <Route path="/certify" element={<Certify />} />
          <Route path="/soc" element={<SocConsole />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to={getApiKey() ? '/dashboard' : '/login'} replace />} />
    </Routes>
  )
}

export default function App() {
  const renderPublic = isPublicHost || !isAppHost
  return <BrowserRouter>{renderPublic ? <PublicRoutes /> : <AppRoutes />}</BrowserRouter>
}
