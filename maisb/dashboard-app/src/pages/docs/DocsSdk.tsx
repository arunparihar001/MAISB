import DocsLayout from '../../components/docs/DocsLayout'

export default function DocsSdk() {
  return (
    <DocsLayout
      eyebrow="SDK Guides"
      title="Mobile SDK Integration"
      description="Integrate MAISB boundary scans into iOS and Android apps at the point where untrusted channel content is captured."
    >
      <div className="docs-block">
        <h2>Integration pattern</h2>
        <p className="muted">
          Call the scan API when your app receives clipboard paste, QR scan results, notification actions,
          deep link payloads, share intents, NFC reads, or WebView context — before forwarding to your AI agent.
        </p>
      </div>
      <div className="docs-block">
        <h2>Recommended flow</h2>
        <ol className="docs-list muted">
          <li>Capture channel metadata and content preview</li>
          <li>POST to /v1/scan with your API key</li>
          <li>Enforce the returned decision in-app</li>
          <li>Log trace_id for cross-channel correlation</li>
        </ol>
      </div>
      <p className="docs-note muted">Platform-specific SDK guides are being published. Use the REST API to integrate today.</p>
    </DocsLayout>
  )
}
