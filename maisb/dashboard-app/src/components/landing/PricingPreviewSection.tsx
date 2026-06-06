import { Link } from 'react-router-dom'
import Button from '../Button'
import LandingSection from './LandingSection'

const PLANS = [
  {
    id: 'free',
    name: 'Free',
    price: '$0',
    period: 'forever',
    copy: 'Evaluate MAISB with sample data, core dashboard access, and API key generation.',
    features: ['Boundary scans', 'Single workspace', 'API key management', 'Security events log'],
    cta: 'Start for free',
    href: '/signup',
    variant: 'primary' as const,
  },
  {
    id: 'pro',
    name: 'Pro',
    price: 'Custom',
    period: 'per month',
    copy: 'Operational analytics, team controls, and higher scan volume for growing security teams.',
    features: ['Multiple workspaces', 'Team members', 'Advanced analytics', 'Compliance reports'],
    cta: 'Coming soon',
    href: 'mailto:sales@maisb.app',
    variant: 'secondary' as const,
    badge: 'Invoice only',
  },
  {
    id: 'certify',
    name: 'Certify',
    price: 'Custom',
    period: 'per month',
    copy: 'Runtime security assessment with boundary trace evidence and verification badge package.',
    features: ['Certify assessment', 'Trace evidence export', 'Verification badge', 'Dedicated engineer'],
    cta: 'Contact sales',
    href: 'mailto:sales@maisb.app',
    variant: 'secondary' as const,
    badge: 'Enterprise',
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: 'Custom',
    period: 'per month',
    copy: 'Complete security governance, SSO, regional deployment, and enterprise rollout support.',
    features: ['SSO integration', 'Custom audit trails', 'Regional deployment', '24/7 support'],
    cta: 'Contact sales',
    href: 'mailto:sales@maisb.app',
    variant: 'secondary' as const,
    badge: 'Custom SLA',
  },
]

export default function PricingPreviewSection() {
  return (
    <LandingSection
      id="pricing"
      eyebrow="Pricing"
      title="Start free. Scale when your boundary goes live."
      lead="Paid plans are available by invoice — no checkout pretense. Upgrade when you are ready for production traffic."
    >
      <div className="landing-pricing">
        {PLANS.map((plan) => (
          <article key={plan.id} className={`landing-pricing__card${plan.id === 'free' ? ' landing-pricing__card--featured' : ''}`}>
            {plan.badge && <span className="landing-pricing__badge">{plan.badge}</span>}
            <p className="landing-pricing__name">{plan.name}</p>
            <p className="landing-pricing__price">
              {plan.price}
              <span className="muted"> / {plan.period}</span>
            </p>
            <p className="muted landing-pricing__copy">{plan.copy}</p>
            <ul className="landing-pricing__features">
              {plan.features.map((feature) => (
                <li key={feature}>{feature}</li>
              ))}
            </ul>
            {plan.href.startsWith('/') ? (
              <Link to={plan.href}>
                <Button variant={plan.variant} className="landing-pricing__cta">
                  {plan.cta}
                </Button>
              </Link>
            ) : (
              <a href={plan.href}>
                <Button variant={plan.variant} className="landing-pricing__cta">
                  {plan.cta}
                </Button>
              </a>
            )}
          </article>
        ))}
      </div>
    </LandingSection>
  )
}
