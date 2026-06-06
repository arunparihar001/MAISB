import { Link } from 'react-router-dom'
import Button from '../Button'

type Plan = {
  id: string
  name: string
  price: string
  period: string
  prefix?: string
  description: string
  features: string[]
  cta: string
  href: string
  featured?: boolean
  badge?: string
  variant?: 'primary' | 'secondary'
}

const PLANS: Plan[] = [
  {
    id: 'free',
    name: 'Free',
    price: '$0',
    period: 'month',
    description: 'Perfect for students and developers.',
    features: [
      '5,000 scans/month',
      '1 workspace',
      '2 API keys',
      'Basic dashboard',
      'Community support',
      'Security events log',
    ],
    cta: 'Start Free',
    href: '/signup',
    variant: 'secondary',
  },
  {
    id: 'pro',
    name: 'Pro',
    price: '$99',
    period: 'month',
    description: 'Production-grade boundary protection for growing teams.',
    features: [
      '100,000 scans/month',
      'Unlimited API keys',
      '10 team members',
      'Advanced analytics',
      'Risk history',
      'Email support',
      'CI/CD integration',
    ],
    cta: 'Start 14-Day Trial',
    href: 'mailto:sales@maisb.app?subject=MAISB%20Pro%20Trial',
    featured: true,
    badge: 'Most Popular',
    variant: 'primary',
  },
  {
    id: 'certify',
    name: 'Certify',
    price: '$499',
    period: 'month',
    prefix: 'Starting at',
    description: 'Security certification workflow with compliance-ready evidence.',
    features: [
      '1,000,000 scans/month',
      'Security certification workflow',
      'Compliance reports',
      'Audit exports',
      'Trace evidence',
      'Verification badge',
      'Priority support',
    ],
    cta: 'Contact Sales',
    href: 'mailto:sales@maisb.app?subject=MAISB%20Certify',
    variant: 'secondary',
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: '$1,499',
    period: 'month',
    prefix: 'Starting at',
    description: 'Complete governance, deployment flexibility, and dedicated support.',
    features: [
      'Unlimited scans',
      'Unlimited workspaces',
      'Unlimited API keys',
      'SSO / SAML',
      'On-prem deployment',
      'Dedicated Security Engineer',
      '24/7 SLA',
      'Custom integrations',
      'Regional deployment',
      'White-label options',
    ],
    cta: 'Book a Demo',
    href: 'mailto:sales@maisb.app?subject=MAISB%20Enterprise%20Demo',
    variant: 'secondary',
  },
]

export default function PricingPlans() {
  return (
    <section className="pricing-plans" aria-label="Pricing plans">
      <div className="pricing-plans__grid">
        {PLANS.map((plan) => (
          <article
            key={plan.id}
            className={`pricing-plans__card${plan.featured ? ' pricing-plans__card--featured' : ''}${plan.id === 'enterprise' ? ' pricing-plans__card--enterprise' : ''}`}
          >
            {plan.badge && (
              <span className="pricing-plans__badge">
                <span aria-hidden="true">⭐</span> {plan.badge}
              </span>
            )}
            <p className="pricing-plans__name">{plan.name}</p>
            {plan.prefix && <p className="pricing-plans__prefix muted">{plan.prefix}</p>}
            <p className="pricing-plans__price">
              {plan.price}
              <span className="muted"> / {plan.period}</span>
            </p>
            <p className="pricing-plans__copy muted">{plan.description}</p>
            <ul className="pricing-plans__features">
              {plan.features.map((feature) => (
                <li key={feature}>{feature}</li>
              ))}
            </ul>
            {plan.href.startsWith('/') ? (
              <Link to={plan.href} className="pricing-plans__cta-link">
                <Button
                  variant={plan.id === 'enterprise' ? 'primary' : plan.variant}
                  className={`pricing-plans__cta pricing-btn${plan.id === 'enterprise' ? ' pricing-plans__cta--enterprise' : ''}`}
                >
                  {plan.cta}
                </Button>
              </Link>
            ) : (
              <a href={plan.href} className="pricing-plans__cta-link">
                <Button
                  variant={plan.id === 'enterprise' ? 'primary' : plan.variant}
                  className={`pricing-plans__cta pricing-btn${plan.id === 'enterprise' ? ' pricing-plans__cta--enterprise' : ''}`}
                >
                  {plan.cta}
                </Button>
              </a>
            )}
          </article>
        ))}
      </div>
      <p className="pricing-plans__disclaimer muted">
        Paid plans are invoice-based. Online checkout is not active on this site.
      </p>
    </section>
  )
}
