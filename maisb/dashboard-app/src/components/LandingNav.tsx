import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Button from './Button'

type NavLink =
  | { label: string; href: string; external?: boolean }
  | { label: string; to: string }

const NAV_LINKS: NavLink[] = [
  { label: 'Product', href: '#features' },
  { label: 'Developers', to: '/developers' },
  { label: 'Security', to: '/security' },
  { label: 'Pricing', to: '/pricing' },
  { label: 'Docs', to: '/docs' },
]

export default function LandingNav() {
  const [mobileOpen, setMobileOpen] = useState(false)

  useEffect(() => {
    if (!mobileOpen) return
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setMobileOpen(false)
    }
    document.addEventListener('keydown', onKey)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
    }
  }, [mobileOpen])

  const closeMobile = () => setMobileOpen(false)

  return (
    <header className="landing-nav">
      <div className="landing-nav__inner">
        <Link to="/" className="landing-brand" onClick={closeMobile}>
          <span className="landing-brand__mark" aria-hidden="true">
            <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="1" y="1" width="30" height="30" rx="9" stroke="currentColor" strokeWidth="1.2" opacity="0.35" />
              <path d="M8 22V10l8 6 8-6v12" stroke="url(#brandGrad)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              <defs>
                <linearGradient id="brandGrad" x1="8" y1="10" x2="24" y2="22" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#60a5fa" />
                  <stop offset="1" stopColor="#34d399" />
                </linearGradient>
              </defs>
            </svg>
          </span>
          <span className="landing-brand__text">
            <strong>MAISB</strong>
            <small>Mobile AI Security Boundary</small>
          </span>
        </Link>

        <nav className="landing-nav__links" aria-label="Primary">
          {NAV_LINKS.map((link) =>
            'to' in link ? (
              <Link key={link.label} to={link.to} className="landing-nav__link">
                {link.label}
              </Link>
            ) : (
              <a
                key={link.label}
                href={link.href}
                className="landing-nav__link"
                {...('external' in link && link.external ? { target: '_blank', rel: 'noopener noreferrer' } : {})}
              >
                {link.label}
              </a>
            ),
          )}
        </nav>

        <div className="landing-nav__actions">
          <Link to="/login" className="landing-nav__signin">
            Sign in
          </Link>
          <Link to="/signup">
            <Button className="landing-nav__cta">Get started</Button>
          </Link>
        </div>

        <button
          type="button"
          className="landing-nav__toggle"
          aria-expanded={mobileOpen}
          aria-controls="landing-mobile-menu"
          aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
          onClick={() => setMobileOpen((open) => !open)}
        >
          <span className="landing-nav__toggle-bar" />
          <span className="landing-nav__toggle-bar" />
          <span className="landing-nav__toggle-bar" />
        </button>
      </div>

      <div
        id="landing-mobile-menu"
        className={`landing-nav__mobile${mobileOpen ? ' landing-nav__mobile--open' : ''}`}
        aria-hidden={!mobileOpen}
      >
        <nav className="landing-nav__mobile-links" aria-label="Mobile">
          {NAV_LINKS.map((link) =>
            'to' in link ? (
              <Link key={link.label} to={link.to} className="landing-nav__mobile-link" onClick={closeMobile}>
                {link.label}
              </Link>
            ) : (
              <a
                key={link.label}
                href={link.href}
                className="landing-nav__mobile-link"
                onClick={closeMobile}
                {...('external' in link && link.external ? { target: '_blank', rel: 'noopener noreferrer' } : {})}
              >
                {link.label}
              </a>
            ),
          )}
        </nav>
        <div className="landing-nav__mobile-actions">
          <Link to="/login" onClick={closeMobile}>
            <Button variant="secondary" className="landing-nav__mobile-btn">
              Sign in
            </Button>
          </Link>
          <Link to="/signup" onClick={closeMobile}>
            <Button className="landing-nav__mobile-btn">Get started</Button>
          </Link>
        </div>
      </div>
      {mobileOpen && <button type="button" className="landing-nav__backdrop" aria-label="Close menu" onClick={closeMobile} />}
    </header>
  )
}
