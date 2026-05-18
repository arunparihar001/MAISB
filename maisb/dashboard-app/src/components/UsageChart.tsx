type UsageChartProps = {
  used: number
  limit: number
}

export default function UsageChart({ used, limit }: UsageChartProps) {
  const pct = limit > 0 ? Math.min(100, Math.round((used / limit) * 100)) : 0
  return (
    <section className="card">
      <h3>Usage</h3>
      <div className="progress-track"><div className="progress-fill" style={{ width: `${pct}%` }} /></div>
      <p className="muted">{used} / {limit} scans this month ({pct}%)</p>
    </section>
  )
}
