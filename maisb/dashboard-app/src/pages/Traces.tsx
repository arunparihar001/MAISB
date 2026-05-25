import { useEffect, useState } from 'react'
import Badge from '../components/Badge'
import Card from '../components/Card'
import TraceTimeline from '../components/TraceTimeline'
import { apiRequest } from '../lib/api'

type Trace = {
  trace_id: string
  channels: string[]
  trust_score?: number
  trust_degradation?: number
  degradation_score?: number
  final_decision?: string
  created_at?: string
}

export default function Traces() {
  const [traces, setTraces] = useState<Trace[]>([])

  useEffect(() => {
    apiRequest<{ traces: Trace[] }>('/v1/dashboard/traces')
      .then((data) => setTraces(data.traces || []))
      .catch(() => setTraces([]))
  }, [])

  return (
    <main className="stack">
      <div className="page-head">
        <div>
          <p className="eyebrow">Traceability</p>
          <h1>Cross-Channel Trace</h1>
          <p className="muted">Single-channel tools miss attacks that become dangerous across mobile context.</p>
        </div>
        <Badge>Sample data</Badge>
      </div>
      <Card title="Trace model" subtitle="Sequence-level risk narrative">
        <p className="muted">MAISB tracks how mobile context accumulates before the LLM acts. Every trace shows channel lineage, trust degradation, and the final verdict.</p>
      </Card>
      <TraceTimeline traces={traces.slice(0, 20)} />
    </main>
  )
}
