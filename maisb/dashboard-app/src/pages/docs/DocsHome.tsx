import { Link } from 'react-router-dom'
import DocsLayout from '../../components/docs/DocsLayout'

export default function DocsHome() {
  return (
    <DocsLayout
      title="MAISB Documentation"
      description="Integrate runtime mobile AI security boundaries with the MAISB API, SDK guides, and integration examples."
    >
      <div className="docs-links">
        <Link to="/docs/api" className="docs-links__item">
          <strong>API Reference</strong>
          <span className="muted">POST /v1/scan, authentication, and response schema</span>
        </Link>
        <Link to="/docs/sdk" className="docs-links__item">
          <strong>SDK Guides</strong>
          <span className="muted">Mobile integration patterns for iOS and Android</span>
        </Link>
        <Link to="/docs/examples" className="docs-links__item">
          <strong>Code Examples</strong>
          <span className="muted">curl, channel-specific scans, and decision handling</span>
        </Link>
      </div>
    </DocsLayout>
  )
}
