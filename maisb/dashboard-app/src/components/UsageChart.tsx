export default function UsageChart({ used, limit }: { used: number; limit: number }) {
  const pct = limit > 0 ? Math.min(100, Math.round((used / limit) * 100)) : 0
  return (
    <div className="card">
      <p>Usage</p>
      <div className="bar"><span style={{ width: `${pct}%` }} /></div>
      <small>{used} / {limit}</small>
    </div>
  )
}
