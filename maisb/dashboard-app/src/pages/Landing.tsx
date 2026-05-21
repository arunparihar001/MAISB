import { Link } from 'react-router-dom'
import PublicFooter from '../components/PublicFooter'
import PricingCard, { Plan } from '../components/PricingCard'

const plans: Plan[] = [
  { id: 'free', name: 'Free Developer', price: '$0/month', features: ['Starter API key', 'Limited monthly scans', 'Basic usage dashboard', 'Android SDK testing'] },
  { id: 'pro', name: 'Pro', price: 'Paid monthly', features: ['Higher quota', 'Commercial use', 'Usage dashboard', 'Email support'] },
  { id: 'enterprise', name: 'Enterprise', price: 'Custom', features: ['SOC workflow', 'Audit/export', 'Tenant policy controls', 'Onboarding support'] },
  { id: 'certify', name: 'MAISB Certify', price: 'Assessment', features: ['PDF report', 'Badge SVG', 'Benchmark-style result', 'Enterprise trust package'] },
]

export default function Landing() {
  return (
    <main className="public-shell">
      <nav className="public-nav"><strong>MAISB Shield</strong><div><a href="#problem">Problem</a><a href="#how">How it works</a><a href="#sdk">SDK</a><a href="#soc">SOC</a><a href="#certify">Certify</a><Link to="/pricing">Pricing</Link><a href="#trust">Trust</a><a href="#contact">Contact</a></div></nav>
      <section className="hero">
        <p className="eyebrow">AI Runtime Security Infrastructure</p>
        <h1>AI Runtime Security for Mobile & Fintech Applications</h1>
        <p>Protect mobile AI agents from prompt injection, cross-channel payload propagation, and unsafe automated actions before untrusted input reaches the model.</p>
        <div className="row"><a className="button" href="https://app.maisb.app/signup">Get API Key</a><a className="button secondary" href="https://api.maisb.app/docs">View Docs</a><a className="button secondary" href="mailto:sales@maisb.app">Contact Sales</a></div>
      </section>
      <section id="problem" className="section-grid"><div><h2>The new risk surface is inside the AI workflow.</h2><p>Clipboard text, deep links, QR codes, notifications, webviews, and documents can carry hidden instructions that change what an AI agent does.</p></div><div className="card"><h3>MAISB blocks risky intent before execution.</h3><p>Scan payloads, classify risk, trace cross-channel movement, and escalate suspicious cases to security workflows.</p></div></section>
      <section id="how" className="steps"><h2>How MAISB Shield works</h2><div className="grid"><div className="card"><b>1. Capture</b><p>SDK or API receives untrusted mobile input.</p></div><div className="card"><b>2. Scan</b><p>Backend classifies intent, channel, and risk.</p></div><div className="card"><b>3. Trace</b><p>Telemetry links related events across channels.</p></div><div className="card"><b>4. Respond</b><p>Dashboard and SOC views show decisions and cases.</p></div></div></section>
      <section id="sdk" className="section-grid"><div className="code-card">{`MAISB.initialize(..., baseUrl="https://api.maisb.app")\nval result = MAISB.scan(payload)`}</div><div><h2>Android SDK</h2><p>Embed MAISB Shield into mobile AI applications and inspect risky payloads before they reach LLM-backed workflows.</p></div></section>
      <section id="soc" className="section-grid"><div><h2>SOC dashboard</h2><p>Review risk queues, cases, usage, and security telemetry from a central analyst surface.</p></div><div id="certify" className="card"><h3>MAISB Certify reports</h3><p>Request benchmark-style assessments with PDF reports and badge SVGs for enterprise trust conversations.</p></div></section>
      <section id="pricing"><h2>Pricing</h2><div className="grid">{plans.map((plan) => <PricingCard key={plan.id} plan={plan} />)}</div></section>
      <section id="trust" className="section-grid"><div><h2>Security and trust</h2><p>Built for defensive AI runtime security with operational telemetry, SOC workflows, and accountable reporting for enterprise readiness.</p></div><div id="contact" className="card"><h3>Contact</h3><p>Commercial and onboarding: <a href="mailto:sales@maisb.app">sales@maisb.app</a></p><p>Support and operations: <a href="mailto:support@maisb.app">support@maisb.app</a></p></div></section>
      <PublicFooter />
    </main>
  )
}
