type Row = {
  id: string
  status: string
  type: string
  created: string
}

type Props = {
  rows: Row[]
}

export default function RiskQueueTable({ rows }: Props) {
  return (
    <div className="card">
      <h3>Risk Queue</h3>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Type</th>
            <th>Status</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={4}>No rows available</td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr key={row.id}>
                <td>{row.id}</td>
                <td>{row.type}</td>
                <td>{row.status}</td>
                <td>{row.created}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}
