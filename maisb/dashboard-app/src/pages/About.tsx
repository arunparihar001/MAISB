import { Link } from 'react-router-dom'
import Button from '../components/Button'
import Card from '../components/Card'

export default function About() {
  return (
    <main className="public-shell">
      <div className="page-head">
        <div>
          <p className="eyebrow">About MAISB</p>
          <h1>Mobile AI Security Boundary</h1>
          <p className="muted">Protecting mobile AI agents from untrusted channel content before it reaches language models.</p>
        </div>
      </div>

      {/* Mission */}
      <section style={{ marginBottom: '3rem' }}>
        <Card title="Our Mission" subtitle="Secure the mobile AI frontier">
          <p className="muted" style={{ marginBottom: '1rem' }}>
            Mobile applications are the fastest-growing interaction point for AI. But mobile channels—clipboard, QR codes, notifications, deep links, NFC tags, share intents, and WebViews—are fundamentally untrusted boundaries.
          </p>
          <p className="muted" style={{ marginBottom: '1rem' }}>
            Existing security tools assume network boundaries are the primary threat surface. They miss attacks that exploit mobile channels.
          </p>
          <p className="muted">
            MAISB is purpose-built to scan untrusted channel content and protect your AI agents from prompt injection, malware, and coordinated multi-channel attacks before user input ever reaches your language model.
          </p>
        </Card>
      </section>

      {/* Why Mobile Channels are Untrusted */}
      <section style={{ marginBottom: '3rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <p className="eyebrow">Threat landscape</p>
          <h2>Why mobile channels are untrusted boundaries</h2>
        </div>

        <div className="grid two-col">
          <Card title="Clipboard Injection" subtitle="User-controlled data without validation">
            <p className="muted">Attackers can modify clipboard content before users paste into your app. If your AI agent processes clipboard input without validation, malicious instructions override legitimate intent.</p>
          </Card>
          <Card title="QR Code Encoding" subtitle="Arbitrary payloads in physical form">
            <p className="muted">QR codes can encode malicious URLs, scripts, or instructions. Users scanning attacker-controlled QR codes may inject payload directly into your app's AI context.</p>
          </Card>
          <Card title="Notification Hijacking" subtitle="Third-party services compromised">
            <p className="muted">Push notifications appear trustworthy but originate from third-party services. Compromised notification providers or man-in-the-middle attacks can inject malicious content.</p>
          </Card>
          <Card title="Deep Link Manipulation" subtitle="Intent-based prompt injection">
            <p className="muted">Deep links pass arbitrary parameters to your app via the OS. Attackers craft malicious links containing instructions that bypass normal validation.</p>
          </Card>
          <Card title="NFC Tag Exploitation" subtitle="Physical proximity attacks">
            <p className="muted">Near-field communication allows attackers to place NFC tags in public spaces. Nearby users can accidentally trigger malicious payloads.</p>
          </Card>
          <Card title="Share Intent Abuse" subtitle="Cross-app data pipelines">
            <p className="muted">When users share content from other apps via share intent, MAISB validates that data. Malicious apps can inject content into the share pipeline.</p>
          </Card>
          <Card title="WebView Injection" subtitle="Embedded web form attacks">
            <p className="muted">WebViews embed web content in native apps. Attackers can inject scripts or malicious forms that extract user input for AI context.</p>
          </Card>
          <Card title="Context Chaining" subtitle="Multi-channel coordinated attacks">
            <p className="muted">Advanced attacks chain multiple channels to form complete instructions. A QR code provides partial instruction, clipboard completes it, notification triggers execution.</p>
          </Card>
        </div>
      </section>

      {/* Boundary Protection */}
      <section style={{ marginBottom: '3rem' }}>
        <Card title="Boundary Protection Architecture" subtitle="How MAISB secures your AI agents">
          <div style={{ display: 'grid', gap: '1.5rem' }}>
            <div>
              <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>1. Boundary Recognition</p>
              <p className="muted" style={{ fontSize: '0.9rem' }}>MAISB treats all mobile channels as untrusted boundaries. No channel is given default trust.</p>
            </div>
            <div>
              <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>2. Content Scanning</p>
              <p className="muted" style={{ fontSize: '0.9rem' }}>Every piece of content entering a channel is scanned for prompt injection, malware, encoding tricks, and linguistic attacks.</p>
            </div>
            <div>
              <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>3. Risk Scoring</p>
              <p className="muted" style={{ fontSize: '0.9rem' }}>Content is assigned a risk score (0-1). Scores inform decisions: ALLOWED (safe), BLOCKED (reject), REVIEW (manual inspection).</p>
            </div>
            <div>
              <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>4. Decision Enforcement</p>
              <p className="muted" style={{ fontSize: '0.9rem' }}>Your app enforces MAISB decisions. BLOCKED content never reaches the AI agent. REVIEW content is logged for security team analysis.</p>
            </div>
            <div>
              <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>5. Audit & Correlation</p>
              <p className="muted" style={{ fontSize: '0.9rem' }}>Every scan is traced and correlated. Trace IDs allow you to reconstruct attack chains and attribute malicious content to sources.</p>
            </div>
          </div>
        </Card>
      </section>

      {/* Cross-Channel Traceability */}
      <section style={{ marginBottom: '3rem' }}>
        <Card title="Cross-Channel Trace Correlation" subtitle="Detect coordinated multi-channel attacks">
          <p className="muted" style={{ marginBottom: '1.5rem' }}>
            Sophisticated attacks don't rely on single channels. Attackers chain multiple channels to bypass detection.
          </p>
          <p className="muted" style={{ marginBottom: '1.5rem' }}>
            MAISB correlates scans across channels using session IDs and trace IDs. Your dashboard shows the complete attack pattern:
          </p>
          <ul className="bullet-list" style={{ marginBottom: '1.5rem' }}>
            <li>QR code provides partial instruction (e.g., "Transfer $")</li>
            <li>Clipboard contains completion (e.g., "5000 to account 1234")</li>
            <li>Notification triggers execution (e.g., "Complete now")</li>
            <li>Deep link finalizes injection (e.g., "?override_security=true")</li>
          </ul>
          <p className="muted">
            Traditional tools see four independent events. MAISB sees one coordinated attack and blocks it.
          </p>
        </Card>
      </section>

      {/* Metadata-Only Security */}
      <section style={{ marginBottom: '3rem' }}>
        <Card title="Metadata-Only Security Events" subtitle="Audit-ready compliance without payload storage">
          <p className="muted" style={{ marginBottom: '1rem' }}>
            MAISB never stores raw user content. We retain only metadata and decisions:
          </p>
          <ul className="bullet-list" style={{ marginBottom: '1rem' }}>
            <li><strong>Metadata:</strong> Channel type, content length, content type (text/URL/code), detection rules matched</li>
            <li><strong>Decisions:</strong> ALLOWED, BLOCKED, REVIEW, risk score, taxonomy class</li>
            <li><strong>Audit trail:</strong> Timestamp, agent_id, session_id, trace_id, user account</li>
          </ul>
          <p className="muted">
            This design satisfies compliance requirements (demonstrable security events) while protecting user privacy (no raw data retention).
          </p>
        </Card>
      </section>

      {/* Enterprise Security */}
      <section style={{ marginBottom: '3rem' }}>
        <Card title="Enterprise Security by Default" subtitle="Governance and auditability from day one">
          <div style={{ display: 'grid', gap: '1rem' }}>
            <div>
              <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Role-Based Access</p>
              <p className="muted" style={{ fontSize: '0.9rem' }}>Admin, Analyst, Viewer roles control who can generate keys, review events, and export data.</p>
            </div>
            <div>
              <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Audit Logs</p>
              <p className="muted" style={{ fontSize: '0.9rem' }}>Every action (API calls, key rotations, report exports) is logged with timestamps and user attribution.</p>
            </div>
            <div>
              <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Encryption in Transit & at Rest</p>
              <p className="muted" style={{ fontSize: '0.9rem' }}>All data is encrypted using industry-standard algorithms. No plaintext storage.</p>
            </div>
            <div>
              <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Compliance Reports</p>
              <p className="muted" style={{ fontSize: '0.9rem' }}>Export CSV/JSON reports for SOC 2, ISO 27001, and industry audits.</p>
            </div>
          </div>
        </Card>
      </section>

      {/* Call to Action */}
      <section style={{ textAlign: 'center' }}>
        <h2>Protect your mobile AI channels today</h2>
        <p className="hero-lead" style={{ maxWidth: '60ch', margin: '1rem auto' }}>
          Start with free tier and get your first API key in minutes. Evaluate MAISB with sample data, then scale to production.
        </p>
        <div className="row-inline" style={{ justifyContent: 'center' }}>
          <Link to="/signup"><Button>Get started free</Button></Link>
          <Link to="/docs"><Button variant="secondary">Read documentation →</Button></Link>
        </div>
      </section>

      {/* Contact */}
      <section style={{ textAlign: 'center', marginTop: '3rem' }}>
        <p className="muted">
          Questions about MAISB or mobile AI security? <Link to="/contact" style={{ color: '#67e8f9' }}>Contact us →</Link>
        </p>
      </section>
    </main>
  )
}
