import { Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Topbar from './components/Topbar'
import { getApiKey } from './lib/auth'
import { isAppHost, isPublicHost } from './lib/config'
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

function RequireApiKey() {
  if (!getApiKey()) return <Navigate to="/login" replace />
  return <Outlet />
}

function AppShell() {
  const key = getApiKey()
  const masked = key ? `${key.slice(0, 10)}****${key.slice(-4)}` : ''
  return (
    <div className="app-shell">
      <Sidebar />
      <section className="content">
        <Topbar apiKeyMasked={masked} />
        <Outlet />
      </section>
    </div>
  )
}

function RootRoute() {
  const hostname = window.location.hostname
  if (isPublicHost(hostname)) return <Landing />
  if (isAppHost(hostname)) return <Navigate to={getApiKey() ? '/dashboard' : '/login'} replace />
  return <Navigate to={getApiKey() ? '/dashboard' : '/login'} replace />
}

function HostAwarePublicOnly({ children }: { children: React.ReactNode }) {
  const hostname = window.location.hostname
  const location = useLocation()
  if (isAppHost(hostname) && ['/', '/pricing', '/terms', '/privacy', '/refund'].includes(location.pathname)) {
    return <Navigate to={getApiKey() ? '/dashboard' : '/login'} replace />
  }
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<RootRoute />} />
      <Route path="/pricing" element={<HostAwarePublicOnly><Pricing /></HostAwarePublicOnly>} />
      <Route path="/terms" element={<HostAwarePublicOnly><Terms /></HostAwarePublicOnly>} />
      <Route path="/privacy" element={<HostAwarePublicOnly><Privacy /></HostAwarePublicOnly>} />
      <Route path="/refund" element={<HostAwarePublicOnly><Refund /></HostAwarePublicOnly>} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route element={<RequireApiKey />}>
        <Route element={<AppShell />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/api-keys" element={<ApiKeys />} />
          <Route path="/usage" element={<Usage />} />
          <Route path="/billing" element={<Billing />} />
          <Route path="/certify" element={<Certify />} />
          <Route path="/soc" element={<SocConsole />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
