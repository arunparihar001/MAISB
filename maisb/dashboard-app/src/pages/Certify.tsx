import Badge from '../components/Badge'
import Button from '../components/Button'
import Card from '../components/Card'
import CertifyBadge from '../components/CertifyBadge'

export default function Certify() {
  return (
    <main className="stack">
      <div className="page-head">
        <div>
          <p className="eyebrow">Security compliance</p>
          <h1>MAISB Certify</h1>
          <p className="muted">Runtime security assessment and verification badge for enterprise AI deployments.</p>
        </div>
        <Badge>Enterprise offering</Badge>
      </div>

      <Card title="What is Certify?" actions={<CertifyBadge grade="A" />}>
        <p className="muted">
          MAISB Certify is a comprehensive runtime security assessment service. We audit your boundary protection implementation, trace cross-channel attack patterns, and deliver a verification badge package. Use Certify to demonstrate AI safety controls to boards, auditors, and enterprise partners.
        </p>
        <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <Badge>Runtime assessment</Badge>
          <Badge>Audit evidence</Badge>
          <Badge>Verification badge</Badge>
        </div>
      </Card>

      <section className="grid two-col">
        <Card title="The assessment process" subtitle="5-step enterprise workflow">
          <ol className="bullet-list" style={{ margin: 0 }}>
            <li><strong>Intake:</strong> Review your MAISB deployment, API keys, and security posture.</li>
            <li><strong>Tracing:</strong> Analyze boundary protection logs and cross-channel trace data.</li>
            <li><strong>Testing:</strong> Execute controlled attack patterns to verify detection effectiveness.</li>
            <li><strong>Reporting:</strong> Generate compliance report with evidence and scoring.</li>
            <li><strong>Badge:</strong> Receive verification badge (A+, A, B+, B) for your dashboard and website.</li>
          </ol>
        </Card>

        <Card title="Deliverables" subtitle="Complete certification package">
          <ul className="bullet-list" style={{ margin: 0 }}>
            <li>60-page compliance report with evidence</li>
            <li>Boundary protection assessment score</li>
            <li>Cross-channel trace analysis</li>
            <li>Security event summary</li>
            <li>Verification badge (for website/dashboard)</li>
            <li>30-minute executive briefing</li>
            <li>12-month validity period</li>
            <li>Renewal guidance and roadmap</li>
          </ul>
        </Card>
      </section>

      <section className="grid">
        <Card title="Assessment criteria" subtitle="How we score your deployment">
          <div style={{ display: 'grid', gap: '1.25rem' }}>
            <div>
              <p style={{ marginBottom: '0.35rem', fontWeight: 500 }}>Channel coverage</p>
              <p className="muted" style={{ fontSize: '0.9rem' }}>Are all mobile channels (clipboard, QR, notifications, deep links, NFC, WebViews, share intents) protected?</p>
            </div>
            <div>
              <p style={{ marginBottom: '0.35rem', fontWeight: 500 }}>Risk scoring accuracy</p>
              <p className="muted" style={{ fontSize: '0.9rem' }}>Does your policy detect prompt injection, instruction embedding, and context manipulation?</p>
            </div>
            <div>
              <p style={{ marginBottom: '0.35rem', fontWeight: 500 }}>Cross-channel tracing</p>
              <p className="muted" style={{ fontSize: '0.9rem' }}>Can you link channel sequences and detect multi-vector attacks?</p>
            </div>
            <div>
              <p style={{ marginBottom: '0.35rem', fontWeight: 500 }}>Metadata-only posture</p>
              <p className="muted" style={{ fontSize: '0.9rem' }}>Are raw payloads never stored? Are audit traces sanitized?</p>
            </div>
            <div>
              <p style={{ marginBottom: '0.35rem', fontWeight: 500 }}>Team & governance</p>
              <p className="muted" style={{ fontSize: '0.9rem' }}>Can your team audit decisions, rotate keys, and report on security posture?</p>
            </div>
          </div>
        </Card>

        <Card title="Verification badge grades" subtitle="What your score means">
          <div style={{ display: 'grid', gap: '1.25rem' }}>
            <div style={{ paddingBottom: '1rem', borderBottom: '1px solid rgba(148, 163, 184, 0.12)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#22c55e' }}>A+</span>
                <strong>Excellent</strong>
              </div>
              <p className="muted" style={{ fontSize: '0.9rem', margin: 0 }}>Enterprise-grade implementation. All channels protected, advanced cross-channel tracing, comprehensive governance.</p>
            </div>
            <div style={{ paddingBottom: '1rem', borderBottom: '1px solid rgba(148, 163, 184, 0.12)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#84cc16' }}>A</span>
                <strong>Very good</strong>
              </div>
              <p className="muted" style={{ fontSize: '0.9rem', margin: 0 }}>Strong boundary protection. Core channels covered, tracing functional, governance in place.</p>
            </div>
            <div style={{ paddingBottom: '1rem', borderBottom: '1px solid rgba(148, 163, 184, 0.12)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#fbbf24' }}>B+</span>
                <strong>Good</strong>
              </div>
              <p className="muted" style={{ fontSize: '0.9rem', margin: 0 }}>Solid foundation. Most channels covered, basic tracing, clear roadmap for improvement.</p>
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#fb923c' }}>B</span>
                <strong>Fair</strong>
              </div>
              <p className="muted" style={{ fontSize: '0.9rem', margin: 0 }}>Baseline protection. Key channels covered. Recommended improvements for production.</p>
            </div>
          </div>
        </Card>
      </section>

      <Card title="How MAISB Certify helps your enterprise" subtitle="Real-world use cases">
        <div style={{ display: 'grid', gap: '1rem' }}>
          <div>
            <p style={{ marginBottom: '0.35rem', fontWeight: 500 }}>📋 Board reporting</p>
            <p className="muted" style={{ fontSize: '0.9rem', margin: 0 }}>Share Certify badge and report with your board. Demonstrates that AI agent safety is being actively managed.</p>
          </div>
          <div>
            <p style={{ marginBottom: '0.35rem', fontWeight: 500 }}>🔍 Audit readiness</p>
            <p className="muted" style={{ fontSize: '0.9rem', margin: 0 }}>Use Certify evidence in SOC 2, HIPAA, and PCI audit responses. Metadata-only architecture aligns with compliance requirements.</p>
          </div>
          <div>
            <p style={{ marginBottom: '0.35rem', fontWeight: 500 }}>🤝 Customer trust</p>
            <p className="muted" style={{ fontSize: '0.9rem', margin: 0 }}>Enterprise customers often require proof of AI safety controls before adoption. Certify badge demonstrates your commitment.</p>
          </div>
          <div>
            <p style={{ marginBottom: '0.35rem', fontWeight: 500 }}>🛡️ Security partnerships</p>
            <p className="muted" style={{ fontSize: '0.9rem', margin: 0 }}>Partner programs and vendor assessments often request security certifications. Certify provides the evidence needed.</p>
          </div>
        </div>
      </Card>

      <section className="grid two-col">
        <Card title="Certify is included in:" subtitle="Enterprise & Certify plans">
          <ul className="bullet-list" style={{ margin: 0 }}>
            <li>MAISB Certify tier (annual)</li>
            <li>MAISB Enterprise tier (included)</li>
            <li>Renewal every 12 months</li>
            <li>Access to dedicated security engineer</li>
            <li>Priority support on assessments</li>
          </ul>
        </Card>

        <Card title="Ready to get certified?" subtitle="Request your Certify assessment">
          <p className="muted">
            MAISB Certify is available for qualified enterprises. Our team will work with you to schedule an assessment, review your deployment, and deliver your verification badge.
          </p>
          <div style={{ marginTop: '1rem' }}>
            <a href="mailto:sales@maisb.app"><Button>Contact sales</Button></a>
          </div>
        </Card>
      </section>

      <Card title="Frequently asked about Certify" subtitle="Key details">
        <div style={{ display: 'grid', gap: '1.5rem' }}>
          <div>
            <p style={{ marginBottom: '0.35rem', fontWeight: 500 }}>How long is an assessment?</p>
            <p className="muted" style={{ fontSize: '0.9rem', margin: 0 }}>2-3 weeks from intake to final report. Includes async communication, test execution, and reporting.</p>
          </div>
          <div>
            <p style={{ marginBottom: '0.35rem', fontWeight: 500 }}>What if I don't get an A+?</p>
            <p className="muted" style={{ fontSize: '0.9rem', margin: 0 }}>Certify reports always include a clear roadmap for improvement. We recommend actions to strengthen your posture before the next cycle.</p>
          </div>
          <div>
            <p style={{ marginBottom: '0.35rem', fontWeight: 500 }}>Can I renew my Certify?</p>
            <p className="muted" style={{ fontSize: '0.9rem', margin: 0 }}>Yes. Certify is valid for 12 months. Renewal assessments typically take 1-2 weeks and often show improved scores as you enhance your deployment.</p>
          </div>
          <div>
            <p style={{ marginBottom: '0.35rem', fontWeight: 500 }}>How much does Certify cost?</p>
            <p className="muted" style={{ fontSize: '0.9rem', margin: 0 }}>Certify is available as a standalone tier or included with Enterprise. Contact sales@maisb.app for pricing based on your deployment size.</p>
          </div>
        </div>
      </Card>
    </main>
  )
}
