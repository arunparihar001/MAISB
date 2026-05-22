import PricingCard, { Plan } from '../components/PricingCard'

const plans: Plan[] = [
  { id: 'free', name: 'Free Developer', price: '$0/month', features: ['Starter API key', 'Limited monthly scans', 'Basic usage dashboard', 'Android SDK testing'] },
  { id: 'pro', name: 'Pro', price: 'Paid monthly', features: ['Higher quota', 'Commercial use', 'Dashboard usage', 'Email support'] },
  { id: 'enterprise', name: 'Enterprise', price: 'Custom quote', features: ['Custom quota', 'SOC workflow', 'Audit/export', 'Tenant policy controls', 'Support/onboarding'] },
  { id: 'certify', name: 'MAISB Certify', price: 'Assessment', features: ['Assessment request', 'PDF report', 'Badge SVG', 'Benchmark-style result'] },
]

export default function Pricing() {
  return <main className="public-shell narrow"><h1>Pricing</h1><p>Start free, upgrade when your mobile AI workflow needs production security controls.</p><div className="grid">{plans.map((plan) => <PricingCard key={plan.id} plan={plan} />)}</div><p className="muted">Online checkout is being configured. For Pro, Enterprise, or Certify plans, request an invoice at <a href="mailto:sales@maisb.app">sales@maisb.app</a>. No card payments are currently accepted online.</p></main>
}
