import Card from './Card'

type Trace = {
  trace_id: string
  channels: string[]
  trust_score?: number
  trust_degradation?: number
  degradation_score?: number
  final_decision?: string
  created_at?: string
}

export default function TraceTimeline({ traces }: { traces: Trace[] }) {
  return (
    <Card title="Cross-channel timeline">
      <div className="timeline">
        {traces.map((trace) => (
          <article key={trace.trace_id} className="timeline-item">
            <p>
              <strong>{trace.trace_id}</strong> · {(trace.final_decision || 'ALLOWED').toUpperCase()}
            </p>
            <p className="muted">{trace.channels.join(' → ') || 'No channels recorded'}</p>
            <p className="muted">
              Trust {(trace.trust_score ?? 0).toFixed(2)} · Degradation {((trace.trust_degradation ?? trace.degradation_score) ?? 0).toFixed(2)}
            </p>
            <small className="muted">{trace.created_at || '—'}</small>
          </article>
        ))}
      </div>
    </Card>
  )
}
