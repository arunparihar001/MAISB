const DECISIONS = [
  {
    id: 'blocked',
    label: 'BLOCKED',
    body: 'High-risk input is stopped before it reaches the model. Your app should prevent execution and log the security event.',
  },
  {
    id: 'review',
    label: 'REVIEW',
    body: 'Suspicious context is flagged for human or policy review. Queue the input before allowing model access.',
  },
  {
    id: 'allowed',
    label: 'ALLOWED',
    body: 'Input passes the runtime boundary check. Proceed to model execution with trace metadata attached.',
  },
]

export default function DecisionCards() {
  return (
    <div className="mkt-decisions">
      {DECISIONS.map((item) => (
        <article key={item.id} className={`mkt-decisions__card mkt-decisions__card--${item.id}`}>
          <span className="mkt-decisions__label">{item.label}</span>
          <p className="muted">{item.body}</p>
        </article>
      ))}
    </div>
  )
}
