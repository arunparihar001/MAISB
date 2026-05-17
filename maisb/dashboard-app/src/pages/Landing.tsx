import PricingCard from '../components/PricingCard'

export default function Landing() {
  return (
    <main className="marketing">
      <section className="hero">
        <p className="eyebrow">Enterprise Mobile AI Security</p>
        <h1>AI Runtime Security for Mobile & Fintech Applications</h1>
        <p>MAISB blocks prompt-injection attacks across clipboard, deep links, notifications, QR, and WebView before payloads reach your models.</p>
        <div>
          <a className="btn" href="https://app.maisb.app/signup">Start Free</a>
          <a className="btn btn-secondary" href="/pricing">View Pricing</a>
        </div>
      </section>

      <section><h2>Problem</h2><p>Mobile-agent input channels are high-risk injection surfaces that can silently override user intent.</p></section>
      <section><h2>How MAISB works</h2><p>Analyze incoming payloads, assign risk and taxonomy, enforce allow/review/block policy, then stream telemetry into SOC workflows.</p></section>
      <section><h2>Android SDK</h2><p>Production-ready Android SDK integrates directly with <code>https://api.maisb.app</code>.</p></section>
      <section><h2>SOC dashboard</h2><p>Track incidents, prioritize risk queue entries, and coordinate investigation actions from one operator console.</p></section>
      <section><h2>MAISB Certify</h2><p>Run benchmark-driven assessments and receive enterprise-ready report PDFs and verification badges.</p></section>

      <section>
        <h2>Pricing</h2>
        <div className="grid">
          <PricingCard title="Free Developer" price="$0 / month" points={["Core scan API", "Community support", "Developer onboarding"]} />
          <PricingCard title="Pro" price="Commercial" points={["Higher quota", "Email support", "Billing-ready upgrades"]} />
          <PricingCard title="Enterprise" price="Custom" points={["SOC workflows", "Policy controls", "Enterprise onboarding"]} />
          <PricingCard title="MAISB Certify" price="Assessment" points={["Benchmark run", "PDF report", "Badge verification"]} />
        </div>
      </section>

      <section><h2>Contact</h2><p>Contact <a href="mailto:sales@maisb.app">sales@maisb.app</a> for pilot onboarding, procurement, and compliance support.</p></section>
    </main>
  )
}
