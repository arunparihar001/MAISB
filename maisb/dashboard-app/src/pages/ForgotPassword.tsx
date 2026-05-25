import { Link } from 'react-router-dom'
import Button from '../components/Button'
import Card from '../components/Card'

export default function ForgotPassword() {
  return (
    <main className="onboarding-page">
      <div className="grid two-col" style={{ alignItems: 'start', gap: '2rem' }}>
        <div className="glass-card" style={{ padding: '2rem' }}>
          <p className="eyebrow">Account recovery</p>
          <h1>Password recovery</h1>
          <p className="muted" style={{ marginBottom: '1.5rem' }}>
            Password recovery is being configured. Our team is setting up the account recovery workflow.
          </p>
          <p style={{ marginBottom: '1.5rem', padding: '1rem', backgroundColor: 'rgba(217, 119, 6, 0.1)', borderRadius: '8px', borderLeft: '3px solid #f59e0b', color: '#cbd5e1', fontSize: '0.9rem' }}>
            <strong>⏳ In the meantime:</strong> If you need account access, contact support at <a href="mailto:support@maisb.app" style={{ color: '#67e8f9' }}>support@maisb.app</a>. Provide your email address and we'll help you recover your account.
          </p>

          <div style={{ marginBottom: '1.5rem' }}>
            <Link to="/login" style={{ display: 'inline-block' }}>
              <Button variant="secondary">Back to login</Button>
            </Link>
          </div>
        </div>

        <div style={{ display: 'grid', gap: '1.5rem' }}>
          <Card title="Account security" subtitle="How we protect your account">
            <ul className="bullet-list" style={{ margin: 0 }}>
              <li>Email-based account verification</li>
              <li>Secure password hashing</li>
              <li>Session-based authentication</li>
              <li>Audit logs of all account changes</li>
              <li>Encrypted credential storage</li>
            </ul>
          </Card>

          <Card title="What happens next?" subtitle="Password recovery steps">
            <ol style={{ margin: 0, fontSize: '0.9rem', lineHeight: '1.8' }}>
              <li>Once recovery workflow is live, you can reset your password via email link</li>
              <li>Check your inbox for a password reset token</li>
              <li>Click the link to set a new password (min 8 characters)</li>
              <li>Login with your new password</li>
            </ol>
          </Card>

          <Card title="Having trouble?" subtitle="We're here to help">
            <p className="muted" style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>
              If you need immediate account access or have security concerns, contact our support team.
            </p>
            <a href="mailto:support@maisb.app">
              <Button variant="secondary">Email support</Button>
            </a>
          </Card>
        </div>
      </div>
    </main>
  )
}
