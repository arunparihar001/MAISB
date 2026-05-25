import { Link } from 'react-router-dom'
import Button from '../components/Button'
import Card from '../components/Card'
import Badge from '../components/Badge'

export default function DocsApi() {
  return (
    <main className="public-shell">
      <div className="page-head">
        <div>
          <p className="eyebrow">Documentation</p>
          <h1>API Reference</h1>
          <p className="muted">Complete reference for the MAISB boundary protection API.</p>
        </div>
        <Link to="/docs"><Button variant="secondary">Back to docs</Button></Link>
      </div>

      {/* Base URL & Auth */}
      <section style={{ marginBottom: '3rem' }} id="base">
        <div className="grid two-col">
          <Card title="Base URL" subtitle="Production API endpoint">
            <div style={{ backgroundColor: '#0f172a', padding: '1rem', borderRadius: '8px', marginBottom: '1rem', fontSize: '0.9rem', color: '#cbd5e1', fontFamily: 'monospace', wordBreak: 'break-all' }}>
              https://api.maisb.app
            </div>
            <p className="muted">All requests must use HTTPS. Plain HTTP requests are rejected.</p>
          </Card>
          <Card title="Authentication" subtitle="Bearer token format">
            <div style={{ backgroundColor: '#0f172a', padding: '1rem', borderRadius: '8px', marginBottom: '1rem' }}>
              <p style={{ margin: 0, fontSize: '0.85rem', color: '#cbd5e1', fontFamily: 'monospace', wordBreak: 'break-all' }}>Authorization: Bearer {'{MAISB_API_KEY}'}</p>
            </div>
            <p className="muted">Generate API keys from your <Link to="/api-keys" style={{ color: '#67e8f9' }}>dashboard API keys page</Link>. Include the key in every request header.</p>
          </Card>
        </div>
      </section>

      <section id="auth" style={{ marginBottom: '3rem' }} />

      {/* POST /v1/scan */}
      <section style={{ marginBottom: '3rem' }} id="endpoint">
        <Card title="POST /v1/scan" subtitle="Scan channel content for boundary violations">
          <p className="muted" style={{ marginBottom: '1.5rem' }}>Scan untrusted channel content (clipboard, QR code, notification, deep link, WebView input) for prompt injection, malware, and other security threats. Returns a risk assessment and security decision.</p>

          <div style={{ marginBottom: '1.5rem' }}>
            <p style={{ fontWeight: 600, marginBottom: '0.75rem' }}>Request body (JSON):</p>
            <div style={{ backgroundColor: '#0f172a', padding: '1rem', borderRadius: '8px', overflow: 'auto', marginBottom: '1rem', fontSize: '0.85rem', lineHeight: '1.5', color: '#cbd5e1', fontFamily: 'monospace' }}>
              <pre style={{ margin: 0 }}>
{`{
  "channel": "clipboard|qr_code|notification|deep_link|nfc|share_intent|webview",
  "content": "The untrusted channel content to scan",
  "agent_id": "your-ai-agent-identifier",
  "session_id": "optional-session-or-user-identifier"
}`}
              </pre>
            </div>
            <ul className="bullet-list" style={{ margin: 0, fontSize: '0.9rem' }}>
              <li><strong>channel</strong> (string, required): Source channel (clipboard, qr_code, notification, deep_link, nfc, share_intent, webview)</li>
              <li><strong>content</strong> (string, required): The channel content to scan (max 10KB)</li>
              <li><strong>agent_id</strong> (string, required): Your mobile AI agent identifier</li>
              <li><strong>session_id</strong> (string, optional): Session or user ID for trace correlation</li>
            </ul>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <p style={{ fontWeight: 600, marginBottom: '0.75rem' }}>Response (200 OK):</p>
            <div style={{ backgroundColor: '#0f172a', padding: '1rem', borderRadius: '8px', overflow: 'auto', marginBottom: '1rem', fontSize: '0.85rem', lineHeight: '1.5', color: '#cbd5e1', fontFamily: 'monospace' }}>
              <pre style={{ margin: 0 }}>
{`{
  "decision": "ALLOWED|BLOCKED|REVIEW",
  "risk_score": 0.94,
  "taxonomy_class": "prompt_injection|malware|spam|suspicious|clean",
  "trace_id": "trace-unique-identifier",
  "boundary_status": "untrusted",
  "metadata": {
    "content_type": "text|url|code",
    "content_length": 142,
    "detection_rules": ["rule_1", "rule_2"]
  }
}`}
              </pre>
            </div>
            <ul className="bullet-list" style={{ margin: 0, fontSize: '0.9rem' }}>
              <li><strong>decision</strong> (string): ALLOWED (safe to pass to LLM), BLOCKED (reject immediately), REVIEW (log for manual review)</li>
              <li><strong>risk_score</strong> (number 0-1): Threat confidence (0 = safe, 1 = critical)</li>
              <li><strong>taxonomy_class</strong> (string): Threat classification</li>
              <li><strong>trace_id</strong> (string): Unique request identifier for audit logs</li>
              <li><strong>boundary_status</strong> (string): Always "untrusted" (channels are not trusted sources)</li>
              <li><strong>metadata</strong> (object): Detection details and rules matched</li>
            </ul>
          </div>

          <div>
            <p style={{ fontWeight: 600, marginBottom: '0.75rem' }}>Error responses (4xx, 5xx):</p>
            <ul className="bullet-list" style={{ margin: 0, fontSize: '0.9rem' }}>
              <li><strong>400 Bad Request</strong>: Invalid request format or missing required fields</li>
              <li><strong>401 Unauthorized</strong>: API key is missing or invalid</li>
              <li><strong>403 Forbidden</strong>: API key lacks permissions or quota exceeded</li>
              <li><strong>429 Too Many Requests</strong>: Rate limit exceeded</li>
              <li><strong>500 Internal Server Error</strong>: Server error (safe to retry)</li>
            </ul>
          </div>
        </Card>
      </section>

      {/* Rate Limits & Key Rotation */}
      <section style={{ marginBottom: '3rem' }}>
        <div className="grid two-col">
          <Card title="Rate Limits" subtitle="Production quotas by plan">
            <ul className="bullet-list" style={{ margin: 0, fontSize: '0.9rem' }}>
              <li><strong>Free:</strong> 100 scans/day, burst limit 10/sec</li>
              <li><strong>Pro:</strong> 10,000 scans/day, burst limit 100/sec</li>
              <li><strong>Enterprise:</strong> Custom limits based on SLA</li>
            </ul>
            <p className="muted" style={{ marginTop: '1rem', fontSize: '0.9rem' }}>When rate limit is exceeded, the API returns <code style={{ color: '#cbd5e1' }}>429 Too Many Requests</code>. Use exponential backoff for retries.</p>
          </Card>
          <Card title="API Key Rotation" subtitle="Manage keys securely">
            <p className="muted" style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>Generate new keys and revoke old ones anytime from your <Link to="/api-keys" style={{ color: '#67e8f9' }}>dashboard</Link>. Old keys are revoked immediately and cannot be reused.</p>
            <div style={{ padding: '1rem', backgroundColor: 'rgba(34, 197, 94, 0.1)', borderRadius: '8px', borderLeft: '3px solid #a3e635' }}>
              <p style={{ margin: 0, fontWeight: 600, color: '#a3e635', fontSize: '0.9rem' }}>✓ Tip: Rotate keys monthly for production workloads</p>
            </div>
          </Card>
        </div>
      </section>

      {/* Examples */}
      <section style={{ marginBottom: '3rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <p className="eyebrow">Code examples</p>
          <h2>Common implementations</h2>
        </div>

        <div style={{ display: 'grid', gap: '1.5rem' }}>
          <Card title="cURL" subtitle="Quick test from command line">
            <div style={{ backgroundColor: '#0f172a', padding: '1rem', borderRadius: '8px', overflow: 'auto', fontSize: '0.85rem', lineHeight: '1.5', color: '#cbd5e1', fontFamily: 'monospace' }}>
              <pre style={{ margin: 0 }}>
{`curl -X POST https://api.maisb.app/v1/scan \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "channel": "clipboard",
    "content": "Paste your test content here",
    "agent_id": "test-agent",
    "session_id": "session-123"
  }'`}
              </pre>
            </div>
          </Card>

          <Card title="JavaScript/TypeScript" subtitle="Using fetch API">
            <div style={{ backgroundColor: '#0f172a', padding: '1rem', borderRadius: '8px', overflow: 'auto', fontSize: '0.85rem', lineHeight: '1.5', color: '#cbd5e1', fontFamily: 'monospace' }}>
              <pre style={{ margin: 0 }}>
{`const response = await fetch('https://api.maisb.app/v1/scan', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    channel: 'clipboard',
    content: 'your-content',
    agent_id: 'my-agent',
    session_id: 'session-123'
  })
});

const result = await response.json();
if (result.decision === 'BLOCKED') {
  console.log('Threat detected:', result.risk_score);
}`}
              </pre>
            </div>
          </Card>

          <Card title="Python" subtitle="Using requests library">
            <div style={{ backgroundColor: '#0f172a', padding: '1rem', borderRadius: '8px', overflow: 'auto', fontSize: '0.85rem', lineHeight: '1.5', color: '#cbd5e1', fontFamily: 'monospace' }}>
              <pre style={{ margin: 0 }}>
{`import requests

response = requests.post(
    'https://api.maisb.app/v1/scan',
    headers={
        'Authorization': 'Bearer YOUR_API_KEY',
        'Content-Type': 'application/json'
    },
    json={
        'channel': 'clipboard',
        'content': 'your-content',
        'agent_id': 'my-agent',
        'session_id': 'session-123'
    }
)

result = response.json()
if result['decision'] == 'BLOCKED':
    print(f"Threat detected: {result['risk_score']}")`}
              </pre>
            </div>
          </Card>
        </div>
      </section>

      {/* Boundary Protection Concept */}
      <section style={{ marginBottom: '3rem' }} id="boundary">
        <Card title="Boundary Protection Concept" subtitle="Why every channel is untrusted">
          <div style={{ display: 'grid', gap: '1rem' }}>
            <div>
              <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Mobile channels are untrusted boundaries</p>
              <p className="muted" style={{ fontSize: '0.9rem' }}>Clipboard, QR codes, notifications, deep links, and WebViews can all be manipulated by attackers. MAISB treats all external channel input as potentially malicious.</p>
            </div>
            <div>
              <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Every scan is a boundary check</p>
              <p className="muted" style={{ fontSize: '0.9rem' }}>Before passing channel content to your LLM, scan it with /v1/scan. The API returns a security decision (ALLOWED, BLOCKED, or REVIEW) and risk score.</p>
            </div>
            <div>
              <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Decision types guide your response</p>
              <p className="muted" style={{ fontSize: '0.9rem' }}><strong>ALLOWED:</strong> Safe, pass to LLM. <strong>BLOCKED:</strong> Reject immediately. <strong>REVIEW:</strong> Log and route to security team.</p>
            </div>
          </div>
        </Card>
      </section>

      {/* Security Note */}
      <section style={{ marginBottom: '3rem' }}>
        <Card title="Data Security" subtitle="How we protect your scans">
          <div style={{ padding: '1rem', backgroundColor: 'rgba(34, 197, 94, 0.1)', borderRadius: '8px', borderLeft: '3px solid #a3e635', marginBottom: '1rem' }}>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#cbd5e1' }}>✓ <strong>Raw payload storage is disabled by default.</strong> Security events retain metadata for auditability.</p>
          </div>
          <p className="muted" style={{ fontSize: '0.9rem' }}>Only scan metadata, decisions, and audit traces are stored. Raw user content is never persisted to disk. All data is encrypted in transit and at rest.</p>
        </Card>
      </section>

      {/* Next Steps */}
      <section style={{ textAlign: 'center' }}>
        <h2>Ready to integrate?</h2>
        <p className="hero-lead" style={{ maxWidth: '60ch', margin: '1rem auto' }}>
          View SDK guides, code examples, or start with the curl example above.
        </p>
        <div className="row-inline" style={{ justifyContent: 'center' }}>
          <Link to="/docs/sdk"><Button variant="secondary">SDK Guides →</Button></Link>
          <Link to="/docs/examples"><Button variant="secondary">Code Examples →</Button></Link>
        </div>
      </section>
    </main>
  )
}
