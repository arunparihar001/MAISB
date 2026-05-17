const links = [
  ['/dashboard', 'Dashboard'],
  ['/api-keys', 'API Keys'],
  ['/usage', 'Usage'],
  ['/billing', 'Billing'],
  ['/certify', 'Certify'],
  ['/soc', 'SOC'],
  ['/settings', 'Settings'],
]

export default function Sidebar() {
  const path = window.location.pathname
  return (
    <aside className="sidebar">
      <h2>MAISB</h2>
      {links.map(([href, label]) => (
        <a className={path === href ? 'active' : ''} href={href} key={href}>{label}</a>
      ))}
    </aside>
  )
}
