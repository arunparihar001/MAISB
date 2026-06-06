import { Link } from 'react-router-dom'

export default function LandingFooter() {
  return (
    <footer className="landing-footer">
      <div className="landing-footer__grid">
        <div>
          <p className="landing-footer__heading">Product</p>
          <ul className="landing-footer__links">
            <li><a href="#features">Features</a></li>
            <li><Link to="/pricing">Pricing</Link></li>
            <li><Link to="/security">Security</Link></li>
            <li><Link to="/docs">Documentation</Link></li>
          </ul>
        </div>
        <div>
          <p className="landing-footer__heading">Developers</p>
          <ul className="landing-footer__links">
            <li><Link to="/developers">Developers</Link></li>
            <li><Link to="/docs/api">API Reference</Link></li>
            <li><Link to="/docs/sdk">SDK Guides</Link></li>
            <li><Link to="/docs/examples">Code Examples</Link></li>
          </ul>
        </div>
        <div>
          <p className="landing-footer__heading">Company</p>
          <ul className="landing-footer__links">
            <li><a href="https://maisb.app/about">About</a></li>
            <li><a href="https://maisb.app/blog">Blog</a></li>
            <li><a href="https://maisb.app/contact">Contact</a></li>
          </ul>
        </div>
        <div>
          <p className="landing-footer__heading">Legal</p>
          <ul className="landing-footer__links">
            <li><Link to="/terms">Terms</Link></li>
            <li><Link to="/privacy">Privacy</Link></li>
            <li><Link to="/refund">Refund</Link></li>
          </ul>
        </div>
      </div>
      <p className="landing-footer__copy muted">© 2026 MAISB. Mobile AI Security Boundary.</p>
    </footer>
  )
}
