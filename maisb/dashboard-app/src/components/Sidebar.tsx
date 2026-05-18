import { NavLink } from 'react-router-dom'

const links = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/api-keys', label: 'API Keys' },
  { to: '/usage', label: 'Usage' },
  { to: '/billing', label: 'Billing' },
  { to: '/certify', label: 'Certify' },
  { to: '/soc', label: 'SOC Console' },
  { to: '/settings', label: 'Settings' },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <h2>MAISB</h2>
      <nav>
        {links.map((link) => (
          <NavLink key={link.to} to={link.to} className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
            {link.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
