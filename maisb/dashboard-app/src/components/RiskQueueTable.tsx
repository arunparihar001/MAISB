export default function RiskQueueTable({ rows }: { rows: Array<Record<string, unknown>> }) {
  return (
    <div className="card">
      <p>Risk Queue</p>
      <table>
        <thead><tr><th>ID</th><th>Severity</th><th>Status</th></tr></thead>
        <tbody>
          {rows.slice(0, 5).map((row, i) => (
            <tr key={i}><td>{String(row.case_id || row.id || '—')}</td><td>{String(row.severity || '—')}</td><td>{String(row.status || 'open')}</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
