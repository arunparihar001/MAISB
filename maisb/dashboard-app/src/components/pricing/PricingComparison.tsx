type Row = {
  feature: string
  free: string
  pro: string
  certify: string
  enterprise: string
}

const ROWS: Row[] = [
  { feature: 'Monthly scans', free: '5,000', pro: '100,000', certify: '1,000,000', enterprise: 'Unlimited' },
  { feature: 'API keys', free: '2', pro: 'Unlimited', certify: 'Unlimited', enterprise: 'Unlimited' },
  { feature: 'Workspaces', free: '1', pro: '1', certify: '3', enterprise: 'Unlimited' },
  { feature: 'Analytics', free: 'Basic', pro: 'Advanced', certify: 'Advanced', enterprise: 'Advanced' },
  { feature: 'Compliance reports', free: '—', pro: '—', certify: '✓', enterprise: '✓' },
  { feature: 'SSO', free: '—', pro: '—', certify: '—', enterprise: '✓' },
  { feature: 'Priority support', free: '—', pro: 'Email', certify: 'Priority', enterprise: '24/7 SLA' },
  { feature: 'On-prem deployment', free: '—', pro: '—', certify: '—', enterprise: '✓' },
]

export default function PricingComparison() {
  return (
    <section className="pricing-compare">
      <header className="pricing-compare__head">
        <p className="eyebrow">Compare plans</p>
        <h2>Feature comparison across tiers</h2>
      </header>
      <div className="pricing-compare__wrap table-wrap">
        <table className="pricing-compare__table">
          <thead>
            <tr>
              <th>Feature</th>
              <th>Free</th>
              <th>Pro</th>
              <th>Certify</th>
              <th>Enterprise</th>
            </tr>
          </thead>
          <tbody>
            {ROWS.map((row) => (
              <tr key={row.feature}>
                <td>{row.feature}</td>
                <td>{row.free}</td>
                <td>{row.pro}</td>
                <td>{row.certify}</td>
                <td>{row.enterprise}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
