import { Link } from 'react-router-dom'
import Button from '../Button'

export default function PricingHero() {
  return (
    <section className="pricing-hero">
      <div className="pricing-hero__backdrop" aria-hidden="true" />
      <div className="pricing-hero__glow" aria-hidden="true" />
      <div className="pricing-hero__content">
        <p className="eyebrow">Pricing</p>
        <h1>Simple pricing for every stage of AI security.</h1>
        <p className="pricing-hero__lead">
          Start free, scale with your mobile AI applications, and upgrade when your organization needs advanced governance and certification.
        </p>
        <div className="pricing-hero__actions">
          <Link to="/signup"><Button className="pricing-btn">Start for free</Button></Link>
          <a href="mailto:sales@maisb.app"><Button variant="secondary" className="pricing-btn">Contact sales</Button></a>
        </div>
      </div>
    </section>
  )
}
