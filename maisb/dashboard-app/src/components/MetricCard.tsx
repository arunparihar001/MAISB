type Props = { title: string; value: string | number; hint?: string }

export default function MetricCard({ title, value, hint }: Props) {
  return (
    <div className="card metric-card">
      <p>{title}</p>
      <h3>{value}</h3>
      {hint && <small>{hint}</small>}
    </div>
  )
}
