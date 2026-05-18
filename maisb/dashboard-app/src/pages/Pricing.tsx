import { Link } from 'react-router-dom'

export default function Pricing() {
  return (
    <main className="public-page legal">
      <h1>Pricing</h1>
      <p>MAISB pricing supports free developer trials, Pro subscriptions, Enterprise contracts, and MAISB Certify assessments.</p>
      <ul>
        <li>Free: $0 for integration and development.</li>
        <li>Pro: monthly subscription managed via Paddle or approved invoice workflow.</li>
        <li>Enterprise: annual contract with SOC and compliance support.</li>
        <li>Certify: assessment package quoted per target application.</li>
      </ul>
      <p>Payment processing may be provided by Paddle (merchant of record). Taxes and obligations follow Paddle checkout jurisdiction and transaction metadata.</p>
      <p>Need a formal quote? Visit <Link to="/signup">Signup</Link> and submit a billing request from the dashboard.</p>
    </main>
  )
}
