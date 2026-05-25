import { Link } from 'react-router-dom'
import Button from '../components/Button'
import Card from '../components/Card'
import Badge from '../components/Badge'

export default function Blog() {
  const posts = [
    {
      id: 'mobile-ai-boundary',
      title: 'Why Mobile AI Agents Need Boundary Security',
      excerpt: 'Mobile channels (clipboard, QR codes, notifications, deep links) are untrusted boundaries. Traditional security tools miss attacks at this layer.',
      date: 'Coming soon',
      category: 'Security',
      featured: true,
    },
    {
      id: 'prompt-injection-mobile',
      title: 'Cross-Channel Prompt Injection in Mobile Workflows',
      excerpt: 'Sophisticated attackers chain multiple channels to form complete malicious instructions. Learn how context correlation detects these attacks.',
      date: 'Coming soon',
      category: 'Threat Intelligence',
      featured: true,
    },
    {
      id: 'metadata-security-events',
      title: 'Designing Metadata-Only Security Events for AI Runtime Risk',
      excerpt: 'How to audit AI security without storing raw payloads. A design pattern for compliance-ready threat detection.',
      date: 'Coming soon',
      category: 'Engineering',
      featured: true,
    },
  ]

  return (
    <main className="public-shell">
      <div className="page-head">
        <div>
          <p className="eyebrow">Blog</p>
          <h1>Mobile AI Security Research</h1>
          <p className="muted">Thoughts on securing mobile AI agents from channel-based attacks.</p>
        </div>
        <Link to="/"><Button variant="secondary">Back home</Button></Link>
      </div>

      {/* Featured Posts */}
      <section style={{ marginBottom: '3rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <p className="eyebrow">Editorial preview</p>
          <h2>Featured articles (coming soon)</h2>
        </div>

        <div style={{ display: 'grid', gap: '1.5rem' }}>
          {posts.map((post) => (
            <Card key={post.id} title={post.title} subtitle={post.category}>
              <p className="muted" style={{ marginBottom: '1rem', minHeight: '2rem' }}>{post.excerpt}</p>
              <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <Badge>{post.date}</Badge>
                </div>
                <div>
                  <Button variant="secondary" disabled>Read article →</Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* Subscription */}
      <section style={{ textAlign: 'center', marginTop: '3rem' }}>
        <Card title="Stay updated" subtitle="Get notified when new articles are published">
          <p className="muted" style={{ marginBottom: '1rem' }}>
            Articles on mobile AI security, boundary protection patterns, and threat research are being prepared.
          </p>
          <p className="muted">
            Email <a href="mailto:research@maisb.app">research@maisb.app</a> to get on the research notification list.
          </p>
        </Card>
      </section>

      {/* Topics */}
      <section style={{ marginTop: '3rem', textAlign: 'center' }}>
        <h2>Topics we're researching</h2>
        <p className="muted" style={{ marginBottom: '1.5rem' }}>
          Articles on these subjects coming soon:
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          <div style={{ padding: '1rem', borderRadius: '8px', border: '1px solid #334155', backgroundColor: 'rgba(30, 41, 59, 0.5)' }}>
            <p style={{ fontSize: '0.9rem', color: '#cbd5e1', margin: 0 }}>Mobile channel threat vectors</p>
          </div>
          <div style={{ padding: '1rem', borderRadius: '8px', border: '1px solid #334155', backgroundColor: 'rgba(30, 41, 59, 0.5)' }}>
            <p style={{ fontSize: '0.9rem', color: '#cbd5e1', margin: 0 }}>Prompt injection detection techniques</p>
          </div>
          <div style={{ padding: '1rem', borderRadius: '8px', border: '1px solid #334155', backgroundColor: 'rgba(30, 41, 59, 0.5)' }}>
            <p style={{ fontSize: '0.9rem', color: '#cbd5e1', margin: 0 }}>Cross-channel trace correlation</p>
          </div>
          <div style={{ padding: '1rem', borderRadius: '8px', border: '1px solid #334155', backgroundColor: 'rgba(30, 41, 59, 0.5)' }}>
            <p style={{ fontSize: '0.9rem', color: '#cbd5e1', margin: 0 }}>LLM context poisoning</p>
          </div>
          <div style={{ padding: '1rem', borderRadius: '8px', border: '1px solid #334155', backgroundColor: 'rgba(30, 41, 59, 0.5)' }}>
            <p style={{ fontSize: '0.9rem', color: '#cbd5e1', margin: 0 }}>Boundary protection patterns</p>
          </div>
          <div style={{ padding: '1rem', borderRadius: '8px', border: '1px solid #334155', backgroundColor: 'rgba(30, 41, 59, 0.5)' }}>
            <p style={{ fontSize: '0.9rem', color: '#cbd5e1', margin: 0 }}>Mobile security architecture</p>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section style={{ textAlign: 'center', marginTop: '3rem' }}>
        <h2>Ready to protect your AI agents?</h2>
        <p className="hero-lead" style={{ maxWidth: '60ch', margin: '1rem auto' }}>
          Start with free tier to evaluate MAISB with sample data and see mobile AI security in action.
        </p>
        <div className="row-inline" style={{ justifyContent: 'center' }}>
          <Link to="/signup"><Button>Get started free</Button></Link>
          <a href="mailto:research@maisb.app"><Button variant="secondary">Join research list</Button></a>
        </div>
      </section>
    </main>
  )
}
