import type { PropsWithChildren, ReactNode } from 'react'

type Props = PropsWithChildren<{ title?: ReactNode; subtitle?: ReactNode; actions?: ReactNode; className?: string }>

export default function Card({ title, subtitle, actions, className = '', children }: Props) {
  return (
    <section className={`card ${className}`.trim()}>
      {(title || subtitle || actions) && (
        <header className="card-head">
          <div>
            {title && <h3>{title}</h3>}
            {subtitle && <p className="muted">{subtitle}</p>}
          </div>
          {actions}
        </header>
      )}
      {children}
    </section>
  )
}
