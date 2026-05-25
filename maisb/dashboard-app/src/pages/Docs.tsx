import { Link } from 'react-router-dom'
import Button from '../components/Button'
import Card from '../components/Card'
import Badge from '../components/Badge'

export default function Docs() {
  return (
    <main className="public-shell">
      <div className="page-head">
        <div>
          <p className="eyebrow">Documentation</p>
          <h1>Build with MAISB</h1>
          <p className="muted">Use the MAISB API and SDK patterns to secure mobile AI agents before untrusted channel content reaches the LLM.</p>
        </div>
        <Link to="/signup"><Button>Get started free</Button></Link>
      </div>

      {/* Quick Links */}
      <section style={{ marginBottom: '3rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <p className="eyebrow">Quick start</p>
          <h2>Find what you need</h2>
        </div>
        <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
          <Link to="/docs/api" style={{ textDecoration: 'none' }}>
            <Card title="API Reference" subtitle="Endpoint specs and examples">
              <p className="muted">Base URL, authentication, POST /v1/scan, request/response formats, error handling.</p>
            </Card>
          </Link>
          <Link to="/docs/sdk" style={{ textDecoration: 'none' }}>
            <Card title="SDK Guides" subtitle="Client implementations">
              <p className="muted">JavaScript, Python, Android/Kotlin starter clients and integration patterns.</p>
            </Card>
          </Link>
          <Link to="/docs/examples" style={{ textDecoration: 'none' }}>
            <Card title="Code Examples" subtitle="Real-world scenarios">
              <p className="muted">Clipboard, QR codes, notifications, deep links, WebViews, and cross-channel tracing.</p>
            </Card>
          </Link>
          <Link to="/docs/api#auth" style={{ textDecoration: 'none' }}>
            <Card title="Authentication" subtitle="API key setup">
              <p className="muted">Generate API keys, Bearer token format, key rotation, and security best practices.</p>
            </Card>
          </Link>
          <Link to="/docs/api#boundary" style={{ textDecoration: 'none' }}>
            <Card title="Boundary Protection" subtitle="Core concepts">
              <p className="muted">Mobile channel trust, boundary scanning, decision types, and risk scoring.</p>
            </Card>
          </Link>
          <Link to="/docs/examples#trace" style={{ textDecoration: 'none' }}>
            <Card title="Cross-Channel Trace" subtitle="Advanced security">
              <p className="muted">Trace context across QR, clipboard, deep links, and workflow paths to the LLM.</p>
            </Card>
          </Link>
        </div>
      </section>

      {/* Getting Started */}
      <section style={{ marginBottom: '3rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <p className="eyebrow">Getting started</p>
          <h2>Your secure onboarding path</h2>
        </div>
        <div style={{ display: 'grid', gap: '1rem' }}>
          <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'flex-start' }}>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#67e8f9', minWidth: '3rem' }}>1</div>
            <div>
              <p style={{ fontWeight: 600, marginBottom: '0.5rem' }}>Create account</p>
              <p className="muted">Sign up with email and password. Verify your email address to unlock your workspace.</p>
              <Link to="/signup" style={{ fontSize: '0.9rem' }}>Start signup →</Link>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'flex-start' }}>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#67e8f9', minWidth: '3rem' }}>2</div>
            <div>
              <p style={{ fontWeight: 600, marginBottom: '0.5rem' }}>Verify email</p>
              <p className="muted">Check your inbox for the verification token. Paste it to confirm account ownership.</p>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'flex-start' }}>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#67e8f9', minWidth: '3rem' }}>3</div>
            <div>
              <p style={{ fontWeight: 600, marginBottom: '0.5rem' }}>Select Free plan</p>
              <p className="muted">Free tier starts immediately with sample data and full API access to evaluate MAISB.</p>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'flex-start' }}>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#67e8f9', minWidth: '3rem' }}>4</div>
            <div>
              <p style={{ fontWeight: 600, marginBottom: '0.5rem' }}>Generate API key</p>
              <p className="muted">Create your first API key from the dashboard. Use it to authenticate /v1/scan requests.</p>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'flex-start' }}>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#67e8f9', minWidth: '3rem' }}>5</div>
            <div>
              <p style={{ fontWeight: 600, marginBottom: '0.5rem' }}>Send first request</p>
              <p className="muted">Use curl or your preferred HTTP client to send a boundary scan request to /v1/scan.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Curl Example */}
      <section style={{ marginBottom: '3rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <p className="eyebrow">Quick example</p>
          <h2>Your first API request</h2>
        </div>
        <Card title="POST /v1/scan" subtitle="Scan clipboard content for boundary violations">
          <div style={{ backgroundColor: '#0f172a', padding: '1rem', borderRadius: '8px', overflow: 'auto', marginBottom: '1rem' }}>
            <pre style={{ margin: 0, fontSize: '0.85rem', lineHeight: '1.5', color: '#cbd5e1', fontFamily: 'monospace' }}>
{`curl -X POST https://api.maisb.app/v1/scan \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "channel": "clipboard",
    "content": "User-provided text from clipboard",
    "agent_id": "my-ai-agent-123",
    "session_id": "session-456"
  }'`}
            </pre>
          </div>
          <p className="muted" style={{ marginBottom: '1rem' }}>Response:</p>
          <div style={{ backgroundColor: '#0f172a', padding: '1rem', borderRadius: '8px', overflow: 'auto' }}>
            <pre style={{ margin: 0, fontSize: '0.85rem', lineHeight: '1.5', color: '#cbd5e1', fontFamily: 'monospace' }}>
{`{
  "decision": "BLOCKED",
  "risk_score": 0.94,
  "taxonomy_class": "prompt_injection",
  "trace_id": "trace-789abc",
  "boundary_status": "untrusted"
}`}
            </pre>
          </div>
        </Card>
      </section>

      {/* Security Note */}
      <section style={{ marginBottom: '3rem' }}>
        <Card title="Security & Data Handling" subtitle="What we protect">
          <div style={{ display: 'grid', gap: '1rem' }}>
            <div>
              <p style={{ fontWeight: 600, marginBottom: '0.25rem', color: '#a3e635' }}>✓ Raw payload storage is disabled by default</p>
              <p className="muted" style={{ fontSize: '0.9rem' }}>Only metadata, decisions, and audit traces are retained for compliance.</p>
            </div>
            <div>
              <p style={{ fontWeight: 600, marginBottom: '0.25rem', color: '#a3e635' }}>✓ Security events retain metadata for auditability</p>
              <p className="muted" style={{ fontSize: '0.9rem' }}>Audit trails track all API calls and decisions without storing raw user input.</p>
            </div>
            <div>
              <p style={{ fontWeight: 600, marginBottom: '0.25rem', color: '#a3e635' }}>✓ API key rotation available</p>
              <p className="muted" style={{ fontSize: '0.9rem' }}>Rotate keys anytime from your dashboard. Old keys are revoked immediately.</p>
            </div>
          </div>
        </Card>
      </section>

      {/* CTA */}
      <section style={{ textAlign: 'center' }}>
        <h2>Ready to start?</h2>
        <p className="hero-lead" style={{ maxWidth: '60ch', margin: '1rem auto' }}>
          Create a free account, generate an API key, and begin protecting your mobile AI channels today.
        </p>
        <div className="row-inline" style={{ justifyContent: 'center' }}>
          <Link to="/signup"><Button>Start free</Button></Link>
          <Link to="/docs/api"><Button variant="secondary">See API reference →</Button></Link>
        </div>
      </section>
    </main>
  )
}
