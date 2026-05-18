type RiskItem = {
  trace_id?: string
  event_id?: string
  decision?: string
  risk_score?: number
  created_at?: string
  channel?: string
}

type RiskQueueTableProps = {
  items: RiskItem[]
}

export default function RiskQueueTable({ items }: RiskQueueTableProps) {
  return (
    <section className="card">
      <h3>Risk Queue</h3>
      <table className="table">
        <thead><tr><th>Trace</th><th>Channel</th><th>Decision</th><th>Risk</th><th>Created</th></tr></thead>
        <tbody>
          {items.length === 0 ? (
            <tr><td colSpan={5} className="muted">No high-risk items found.</td></tr>
          ) : items.map((item, idx) => (
            <tr key={item.event_id || item.trace_id || `risk-${idx}`}>
              <td>{item.trace_id || '-'}</td><td>{item.channel || '-'}</td><td>{item.decision || '-'}</td><td>{typeof item.risk_score === 'number' ? item.risk_score.toFixed(2) : '-'}</td><td>{item.created_at || '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
