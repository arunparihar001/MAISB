interface Plan {
  id: string
  name: string
  price: string
  limit: number | null
  features: string[]
}

export default function PricingCard({ plan }: { plan: Plan }) {
  return (
    <article className="card pricing-card">
      <h3>{plan.name}</h3>
      <p className="price">{plan.price}</p>
      <p className="muted">{plan.limit ? `${plan.limit.toLocaleString()} scans / month` : 'Custom limits'}</p>
      <ul>{plan.features.map((feature) => <li key={feature}>{feature}</li>)}</ul>
    </article>
  )
}
