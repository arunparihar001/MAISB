import { useEffect, useRef, type ReactNode } from 'react'

type Props = {
  id?: string
  eyebrow?: string
  title?: string
  lead?: string
  children: ReactNode
  className?: string
  centered?: boolean
}

export default function LandingSection({
  id,
  eyebrow,
  title,
  lead,
  children,
  className = '',
  centered = true,
}: Props) {
  const ref = useRef<HTMLElement>(null)

  useEffect(() => {
    const node = ref.current
    if (!node) return

    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (reduced) {
      node.classList.add('landing-section--visible')
      return
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          node.classList.add('landing-section--visible')
          observer.disconnect()
        }
      },
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' },
    )

    observer.observe(node)
    return () => observer.disconnect()
  }, [])

  return (
    <section ref={ref} id={id} className={`landing-section ${className}`.trim()}>
      {(eyebrow || title || lead) && (
        <header className={`landing-section__head${centered ? ' landing-section__head--center' : ''}`}>
          {eyebrow && <p className="eyebrow">{eyebrow}</p>}
          {title && <h2 className="landing-section__title">{title}</h2>}
          {lead && <p className="landing-section__lead">{lead}</p>}
        </header>
      )}
      {children}
    </section>
  )
}
