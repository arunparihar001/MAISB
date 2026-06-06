import type { ReactNode } from 'react'

type Props = {
  eyebrow: string
  title: string
  subtitle: string
  children: ReactNode
}

export default function MarketingHero({ eyebrow, title, subtitle, children }: Props) {
  return (
    <section className="mkt-hero">
      <div className="mkt-hero__backdrop" aria-hidden="true" />
      <div className="mkt-hero__glow" aria-hidden="true" />
      <div className="mkt-hero__content">
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p className="mkt-hero__lead">{subtitle}</p>
        <div className="mkt-hero__actions">{children}</div>
      </div>
    </section>
  )
}
