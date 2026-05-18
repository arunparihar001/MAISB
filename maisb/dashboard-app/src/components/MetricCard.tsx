type MetricCardProps = {
  title: string
  value: string | number
  subtitle?: string
}

export default function MetricCard({ title, value, subtitle }: MetricCardProps) {
  return (
    <article className="metric-card card">
      <p className="metric-title">{title}</p>
      <h3>{value}</h3>
      {subtitle ? <p className="metric-subtitle">{subtitle}</p> : null}
    </article>
  )
}
