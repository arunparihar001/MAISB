type Props = { apiKeyMasked: string }

export default function ApiKeyCard({ apiKeyMasked }: Props) {
  return (
    <div className="card">
      <h3>Current API Key</h3>
      <code>{apiKeyMasked || 'Not available'}</code>
      <p className="muted">Raw API keys are only shown once during signup. Store them securely.</p>
    </div>
  )
}
