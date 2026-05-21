import { Link } from 'react-router-dom'

export default function PublicFooter() {
  return (
    <footer>
      <Link to="/pricing">Pricing</Link>
      <Link to="/terms">Terms</Link>
      <Link to="/privacy">Privacy</Link>
      <Link to="/refund">Refund</Link>
      <a href="mailto:support@maisb.app">Contact</a>
      <a href="mailto:support@maisb.app">support@maisb.app</a>
      <a href="mailto:sales@maisb.app">sales@maisb.app</a>
    </footer>
  )
}
