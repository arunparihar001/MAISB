export default function ApiKeyCard({ masked }: { masked: string }) {
  return <div className="card"><p>Active API Key</p><h3>{masked || 'Not connected'}</h3></div>
}
