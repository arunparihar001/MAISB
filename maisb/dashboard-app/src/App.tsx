import type { ReactElement } from 'react'
import { Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Topbar from './components/Topbar'
import { getApiKey } from './lib/auth'
import { isAppHost } from './lib/config'
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
import VerifyEmail from './pages/VerifyEmail'

function RequireApiKey({ children }: { children: ReactElement }) {
  const location = useLocation()
  if (!getApiKey() && location.pathname !== '/api-keys') return <Navigate to="/login" replace />
  return children
}

function AppLayout() {
  return (
    <div className="layout">
      <Sidebar />
      <div className="content">
        <Topbar />
        <Outlet />
      </div>
    </div>
  )
}

function HostHome() {
  if (isAppHost()) return <Navigate to={getApiKey() ? '/dashboard' : '/login'} replace />
  return <Landing />
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HostHome />} />
      <Route path="/pricing" element={<Pricing />} />
      <Route path="/terms" element={<Terms />} />
      <Route path="/privacy" element={<Privacy />} />
      <Route path="/refund" element={<Refund />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/verify-email" element={<VerifyEmail />} />
      <Route
        element={
          <RequireApiKey>
            <AppLayout />
          </RequireApiKey>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/api-keys" element={<ApiKeys />} />
        <Route path="/usage" element={<Usage />} />
        <Route path="/billing" element={<Billing />} />
        <Route path="/certify" element={<Certify />} />
        <Route path="/soc" element={<SocConsole />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
