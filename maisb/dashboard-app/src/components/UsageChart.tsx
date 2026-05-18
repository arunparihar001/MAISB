type Props = {
  used: number
  limit: number
}

export default function UsageChart({ used, limit }: Props) {
  const percent = limit > 0 ? Math.min(100, Math.round((used / limit) * 100)) : 0
  return (
    <div className="card">
      <p>Monthly usage</p>
      <div className="bar-wrap">
        <div className="bar" style={{ width: `${percent}%` }} />
      </div>
      <small>
        {used} / {limit} scans ({percent}%)
      </small>
    </div>
  )
}
