type PricingCardProps = {
  name: string
  price: string
  features: string[]
}

export default function PricingCard({ name, price, features }: PricingCardProps) {
  return (
    <article className="pricing-card">
      <h3>{name}</h3>
      <p className="price">{price}</p>
      <ul>{features.map((feature) => <li key={feature}>{feature}</li>)}</ul>
    </article>
  )
}
