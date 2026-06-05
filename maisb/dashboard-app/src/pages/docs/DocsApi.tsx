import DocsLayout from '../../components/docs/DocsLayout'

export default function DocsApi() {
  return (
    <DocsLayout
      eyebrow="API Reference"
      title="Scan API"
      description="Send mobile channel context to POST /v1/scan and receive a runtime risk decision before content reaches your LLM."
    >
      <div className="docs-block">
        <h2>Endpoint</h2>
        <code className="raw-key">POST https://api.maisb.app/v1/scan</code>
      </div>
      <div className="docs-block">
        <h2>Authentication</h2>
        <p className="muted">Include your workspace API key as a Bearer token in the Authorization header.</p>
        <code className="raw-key">Authorization: Bearer &lt;MAISB_API_KEY&gt;</code>
      </div>
      <div className="docs-block">
        <h2>Response fields</h2>
        <ul className="docs-list muted">
          <li><code>decision</code> — ALLOWED, REVIEW, or BLOCKED</li>
          <li><code>risk_score</code> — calibrated score from 0.0 to 1.0</li>
          <li><code>reasons</code> — detected risk patterns</li>
          <li><code>trace_id</code> — cross-channel trace identifier</li>
        </ul>
      </div>
      <p className="docs-note muted">Full reference documentation is being expanded. Start with a free API key from the dashboard.</p>
    </DocsLayout>
  )
}
