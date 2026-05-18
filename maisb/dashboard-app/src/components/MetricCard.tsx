type Props = {
  title: string
  value: string | number
}

export default function MetricCard({ title, value }: Props) {
  return (
    <div className="card metric-card">
      <p>{title}</p>
      <h3>{value}</h3>
    </div>
  )
}
