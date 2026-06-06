import { Link } from 'react-router-dom'
import Button from '../Button'
import LandingSection from './LandingSection'

const HIGHLIGHTS = [
  'Free developer access',
  'Pro production scale',
  'Certify and Enterprise governance',
]

export default function PricingPreviewSection() {
  return (
    <LandingSection
      id="pricing"
      eyebrow="Enterprise pricing"
      title="Pricing built for every stage of mobile AI security."
      lead="Start free, scale with production scan volume, and upgrade when your organization needs governance, certification, private deployment, or enterprise support."
    >
      <div className="landing-pricing-teaser">
        <ul className="landing-pricing-teaser__highlights">
          {HIGHLIGHTS.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
        <div className="landing-pricing-teaser__actions">
          <Link to="/pricing">
            <Button>View Pricing</Button>
          </Link>
          <a href="mailto:sales@maisb.app">
            <Button variant="secondary">Contact Sales</Button>
          </a>
        </div>
      </div>
    </LandingSection>
  )
}
