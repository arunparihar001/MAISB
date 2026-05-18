export default function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="metric-card card">
      <p>{label}</p>
      <h3>{value}</h3>
    </div>
  )
}
