export default function ApiKeyCard({ keyMasked }: { keyMasked: string }) {
  return (
    <div className="card">
      <h3>Current API Key</h3>
      <p className="mono">{keyMasked || 'No key available'}</p>
      <p className="muted">Raw keys are only returned one time at signup. Store them securely.</p>
    </div>
  )
}
