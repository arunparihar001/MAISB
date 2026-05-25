import { FormEvent, useState } from 'react'
import Button from '../components/Button'
import Card from '../components/Card'

export default function Contact() {
  const [form, setForm] = useState({ name: '', email: '', company: '', use_case: '', message: '' })
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setLoading(true)
    // Placeholder behavior: just show success message
    // No actual backend contact endpoint exists yet
    setTimeout(() => {
      setSubmitted(true)
      setLoading(false)
    }, 500)
  }

  if (submitted) {
    return (
      <main className="public-shell">
        <div style={{ maxWidth: '600px', margin: '3rem auto', textAlign: 'center' }}>
          <Card>
            <p className="eyebrow">Contact us</p>
            <h1>Thanks for reaching out</h1>
            <p className="muted" style={{ marginBottom: '1.5rem' }}>
              Sales contact workflow is being configured. We'll respond within 24-48 hours.
            </p>
            <p className="muted" style={{ marginBottom: '1.5rem' }}>
              In the meantime, you can also reach us at <a href="mailto:sales@maisb.app" style={{ color: '#67e8f9' }}>sales@maisb.app</a>
            </p>
            <Button onClick={() => window.location.href = '/'}>
              Back to home
            </Button>
          </Card>
        </div>
      </main>
    )
  }

  return (
    <main className="public-shell">
      <div className="page-head">
        <div>
          <p className="eyebrow">Contact us</p>
          <h1>Enterprise sales & support</h1>
          <p className="muted">Tell us about your mobile AI security needs. Our team will get back to you within 24-48 hours.</p>
        </div>
      </div>

      <section style={{ maxWidth: '600px', margin: '0 auto' }}>
        <form className="glass-card" style={{ padding: '2rem' }} onSubmit={onSubmit}>
          <div className="form-grid" style={{ marginBottom: '1.5rem' }}>
            <div>
              <label style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.35rem', display: 'block' }}>
                Full name
              </label>
              <input
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="John Doe"
              />
            </div>
            <div>
              <label style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.35rem', display: 'block' }}>
                Email address
              </label>
              <input
                required
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="you@company.com"
              />
            </div>
            <div>
              <label style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.35rem', display: 'block' }}>
                Company name
              </label>
              <input
                required
                value={form.company}
                onChange={(e) => setForm({ ...form, company: e.target.value })}
                placeholder="Acme Corp"
              />
            </div>
            <div>
              <label style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.35rem', display: 'block' }}>
                Use case
              </label>
              <input
                required
                value={form.use_case}
                onChange={(e) => setForm({ ...form, use_case: e.target.value })}
                placeholder="e.g., Mobile banking AI, FinTech assistant"
              />
            </div>
            <div style={{ gridColumn: '1 / -1' }}>
              <label style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.35rem', display: 'block' }}>
                Message
              </label>
              <textarea
                required
                value={form.message}
                onChange={(e) => setForm({ ...form, message: e.target.value })}
                placeholder="Tell us about your mobile AI security needs, team size, and timeline..."
                style={{ minHeight: '120px', fontFamily: 'inherit', resize: 'vertical' }}
              />
            </div>
          </div>

          <Button type="submit" disabled={loading} style={{ width: '100%', marginBottom: '1rem' }}>
            {loading ? 'Sending…' : 'Send message'}
          </Button>

          <div style={{ textAlign: 'center' }}>
            <p className="muted" style={{ fontSize: '0.9rem' }}>
              Or email directly: <a href="mailto:sales@maisb.app" style={{ color: '#67e8f9' }}>sales@maisb.app</a>
            </p>
          </div>
        </form>
      </section>

      {/* Additional Info */}
      <section style={{ marginTop: '3rem' }}>
        <div className="grid two-col">
          <Card title="Enterprise SSO" subtitle="Google Workspace, Microsoft Entra ID, Okta/SAML">
            <p className="muted" style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>
              Enterprise plans include dedicated SSO integration and custom authentication workflows.
            </p>
            <p className="muted" style={{ fontSize: '0.9rem' }}>
              Ask about SSO support in your message above.
            </p>
          </Card>

          <Card title="Custom Integration" subtitle="White-label options, webhooks, API extensions">
            <p className="muted" style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>
              Enterprise customers get custom integration support for your security infrastructure.
            </p>
            <p className="muted" style={{ fontSize: '0.9rem' }}>
              Contact sales to discuss your integration requirements.
            </p>
          </Card>

          <Card title="SLA & Support" subtitle="24/7 support, dedicated account manager">
            <p className="muted" style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>
              Enterprise plans include SLA guarantees, priority support, and quarterly security reviews.
            </p>
            <p className="muted" style={{ fontSize: '0.9rem' }}>
              Let's discuss your support needs.
            </p>
          </Card>

          <Card title="Data Residency" subtitle="Regional deployment options">
            <p className="muted" style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>
              Enterprise customers can request regional deployments and data residency options.
            </p>
            <p className="muted" style={{ fontSize: '0.9rem' }}>
              Mention your data residency requirements in your message.
            </p>
          </Card>
        </div>
      </section>
    </main>
  )
}
