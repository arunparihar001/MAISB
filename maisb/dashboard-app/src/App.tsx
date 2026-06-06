import type { ReactElement } from 'react'
import { Navigate, Outlet, Route, Routes } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Topbar from './components/Topbar'
import { getApiKeyExists, getSelectedPlan, getSessionToken, getStoredProfile } from './lib/auth'
import Analytics from './pages/Analytics'
import ApiKeys from './pages/ApiKeys'
import Billing from './pages/Billing'
import BoundaryProtection from './pages/BoundaryProtection'
import Certify from './pages/Certify'
import Dashboard from './pages/Dashboard'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Pricing from './pages/Pricing'
import ForgotPassword from './pages/ForgotPassword'
import Privacy from './pages/Privacy'
import Refund from './pages/Refund'
import Reports from './pages/Reports'
import SecurityEvents from './pages/Security'
import Developers from './pages/Developers'
import SecurityOverview from './pages/SecurityOverview'
import SelectPlan from './pages/SelectPlan'
import Settings from './pages/Settings'
import Signup from './pages/Signup'
import ResetPassword from './pages/ResetPassword'
import Team from './pages/Team'
import Terms from './pages/Terms'
import Traces from './pages/Traces'
import VerifyEmail from './pages/VerifyEmail'
import DocsHome from './pages/docs/DocsHome'
import DocsApi from './pages/docs/DocsApi'
import DocsSdk from './pages/docs/DocsSdk'
import DocsExamples from './pages/docs/DocsExamples'

type Gate = 'ok' | 'login' | 'verify-email' | 'select-plan' | 'api-keys'

function resolveGate(): Gate {
  const token = getSessionToken()
  if (!token) return 'login'

  const profile = getStoredProfile()
  if (!profile?.verified) return 'verify-email'

  const selectedPlan = getSelectedPlan()
  if (!selectedPlan) return 'select-plan'

  if (selectedPlan === 'free' && !getApiKeyExists()) {
    return 'api-keys'
  }

  return 'ok'
}

function redirectForGate(gate: Gate): string {
  if (gate === 'login') return '/login'
  if (gate === 'verify-email') return '/verify-email'
  if (gate === 'select-plan') return '/select-plan'
  if (gate === 'api-keys') return '/api-keys'
  return '/dashboard'
}

function RequireAuth({ children }: { children: ReactElement }) {
  const gate = resolveGate()
  if (gate === 'login') return <Navigate to="/login" replace />
  return children
}

function RequireVerified({ children }: { children: ReactElement }) {
  const gate = resolveGate()
  if (gate === 'login') return <Navigate to="/login" replace />
  if (gate === 'verify-email') return <Navigate to="/verify-email" replace />
  return children
}

function RequireReady({ children }: { children: ReactElement }) {
  const gate = resolveGate()
  if (gate !== 'ok') return <Navigate to={redirectForGate(gate)} replace />
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

function AuthEntry({ children }: { children: ReactElement }) {
  const gate = resolveGate()
  if (gate === 'ok') return <Navigate to="/dashboard" replace />
  if (gate === 'select-plan') return <Navigate to="/select-plan" replace />
  if (gate === 'api-keys') return <Navigate to="/api-keys" replace />
  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/pricing" element={<Pricing />} />
      <Route path="/developers" element={<Developers />} />
      <Route path="/security" element={<SecurityOverview />} />
      <Route path="/terms" element={<Terms />} />
      <Route path="/privacy" element={<Privacy />} />
      <Route path="/refund" element={<Refund />} />
      <Route path="/docs" element={<DocsHome />} />
      <Route path="/docs/api" element={<DocsApi />} />
      <Route path="/docs/sdk" element={<DocsSdk />} />
      <Route path="/docs/examples" element={<DocsExamples />} />

      <Route path="/signup" element={<AuthEntry><Signup /></AuthEntry>} />
      <Route path="/verify-email" element={<VerifyEmail />} />
      <Route path="/login" element={<AuthEntry><Login /></AuthEntry>} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />

      <Route path="/select-plan" element={<RequireVerified><SelectPlan /></RequireVerified>} />
      <Route path="/api-keys" element={<RequireVerified><ApiKeys /></RequireVerified>} />

      <Route
        element={
          <RequireReady>
            <AppLayout />
          </RequireReady>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/boundary-protection" element={<BoundaryProtection />} />
        <Route path="/traces" element={<Traces />} />
        <Route path="/security-events" element={<SecurityEvents />} />
        <Route path="/team" element={<Team />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/billing" element={<Billing />} />
        <Route path="/certify" element={<Certify />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
