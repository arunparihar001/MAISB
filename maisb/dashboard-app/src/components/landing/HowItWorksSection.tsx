import LandingSection from './LandingSection'

const STEPS = [
  {
    step: '01',
    title: 'Capture mobile channel context',
    body: 'Your app sends channel metadata and content to POST /v1/scan. MAISB receives clipboard, QR, notification, deep link, share intent, NFC, and WebView context in a single API call.',
  },
  {
    step: '02',
    title: 'Score runtime risk and trace cross-channel behavior',
    body: 'MAISB evaluates prompt-injection patterns, channel reputation, and cross-channel sequences. Returns risk_score (0.0–1.0), trace_id, and cross_channel_trace status.',
  },
  {
    step: '03',
    title: 'Allow, review, or block before LLM execution',
    body: 'Enforce the decision in your app. Low-risk content reaches the LLM. Medium-risk enters a review queue. High-risk is blocked immediately — with full audit evidence in the dashboard.',
  },
]

export default function HowItWorksSection() {
  return (
    <LandingSection
      eyebrow="How MAISB works"
      title="A three-step runtime boundary workflow"
      lead="From channel capture to LLM enforcement — every scan is scored, traced, and logged."
    >
      <div className="landing-workflow">
        {STEPS.map((item, index) => (
          <div key={item.step} className="landing-workflow__item">
            {index > 0 && <div className="landing-workflow__connector" aria-hidden="true" />}
            <article className="landing-workflow__card">
              <span className="landing-workflow__step">{item.step}</span>
              <h3>{item.title}</h3>
              <p className="muted">{item.body}</p>
            </article>
          </div>
        ))}
      </div>
    </LandingSection>
  )
}
