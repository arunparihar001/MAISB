import { Link } from 'react-router-dom'
import Button from '../components/Button'
import LandingNav from '../components/LandingNav'
import FoundingBanner from '../components/pricing/FoundingBanner'
import PricingComparison from '../components/pricing/PricingComparison'
import PricingFaq from '../components/pricing/PricingFaq'
import PricingHero from '../components/pricing/PricingHero'
import PricingPlans from '../components/pricing/PricingPlans'
import PricingTrustBar from '../components/pricing/PricingTrustBar'

export default function Pricing() {
  return (
    <>
      <LandingNav />
      <main className="public-shell pricing-page">
        <div className="pricing-page__grid" aria-hidden="true" />
        <PricingHero />
        <div className="pricing-divider" aria-hidden="true" />
        <PricingTrustBar />
        <div className="pricing-divider" aria-hidden="true" />
        <FoundingBanner />
        <div className="pricing-divider" aria-hidden="true" />
        <PricingPlans />
        <div className="pricing-divider" aria-hidden="true" />
        <PricingComparison />
        <div className="pricing-divider" aria-hidden="true" />
        <PricingFaq />

        <div className="pricing-divider" aria-hidden="true" />
        <section className="pricing-final-cta">
          <h2>Ready to secure every mobile AI interaction?</h2>
          <div className="pricing-final-cta__actions">
            <Link to="/signup"><Button className="pricing-btn">Start for free</Button></Link>
            <a href="mailto:sales@maisb.app?subject=MAISB%20Enterprise%20Demo">
              <Button variant="secondary" className="pricing-btn">Book a demo</Button>
            </a>
          </div>
        </section>
      </main>
    </>
  )
}
