import Card from './Card'

type Props = { label: string; value: string | number; hint?: string }

export default function StatCard({ label, value, hint }: Props) {
  return (
    <Card className="stat-card">
      <p className="muted">{label}</p>
      <strong>{value}</strong>
      {hint && <small className="muted">{hint}</small>}
    </Card>
  )
}
