import { useState } from 'react'
import { Link } from 'react-router-dom'
import Button from '../components/Button'
import Card from '../components/Card'
import Badge from '../components/Badge'

const plans = [
  {
    id: 'free',
    name: 'Free',
    price: '$0',
    period: 'forever',
    copy: 'Sample data, core dashboard access, and API key generation. Perfect for evaluating MAISB.',
    features: [
      { name: 'Boundary scans', included: true },
      { name: 'Single workspace', included: true },
      { name: 'Dashboard access', included: true },
      { name: 'API key management', included: true },
      { name: 'Sample data labels', included: true },
      { name: 'Security events log', included: true },
      { name: 'Team members', included: false },
      { name: 'Advanced analytics', included: false },
      { name: 'Compliance reports', included: false },
      { name: 'Dedicated support', included: false },
    ],
    cta: 'Start for free',
    action: 'https://maisb.app/signup',
  },
  {
    id: 'pro',
    name: 'Pro',
    price: 'Custom',
    period: 'per month',
    copy: 'Operational analytics, team controls, and higher scan volume. For growing security teams.',
    features: [
      { name: 'Boundary scans', included: true },
      { name: 'Multiple workspaces', included: true },
      { name: 'Dashboard access', included: true },
      { name: 'API key management', included: true },
      { name: 'Sample data labels', included: true },
      { name: 'Security events log', included: true },
      { name: 'Team members', included: true },
      { name: 'Advanced analytics', included: true },
      { name: 'Compliance reports', included: true },
      { name: 'Priority support', included: true },
    ],
    cta: 'Request invoice',
    action: 'mailto:sales@maisb.app',
    badge: 'Coming soon',
  },
  {
    id: 'certify',
    name: 'Certify',
    price: 'Custom',
    period: 'per month',
    copy: 'MAISB Certify runtime security assessment. Enterprise security verification.',
    features: [
      { name: 'All Pro features', included: true },
      { name: 'Runtime security assessment', included: true },
      { name: 'Boundary trace evidence', included: true },
      { name: 'Verification badge package', included: true },
      { name: 'Enterprise review workflow', included: true },
      { name: 'Compliance report package', included: true },
      { name: 'Custom integration', included: true },
      { name: 'Dedicated security engineer', included: true },
      { name: 'SLA guarantee', included: true },
      { name: 'Quarterly reviews', included: true },
    ],
    cta: 'Contact sales',
    action: 'mailto:sales@maisb.app',
    badge: 'Request invoice',
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: 'Custom',
    period: 'per month',
    copy: 'Complete security governance, certification, and enterprise rollout support.',
    features: [
      { name: 'All Certify features', included: true },
      { name: 'SSO integration', included: true },
      { name: 'Custom audit trails', included: true },
      { name: 'Webhook integrations', included: true },
      { name: 'Regional deployment', included: true },
      { name: 'Data residency', included: true },
      { name: 'White-label options', included: true },
      { name: 'Account manager', included: true },
      { name: '24/7 support', included: true },
      { name: 'Custom SLA', included: true },
    ],
    cta: 'Contact sales',
    action: 'mailto:sales@maisb.app',
    badge: 'Request invoice',
  },
]

const comparisonFeatures = [
  'Boundary scans',
  'Dashboard access',
  'API key management',
  'Team members',
  'Advanced analytics',
  'Compliance reports',
  'Certify assessment',
  'SSO integration',
  'Dedicated support',
]

export default function Pricing() {
  const [expandedFaq, setExpandedFaq] = useState<string | null>(null)

  const faqs = [
    {
      id: 'free-upgrade',
      question: 'Can I upgrade from Free to Pro later?',
      answer: 'Yes. Start free with sample data to evaluate MAISB. When you\'re ready to move to production with live traffic, upgrade to Pro or Enterprise. Your workspace and API keys carry over.',
    },
    {
      id: 'payment',
      question: 'How do I pay?',
      answer: 'Online checkout is being configured. We currently do not collect card payments directly on this website. All Pro, Certify, and Enterprise plans are invoice-based. Contact sales@maisb.app to discuss billing and SLA terms.',
    },
    {
      id: 'scans',
      question: 'What is the scan volume limit?',
      answer: 'Free tier has sample data and does not reflect real scan volume. Pro and Enterprise tiers scale with your usage. Volume-based pricing is available for high-traffic workloads. Contact sales for details.',
    },
    {
      id: 'certify',
      question: 'What is MAISB Certify?',
      answer: 'Certify is our runtime security assessment service. We perform a boundary trace evidence audit, deliver a verification badge package, and provide enterprise review workflows. It\'s perfect for demonstrating compliance to boards, auditors, and enterprise partners.',
    },
    {
      id: 'sso',
      question: 'Do you support SSO/SAML?',
      answer: 'SSO is available on Enterprise. For Pro, we\'re building SSO support—contact sales for early access. Team members can be invited with email-based authentication today.',
    },
    {
      id: 'data-storage',
      question: 'Where is my data stored?',
      answer: 'All data is stored in secure, encrypted environments. Free and Pro are hosted in US regions (multi-AZ). Enterprise has regional deployment and data residency options available. We never store raw payloads—only metadata, decisions, and audit traces.',
    },
    {
      id: 'export',
      question: 'Can I export my data?',
      answer: 'Yes. Export scan metadata, security events, traces, and audit logs as CSV or JSON. Pro and Enterprise have scheduled export options. All exports are metadata-only—never raw payloads.',
    },
    {
      id: 'api-quota',
      question: 'Are there API rate limits?',
      answer: 'Free tier has a development rate limit. Pro and Enterprise have production-grade quotas. Custom limits available for high-volume workloads. Contact sales to discuss your traffic profile.',
    },
  ]

  return (
    <main className="public-shell">
      <div className="page-head">
        <div>
          <p className="eyebrow">Pricing</p>
          <h1>Enterprise plans with clear boundaries.</h1>
          <p className="muted">Free starts now. Pro, Certify, and Enterprise are invoice-based during rollout.</p>
        </div>
        <Link to="/signup"><Button>Get started free</Button></Link>
      </div>

      {/* Plan Cards */}
      <section className="grid two-col" style={{ marginBottom: '3rem' }}>
        {plans.map((plan) => (
          <Card
            key={plan.id}
            title={plan.name}
            subtitle={`${plan.price} ${plan.period}`}
            className={plan.id === 'free' ? 'plan-highlight' : ''}
          >
            <p className="muted" style={{ marginBottom: '1rem', minHeight: '3rem' }}>{plan.copy}</p>
            {plan.badge && <div style={{ marginBottom: '0.75rem' }}><Badge>{plan.badge}</Badge></div>}
            <ul className="bullet-list">
              {plan.features.map((feature) => (
                <li key={feature.name} style={{ color: feature.included ? '#cbd5e1' : '#6b7280' }}>
                  {feature.included ? '✓' : '—'} {feature.name}
                </li>
              ))}
            </ul>
            <div style={{ marginTop: '1.5rem' }}>
              {plan.id === 'free' ? (
                <Link to="/signup"><Button>{plan.cta}</Button></Link>
              ) : (
                <a href={plan.action}><Button variant={plan.id === 'pro' ? 'primary' : 'secondary'}>{plan.cta}</Button></a>
              )}
            </div>
          </Card>
        ))}
      </section>

      {/* Feature Comparison */}
      <section style={{ marginBottom: '3rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <p className="eyebrow">Full feature comparison</p>
          <h2>Choose the plan that fits your team</h2>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th style={{ minWidth: '240px' }}>Feature</th>
                <th>Free</th>
                <th>Pro</th>
                <th>Certify</th>
                <th>Enterprise</th>
              </tr>
            </thead>
            <tbody>
              {comparisonFeatures.map((feature) => (
                <tr key={feature}>
                  <td>{feature}</td>
                  {['free', 'pro', 'certify', 'enterprise'].map((plan) => (
                    <td key={plan} style={{ textAlign: 'center' }}>
                      {plan === 'free' && feature === 'Boundary scans' && '✓'}
                      {plan === 'free' && feature === 'Dashboard access' && '✓'}
                      {plan === 'free' && feature === 'API key management' && '✓'}
                      {plan === 'pro' && ['Boundary scans', 'Dashboard access', 'API key management', 'Team members', 'Advanced analytics', 'Compliance reports'].includes(feature) && '✓'}
                      {plan === 'certify' && ['Boundary scans', 'Dashboard access', 'API key management', 'Team members', 'Advanced analytics', 'Compliance reports', 'Certify assessment', 'Dedicated support'].includes(feature) && '✓'}
                      {plan === 'enterprise' && ['Boundary scans', 'Dashboard access', 'API key management', 'Team members', 'Advanced analytics', 'Compliance reports', 'Certify assessment', 'SSO integration', 'Dedicated support'].includes(feature) && '✓'}
                      {feature === 'SSO integration' && plan === 'enterprise' && '✓'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* FAQ */}
      <section style={{ marginBottom: '3rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <p className="eyebrow">Questions?</p>
          <h2>Frequently asked questions</h2>
        </div>
        <div style={{ display: 'grid', gap: '0.75rem' }}>
          {faqs.map((faq) => (
            <Card key={faq.id} title={faq.question} className={expandedFaq === faq.id ? '' : ''}>
              {expandedFaq === faq.id && (
                <div>
                  <p className="muted">{faq.answer}</p>
                  <div style={{ marginTop: '0.75rem' }}>
                    <Button
                      variant="secondary"
                      onClick={() => setExpandedFaq(null)}
                    >
                      Collapse
                    </Button>
                  </div>
                </div>
              )}
              {expandedFaq !== faq.id && (
                <Button
                  variant="secondary"
                  onClick={() => setExpandedFaq(faq.id)}
                >
                  Learn more
                </Button>
              )}
            </Card>
          ))}
        </div>
      </section>

      {/* Commercial Notice */}
      <Card title="Commercial rollout" subtitle="Invoice-based during early access">
        <p className="muted">
          MAISB is in early access. Free tier is available now with sample data and core dashboard features. Pro, Certify, and Enterprise plans are available by invoice. We do not currently collect card payments directly on this website.
        </p>
        <p className="muted" style={{ marginTop: '1rem' }}>
          <strong>Ready to go production?</strong> <a href="mailto:sales@maisb.app">Contact sales@maisb.app</a> to discuss your use case and get pricing aligned with your team's needs.
        </p>
      </Card>

      {/* Final CTA */}
      <section style={{ marginTop: '3rem', textAlign: 'center' }}>
        <h2>Start protecting mobile AI channels today.</h2>
        <p className="hero-lead" style={{ maxWidth: '60ch', margin: '1rem auto' }}>
          Begin with Free tier and evaluate MAISB with sample data. Upgrade to Pro or Enterprise as you scale.
        </p>
        <div className="row-inline" style={{ justifyContent: 'center' }}>
          <Link to="/signup"><Button>Get started free</Button></Link>
          <a href="mailto:sales@maisb.app"><Button variant="secondary">Contact sales</Button></a>
        </div>
      </section>
    </main>
  )
}
