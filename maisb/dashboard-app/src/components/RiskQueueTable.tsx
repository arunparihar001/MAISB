interface RiskItem {
  event_id?: string
  trace_id?: string
  channel?: string
  decision?: string
  risk_score?: number
}

export default function RiskQueueTable({ items }: { items: RiskItem[] }) {
  return (
    <div className="card">
      <h3>Risk Queue</h3>
      <table>
        <thead>
          <tr><th>Trace/Event</th><th>Channel</th><th>Decision</th><th>Risk</th></tr>
        </thead>
        <tbody>
          {items.slice(0, 8).map((item, idx) => (
            <tr key={`${item.event_id || 'evt'}-${item.trace_id || 'trace'}-${idx}`}>
              <td>{item.trace_id || item.event_id || '-'}</td>
              <td>{item.channel || '-'}</td>
              <td>{item.decision || '-'}</td>
              <td>{item.risk_score ?? '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
