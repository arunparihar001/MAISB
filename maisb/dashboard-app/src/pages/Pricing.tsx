import { Link } from 'react-router-dom'

export default function Pricing() {
  return (
    <main className="marketing legal">
      <h1>Pricing</h1>
      <p>MAISB plans are designed for production AI security teams with predictable metering and enterprise-ready support.</p>
      <h2>Free Developer</h2>
      <p>$0/month. Includes runtime scan API access and dashboard essentials for prototyping and evaluation.</p>
      <h2>Pro</h2>
      <p>Commercial monthly subscription for teams requiring higher quotas, usage insights, and email support.</p>
      <h2>Enterprise</h2>
      <p>Custom plan with SOC workflows, deployment controls, and procurement support for regulated environments.</p>
      <h2>MAISB Certify</h2>
      <p>One-time or recurring assessment package with report PDF and badge issuance for security review workflows.</p>
      <p className="muted">By purchasing, you agree to our <Link to="/terms">Terms</Link>, <Link to="/privacy">Privacy Policy</Link>, and <Link to="/refund">Refund Policy</Link>.</p>
    </main>
  )
}
