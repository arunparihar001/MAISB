import LandingSection from './LandingSection'
import {
  BoundaryIcon,
  CertifyIcon,
  ChartIcon,
  EventsIcon,
  InjectionIcon,
  RiskIcon,
  SdkIcon,
  TraceIcon,
} from './LandingIcons'

const CAPABILITIES = [
  {
    icon: BoundaryIcon,
    title: 'Boundary Protection',
    subtitle: 'Channel-aware enforcement',
    body: 'Treat every mobile channel as an untrusted boundary. Score and enforce policy per channel before content reaches your agent.',
  },
  {
    icon: TraceIcon,
    title: 'Cross-Channel Trace Engine',
    subtitle: 'Coordinated attack detection',
    body: 'Link channel sequences with trace_id. Detect multi-step injection campaigns that single-channel tools miss entirely.',
  },
  {
    icon: RiskIcon,
    title: 'Runtime Risk Scoring',
    subtitle: '0.0–1.0 confidence scale',
    body: 'Every scan returns a calibrated risk_score and decision. Tune thresholds per workspace and channel type.',
  },
  {
    icon: InjectionIcon,
    title: 'Prompt Injection Detection',
    subtitle: 'Pattern and intent analysis',
    body: 'Detect instruction override, role manipulation, and exfiltration patterns in mobile-bound content at scan time.',
  },
  {
    icon: EventsIcon,
    title: 'Security Events',
    subtitle: 'Audit timeline and exports',
    body: 'Every decision is logged with metadata-only records. Export CSV or JSON for compliance and SOC workflows.',
  },
  {
    icon: SdkIcon,
    title: 'API + SDK Integration',
    subtitle: 'Developer-first deployment',
    body: 'REST API with Bearer auth, SDK guides, and curl-ready examples. Integrate in minutes, not sprints.',
  },
  {
    icon: ChartIcon,
    title: 'Dashboard Analytics',
    subtitle: 'Boundary health at a glance',
    body: 'Scans over time, decision breakdown, risk distribution, and channel reputation — with sample data until live traffic.',
  },
  {
    icon: CertifyIcon,
    title: 'Certify Workflow',
    subtitle: 'Enterprise verification',
    body: 'Runtime security assessment with boundary trace evidence, verification badge package, and compliance reporting.',
  },
]

export default function ProductCapabilitiesSection() {
  return (
    <LandingSection
      id="features"
      eyebrow="Product capabilities"
      title="Enterprise-grade boundary protection for mobile AI"
      lead="Everything security teams and developers need to inspect, score, and enforce mobile AI context at runtime."
    >
      <div className="landing-capabilities">
        {CAPABILITIES.map(({ icon: Icon, title, subtitle, body }) => (
          <article key={title} className="landing-capability">
            <span className="landing-capability__icon">
              <Icon />
            </span>
            <div>
              <h3>{title}</h3>
              <p className="landing-capability__subtitle">{subtitle}</p>
              <p className="muted">{body}</p>
            </div>
          </article>
        ))}
      </div>
    </LandingSection>
  )
}
