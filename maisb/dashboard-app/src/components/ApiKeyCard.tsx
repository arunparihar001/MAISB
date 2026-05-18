type ApiKeyCardProps = {
  maskedKey: string
  plan: string
  created?: string
}

export default function ApiKeyCard({ maskedKey, plan, created }: ApiKeyCardProps) {
  return (
    <section className="card">
      <h3>Active API Key</h3>
      <p className="mono">{maskedKey}</p>
      <p className="muted">Plan: {plan}</p>
      {created ? <p className="muted">Created: {created}</p> : null}
    </section>
  )
}
