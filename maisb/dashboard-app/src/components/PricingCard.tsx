export default function PricingCard({ title, price, points }: { title: string; price: string; points: string[] }) {
  return <div className="card"><h3>{title}</h3><p>{price}</p><ul>{points.map((p) => <li key={p}>{p}</li>)}</ul></div>
}
