import { Link } from 'react-router-dom'
import Button from '../components/Button'
import LandingNav from '../components/LandingNav'
import LandingSection from '../components/landing/LandingSection'
import DecisionCards from '../components/marketing/DecisionCards'
import MarketingHero from '../components/marketing/MarketingHero'

const THREAT_CHANNELS = [
  'Clipboard',
  'QR codes',
  'Push notifications',
  'Deep links',
  'NFC',
  'Share sheets',
  'WebViews',
  'Files',
  'User-generated text',
]

const DETECTIONS = [
  'Prompt injection attempts',
  'Hidden instruction payloads',
  'Malicious links',
  'Data exfiltration patterns',
  'Unsafe tool-use instructions',
  'Suspicious mobile-channel context',
  'Policy violations',
]

const RUNTIME_POINTS = [
  { title: 'BLOCKED / REVIEW / ALLOWED', body: 'Every scan returns an enforceable decision your app applies before model execution.' },
  { title: 'Risk scoring', body: 'Calibrated risk_score (0.0–1.0) helps tune thresholds per channel and workspace.' },
  { title: 'Reason codes', body: 'Structured reasons explain why content was flagged — useful for SOC review and developer debugging.' },
  { title: 'Audit event creation', body: 'Each decision generates metadata-only security events for timeline and export workflows.' },
]

const PRIVACY = [
  'No payload storage by default',
  'Privacy-preserving runtime analysis',
  'In-memory inspection design',
  'API-first boundary architecture',
  'Enterprise deployment discussions available',
  'Regional and private deployment options for Enterprise customers',
]

const GOVERNANCE = [
  'Security events',
  'Audit logs',
  'Compliance reports',
  'Trace evidence',
  'Certification workflows',
  'Verification badge for Certify customers',
]

export default function SecurityOverview() {
  return (
    <>
      <LandingNav />
      <main className="public-shell marketing-page">
        <div className="marketing-page__grid" aria-hidden="true" />

        <MarketingHero
          eyebrow="Security"
          title="Security for the mobile AI runtime boundary."
          subtitle="MAISB protects mobile AI agents before untrusted mobile-channel input reaches the model."
        >
          <Link to="/pricing"><Button className="mkt-btn">View Pricing</Button></Link>
          <a href="mailto:security@maisb.app"><Button variant="secondary" className="mkt-btn">Contact Security Team</Button></a>
        </MarketingHero>

        <div className="mkt-divider" aria-hidden="true" />

        <LandingSection
          title="Mobile AI creates a new attack surface."
          lead="Mobile AI agents receive input from channels that were never designed as trusted model context. Attackers exploit that gap with hidden prompts, malicious instructions, unsafe links, and data exfiltration attempts."
        >
          <div className="mkt-tag-grid">
            {THREAT_CHANNELS.map((channel) => (
              <span key={channel} className="mkt-tag">{channel}</span>
            ))}
          </div>
        </LandingSection>

        <div className="mkt-divider" aria-hidden="true" />

        <LandingSection title="What MAISB detects." lead="Runtime pattern analysis across mobile-channel context before it becomes model input.">
          <div className="mkt-detect-grid">
            {DETECTIONS.map((item) => (
              <article key={item} className="mkt-detect-card">
                <span className="mkt-detect-card__dot" aria-hidden="true" />
                <h3>{item}</h3>
              </article>
            ))}
          </div>
        </LandingSection>

        <div className="mkt-divider" aria-hidden="true" />

        <LandingSection title="Runtime decision layer." lead="Structured outputs designed for enforcement, review queues, and audit evidence.">
          <DecisionCards />
          <div className="mkt-runtime-grid">
            {RUNTIME_POINTS.map((point) => (
              <article key={point.title} className="mkt-runtime-card">
                <h3>{point.title}</h3>
                <p className="muted">{point.body}</p>
              </article>
            ))}
          </div>
        </LandingSection>

        <div className="mkt-divider" aria-hidden="true" />

        <LandingSection title="Privacy and data handling." lead="Metadata-first architecture built for security teams that cannot store raw mobile content.">
          <ul className="mkt-checklist">
            {PRIVACY.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </LandingSection>

        <div className="mkt-divider" aria-hidden="true" />

        <LandingSection title="Governance and evidence." lead="Operational visibility for security, compliance, and certification workflows.">
          <ul className="mkt-checklist mkt-checklist--cols">
            {GOVERNANCE.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </LandingSection>

        <div className="mkt-divider" aria-hidden="true" />

        <section className="mkt-final-cta mkt-final-cta--security">
          <h2>Deploy mobile AI with runtime security controls.</h2>
          <div className="mkt-final-cta__actions">
            <Link to="/pricing"><Button className="mkt-btn">View Pricing</Button></Link>
            <a href="mailto:sales@maisb.app"><Button variant="secondary" className="mkt-btn">Contact Sales</Button></a>
          </div>
        </section>
      </main>
    </>
  )
}
