export type Plan = { id: string; name: string; price: string; features: string[]; cta?: string }

type Props = { plan: Plan; action?: () => void }

export default function PricingCard({ plan, action }: Props) {
  return (
    <div className={plan.id === 'pro' ? 'card pricing-card highlighted' : 'card pricing-card'}>
      <h3>{plan.name}</h3>
      <p className="price">{plan.price}</p>
      <ul>{plan.features.map((feature) => <li key={feature}>{feature}</li>)}</ul>
      {action && <button type="button" onClick={action}>{plan.cta || 'Select'}</button>}
    </div>
  )
}
