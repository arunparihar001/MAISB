const TRUST_POINTS = [
  'API First',
  'Runtime Boundary Protection',
  'No Payload Storage',
  'Enterprise SLA',
  'Regional Deployment',
]

export default function PricingTrustBar() {
  return (
    <section className="pricing-trust" aria-label="Enterprise trust">
      <ul className="pricing-trust__list">
        {TRUST_POINTS.map((point) => (
          <li key={point} className="pricing-trust__item">
            <span className="pricing-trust__dot" aria-hidden="true" />
            {point}
          </li>
        ))}
      </ul>
    </section>
  )
}
