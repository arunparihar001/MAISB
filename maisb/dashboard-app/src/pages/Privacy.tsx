export default function Privacy() {
  return (
    <main className="marketing legal">
      <h1>Privacy Policy</h1>
      <p>MAISB processes customer security telemetry to deliver runtime protection and dashboard reporting.</p>
      <h2>Data Processed</h2>
      <p>We process account metadata, API usage totals, selected telemetry fields, and support/billing records required to provide service.</p>
      <h2>Credential Handling</h2>
      <p>Dashboard authentication stores API keys in browser localStorage on the customer device. Keys are never embedded in dashboard route URLs.</p>
      <h2>Billing Data</h2>
      <p>Payments are processed by approved providers. MAISB stores minimal billing metadata and webhook status updates for subscription lifecycle handling.</p>
      <h2>Retention and Security</h2>
      <p>Operational logs and SOC records are retained according to platform policy and access-controlled by administrative authorization.</p>
      <h2>User Rights</h2>
      <p>Customers can request data access or deletion for account-level records as permitted by applicable law and contractual obligations.</p>
    </main>
  )
}
