import { Link } from 'react-router-dom'
import Button from '../components/Button'
import Card from '../components/Card'
import Badge from '../components/Badge'

export default function DocsSdk() {
  return (
    <main className="public-shell">
      <div className="page-head">
        <div>
          <p className="eyebrow">Documentation</p>
          <h1>SDK Guides</h1>
          <p className="muted">Client implementations and integration patterns for mobile AI boundary protection.</p>
        </div>
        <Link to="/docs"><Button variant="secondary">Back to docs</Button></Link>
      </div>

      {/* SDK Status */}
      <section style={{ marginBottom: '3rem' }}>
        <Card>
          <div style={{ padding: '1rem', backgroundColor: 'rgba(217, 119, 6, 0.1)', borderRadius: '8px', borderLeft: '3px solid #f59e0b' }}>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#cbd5e1' }}>
              <strong style={{ color: '#f59e0b' }}>📦 SDK Status:</strong> Official SDK packages are in staged rollout. Until then, use the HTTPS API directly or copy the starter clients below.
            </p>
          </div>
        </Card>
      </section>

      {/* Starter Clients */}
      <section style={{ marginBottom: '3rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <p className="eyebrow">Starter clients</p>
          <h2>Ready-to-use implementations</h2>
        </div>

        <div style={{ display: 'grid', gap: '1.5rem' }}>
          {/* JavaScript/TypeScript */}
          <Card title="JavaScript / TypeScript" subtitle="Fetch-based HTTP client for web and Node.js">
            <p className="muted" style={{ marginBottom: '1rem', fontSize: '0.9rem' }}>Copy this client into your project. It handles API key management, request formatting, and error handling.</p>
            <div style={{ backgroundColor: '#0f172a', padding: '1rem', borderRadius: '8px', overflow: 'auto', fontSize: '0.85rem', lineHeight: '1.5', color: '#cbd5e1', fontFamily: 'monospace', marginBottom: '1rem' }}>
              <pre style={{ margin: 0 }}>
{`import type { BoundaryDecision, ScanRequest, ScanResponse } from './types'

const API_BASE = 'https://api.maisb.app'

export class MAISBClient {
  constructor(private apiKey: string) {
    if (!apiKey) throw new Error('MAISB_API_KEY is required')
  }

  async scan(request: ScanRequest): Promise<ScanResponse> {
    const response = await fetch(\`\${API_BASE}/v1/scan\`, {
      method: 'POST',
      headers: {
        'Authorization': \`Bearer \${this.apiKey}\`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(request)
    })

    if (!response.ok) {
      throw new Error(\`Scan failed: \${response.status}\`)
    }

    return response.json()
  }
}

// Usage:
const client = new MAISBClient(process.env.MAISB_API_KEY!)
const result = await client.scan({
  channel: 'clipboard',
  content: 'user-input-here',
  agent_id: 'my-agent',
  session_id: 'session-123'
})

if (result.decision === 'BLOCKED') {
  console.log(\`Blocked at risk: \${result.risk_score}\`)
}`}
              </pre>
            </div>
            <p className="muted" style={{ fontSize: '0.9rem' }}>
              <strong>TypeScript types:</strong> Define ScanRequest with channel, content, agent_id, session_id fields. ScanResponse includes decision (ALLOWED|BLOCKED|REVIEW), risk_score (0-1), taxonomy_class, trace_id, boundary_status, and metadata.
            </p>
          </Card>

          {/* Python */}
          <Card title="Python" subtitle="requests/httpx client for backend services">
            <p className="muted" style={{ marginBottom: '1rem', fontSize: '0.9rem' }}>Use with Python 3.8+. Install with: pip install requests</p>
            <div style={{ backgroundColor: '#0f172a', padding: '1rem', borderRadius: '8px', overflow: 'auto', fontSize: '0.85rem', lineHeight: '1.5', color: '#cbd5e1', fontFamily: 'monospace', marginBottom: '1rem' }}>
              <pre style={{ margin: 0 }}>
{`import requests
from typing import Literal, Optional
from dataclasses import dataclass

API_BASE = 'https://api.maisb.app'

@dataclass
class ScanRequest:
    channel: str
    content: str
    agent_id: str
    session_id: Optional[str] = None

@dataclass
class ScanResponse:
    decision: Literal['ALLOWED', 'BLOCKED', 'REVIEW']
    risk_score: float
    taxonomy_class: str
    trace_id: str
    boundary_status: str

class MAISBClient:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError('MAISB_API_KEY is required')
        self.api_key = api_key

    def scan(self, request: ScanRequest) -> ScanResponse:
        response = requests.post(
            f'{API_BASE}/v1/scan',
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'channel': request.channel,
                'content': request.content,
                'agent_id': request.agent_id,
                'session_id': request.session_id
            }
        )
        response.raise_for_status()
        return ScanResponse(**response.json())

# Usage:
import os
client = MAISBClient(os.environ['MAISB_API_KEY'])
result = client.scan(ScanRequest(
    channel='clipboard',
    content='user-input-here',
    agent_id='my-agent',
    session_id='session-123'
))

if result.decision == 'BLOCKED':
    print(f'Blocked at risk: {result.risk_score}')`}
              </pre>
            </div>
          </Card>

          {/* Android/Kotlin */}
          <Card title="Android / Kotlin" subtitle="Conceptual integration pattern">
            <p className="muted" style={{ marginBottom: '1rem', fontSize: '0.9rem' }}>Pattern for native Android apps using OkHttp. Adapt to your networking library (Retrofit, Apollo, etc).</p>
            <div style={{ backgroundColor: '#0f172a', padding: '1rem', borderRadius: '8px', overflow: 'auto', fontSize: '0.85rem', lineHeight: '1.5', color: '#cbd5e1', fontFamily: 'monospace', marginBottom: '1rem' }}>
              <pre style={{ margin: 0 }}>
{`// MAISBClient.kt - Kotlin with OkHttp
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import kotlinx.serialization.json.*

data class ScanRequest(
    val channel: String,
    val content: String,
    val agent_id: String,
    val session_id: String? = null
)

data class ScanResponse(
    val decision: String, // ALLOWED, BLOCKED, REVIEW
    val risk_score: Double,
    val taxonomy_class: String,
    val trace_id: String,
    val boundary_status: String
)

class MAISBClient(private val apiKey: String) {
    private val client = OkHttpClient()
    private val json = Json { ignoreUnknownKeys = true }

    suspend fun scan(request: ScanRequest): ScanResponse {
        val body = Json.encodeToString(request)
        val okRequest = Request.Builder()
            .url("https://api.maisb.app/v1/scan")
            .addHeader("Authorization", "Bearer $apiKey")
            .post(body.toRequestBody("application/json".toMediaType()))
            .build()

        val response = client.newCall(okRequest).execute()
        if (!response.isSuccessful) throw Exception("Scan failed")
        
        val bodyString = response.body?.string() ?: ""
        return json.decodeFromString(bodyString)
    }
}

// Usage in your Activity/Fragment:
val client = MAISBClient(BuildConfig.MAISB_API_KEY)
val result = client.scan(ScanRequest(
    channel = "clipboard",
    content = clipboardText,
    agent_id = "my-mobile-agent"
))

when (result.decision) {
    "BLOCKED" -> showError("Content blocked at risk \${result.risk_score}")
    "ALLOWED" -> sendToAIAgent(clipboardText)
    "REVIEW" -> logForManualReview(result.trace_id)
}`}
              </pre>
            </div>
          </Card>
        </div>
      </section>

      {/* Integration Patterns */}
      <section style={{ marginBottom: '3rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <p className="eyebrow">Integration patterns</p>
          <h2>Common architectures</h2>
        </div>

        <div className="grid two-col">
          <Card title="API-First Workflow" subtitle="Scan before passing to LLM">
            <ol style={{ margin: 0, fontSize: '0.9rem', lineHeight: '1.8' }}>
              <li>User provides input via mobile channel (clipboard, QR, notification, etc.)</li>
              <li>App extracts content and sends to MAISB API</li>
              <li>API returns decision and risk score</li>
              <li>If ALLOWED, pass to LLM safely</li>
              <li>If BLOCKED, reject and show message</li>
              <li>If REVIEW, log trace_id for manual inspection</li>
            </ol>
          </Card>
          <Card title="SDK-Ready Design" subtitle="Prepare for official SDK rollout">
            <ol style={{ margin: 0, fontSize: '0.9rem', lineHeight: '1.8' }}>
              <li>Build your scanner using HTTP client</li>
              <li>Use types defined in starter clients</li>
              <li>When official SDK is released, replace HTTP calls</li>
              <li>No interface changes required</li>
              <li>Get added security features (caching, retry logic, analytics) automatically</li>
            </ol>
          </Card>
        </div>
      </section>

      {/* Best Practices */}
      <section style={{ marginBottom: '3rem' }}>
        <Card title="Implementation Best Practices" subtitle="Build secure integrations">
          <div style={{ display: 'grid', gap: '1rem' }}>
            <div>
              <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Never hardcode API keys</p>
              <p className="muted" style={{ fontSize: '0.9rem' }}>Use environment variables, secure key management, or backend proxies. For mobile apps, call a backend endpoint that holds the key.</p>
            </div>
            <div>
              <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Implement retry logic</p>
              <p className="muted" style={{ fontSize: '0.9rem' }}>Use exponential backoff for 5xx errors. On timeout, default to safe behavior (BLOCKED or REVIEW).</p>
            </div>
            <div>
              <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Log trace_id for audit</p>
              <p className="muted" style={{ fontSize: '0.9rem' }}>Store trace_id with every scan decision. Use it to correlate with MAISB dashboard events.</p>
            </div>
            <div>
              <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Rotate API keys regularly</p>
              <p className="muted" style={{ fontSize: '0.9rem' }}>Generate new keys monthly. Revoke old keys immediately from your dashboard.</p>
            </div>
            <div>
              <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Monitor risk score distribution</p>
              <p className="muted" style={{ fontSize: '0.9rem' }}>Track which channels and content types have highest risk scores. Use dashboard analytics for insights.</p>
            </div>
          </div>
        </Card>
      </section>

      {/* Next Steps */}
      <section style={{ textAlign: 'center' }}>
        <h2>Ready to build?</h2>
        <p className="hero-lead" style={{ maxWidth: '60ch', margin: '1rem auto' }}>
          Copy a starter client, review code examples, and deploy your boundary protection today.
        </p>
        <div className="row-inline" style={{ justifyContent: 'center' }}>
          <Link to="/docs/examples"><Button variant="secondary">Code Examples →</Button></Link>
          <Link to="/docs/api"><Button variant="secondary">API Reference →</Button></Link>
        </div>
      </section>
    </main>
  )
}
