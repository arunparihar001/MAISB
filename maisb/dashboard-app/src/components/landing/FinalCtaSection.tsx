import { Link } from 'react-router-dom'
import Button from '../Button'

export default function FinalCtaSection() {
  return (
    <section className="landing-final-cta">
      <div className="landing-final-cta__inner">
        <h2>Build a runtime security boundary for your mobile AI agents.</h2>
        <p className="landing-final-cta__lead">
          Start with the free tier — sample data, dashboard access, and API keys. Read the docs to integrate your first scan in minutes.
        </p>
        <div className="landing-final-cta__actions">
          <Link to="/signup">
            <Button>Start for free</Button>
          </Link>
          <Link to="/docs">
            <Button variant="secondary">Read the docs</Button>
          </Link>
        </div>
      </div>
    </section>
  )
}
