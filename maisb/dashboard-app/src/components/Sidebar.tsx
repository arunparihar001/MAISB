import { NavLink } from 'react-router-dom'
import { GridIcon, RadarIcon, SettingsIcon, ShieldIcon, SparkIcon, TraceIcon, UsersIcon, KeyIcon } from './Icons'

const links = [
  { to: '/dashboard', label: 'Overview', icon: GridIcon },
  { to: '/analytics', label: 'Analytics', icon: RadarIcon },
  { to: '/boundary-protection', label: 'Boundary Protection', icon: ShieldIcon },
  { to: '/traces', label: 'Trace', icon: TraceIcon },
  { to: '/security', label: 'Security Events', icon: SparkIcon },
  { to: '/api-keys', label: 'API Keys', icon: KeyIcon },
  { to: '/team', label: 'Team', icon: UsersIcon },
  { to: '/reports', label: 'Reports', icon: GridIcon },
  { to: '/settings', label: 'Settings', icon: SettingsIcon },
  { to: '/billing', label: 'Billing', icon: GridIcon },
  { to: '/certify', label: 'Certify', icon: ShieldIcon },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <a className="brand" href="/dashboard" aria-label="MAISB dashboard">
        <span className="brand-mark"><SparkIcon /></span>
        <span>
          MAISB
          <small>Premium Boundary Security</small>
        </span>
      </a>
      <div className="sidebar-context">
        <span className="status-chip status-chip--live">Scanning boundary</span>
        <span className="status-chip">Enterprise dashboard</span>
      </div>
      <nav className="sidebar-nav">
        {links.map((link) => (
          <NavLink key={link.to} to={link.to} className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`.trim()}>
            <link.icon className="nav-icon" />
            <span>{link.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
