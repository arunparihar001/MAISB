export type RiskRow = { id: string; status: string; type: string; created: string; severity?: string }

type Props = { title?: string; rows: RiskRow[] }

export default function RiskQueueTable({ title = 'Risk Queue', rows }: Props) {
  return (
    <div className="card table-card">
      <h3>{title}</h3>
      <table>
        <thead><tr><th>ID</th><th>Type</th><th>Status</th><th>Severity</th><th>Created</th></tr></thead>
        <tbody>
          {rows.length === 0 ? (
            <tr><td colSpan={5}>No rows available.</td></tr>
          ) : rows.map((row) => (
            <tr key={`${row.type}-${row.id}`}>
              <td>{row.id}</td><td>{row.type}</td><td>{row.status}</td><td>{row.severity || '—'}</td><td>{row.created || '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
