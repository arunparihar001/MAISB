import './styles.css'
import Sidebar from './components/Sidebar'
import Topbar from './components/Topbar'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Dashboard from './pages/Dashboard'
import ApiKeys from './pages/ApiKeys'
import Usage from './pages/Usage'
import Billing from './pages/Billing'
import Certify from './pages/Certify'
import SocConsole from './pages/SocConsole'
import Settings from './pages/Settings'
import Pricing from './pages/Pricing'
import Terms from './pages/Terms'
import Privacy from './pages/Privacy'
import Refund from './pages/Refund'
import { APP_HOSTNAMES, MARKETING_HOSTNAMES } from './lib/config'

function appPage(path: string) {
  if (path === '/signup') return <Signup />
  if (path === '/login') return <Login />
  if (path === '/api-keys') return <ApiKeys />
  if (path === '/usage') return <Usage />
  if (path === '/billing') return <Billing />
  if (path === '/certify') return <Certify />
  if (path === '/soc') return <SocConsole />
  if (path === '/settings') return <Settings />
  return <Dashboard />
}

function marketingPage(path: string) {
  if (path === '/pricing') return <Pricing />
  if (path === '/terms') return <Terms />
  if (path === '/privacy') return <Privacy />
  if (path === '/refund') return <Refund />
  return <Landing />
}

export default function App() {
  const host = window.location.hostname
  const path = window.location.pathname

  if (MARKETING_HOSTNAMES.has(host)) return marketingPage(path)

  if (APP_HOSTNAMES.has(host)) {
    const isAuth = path === '/login' || path === '/signup'
    return isAuth ? appPage(path) : <div className="layout"><Sidebar /><div className="content"><Topbar />{appPage(path)}</div></div>
  }

  return marketingPage(path)
}
