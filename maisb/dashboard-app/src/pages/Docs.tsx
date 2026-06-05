import { Link } from 'react-router-dom'
import Card from '../components/Card'

export default function Docs() {
  return (
    <main className="public-shell">
      <div className="page-head">
        <div>
          <p className="eyebrow">Documentation</p>
          <h1>MAISB runtime boundary protection</h1>
          <p className="muted">
            MAISB protects mobile AI applications by scanning untrusted channel input before content reaches your LLM.
          </p>
        </div>
      </div>

      <section className="grid two-col" style={{ marginBottom: '2rem' }}>
        <Card title="What MAISB does">
          <p className="muted">
            MAISB enforces a runtime security boundary for mobile AI. Every scan returns an allow/review/block decision before downstream LLM execution.
          </p>
        </Card>
        <Card title="Protected channels">
          <ul className="bullet-list">
            <li>Clipboard</li>
            <li>QR</li>
            <li>Notifications</li>
            <li>Deep Links</li>
            <li>NFC</li>
            <li>Share Intents</li>
            <li>WebViews</li>
          </ul>
        </Card>
        <Card title="Boundary Protection">
          <p className="muted">Channel input is evaluated at runtime with policy-aware checks before any content reaches your AI model.</p>
        </Card>
        <Card title="Cross-Channel Trace">
          <p className="muted">MAISB correlates repeated or coordinated payload patterns across channels to detect attack chains.</p>
        </Card>
        <Card title="Runtime risk scoring">
          <p className="muted">Each event receives a runtime risk score so your app can programmatically enforce safe actions.</p>
        </Card>
        <Card title="Metadata-only event logging">
          <p className="muted">MAISB logs channel, decision, risk score, and trace metadata only. Raw payload content is not persisted.</p>
        </Card>
      </section>

      <section className="row-inline" style={{ gap: '1rem' }}>
        <Link to="/docs/api">API docs</Link>
        <Link to="/docs/sdk">SDK guides</Link>
        <Link to="/docs/examples">Examples</Link>
      </section>
    </main>
  )
}
