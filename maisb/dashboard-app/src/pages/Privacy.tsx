export default function Privacy() {
  return (
    <main className="public-page legal">
      <h1>Privacy Policy</h1>
      <p>MAISB collects account, billing, and operational telemetry data required to deliver security services and support.</p>
      <h2>Data collected</h2>
      <ul>
        <li>Signup profile data: email, company, and intended use case.</li>
        <li>Service telemetry: request metadata, risk events, and SOC workflow records.</li>
        <li>Billing records: purchase and subscription status from payment providers.</li>
      </ul>
      <h2>Use of data</h2>
      <p>Data is used to operate security analysis, investigate abuse, provide customer support, and comply with legal obligations.</p>
      <h2>Third-party processors</h2>
      <p>Paddle may process transactions as merchant of record. Infrastructure providers may process data strictly for hosting and delivery operations.</p>
      <h2>Retention</h2>
      <p>Security event data is retained based on product plan and compliance settings. Customers can request deletion subject to legal and contractual requirements.</p>
    </main>
  )
}
