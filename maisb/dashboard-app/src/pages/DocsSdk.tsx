import { Link } from 'react-router-dom'
import Card from '../components/Card'

export default function DocsSdk() {
  return (
    <main className="public-shell narrow">
      <div className="page-head">
        <div>
          <p className="eyebrow">SDK guides</p>
          <h1>Integrate MAISB in your mobile AI stack</h1>
          <p className="muted">Use the API in your runtime boundary layer before content is forwarded to any LLM.</p>
        </div>
      </div>

      <Card title="Suggested flow">
        <ol className="bullet-list">
          <li>Capture mobile channel input.</li>
          <li>Call MAISB scan API before LLM invocation.</li>
          <li>Apply decision policy (ALLOW/REVIEW/BLOCK).</li>
          <li>Log metadata-only audit records.</li>
        </ol>
      </Card>

      <section className="row-inline" style={{ gap: '1rem' }}>
        <Link to="/docs">Docs home</Link>
        <Link to="/docs/api">API docs</Link>
        <Link to="/docs/examples">Examples</Link>
      </section>
    </main>
  )
}
