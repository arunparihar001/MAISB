type Props = {
  apiKeyMasked: string
}

export default function ApiKeyCard({ apiKeyMasked }: Props) {
  return (
    <div className="card">
      <h3>Current API Key</h3>
      <code>{apiKeyMasked || 'Not available'}</code>
    </div>
  )
}
