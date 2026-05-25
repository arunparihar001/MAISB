import { useState } from 'react'
import Badge from '../components/Badge'
import Button from '../components/Button'
import Card from '../components/Card'
import { apiRequest, downloadWithAuth } from '../lib/api'

export default function Reports() {
  const [message, setMessage] = useState('')

  async function generateCompliance() {
    setMessage('')
    try {
      const data = await apiRequest<{ report_id: string; status: string }>('/v1/reports/compliance', {
        method: 'POST',
        body: JSON.stringify({ framework: 'soc2' }),
      })
      setMessage(`Compliance report ${data.report_id} is ${data.status}.`)
    } catch (err) {
      setMessage((err as Error).message)
    }
  }

  return (
    <main className="stack">
      <div className="page-head">
        <div>
          <p className="eyebrow">Reporting & exports</p>
          <h1>Reports</h1>
          <p className="muted">Export audit evidence and generate compliance-ready reports. Metadata only—raw payloads are never included.</p>
        </div>
        <Badge>Metadata-only</Badge>
      </div>

      <section className="grid two-col">
        <Card title="Export CSV" subtitle="Tabular scan data">
          <p className="muted">Export boundary scans, decisions, risk scores, and channel metadata as CSV. Perfect for spreadsheet analysis and data warehouse ingestion.</p>
          <div style={{ marginTop: '1rem' }}>
            <Button variant="secondary" onClick={() => downloadWithAuth('/v1/reports/export.csv', 'maisb-report.csv')}>
              Download CSV
            </Button>
          </div>
        </Card>

        <Card title="Export JSON" subtitle="Structured audit evidence">
          <p className="muted">Export complete scan records, traces, decisions, and timeline data as JSON. Includes cross-channel trace IDs and boundary metadata.</p>
          <div style={{ marginTop: '1rem' }}>
            <Button variant="secondary" onClick={() => downloadWithAuth('/v1/reports/export.json', 'maisb-report.json')}>
              Download JSON
            </Button>
          </div>
        </Card>
      </section>

      <section className="grid two-col">
        <Card title="Generate Compliance Report" subtitle="SOC 2 & audit frameworks">
          <p className="muted">Generate a compliance-ready report summarizing boundary protection, metadata-only architecture, and audit trails. Use for SOC 2 Type II reviews, HIPAA/PCI audits, and board reporting.</p>
          <div style={{ marginTop: '1rem' }}>
            <Button onClick={generateCompliance}>
              Generate SOC 2 Report
            </Button>
          </div>
        </Card>

        <Card title="Schedule Report" subtitle="Automated delivery (Pro+)">
          <p className="muted">Set up recurring weekly or monthly report exports. Delivered to email or webhook. Includes all audit evidence needed for compliance teams.</p>
          <div style={{ marginTop: '1rem' }}>
            <Badge>Coming soon</Badge>
          </div>
        </Card>
      </section>

      <section className="grid">
        <Card title="What's included in exports" subtitle="Comprehensive audit data">
          <ul className="bullet-list" style={{ margin: 0 }}>
            <li>Scan metadata (timestamp, channel, content preview hash)</li>
            <li>Security decisions (ALLOWED, REVIEW, BLOCKED)</li>
            <li>Risk scores and scoring rationale</li>
            <li>Cross-channel trace IDs and attack patterns</li>
            <li>Boundary health indicators per channel</li>
            <li>API key usage and access logs</li>
            <li>Team activity and permission changes</li>
            <li>Compliance audit trail</li>
          </ul>
        </Card>

        <Card title="What's NOT included" subtitle="Privacy by design">
          <ul className="bullet-list" style={{ margin: 0 }}>
            <li>Raw payload content (never stored)</li>
            <li>PII or sensitive data fragments</li>
            <li>Unredacted user information</li>
            <li>Backend configuration or secrets</li>
            <li>API key material (only key_prefix shown)</li>
          </ul>
        </Card>
      </section>

      {message && <p className="notice">{message}</p>}
    </main>
  )
}
