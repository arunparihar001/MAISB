import { AuditIcon, CodeIcon, DatabaseIcon, MobileIcon, ShieldIcon } from './LandingIcons'

const TRUST_POINTS = [
  { icon: ShieldIcon, label: 'Metadata-only scanning', detail: 'Pattern and channel signals only' },
  { icon: DatabaseIcon, label: 'No raw payload persistence', detail: 'Content never stored at rest' },
  { icon: CodeIcon, label: 'API-first deployment', detail: 'Integrate with curl in minutes' },
  { icon: MobileIcon, label: 'Built for mobile AI agents', detail: 'Every untrusted channel covered' },
  { icon: AuditIcon, label: 'Dashboard-ready audit trail', detail: 'Export-ready security events' },
]

export default function TrustStrip() {
  return (
    <section id="security" className="landing-trust" aria-label="Trust and security">
      <div className="landing-trust__inner">
        {TRUST_POINTS.map(({ icon: Icon, label, detail }) => (
          <div key={label} className="landing-trust__item">
            <span className="landing-trust__icon">
              <Icon />
            </span>
            <div>
              <p className="landing-trust__label">{label}</p>
              <p className="landing-trust__detail">{detail}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
