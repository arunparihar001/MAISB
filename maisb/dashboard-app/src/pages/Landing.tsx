import { Link } from 'react-router-dom'
import Button from '../components/Button'

export default function Landing() {
  return (
    <main className="public-shell">
      <nav className="public-nav">
        <div>
          <strong>MAISB</strong>
          <p className="muted">Mobile AI Security Boundary</p>
        </div>
        <div className="row-inline">
          <Link to="/pricing">Pricing</Link>
          <Link to="/terms">Terms</Link>
          <Link to="/privacy">Privacy</Link>
          <Link to="/refund">Refund</Link>
        </div>
      </nav>

      <section className="hero hero-grid">
        <div className="hero-copy">
          <p className="eyebrow">Scanning the Boundary</p>
          <h1>Shielding mobile AI agents from untrusted channels.</h1>
          <p className="hero-lead">
            MAISB hardens clipboard, NFC, QR, share intents, notifications, webviews, and deep links before they reach an AI runtime.
          </p>
          <div className="row-inline">
            <Link to="/signup"><Button>Start secure onboarding</Button></Link>
            <Link to="/pricing"><Button variant="secondary">Review plans</Button></Link>
          </div>
          <div className="hero-pills">
            <span className="status-chip status-chip--live">Live scanning</span>
            <span className="status-chip">Traceability</span>
            <span className="status-chip">Hardened Security</span>
          </div>
        </div>

        <div className="scan-visual card">
          <div className="scan-visual__ring scan-visual__ring--outer" />
          <div className="scan-visual__ring scan-visual__ring--inner" />
          <div className="scan-visual__beam" />
          <div className="scan-visual__node scan-visual__node--source">Clipboard</div>
          <div className="scan-visual__node scan-visual__node--target">LLM boundary</div>
          <div className="scan-visual__panel">
            <span className="status-chip status-chip--success">Blocked</span>
            <strong>Cross-channel risk scored</strong>
            <p className="muted">Sample data · policy matched · trace captured</p>
          </div>
        </div>
      </section>

      <section className="grid two-col">
        <section className="card">
          <p className="eyebrow">Control plane</p>
          <h3>Security operators get a single source of truth.</h3>
          <p className="muted">Boundary protection, analytics, team controls, and compliance reporting stay aligned across the same workspace.</p>
        </section>
        <section className="card">
          <p className="eyebrow">Operational posture</p>
          <h3>Serious, traceable, and ready for enterprise review.</h3>
          <p className="muted">Every signal is designed for auditability, with clear status indicators and minimal noise.</p>
        </section>
      </section>
    </main>
  )
}
