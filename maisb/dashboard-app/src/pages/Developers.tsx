import { Link } from 'react-router-dom'
import Button from '../components/Button'
import LandingNav from '../components/LandingNav'
import LandingSection from '../components/landing/LandingSection'
import {
  BellIcon,
  ClipboardIcon,
  LinkIcon,
  NfcIcon,
  QrIcon,
  ShareIcon,
  WebViewIcon,
} from '../components/landing/LandingIcons'
import DecisionCards from '../components/marketing/DecisionCards'
import MarketingHero from '../components/marketing/MarketingHero'

const CHANNELS = [
  { icon: ClipboardIcon, name: 'Clipboard' },
  { icon: QrIcon, name: 'QR codes' },
  { icon: LinkIcon, name: 'Deep links' },
  { icon: BellIcon, name: 'Push notifications' },
  { icon: NfcIcon, name: 'NFC' },
  { icon: ShareIcon, name: 'Share sheets' },
  { icon: WebViewIcon, name: 'WebViews' },
  { icon: ClipboardIcon, name: 'Files and user-generated text' },
]

const WORKFLOW = [
  { step: '01', title: 'Capture mobile-channel input', body: 'Intercept clipboard paste, QR results, notifications, deep links, and other channel context at the point of capture.' },
  { step: '02', title: 'Send context to MAISB', body: 'POST channel metadata and content preview to the scan API. No heavy SDK required to start.' },
  { step: '03', title: 'Receive risk score and decision', body: 'Get a structured response with decision, risk_score, reason codes, and trace_id.' },
  { step: '04', title: 'Enforce block, review, or allow', body: 'Apply the decision in your app before untrusted context reaches the AI model.' },
]

const PRODUCTION = [
  'API-first architecture',
  'Structured risk decisions',
  'Reason codes',
  'Security event logs',
  'CI/CD friendly workflows',
  'Team and API key management',
  'Audit-ready exports on higher plans',
]

const CODE_EXAMPLE = `const result = await maisb.scan({
  channel: "clipboard",
  content: input,
  appId: "mobile-agent"
});

if (result.decision === "BLOCKED") {
  preventModelExecution();
}`

export default function Developers() {
  return (
    <>
      <LandingNav />
      <main className="public-shell marketing-page">
        <div className="marketing-page__grid" aria-hidden="true" />

        <MarketingHero
          eyebrow="Developers"
          title="Build mobile AI apps with runtime security built in."
          subtitle="Use MAISB APIs to inspect mobile-channel inputs, enforce boundary decisions, and generate security events before risky content reaches your AI model."
        >
          <Link to="/docs/api"><Button className="mkt-btn">View API Docs</Button></Link>
          <Link to="/signup"><Button variant="secondary" className="mkt-btn">Start for free</Button></Link>
        </MarketingHero>

        <div className="mkt-divider" aria-hidden="true" />

        <LandingSection
          title="One security layer before model execution."
          lead="MAISB gives developers a runtime checkpoint between untrusted mobile-channel input and AI model execution. Send input context to MAISB, receive a structured decision, and enforce the result inside your app."
        >
          <DecisionCards />
        </LandingSection>

        <div className="mkt-divider" aria-hidden="true" />

        <LandingSection
          title="Protect the inputs mobile AI actually receives."
          lead="Every mobile channel is an untrusted boundary. MAISB scores them consistently through a single API."
        >
          <div className="mkt-channel-grid">
            {CHANNELS.map(({ icon: Icon, name }) => (
              <article key={name} className="mkt-channel-card">
                <span className="mkt-channel-card__icon"><Icon /></span>
                <h3>{name}</h3>
              </article>
            ))}
          </div>
        </LandingSection>

        <div className="mkt-divider" aria-hidden="true" />

        <LandingSection title="Simple integration flow." lead="Four steps from channel capture to enforced boundary decision.">
          <div className="mkt-workflow">
            {WORKFLOW.map((item) => (
              <article key={item.step} className="mkt-workflow__step">
                <span className="mkt-workflow__num">{item.step}</span>
                <div>
                  <h3>{item.title}</h3>
                  <p className="muted">{item.body}</p>
                </div>
              </article>
            ))}
          </div>
        </LandingSection>

        <div className="mkt-divider" aria-hidden="true" />

        <LandingSection title="Example API flow." lead="Static integration pattern — replace with your SDK or REST client.">
          <div className="mkt-code-panel">
            <div className="mkt-code-panel__head">
              <span className="mkt-code-panel__tag">TypeScript</span>
              <span className="muted">Boundary enforcement</span>
            </div>
            <pre className="raw-key mkt-code-panel__pre">{CODE_EXAMPLE}</pre>
          </div>
        </LandingSection>

        <div className="mkt-divider" aria-hidden="true" />

        <LandingSection title="Built for production teams." lead="Operational controls that scale from developer sandboxes to enterprise governance.">
          <ul className="mkt-checklist">
            {PRODUCTION.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </LandingSection>

        <div className="mkt-divider" aria-hidden="true" />

        <section className="mkt-final-cta">
          <h2>Start securing mobile AI inputs today.</h2>
          <div className="mkt-final-cta__actions">
            <Link to="/signup"><Button className="mkt-btn">Start for free</Button></Link>
            <Link to="/pricing"><Button variant="secondary" className="mkt-btn">View Pricing</Button></Link>
          </div>
        </section>
      </main>
    </>
  )
}
