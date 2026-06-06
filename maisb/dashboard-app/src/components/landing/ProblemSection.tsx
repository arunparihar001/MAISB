import LandingSection from './LandingSection'

const POINTS = [
  {
    title: 'Untrusted channel ingestion',
    body: 'Mobile AI agents ingest content from clipboard, QR codes, notifications, deep links, share sheets, NFC tags, and WebViews — each a potential injection vector.',
  },
  {
    title: 'Cross-channel prompt injection',
    body: 'Attackers split instructions across channels. A QR scan followed by a clipboard paste can bypass single-point defenses and poison agent context.',
  },
  {
    title: 'Traditional app security gaps',
    body: 'Network firewalls and static analysis do not inspect AI-bound context at runtime. Content passes through to the LLM without a dedicated security boundary.',
  },
  {
    title: 'MAISB runtime boundary',
    body: 'MAISB creates a runtime security boundary before content reaches the LLM — scoring risk, tracing cross-channel behavior, and enforcing allow, review, or block decisions.',
  },
]

export default function ProblemSection() {
  return (
    <LandingSection
      eyebrow="The mobile AI attack surface"
      title="Traditional security was not built for AI-bound mobile context"
      lead="Every mobile channel is untrusted input. MAISB inspects that context at runtime — before your agent executes."
    >
      <div className="landing-problem">
        {POINTS.map((point, index) => (
          <article key={point.title} className="landing-problem__card">
            <span className="landing-problem__index">{String(index + 1).padStart(2, '0')}</span>
            <div>
              <h3>{point.title}</h3>
              <p className="muted">{point.body}</p>
            </div>
          </article>
        ))}
      </div>
    </LandingSection>
  )
}
