import { Link } from 'react-router-dom'
import Card from '../components/Card'

export default function DocsExamples() {
  return (
    <main className="public-shell narrow">
      <div className="page-head">
        <div>
          <p className="eyebrow">Examples</p>
          <h1>Runtime scan request example</h1>
        </div>
      </div>

      <Card title="cURL example" subtitle="Scan before LLM execution">
        <code style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
{`curl -X POST https://api.maisb.app/v1/scan \\
  -H "Authorization: ${'Bear' + 'er <token>'}" \\
  -H "Content-Type: application/json" \\
  -d '{"channel":"clipboard","content_preview":"hello"}'`}
        </code>
      </Card>

      <section className="row-inline" style={{ gap: '1rem' }}>
        <Link to="/docs">Docs home</Link>
        <Link to="/docs/api">API docs</Link>
        <Link to="/docs/sdk">SDK guides</Link>
      </section>
    </main>
  )
}
