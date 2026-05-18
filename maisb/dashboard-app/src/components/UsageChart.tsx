export default function UsageChart({ used, limit }: { used: number; limit: number }) {
  const pct = limit > 0 ? Math.min(100, Math.round((used / limit) * 100)) : 0
  return (
    <div className="card">
      <h3>Usage Capacity</h3>
      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${pct}%` }} />
      </div>
      <p className="muted">{used.toLocaleString()} / {limit.toLocaleString()} scans ({pct}%)</p>
    </div>
  )
}
