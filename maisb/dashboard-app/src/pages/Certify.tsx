import Badge from '../components/Badge'
import Card from '../components/Card'
import CertifyBadge from '../components/CertifyBadge'

export default function Certify() {
  return (
    <main className="stack">
      <div className="page-head">
        <div>
          <p className="eyebrow">Security compliance</p>
          <h1>Certify</h1>
          <p className="muted">Compliance reporting and certification workflows for enterprise review.</p>
        </div>
        <Badge>Sample data</Badge>
      </div>
      <Card title="MAISB Certify" actions={<CertifyBadge grade="A" />}>
        <p className="muted">Certify onboarding is in staged rollout. Request invoice/contact sales to begin enterprise certification workflows.</p>
        <ul className="bullet-list">
          <li>Boundary tracing evidence</li>
          <li>Security event summary</li>
          <li>Audit-ready status badge</li>
        </ul>
      </Card>
    </main>
  )
}
