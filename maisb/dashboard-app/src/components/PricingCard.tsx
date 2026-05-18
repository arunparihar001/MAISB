type Plan = {
  id: string
  name: string
  price: string
  features: string[]
}

type Props = {
  plan: Plan
}

export default function PricingCard({ plan }: Props) {
  return (
    <div className="card">
      <h3>{plan.name}</h3>
      <p>{plan.price}</p>
      <ul>
        {plan.features.map((feature) => (
          <li key={feature}>{feature}</li>
        ))}
      </ul>
    </div>
  )
}
