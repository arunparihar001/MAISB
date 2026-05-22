import { Link } from 'react-router-dom'
import Button from '../components/Button'

export default function Landing() {
  return (
    <main className="public-shell">
      <nav className="public-nav">
        <strong>MAISB</strong>
        <div className="row-inline">
          <Link to="/pricing">Pricing</Link>
          <Link to="/terms">Terms</Link>
          <Link to="/privacy">Privacy</Link>
          <Link to="/refund">Refund</Link>
        </div>
      </nav>

      <section className="hero">
        <p className="eyebrow">Enterprise mobile AI security</p>
        <h1>Cybersecurity control center for AI runtime risk</h1>
        <p>
          MAISB protects mobile AI agents before untrusted channel content reaches the LLM.
          Monitor boundary decisions, cross-channel traces, and security events in one workspace.
        </p>
        <div className="row-inline">
          <Link to="/signup"><Button>Get Started</Button></Link>
          <Link to="/pricing"><Button variant="secondary">View Plans</Button></Link>
        </div>
      </section>
    </main>
  )
}
