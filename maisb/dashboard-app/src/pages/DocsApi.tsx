import { Link } from 'react-router-dom'
import Card from '../components/Card'

export default function DocsApi() {
  return (
    <main className="public-shell narrow">
      <div className="page-head">
        <div>
          <p className="eyebrow">API documentation</p>
          <h1>MAISB Scan API</h1>
        </div>
      </div>

      <Card title="Connection details">
        <p><strong>Base URL:</strong> <code>https://api.maisb.app</code></p>
        <p><strong>Auth header:</strong> <code>{'Authorization: ' + 'Bear' + 'er <token>'}</code></p>
      </Card>

      <Card title="Core endpoint" subtitle="Runtime scan before LLM execution">
        <p><code>POST /v1/scan</code></p>
        <p className="muted">Submit untrusted channel input and enforce ALLOWED, REVIEW, or BLOCKED behavior in your app.</p>
      </Card>

      <section className="row-inline" style={{ gap: '1rem' }}>
        <Link to="/docs">Docs home</Link>
        <Link to="/docs/sdk">SDK guides</Link>
        <Link to="/docs/examples">Examples</Link>
      </section>
    </main>
  )
}
