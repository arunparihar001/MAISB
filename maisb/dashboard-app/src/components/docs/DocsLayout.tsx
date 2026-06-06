import type { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import Button from '../Button'

export const DOCS_NAV = [
  { label: 'Overview', to: '/docs' },
  { label: 'API Reference', to: '/docs/api' },
  { label: 'SDK Guides', to: '/docs/sdk' },
  { label: 'Examples', to: '/docs/examples' },
] as const

type Props = {
  title: string
  eyebrow?: string
  description: string
  children?: ReactNode
}

export default function DocsLayout({ title, eyebrow = 'Documentation', description, children }: Props) {
  const { pathname } = useLocation()

  return (
    <>
      <header className="docs-topbar">
        <div className="docs-topbar__inner">
          <Link to="/" className="docs-topbar__brand">
            <span className="landing-brand__mark" aria-hidden="true">
              <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="1" y="1" width="30" height="30" rx="9" stroke="currentColor" strokeWidth="1.2" opacity="0.35" />
                <path d="M8 22V10l8 6 8-6v12" stroke="url(#docsBrandGrad)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                <defs>
                  <linearGradient id="docsBrandGrad" x1="8" y1="10" x2="24" y2="22" gradientUnits="userSpaceOnUse">
                    <stop stopColor="#60a5fa" />
                    <stop offset="1" stopColor="#34d399" />
                  </linearGradient>
                </defs>
              </svg>
            </span>
            <span>MAISB Docs</span>
          </Link>
          <Link to="/">
            <Button variant="secondary" className="docs-topbar__home">
              Back to homepage
            </Button>
          </Link>
        </div>
      </header>

      <main className="public-shell docs-page">
        <aside className="docs-sidebar" aria-label="Documentation sections">
          <nav className="docs-sidebar__nav">
            {DOCS_NAV.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className="docs-sidebar__link"
                {...(item.to === pathname ? { 'aria-current': 'page' as const } : {})}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </aside>

        <article className="docs-content card">
          <p className="eyebrow">{eyebrow}</p>
          <h1 className="docs-content__title">{title}</h1>
          <p className="docs-content__lead">{description}</p>
          {children}
        </article>
      </main>
    </>
  )
}
