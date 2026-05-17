import PricingCard from '../components/PricingCard'

export default function Landing() {
  return (
    <main className="marketing">
      <section><h1>AI Runtime Security for Mobile & Fintech Applications</h1><p>Protect AI agents from prompt-injection before payloads reach models.</p></section>
      <section><h2>Problem</h2><p>Mobile channels such as clipboard, deep links, QR, notifications, and WebView can inject malicious instructions.</p></section>
      <section><h2>How MAISB works</h2><p>MAISB scans payloads, scores risk, classifies taxonomy, and returns clear enforcement decisions.</p></section>
      <section><h2>Android SDK</h2><p>Production-ready Android SDK integrated with https://api.maisb.app.</p></section>
      <section><h2>SOC dashboard</h2><p>Monitor risk queues, case workflows, and response activity from a centralized console.</p></section>
      <section><h2>MAISB Certify</h2><p>Order benchmark assessments with PDF reports and verification badges for enterprise trust.</p></section>
      <section><h2>Pricing</h2><div className="grid"><PricingCard title="Free Developer" price="$0" points={["Basic scan quota", "Community support"]} /><PricingCard title="Pro" price="Paid" points={["Higher quota", "Email support"]} /><PricingCard title="Enterprise" price="Custom" points={["SOC workflows", "Policy controls"]} /><PricingCard title="MAISB Certify" price="Assessment" points={["PDF report", "Badge"]} /></div></section>
      <section><h2>Contact</h2><p>Email sales@maisb.app for onboarding and enterprise support.</p></section>
    </main>
  )
}
