import { Link } from 'react-router-dom'

export default function Landing() {
  return (
    <main className="public-page landing">
      <section className="hero">
        <p className="eyebrow">MAISB Platform</p>
        <h1>Enterprise runtime security for mobile AI systems</h1>
        <p>Protect AI-driven app flows with injection detection, trace telemetry, SOC operations, and certification-ready reporting.</p>
        <div className="cta-row">
          <Link to="/signup" className="btn">Start Free</Link>
          <Link to="/pricing" className="btn secondary">View Pricing</Link>
        </div>
      </section>
    </main>
  )
}
