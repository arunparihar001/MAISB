import { Link } from 'react-router-dom'
import Button from '../components/Button'
import LandingNav from '../components/LandingNav'
import HeroVisual from '../components/HeroVisual'
import TrustStrip from '../components/landing/TrustStrip'
import ProblemSection from '../components/landing/ProblemSection'
import HowItWorksSection from '../components/landing/HowItWorksSection'
import ProductCapabilitiesSection from '../components/landing/ProductCapabilitiesSection'
import DashboardPreviewSection from '../components/landing/DashboardPreviewSection'
import DeveloperSection from '../components/landing/DeveloperSection'
import MobileChannelsSection from '../components/landing/MobileChannelsSection'
import PricingPreviewSection from '../components/landing/PricingPreviewSection'
import FinalCtaSection from '../components/landing/FinalCtaSection'
import LandingFooter from '../components/landing/LandingFooter'

export default function Landing() {
  return (
    <>
      <LandingNav />
      <main className="public-shell landing-page">
        <section className="landing-hero">
          <div className="landing-hero__backdrop" aria-hidden="true" />
          <div className="landing-hero__grid">
            <div className="landing-hero__copy">
              <p className="eyebrow landing-hero__eyebrow">Enterprise mobile AI security</p>
              <h1 className="landing-hero__title">
                Stop malicious mobile context before it reaches your AI agent.
              </h1>
              <p className="hero-lead landing-hero__lead">
                MAISB protects mobile AI agents across clipboard, QR, notifications, deep links, NFC, share intents, and WebViews with runtime risk scoring and cross-channel traceability.
              </p>
              <div className="landing-hero__ctas">
                <Link to="/signup"><Button className="landing-hero__btn">Start for free</Button></Link>
                <Link to="/docs/api">
                  <Button variant="secondary" className="landing-hero__btn">View API docs</Button>
                </Link>
              </div>
              <div className="landing-hero__trust">
                <span>Metadata-only scanning</span>
                <span aria-hidden="true">·</span>
                <span>API-first workflow</span>
                <span aria-hidden="true">·</span>
                <span>Audit-ready exports</span>
              </div>
            </div>
            <div className="landing-hero__visual">
              <HeroVisual />
            </div>
          </div>
        </section>

        <TrustStrip />
        <ProblemSection />
        <HowItWorksSection />
        <ProductCapabilitiesSection />
        <DashboardPreviewSection />
        <DeveloperSection />
        <MobileChannelsSection />
        <PricingPreviewSection />
        <FinalCtaSection />
        <LandingFooter />
      </main>
    </>
  )
}
