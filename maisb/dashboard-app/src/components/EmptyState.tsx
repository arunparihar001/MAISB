import Card from './Card'

type Props = { title: string; message: string }

export default function EmptyState({ title, message }: Props) {
  return (
    <Card className="empty-state">
      <h3>{title}</h3>
      <p className="muted">{message}</p>
    </Card>
  )
}
