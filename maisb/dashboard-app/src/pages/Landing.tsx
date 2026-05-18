import { Link } from 'react-router-dom'

export default function Landing() {
  return (
    <main className="public-page">
      <h1>MAISB</h1>
      <p>Protect mobile AI agents from prompt injection across real-world channels.</p>
      <div className="row">
        <Link to="/pricing">Pricing</Link>
        <Link to="/signup">Start free</Link>
        <Link to="/login">Login</Link>
      </div>
    </main>
  )
}
