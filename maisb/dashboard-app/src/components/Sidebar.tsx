import { NavLink } from 'react-router-dom'

const links = [
  { to: '/dashboard', label: 'Overview' },
  { to: '/analytics', label: 'Analytics' },
  { to: '/boundary-protection', label: 'Boundary Protection' },
  { to: '/traces', label: 'Cross-Channel Trace' },
  { to: '/security', label: 'Security Events' },
  { to: '/api-keys', label: 'API Keys' },
  { to: '/team', label: 'Team' },
  { to: '/reports', label: 'Reports' },
  { to: '/settings', label: 'Settings' },
  { to: '/billing', label: 'Billing' },
  { to: '/certify', label: 'Certify' },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <a className="brand" href="/dashboard">
        <span>⬢</span> MAISB
      </a>
      <nav>
        {links.map((link) => (
          <NavLink key={link.to} to={link.to} className={({ isActive }) => (isActive ? 'active' : '')}>
            {link.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
