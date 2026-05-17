export default function MetricCard({ label, value }: { label: string; value: string | number }) {
  return <div className="card"><p>{label}</p><h3>{value}</h3></div>
}
