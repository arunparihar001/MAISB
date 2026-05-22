import Badge from './Badge'
import Button from './Button'
import Card from './Card'

type Props = {
  name: string
  code: string
  price: string
  features: string[]
  comingSoon?: boolean
  onSelect: () => void
  actionLabel: string
}

export default function PlanCard({ name, code, price, features, comingSoon, onSelect, actionLabel }: Props) {
  return (
    <Card title={name} subtitle={price} className={code === 'free' ? 'plan-highlight' : ''}>
      <ul className="bullet-list">
        {features.map((feature) => (
          <li key={feature}>{feature}</li>
        ))}
      </ul>
      {comingSoon && <Badge>Coming soon</Badge>}
      <div style={{ marginTop: '0.9rem' }}>
        <Button onClick={onSelect}>{actionLabel}</Button>
      </div>
    </Card>
  )
}
