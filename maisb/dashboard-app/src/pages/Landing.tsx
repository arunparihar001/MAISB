import { Link } from 'react-router-dom'
import { DASHBOARD_URL } from '../lib/config'

export default function Landing() {
  return (
    <main className="marketing">
      <section className="hero">
        <p className="kicker">Mobile AI Security Platform</p>
        <h1>Enterprise-grade runtime protection for mobile AI agents.</h1>
        <p className="lead">MAISB delivers cross-channel threat detection, SOC workflows, and benchmark-backed certification for production AI teams.</p>
        <div className="row">
          <a className="btn" href={`${DASHBOARD_URL}/signup`}>Start free</a>
          <a className="btn secondary" href={`${DASHBOARD_URL}/login`}>Open dashboard</a>
        </div>
      </section>
      <section className="grid">
        <article className="card"><h3>Phase 1 Foundation</h3><p>Policy controls, key governance, and production-safe defaults.</p></article>
        <article className="card"><h3>Phase 2 Trace Engine</h3><p>Cross-channel trace visibility for clipboard, QR, deep links, notifications, and more.</p></article>
        <article className="card"><h3>Phase 3 Analytics</h3><p>Security KPIs, telemetry trends, and decision analytics for operations teams.</p></article>
        <article className="card"><h3>Phase 4 SOC</h3><p>Risk queue, case workflow, timeline evidence, and audit-friendly exports.</p></article>
      </section>
      <section className="legal-links">
        <Link to="/pricing">Pricing</Link>
        <Link to="/terms">Terms</Link>
        <Link to="/privacy">Privacy</Link>
        <Link to="/refund">Refund</Link>
      </section>
    </main>
  )
}
